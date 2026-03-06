#!/usr/bin/env python3

from log2incident.ingestion.sqs_consumer import SQSConsumer
from log2incident.tagging.tagger import Tagger
from log2incident.storage.s3_uploader import S3Uploader
from log2incident.events.event_creator import EventCreator
from log2incident.incidents.incident_manager import IncidentManager

def main():
    consumer = SQSConsumer()
    tagger = Tagger()
    uploader = S3Uploader()
    event_creator = EventCreator()
    incident_manager = IncidentManager()

    # Consume logs
    raw_logs = consumer.consume_logs()

    for log in raw_logs:
        # Tag
        tagged_log = tagger.tag_log(log)
        # Upload
        uploader.upload_log(tagged_log)
        # Create event (in real, this would be in Flink)
        event = event_creator.create_event(tagged_log)
        # Process incident
        incident_manager.process_event(event)

    print(f"Processed {len(raw_logs)} logs")

if __name__ == "__main__":
    main()