import boto3
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


class LogReceiver:
    """Receives logs and sends them to Kinesis for processing."""

    def __init__(self):
        self.kinesis = boto3.client('kinesis', region_name=get_aws_region())
        self.stream_name = get_kinesis_stream_name()
        self.logger = logging.getLogger("log_receiver")
        self.logger.setLevel(logging.INFO)
        if _WATCHTOWER_AVAILABLE:
            # Use a custom formatter for JSON logs
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

    def receive_and_queue_log(self, log_data: dict) -> str:
        """
        Receive a log entry and queue it to Kinesis.

        Args:
            log_data: Dictionary containing log information.
                     Must include: source, message
                     Optional: id, timestamp, metadata

        Returns:
            The sequence number of the Kinesis record.
        """
        # Generate ID and timestamp if not provided
        log_id = log_data.get('id', str(uuid.uuid4()))
        # Client-provided or generated event time
        timestamp = log_data.get('timestamp', datetime.now(timezone.utc).isoformat())
        # Server receive time for age tracking
        server_receive_time = datetime.now(timezone.utc).isoformat()
        source = log_data.get('source', 'unknown')
        message = log_data.get('message', '')
        metadata = log_data.get('metadata', {})

        # Create RawLog model to validate data
        raw_log = RawLog(
            id=log_id,
            timestamp=timestamp if isinstance(timestamp, datetime) else datetime.fromisoformat(timestamp),
            source=source,
            message=message,
            metadata=metadata
        )

        # Send to Kinesis
        record_data = {
            'id': raw_log.id,
            'timestamp': raw_log.timestamp.isoformat(),
            'server_receive_time': server_receive_time,
            'source': raw_log.source,
            'message': raw_log.message,
            'metadata': raw_log.metadata
        }

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
