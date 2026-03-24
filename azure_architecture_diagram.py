from diagrams import Diagram, Cluster
from diagrams.azure.containers import KubernetesServices
from diagrams.azure.network import ApplicationGateway
from diagrams.azure.database import CosmosDb, DatabaseForPostgresqlServers
from diagrams.azure.storage import BlobStorage
from diagrams.azure.general import AllResources
from diagrams.onprem.queue import Kafka
from diagrams.onprem.inmemory import Redis

with Diagram("Azure Log2Incident Architecture", show=False, filename="azure_architecture", outformat="png"):
    user = AllResources("Client")
    api = ApplicationGateway("API Gateway")
    receiver = KubernetesServices("Log Receiver & Enricher (AKS)")
    kafka1 = Kafka("Kafka Topic")
    blob = BlobStorage("Blob Storage")
    kafka2 = Kafka("Kafka Topic (Filtered)")
    etl = KubernetesServices("ETL Filter (AKS)")
    kafka3 = Kafka("Kafka Topic (Matched)")
    matcher = KubernetesServices("Model Matching (AKS)")
    events = CosmosDb("CosmosDB: Events")
    incidents = CosmosDb("CosmosDB: Incidents")
    products = KubernetesServices("Products API (AKS)")
    postgres = DatabaseForPostgresqlServers("Postgres")
    redis = Redis("Redis")

    user >> api >> receiver >> kafka1 >> blob >> kafka2 >> etl >> kafka3 >> matcher >> events >> incidents
    api >> products
    products >> postgres
    products >> redis
