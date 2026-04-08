from diagrams import Diagram
from diagrams.azure.containers import KubernetesServices
from diagrams.azure.network import ApplicationGateway
from diagrams.azure.database import CosmosDb, DatabaseForPostgresqlServers
from diagrams.azure.storage import BlobStorage
from diagrams.azure.general import AllResources
from diagrams.onprem.client import Users
from diagrams.onprem.queue import Kafka
from diagrams.onprem.inmemory import Redis

with Diagram("Azure Log2Incident Architecture", show=False, filename="azure_architecture", outformat="png"):
    # Users and UIs
    frontend = Users("Frontend (React)")
    incident_view = Users("Incident View UI")
    operator = Users("User/Operator")

    # Core services
    api = ApplicationGateway("API Gateway")
    auth = KubernetesServices("Auth Service (AKS)")
    receiver = KubernetesServices("Log Receiver & Enricher (AKS)")
    blob = BlobStorage("Blob Storage")
    kafka1 = Kafka("Kafka Topic 1")
    etl = KubernetesServices("ETL Filter (AKS)")
    kafka2 = Kafka("Kafka Topic 2")
    matcher = KubernetesServices("Model Matching (AKS/Flink)")
    kafka_events = Kafka("Kafka Topic: Events")
    incident_creator = KubernetesServices("Incident Creator (AKS)")
    kafka_incidents = Kafka("Kafka Topic: Incidents")
    notification = KubernetesServices("Notification Service (AKS)")

    # Data stores
    events = CosmosDb("CosmosDB: Events")
    incidents = CosmosDb("CosmosDB: Incidents")
    event_history = CosmosDb("CosmosDB: Event History")
    products = KubernetesServices("Products API (AKS)")
    postgres = DatabaseForPostgresqlServers("Postgres")
    redis = Redis("Redis (Cache)")

    # Flows
    frontend >> auth >> api
    api >> receiver
    receiver >> kafka1
    receiver >> blob
    kafka1 >> etl
    etl >> kafka2
    kafka2 >> matcher
    matcher >> kafka_events
    kafka_events >> incident_creator
    incident_creator >> kafka_incidents
    incident_creator >> incidents
    kafka_incidents >> notification
    notification >> operator
    incidents >> incident_view
    kafka_events >> event_history
    # Product management
    frontend >> products
    products >> postgres
    products >> redis
