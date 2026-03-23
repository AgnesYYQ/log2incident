import os
import json
import logging
from kafka import KafkaConsumer
from log2incident.models import TaggedLog
from log2incident.storage.s3_uploader import S3Uploader
from log2incident.model_matching.model_matcher import ModelMatcher

class ModelMatchingService:
    """
    Consumes filtered S3 keys from Kafka, loads logs from S3, applies model/rule matching, and creates events/incidents.
    """
    def __init__(self):
        self.logger = logging.getLogger("model_matching_service")
        self.s3_uploader = S3Uploader()
        self.kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.input_topic = os.getenv("KAFKA_FILTERED_TOPIC", "log2incident-filtered")
        self.consumer = KafkaConsumer(
            self.input_topic,
            bootstrap_servers=self.kafka_bootstrap,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id=os.getenv("KAFKA_MM_GROUP", "model-matching-group")
        )
        self.model_matcher = ModelMatcher()
        from log2incident.storage.event_incident_store import EventIncidentStore
        self.store = EventIncidentStore()

    def run(self):
        self.logger.info(f"ModelMatchingService started, listening to topic: {self.input_topic}")
        for msg in self.consumer:
            s3_key = msg.value['s3_key']
            log_id = msg.value['log_id']
            log_data = self.s3_uploader.download_log(s3_key)
            log = TaggedLog(**log_data)
            events = self.model_matcher.match([log])
            for event in events:
                self.logger.info(f"Created event {event.id} from log {log_id}")
                self.store.save_event(event)
            # Incident aggregation (example: one incident per event)
            from log2incident.incidents.incident_manager import IncidentManager
            incident_manager = IncidentManager()
            for event in events:
                incident_manager.process_event(event)
                if incident_manager.incidents:
                    incident = incident_manager.incidents[-1]
                    self.store.save_incident(incident)
