import os
import logging
from log2incident.models import Event, Incident
from typing import Dict, Any

class EventIncidentStore:
    """
    Persists events and incidents to DynamoDB (AWS) or CosmosDB (Azure).
    """
    def __init__(self):
        self.logger = logging.getLogger("event_incident_store")
        self.cloud = os.getenv("CLOUD_PROVIDER", "aws").lower()
        if self.cloud == "aws":
            import boto3
            self.dynamodb = boto3.resource('dynamodb', region_name=os.getenv("AWS_REGION", "us-east-1"))
            self.events_table = self.dynamodb.Table(os.getenv("DYNAMODB_EVENTS_TABLE", "log2incident-events"))
            self.incidents_table = self.dynamodb.Table(os.getenv("DYNAMODB_INCIDENTS_TABLE", "log2incident-incidents"))
        elif self.cloud == "azure":
            from azure.cosmos import CosmosClient
            endpoint = os.getenv("COSMOSDB_ENDPOINT")
            key = os.getenv("COSMOSDB_KEY")
            database_name = os.getenv("COSMOSDB_DATABASE", "log2incident")
            self.client = CosmosClient(endpoint, key)
            self.database = self.client.get_database_client(database_name)
            self.events_container = self.database.get_container_client(os.getenv("COSMOSDB_EVENTS_CONTAINER", "events"))
            self.incidents_container = self.database.get_container_client(os.getenv("COSMOSDB_INCIDENTS_CONTAINER", "incidents"))
        else:
            raise ValueError(f"Unsupported CLOUD_PROVIDER: {self.cloud}")

    def save_event(self, event: Event):
        data = event.model_dump()
        if self.cloud == "aws":
            self.events_table.put_item(Item=data)
        elif self.cloud == "azure":
            self.events_container.upsert_item(data)
        self.logger.info(f"Persisted event {event.id}")

    def save_incident(self, incident: Incident):
        data = incident.model_dump()
        if self.cloud == "aws":
            self.incidents_table.put_item(Item=data)
        elif self.cloud == "azure":
            self.incidents_container.upsert_item(data)
        self.logger.info(f"Persisted incident {incident.id}")
