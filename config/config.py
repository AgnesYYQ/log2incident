import os
import json
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


def get_dynamodb_rules_table():
    return os.getenv('DYNAMODB_RULES_TABLE')


def get_redis_url():
    return os.getenv('REDIS_URL', 'redis://localhost:6379/0')


def get_postgres_dsn():
    return os.getenv(
        'POSTGRES_DSN',
        'postgresql://postgres:postgres@localhost:5432/log2incident'
    )


def get_frontend_origin():
    return os.getenv('FRONTEND_ORIGIN', 'http://localhost:5173')


def get_auth_users():
    default_users = {
        'admin': 'admin123',
        'demo': 'demo123'
    }
    raw = os.getenv('AUTH_USERS_JSON')
    if not raw:
        return default_users
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and parsed:
            return {str(k): str(v) for k, v in parsed.items()}
    except json.JSONDecodeError:
        pass
    return default_users