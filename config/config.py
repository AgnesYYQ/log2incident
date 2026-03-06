import os
from dotenv import load_dotenv

load_dotenv()

def get_aws_region():
    return os.getenv('AWS_REGION', 'us-east-1')

def get_sqs_queue_url():
    return os.getenv('SQS_QUEUE_URL')

def get_s3_bucket():
    return os.getenv('S3_BUCKET')

def get_flink_master():
    return os.getenv('FLINK_MASTER', 'localhost:8081')