import os
import uuid
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict
from kafka import KafkaConsumer, KafkaProducer
from log2incident.models import Event, Incident
from log2incident.storage.event_incident_store import EventIncidentStore

class IncidentCreatorService:
    def __init__(self):
        self.kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.event_topic = os.getenv("KAFKA_EVENT_TOPIC", "log2incident-events")
        self.incident_topic = os.getenv("KAFKA_INCIDENT_TOPIC", "log2incident-incidents")
        self.consumer = KafkaConsumer(
            self.event_topic,
            bootstrap_servers=self.kafka_bootstrap,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id=os.getenv("KAFKA_INCIDENT_CREATOR_GROUP", "incident-creator-group")
        )
        self.producer = KafkaProducer(
            bootstrap_servers=self.kafka_bootstrap,
            value_serializer=lambda m: json.dumps(m).encode('utf-8')
        )
        self.event_window = defaultdict(list)  # {key: [event, ...]}
        self.window_seconds = int(os.getenv("INCIDENT_WINDOW_SECONDS", "60"))
        self.failed_login_threshold = int(os.getenv("INCIDENT_FAILED_LOGIN_THRESHOLD", "10"))
        self.store = EventIncidentStore()

    def run(self):
        print("Incident Creator Service started. Waiting for events...")
        for msg in self.consumer:
            event = Event(**msg.value)
            self.handle_event(event)

    def handle_event(self, event: Event):
        # Example: Brute Force Attack detection
        if event.type == "login_failed":
            key = event.metadata.get("ip")
            now = datetime.now()
            self.event_window[key] = [e for e in self.event_window[key] if (now - e.timestamp).total_seconds() < self.window_seconds]
            self.event_window[key].append(event)
            if len(self.event_window[key]) >= self.failed_login_threshold:
                self.create_incident(event, self.event_window[key])
                self.event_window[key] = []  # reset after incident

    def create_incident(self, event: Event, events):
        incident = Incident(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            events=[e.id for e in events],
            status="open",
            summary=f"Brute Force Attack: {len(events)} failed logins from {event.metadata.get('ip')}",
            owner="auto-assigned"
        )
        # Push to Kafka Topic 3
        self.producer.send(self.incident_topic, incident.dict())
        # Store in DynamoDB
        self.store.save_incident(incident)
        print(f"Incident created: {incident.summary}")
