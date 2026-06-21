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
            # Extract trace_id from Kafka record headers
            headers = dict(msg.headers or [])
            trace_id = headers.get('trace_id', b'').decode('utf-8') or msg.value.get('trace_id', '')

            event = Event(**msg.value)
            print(f"trace_id={trace_id} event_id={event.id} Received event")
            self.handle_event(event, trace_id=trace_id)

    def handle_event(self, event: Event, trace_id: str = ''):
        # Example: Brute Force Attack detection
        if event.type == "login_failed":
            key = event.metadata.get("ip")
            now = datetime.now()
            self.event_window[key] = [e for e in self.event_window[key] if (now - e.timestamp).total_seconds() < self.window_seconds]
            self.event_window[key].append(event)
            if len(self.event_window[key]) >= self.failed_login_threshold:
                self.create_incident(event, self.event_window[key], trace_id=trace_id)
                self.event_window[key] = []  # reset after incident

    def create_incident(self, event: Event, events, trace_id: str = ''):
        incident = Incident(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            events=[e.id for e in events],
            status="open",
            summary=f"Brute Force Attack: {len(events)} failed logins from {event.metadata.get('ip')}",
            owner="auto-assigned"
        )
        # Push to Kafka Topic 3 with trace_id
        incident_data = incident.dict()
        incident_data['trace_id'] = trace_id
        kafka_headers = [('trace_id', trace_id.encode('utf-8'))]
        self.producer.send(self.incident_topic, incident_data, headers=kafka_headers)
        # Store in DynamoDB
        self.store.save_incident(incident)
        print(f"trace_id={trace_id} incident_id={incident.id} Incident created: {incident.summary}")
