

import os
import json
from typing import List
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
    from azure.eventhub import EventHubConsumerClient
    _AZURE_EVENTHUB_AVAILABLE = True
except ImportError:
    _AZURE_EVENTHUB_AVAILABLE = False

def fetch_raw_logs_from_kinesis(max_records: int = 100) -> List[RawLog]:
    """
    Fetch raw logs from the Kinesis stream (AWS) or Event Hubs (Azure).
    Args:
        max_records: Maximum number of records to fetch.
    Returns:
        List of RawLog objects.
    """
    logger = logging.getLogger("kinesis_consumer")
    logger.setLevel(logging.INFO)
    if _WATCHTOWER_AVAILABLE and not any(isinstance(h, watchtower.CloudWatchLogHandler) for h in logger.handlers):
        logger.addHandler(watchtower.CloudWatchLogHandler(log_group="log2incident-model-matching"))

    cloud_provider = os.getenv("CLOUD_PROVIDER", "aws").lower()
    records = []
    if cloud_provider == "aws":
        import boto3
        kinesis = boto3.client('kinesis', region_name=get_aws_region())
        stream_name = get_kinesis_stream_name()
        stream_desc = kinesis.describe_stream(StreamName=stream_name)
        shard_id = stream_desc['StreamDescription']['Shards'][0]['ShardId']
        shard_iterator = kinesis.get_shard_iterator(
            StreamName=stream_name,
            ShardId=shard_id,
            ShardIteratorType='TRIM_HORIZON'
        )['ShardIterator']
        while len(records) < max_records and shard_iterator:
            response = kinesis.get_records(ShardIterator=shard_iterator, Limit=min(100, max_records - len(records)))
            for rec in response['Records']:
                try:
                    payload = json.loads(rec['Data'])
                    records.append(RawLog(**payload))
                    logger.info(f"Consumed log from Kinesis: {payload.get('id', 'unknown')}")
                except Exception:
                    continue
            shard_iterator = response.get('NextShardIterator')
            if not response['Records']:
                break
    elif cloud_provider == "azure":
        if not _AZURE_EVENTHUB_AVAILABLE:
            raise ImportError("azure-eventhub package is required for Azure support.")
        eventhub_conn_str = os.getenv("AZURE_EVENT_HUB_CONNECTION_STRING")
        eventhub_name = os.getenv("AZURE_EVENT_HUB_NAME", "log2incident-eventhub")
        if not eventhub_conn_str:
            raise ValueError("AZURE_EVENT_HUB_CONNECTION_STRING must be set for Azure Event Hubs.")

        def on_event(partition_context, event):
            try:
                payload = json.loads(event.body_as_str())
                records.append(RawLog(**payload))
                logger.info(f"Consumed log from Event Hubs: {payload.get('id', 'unknown')}")
            except Exception:
                pass
            if len(records) >= max_records:
                partition_context.update_checkpoint(event)
                raise StopIteration()

        client = EventHubConsumerClient.from_connection_string(
            conn_str=eventhub_conn_str,
            consumer_group=os.getenv("AZURE_EVENT_HUB_CONSUMER_GROUP", "$Default"),
            eventhub_name=eventhub_name
        )
        try:
            # Use a short receive window to avoid blocking
            with client:
                client.receive(
                    on_event=on_event,
                    starting_position="-1",  # from beginning
                    max_wait_time=5
                )
        except StopIteration:
            pass
    else:
        raise ValueError(f"Unsupported CLOUD_PROVIDER: {cloud_provider}")
    return records
