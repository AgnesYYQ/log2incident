import boto3
import json
import uuid
from datetime import datetime
from log2incident.models import RawLog
from config.config import get_aws_region, get_sqs_queue_url


class LogReceiver:
    """Receives logs and sends them to SQS for processing."""
    
    def __init__(self):
        self.sqs = boto3.client('sqs', region_name=get_aws_region())
        self.queue_url = get_sqs_queue_url()
    
    def receive_and_queue_log(self, log_data: dict) -> str:
        """
        Receive a log entry and queue it to SQS.
        
        Args:
            log_data: Dictionary containing log information.
                     Must include: source, message
                     Optional: id, timestamp, metadata
        
        Returns:
            The message ID of the queued log.
        """
        # Generate ID and timestamp if not provided
        log_id = log_data.get('id', str(uuid.uuid4()))
        timestamp = log_data.get('timestamp', datetime.utcnow().isoformat())
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
        
        # Send to SQS
        message_body = {
            'id': raw_log.id,
            'timestamp': raw_log.timestamp.isoformat(),
            'source': raw_log.source,
            'message': raw_log.message,
            'metadata': raw_log.metadata
        }
        
        response = self.sqs.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(message_body)
        )
        
        return response['MessageId']
