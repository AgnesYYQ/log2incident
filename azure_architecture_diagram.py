from diagrams import Diagram, Cluster
from diagrams.azure.compute import FunctionApps
from diagrams.azure.network import ApplicationGateway
from diagrams.azure.database import CosmosDb, DatabaseForPostgresqlServers
from diagrams.azure.storage import BlobStorage
from diagrams.azure.general import AllResources
from diagrams.onprem.queue import Kafka
from diagrams.onprem.inmemory import Redis

with Diagram("Azure Log2Incident Architecture", show=False, filename="azure_architecture", outformat="png"):
    user = AllResources("Client")
    api = ApplicationGateway("API Gateway")
    receiver = FunctionApps("Log Receiver")
    kafka1 = Kafka("Kafka Topic")
    enrich = FunctionApps("Log Enrichment")
    blob = BlobStorage("Blob Storage")
    kafka2 = Kafka("Kafka Topic (Filtered)")
    etl = FunctionApps("ETL Filter")
    kafka3 = Kafka("Kafka Topic (Matched)")
    matcher = FunctionApps("Model Matching")
    events = CosmosDb("CosmosDB: Events")
    incidents = CosmosDb("CosmosDB: Incidents")
    products = FunctionApps("Products API")
    postgres = DatabaseForPostgresqlServers("Postgres")
    redis = Redis("Redis")

    user >> api >> receiver >> kafka1 >> enrich >> blob >> kafka2 >> etl >> kafka3 >> matcher >> events >> incidents
    api >> products
    products >> postgres
    products >> redis
