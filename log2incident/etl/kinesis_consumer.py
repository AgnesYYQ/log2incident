
import boto3
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

def fetch_raw_logs_from_kinesis(max_records: int = 100) -> List[RawLog]:
    """
    Fetch raw logs from the Kinesis stream.
    Args:
        max_records: Maximum number of records to fetch.
    Returns:
        List of RawLog objects.
    """
    logger = logging.getLogger("kinesis_consumer")
    logger.setLevel(logging.INFO)
    if _WATCHTOWER_AVAILABLE and not any(isinstance(h, watchtower.CloudWatchLogHandler) for h in logger.handlers):
        logger.addHandler(watchtower.CloudWatchLogHandler(log_group="log2incident-model-matching"))

    kinesis = boto3.client('kinesis', region_name=get_aws_region())
    stream_name = get_kinesis_stream_name()
    # Get the first shard
    stream_desc = kinesis.describe_stream(StreamName=stream_name)
    shard_id = stream_desc['StreamDescription']['Shards'][0]['ShardId']
    # Get a shard iterator
    shard_iterator = kinesis.get_shard_iterator(
        StreamName=stream_name,
        ShardId=shard_id,
        ShardIteratorType='TRIM_HORIZON'
    )['ShardIterator']
    # Fetch records
    records = []
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
    return records
