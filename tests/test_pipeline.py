import json
import importlib
from datetime import datetime
import boto3
from moto import mock_aws
import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from log2incident.models import RawLog, TaggedLog, Event, Incident
from log2incident.ingestion.sqs_consumer import SQSConsumer
from log2incident.tagging.tagger import Tagger
from log2incident.storage.s3_uploader import S3Uploader
from log2incident.events.event_creator import EventCreator
from log2incident.incidents.incident_manager import IncidentManager
from config.config import get_aws_region


@mock_aws
def test_sqs_consumer_consume_logs(monkeypatch):
    # set up fake queue
    sqs = boto3.client('sqs', region_name=get_aws_region())
    queue = sqs.create_queue(QueueName='test-queue')
    url = queue['QueueUrl']
    monkeypatch.setenv('SQS_QUEUE_URL', url)

    body = {
        'id': '1',
        'timestamp': datetime.now().isoformat(),
        'source': 'test',
        'message': 'hello',
    }
    sqs.send_message(QueueUrl=url, MessageBody=json.dumps(body))

    consumer = SQSConsumer()
    logs = consumer.consume_logs()
    assert len(logs) == 1
    assert isinstance(logs[0], RawLog)
    assert logs[0].message == 'hello'


def test_tagger_tag_log():
    tagger = Tagger()
    raw = RawLog(id='2', timestamp=datetime.now(), source='s', message='ERROR occurred')
    tagged = tagger.tag_log(raw)
    assert isinstance(tagged, TaggedLog)
    assert 'error' in tagged.tags


@mock_aws
def test_tagger_loads_rules_from_dynamodb(monkeypatch):
    dynamodb = boto3.client('dynamodb', region_name=get_aws_region())
    table_name = 'tag-rules'
    dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{'AttributeName': 'tag', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'tag', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST',
    )
    dynamodb.put_item(
        TableName=table_name,
        Item={
            'tag': {'S': 'critical'},
            'keywords': {'L': [{'S': 'SEV1'}, {'S': 'OUTAGE'}]},
        },
    )
    monkeypatch.setenv('DYNAMODB_RULES_TABLE', table_name)

    tagger = Tagger()
    raw = RawLog(id='2b', timestamp=datetime.now(), source='s', message='SEV1 incident')
    tagged = tagger.tag_log(raw)
    assert 'critical' in tagged.tags


@mock_aws
def test_s3_uploader_upload_log(monkeypatch):
    # create bucket
    s3 = boto3.client('s3', region_name=get_aws_region())
    bucket = 'test-bucket'
    s3.create_bucket(Bucket=bucket)
    monkeypatch.setenv('S3_BUCKET', bucket)

    uploader = S3Uploader()
    tagged = TaggedLog(id='3', timestamp=datetime.now(), source='s', message='INFO', tags=['info'])
    uploader.upload_log(tagged)

    objs = s3.list_objects_v2(Bucket=bucket)
    assert objs['KeyCount'] == 1
    key = objs['Contents'][0]['Key']
    assert key == "logs/3.json"


@mock_aws
def test_end_to_end_raw_log_to_incident(monkeypatch):
    """Test full pipeline: raw log -> SQS -> tag -> S3 -> event -> incident"""
    
    # Setup SQS
    sqs = boto3.client('sqs', region_name=get_aws_region())
    queue = sqs.create_queue(QueueName='test-queue')
    queue_url = queue['QueueUrl']
    monkeypatch.setenv('SQS_QUEUE_URL', queue_url)

    # Setup S3
    s3 = boto3.client('s3', region_name=get_aws_region())
    bucket = 'test-bucket'
    s3.create_bucket(Bucket=bucket)
    monkeypatch.setenv('S3_BUCKET', bucket)

    # Send raw log with ERROR (high severity)
    raw_log_data = {
        'id': 'log-001',
        'timestamp': datetime.now().isoformat(),
        'source': 'app-server',
        'message': 'ERROR: Database connection failed'
    }
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(raw_log_data))

    # Step 1: Consume raw log from SQS
    consumer = SQSConsumer()
    raw_logs = consumer.consume_logs()
    assert len(raw_logs) == 1
    raw_log = raw_logs[0]
    assert raw_log.id == 'log-001'

    # Step 2: Tag the log
    tagger = Tagger()
    tagged_log = tagger.tag_log(raw_log)
    assert 'error' in tagged_log.tags

    # Step 3: Upload to S3
    uploader = S3Uploader()
    uploader.upload_log(tagged_log)
    objs = s3.list_objects_v2(Bucket=bucket)
    assert objs['KeyCount'] == 1

    # Step 4: Create event from tagged log
    event_creator = EventCreator()
    event = event_creator.create_event(tagged_log)
    assert isinstance(event, Event)
    assert event.log_id == 'log-001'
    assert event.severity == 'high'  # high because 'error' tag

    # Step 5: Create incident from event
    incident_manager = IncidentManager()
    incident_manager.process_event(event)
    assert len(incident_manager.incidents) == 1
    incident = incident_manager.incidents[0]
    assert isinstance(incident, Incident)
    assert incident.status == 'open'
    assert event.id in incident.events


@mock_aws
def test_accumulated_incident_creation(monkeypatch):
    """Test accumulated incident: need 3 events from same log"""
    
    # Setup SQS and S3
    sqs = boto3.client('sqs', region_name=get_aws_region())
    queue = sqs.create_queue(QueueName='test-queue')
    queue_url = queue['QueueUrl']
    monkeypatch.setenv('SQS_QUEUE_URL', queue_url)

    s3 = boto3.client('s3', region_name=get_aws_region())
    bucket = 'test-bucket'
    s3.create_bucket(Bucket=bucket)
    monkeypatch.setenv('S3_BUCKET', bucket)

    # Send raw log with WARNING (medium severity - won't trigger instant incident)
    raw_log_data = {
        'id': 'log-002',
        'timestamp': datetime.now().isoformat(),
        'source': 'app-server',
        'message': 'WARNING: Connection timeout'
    }
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(raw_log_data))

    consumer = SQSConsumer()
    raw_logs = consumer.consume_logs()
    raw_log = raw_logs[0]

    tagger = Tagger()
    tagged_log = tagger.tag_log(raw_log)

    uploader = S3Uploader()
    uploader.upload_log(tagged_log)

    event_creator = EventCreator()
    incident_manager = IncidentManager()

    # Create 3 events from same log
    for i in range(3):
        event = event_creator.create_event(tagged_log)
        incident_manager.process_event(event)

    # Should have 1 accumulated incident (created on 3rd event)
    assert len(incident_manager.incidents) == 1
    assert incident_manager.incidents[0].status == 'open'


@mock_aws
def test_api_gateway_log_receiver_end_to_end(monkeypatch):
    """Test API Gateway + LogReceiver path through to incident creation."""

    # Setup SQS and S3 infrastructure.
    sqs = boto3.client('sqs', region_name=get_aws_region())
    queue = sqs.create_queue(QueueName='test-queue-api-e2e')
    queue_url = queue['QueueUrl']
    monkeypatch.setenv('SQS_QUEUE_URL', queue_url)

    s3 = boto3.client('s3', region_name=get_aws_region())
    bucket = 'test-bucket-api-e2e'
    s3.create_bucket(Bucket=bucket)
    monkeypatch.setenv('S3_BUCKET', bucket)

    # Import after env setup because the module creates LogReceiver at import time.
    api_module = importlib.import_module('log2incident.api_gateway.app')
    api_module = importlib.reload(api_module)
    client = TestClient(api_module.app)

    payload = {
        'id': 'api-log-001',
        'source': 'api-client',
        'message': 'ERROR: Service unavailable',
        'metadata': {'request_id': 'req-1'}
    }
    response = client.post('/logs', json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body['success'] is True
    assert body['message_id']
    assert body['log_id'] == 'api-log-001'

    # Continue with the regular pipeline and verify incident creation.
    consumer = SQSConsumer()
    raw_logs = consumer.consume_logs()
    assert len(raw_logs) == 1
    assert raw_logs[0].id == 'api-log-001'

    tagger = Tagger()
    tagged_log = tagger.tag_log(raw_logs[0])
    assert 'error' in tagged_log.tags

    uploader = S3Uploader()
    uploader.upload_log(tagged_log)
    objs = s3.list_objects_v2(Bucket=bucket)
    assert objs['KeyCount'] == 1

    event_creator = EventCreator()
    event = event_creator.create_event(tagged_log)
    assert event.severity == 'high'

    incident_manager = IncidentManager()
    incident_manager.process_event(event)
    assert len(incident_manager.incidents) == 1
