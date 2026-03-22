
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
        if _WATCHTOWER_AVAILABLE:
            handler = watchtower.CloudWatchLogHandler(log_group="log2incident-log-receiver")
            class JsonFormatter(logging.Formatter):
                def format(self, record):
                    log_record = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "level": record.levelname,
                        "logger": record.name,
                        "message": record.getMessage(),
                    }
                    if hasattr(record, 'extra_data'):
                        log_record.update(record.extra_data)
                    return json.dumps(log_record)
            handler.setFormatter(JsonFormatter())
            self.logger.addHandler(handler)

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

    def receive_and_queue_log(self, log_data: dict) -> str:
        """
        Receive a log entry and queue it to Kinesis (AWS) or Event Hubs (Azure).

        Args:
            log_data: Dictionary containing log information.
                     Must include: source, message
                     Optional: id, timestamp, metadata

        Returns:
            The sequence number (AWS) or message ID (Azure) of the record.
        """
        log_id = log_data.get('id', str(uuid.uuid4()))
        timestamp = log_data.get('timestamp', datetime.now(timezone.utc).isoformat())
        server_receive_time = datetime.now(timezone.utc).isoformat()
        source = log_data.get('source', 'unknown')
        message = log_data.get('message', '')
        metadata = log_data.get('metadata', {})

        raw_log = RawLog(
            id=log_id,
            timestamp=timestamp if isinstance(timestamp, datetime) else datetime.fromisoformat(timestamp),
            source=source,
            message=message,
            metadata=metadata
        )

        record_data = {
            'id': raw_log.id,
            'timestamp': raw_log.timestamp.isoformat(),
            'server_receive_time': server_receive_time,
            'source': raw_log.source,
            'message': raw_log.message,
            'metadata': raw_log.metadata
        }

        if self.cloud_provider == "aws":
            response = self.kinesis.put_record(
                StreamName=self.stream_name,
                Data=json.dumps(record_data),
                PartitionKey=raw_log.id
            )
            self.logger.info(
                f"Queued log to Kinesis",
                extra={"extra_data": record_data}
            )
            return response['SequenceNumber']
        elif self.cloud_provider == "azure":
            event_data = EventData(json.dumps(record_data))
            with self.eventhub_producer:
                self.eventhub_producer.send_batch([event_data])
            self.logger.info(
                f"Queued log to Azure Event Hubs",
                extra={"extra_data": record_data}
            )
            return raw_log.id  # Azure Event Hubs does not return a sequence number
        else:
            raise ValueError(f"Unsupported CLOUD_PROVIDER: {self.cloud_provider}")
