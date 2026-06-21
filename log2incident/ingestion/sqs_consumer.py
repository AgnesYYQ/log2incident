
from log2incident.models import RawLog
from config.config import get_aws_region, get_sqs_queue_url
import json
import uuid
from datetime import datetime


class SQSConsumer:
    def __init__(self):
        # SQS client is used for queueing, not for log shipping. No direct log push to CloudWatch here.
        import boto3
        self.sqs = boto3.client('sqs', region_name=get_aws_region())
        self.queue_url = get_sqs_queue_url()

    def consume_logs(self):
        response = self.sqs.receive_message(QueueUrl=self.queue_url, MaxNumberOfMessages=10)
        messages = response.get('Messages', [])
        logs = []
        for msg in messages:
            body = json.loads(msg['Body'])
            log = RawLog(
                id=body['id'],
                timestamp=datetime.fromisoformat(body['timestamp']),
                source=body['source'],
                message=body['message'],
                trace_id=body.get('trace_id') or str(uuid.uuid4()),
                metadata=body.get('metadata', {})
            )
            logs.append(log)
            # Delete message after processing
            self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=msg['ReceiptHandle'])
        return logs