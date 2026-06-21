import os
import json
import logging
from kafka import KafkaConsumer, KafkaProducer
from log2incident.models import TaggedLog
from log2incident.storage.s3_uploader import S3Uploader
from typing import List

class ETLFilterService:
    """
    Service to apply ETL filter logic to logs. Consumes S3 keys from Kafka, loads logs from S3, applies filter, and publishes filtered S3 keys to Kafka.
    """
    def __init__(self, filter_rules=None):
        self.logger = logging.getLogger("etl_filter_service")
        self.filter_rules = filter_rules or self.default_rules()
        self.s3_uploader = S3Uploader()
        self.kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.input_topic = os.getenv("KAFKA_LOG_TOPIC", "log2incident-logs")
        self.output_topic = os.getenv("KAFKA_FILTERED_TOPIC", "log2incident-filtered")
        self.consumer = KafkaConsumer(
            self.input_topic,
            bootstrap_servers=self.kafka_bootstrap,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id=os.getenv("KAFKA_ETL_GROUP", "etl-filter-group")
        )
        self.producer = KafkaProducer(
            bootstrap_servers=self.kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def default_rules(self):
        # Example: Only pass logs with 'error' or 'warning' tags
        return {"tags": ["error", "warning"]}

    def filter_log(self, log: TaggedLog) -> bool:
        allowed_tags = set(self.filter_rules.get("tags", []))
        return bool(allowed_tags.intersection(set(log.tags)))

    def run(self):
        self.logger.info(f"ETLFilterService started, listening to topic: {self.input_topic}")
        for msg in self.consumer:
            s3_key = msg.value['s3_key']
            log_id = msg.value['log_id']
            # Extract trace_id from Kafka record headers
            headers = dict(msg.headers or [])
            trace_id = headers.get('trace_id', b'').decode('utf-8') or msg.value.get('trace_id', '')

            log_data = self.s3_uploader.download_log(s3_key)
            log = TaggedLog(**log_data)
            if self.filter_log(log):
                kafka_message = {
                    's3_key': s3_key,
                    'log_id': log_id,
                    'tags': log.tags,
                    'trace_id': trace_id,
                }
                kafka_headers = [('trace_id', trace_id.encode('utf-8'))]
                self.producer.send(self.output_topic, kafka_message, headers=kafka_headers)
                self.logger.info("trace_id=%s log_id=%s Passed filter and published to %s", trace_id, log_id, self.output_topic)
            else:
                self.logger.info("trace_id=%s log_id=%s Did not pass filter", trace_id, log_id)
        self.producer.flush()
