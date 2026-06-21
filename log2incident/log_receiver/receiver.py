
import os
import json
import uuid
from datetime import datetime, timezone
from log2incident.models import RawLog
from config.config import get_aws_region, get_kinesis_stream_name
import logging
try:
    import watchtower
    _WATCHTOWER_AVAILABLE = True
except ImportError:
    _WATCHTOWER_AVAILABLE = False

# Azure Event Hubs
try:
    from azure.eventhub import EventHubProducerClient, EventData
    _AZURE_EVENTHUB_AVAILABLE = True
except ImportError:
    _AZURE_EVENTHUB_AVAILABLE = False



class LogReceiver:
    """Receives logs and sends them to Kinesis (AWS) or Event Hubs (Azure) for processing."""

    def __init__(self):
        self.cloud_provider = os.getenv("CLOUD_PROVIDER", "aws").lower()
        self.logger = logging.getLogger("log_receiver")
        self.logger.setLevel(logging.INFO)
        # Removed Watchtower/CloudWatch log handler. Logs will be written to stdout/stderr only.
        # Removed direct log push to Elasticsearch. Use DaemonSets for log shipping.
        if self.cloud_provider == "aws":
            import boto3
            self.kinesis = boto3.client('kinesis', region_name=get_aws_region())
            self.stream_name = get_kinesis_stream_name()
        elif self.cloud_provider == "azure":
            if not _AZURE_EVENTHUB_AVAILABLE:
                raise ImportError("azure-eventhub package is required for Azure support.")
            self.eventhub_conn_str = os.getenv("AZURE_EVENT_HUB_CONNECTION_STRING")
            self.eventhub_name = os.getenv("AZURE_EVENT_HUB_NAME", "log2incident-eventhub")
            if not self.eventhub_conn_str:
                raise ValueError("AZURE_EVENT_HUB_CONNECTION_STRING must be set for Azure Event Hubs.")
            self.eventhub_producer = EventHubProducerClient.from_connection_string(
                conn_str=self.eventhub_conn_str, eventhub_name=self.eventhub_name
            )
        else:
            raise ValueError(f"Unsupported CLOUD_PROVIDER: {self.cloud_provider}")

    def receive_and_queue_log(self, log_data: dict, trace_id: str | None = None) -> str:
        """
        Receive a log entry, enrich it, store in S3, and publish S3 key to Kafka.

        Args:
            log_data: Dictionary containing log information.
                     Must include: source, message
                     Optional: id, timestamp, metadata
            trace_id: Distributed tracing ID for correlating this log across services.

        Returns:
            The S3 key of the stored log.
        """
        from log2incident.tagging.tagger import Tagger
        from log2incident.storage.s3_uploader import S3Uploader
        from kafka import KafkaProducer
        tagger = Tagger()
        s3_uploader = S3Uploader()
        producer = KafkaProducer(bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
                                 value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        kafka_topic = os.getenv("KAFKA_LOG_TOPIC", "log2incident-logs")

        # Normalization and enrichment
        log_id = log_data.get('id', str(uuid.uuid4()))
        timestamp = log_data.get('timestamp', datetime.now(timezone.utc).isoformat())
        source = log_data.get('source', 'unknown').strip().lower()
        message = log_data.get('message', '').strip()
        metadata = log_data.get('metadata', {})
        metadata['received_by'] = 'log_receiver'
        metadata['normalized'] = True
        if trace_id:
            metadata['trace_id'] = trace_id

        raw_log = RawLog(
            id=log_id,
            timestamp=timestamp if isinstance(timestamp, datetime) else datetime.fromisoformat(timestamp),
            source=source,
            message=message,
            trace_id=trace_id,
            metadata=metadata
        )

        # Basic tagging
        tagged_log = tagger.tag_log(raw_log)

        # Store in S3 (trace_id is embedded in the JSON via the model)
        s3_uploader.upload_log(tagged_log)
        s3_key = f"logs/{tagged_log.id}.json"

        # Publish S3 key to Kafka with trace_id in both headers and body
        kafka_message = {
            's3_key': s3_key,
            'log_id': tagged_log.id,
            'timestamp': tagged_log.timestamp.isoformat(),
            'tags': tagged_log.tags,
            'trace_id': trace_id or '',
        }
        kafka_headers = [('trace_id', (trace_id or '').encode('utf-8'))]
        producer.send(kafka_topic, kafka_message, headers=kafka_headers)
        producer.flush()
        self.logger.info("trace_id=%s log_id=%s Enriched log stored in S3 and published to Kafka", trace_id, tagged_log.id)
        return s3_key
