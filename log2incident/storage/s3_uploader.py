
from log2incident.models import TaggedLog
from config.config import get_aws_region, get_s3_bucket
import json


class S3Uploader:
    def __init__(self):
        # S3 client is used for log storage, not for log shipping to CloudWatch/Elasticsearch.
        import boto3
        self.s3 = boto3.client('s3', region_name=get_aws_region())
        self.bucket = get_s3_bucket()

    def upload_log(self, log: TaggedLog):
        key = f"logs/{log.id}.json"
        data = log.model_dump_json()
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=data)

    def download_log(self, key: str) -> dict:
        response = self.s3.get_object(Bucket=self.bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)