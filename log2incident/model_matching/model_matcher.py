
"""
ModelMatcher: Applies model/rule-based matching to logs to create events.

Features:
- Loads rules/models from DynamoDB (AWS) or CosmosDB (Azure) if available.
- Falls back to default rules if not configured.
- Supports both local and Flink-based matching.

Usage:
    matcher = ModelMatcher()
    events = matcher.match([tagged_log1, tagged_log2])
    # or, for Flink integration:
    events = matcher.flink_match([tagged_log1, tagged_log2])
"""

from typing import List
from log2incident.models import TaggedLog, Event
import logging

class ModelMatcher:
    """
    Model Matching logic using rules/models. Can be used with Flink or locally.
    """
    def __init__(self, rules=None):
        self.logger = logging.getLogger("model_matcher")
        self.rules = rules or self._load_rules_from_db() or self.default_rules()

    def _load_rules_from_db(self):
        import os
        cloud = os.getenv("CLOUD_PROVIDER", "aws").lower()
        try:
            if cloud == "aws":
                import boto3
                table_name = os.getenv("DYNAMODB_MODEL_RULES_TABLE", "log2incident-model-rules")
                dynamodb = boto3.resource('dynamodb', region_name=os.getenv("AWS_REGION", "us-east-1"))
                table = dynamodb.Table(table_name)
                response = table.scan()
                items = response.get('Items', [])
                rules = {}
                for item in items:
                    tag = str(item.get('tag', '')).strip().lower()
                    keywords = item.get('keywords', [])
                    if isinstance(keywords, str):
                        keywords = [k.strip() for k in keywords.split(',') if k.strip()]
                    if tag and keywords:
                        rules[tag] = keywords
                return {"event_tags": list(rules.keys())} if rules else None
            elif cloud == "azure":
                from azure.cosmos import CosmosClient
                endpoint = os.getenv("COSMOSDB_ENDPOINT")
                key = os.getenv("COSMOSDB_KEY")
                database_name = os.getenv("COSMOSDB_DATABASE", "log2incident")
                container_name = os.getenv("COSMOSDB_MODEL_RULES_CONTAINER", "model-rules")
                if not endpoint or not key:
                    return None
                client = CosmosClient(endpoint, key)
                database = client.get_database_client(database_name)
                container = database.get_container_client(container_name)
                rules = {}
                for item in container.read_all_items():
                    tag = str(item.get('tag', '')).strip().lower()
                    keywords = item.get('keywords', [])
                    if isinstance(keywords, str):
                        keywords = [k.strip() for k in keywords.split(',') if k.strip()]
                    if tag and keywords:
                        rules[tag] = keywords
                return {"event_tags": list(rules.keys())} if rules else None
        except Exception as e:
            self.logger.warning(f"Failed to load rules/models from DB: {e}")
            return None

    def default_rules(self):
        # Example: match logs with 'error' or 'critical' tags
        return {"event_tags": ["error", "critical"]}

    def match(self, logs: List[TaggedLog]) -> List[Event]:
        """
        Apply model/rule-based matching to logs and create events.
        """
        from log2incident.events.event_creator import EventCreator
        event_tags = set(self.rules.get("event_tags", []))
        creator = EventCreator()
        matched_events = []
        for log in logs:
            if event_tags.intersection(set(log.tags)):
                matched_events.append(creator.create_event(log))
        self.logger.info(f"ModelMatcher: matched {len(matched_events)}/{len(logs)} logs as events.")
        return matched_events

    # Flink integration stub (to be expanded for real Flink jobs)
    def flink_match(self, logs: List[TaggedLog]):
        # Here you would use PyFlink DataStream API to process logs at scale
        # For now, just call match()
        return self.match(logs)
