import os
import pytest
from unittest.mock import patch, MagicMock
from log2incident.model_matching.model_matcher import ModelMatcher
from log2incident.models import TaggedLog

def test_default_rules():
    matcher = ModelMatcher()
    assert 'event_tags' in matcher.rules
    assert isinstance(matcher.rules['event_tags'], list)

def test_match_with_default_rules():
    matcher = ModelMatcher()
    log = TaggedLog(id='1', timestamp='2024-01-01T00:00:00', source='test', message='error occurred', metadata={}, tags=['error'])
    events = matcher.match([log])
    assert len(events) == 1

def test_load_rules_from_dynamodb(monkeypatch):
    # Patch boto3 resource and table
    mock_table = MagicMock()
    mock_table.scan.return_value = {'Items': [{'tag': 'critical', 'keywords': ['CRIT']}]}
    mock_dynamodb = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    with patch('boto3.resource', return_value=mock_dynamodb):
        monkeypatch.setenv('CLOUD_PROVIDER', 'aws')
        matcher = ModelMatcher()
        assert 'critical' in matcher.rules['event_tags']

def test_load_rules_from_cosmosdb(monkeypatch):
    # Patch CosmosClient and container
    class MockContainer:
        def read_all_items(self):
            return [{'tag': 'alert', 'keywords': ['ALERT']}] 
    class MockDatabase:
        def get_container_client(self, name):
            return MockContainer()
    class MockCosmosClient:
        def get_database_client(self, name):
            return MockDatabase()
    with patch('azure.cosmos.CosmosClient', return_value=MockCosmosClient()):
        monkeypatch.setenv('CLOUD_PROVIDER', 'azure')
        monkeypatch.setenv('COSMOSDB_ENDPOINT', 'fake')
        monkeypatch.setenv('COSMOSDB_KEY', 'fake')
        matcher = ModelMatcher()
        assert 'alert' in matcher.rules['event_tags']
