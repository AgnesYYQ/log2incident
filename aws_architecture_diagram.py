from diagrams import Diagram, Cluster
from diagrams.aws.compute import EC2
from diagrams.aws.network import APIGateway
# from diagrams.aws.integration import MSK
from diagrams.aws.storage import S3
from diagrams.aws.database import Dynamodb
from diagrams.aws.general import User
from diagrams.onprem.queue import Kafka

with Diagram("AWS Log2Incident Architecture", show=False, filename="aws_architecture", outformat="png"):
    user = User("Client")
    api = APIGateway("API Gateway")
    receiver = EC2("Log Receiver")
    kafka1 = Kafka("Kafka Topic")
    enrich = EC2("Log Enrichment")
    s3 = S3("S3 Storage")
    kafka2 = Kafka("Kafka Topic (Filtered)")
    etl = EC2("ETL Filter")
    kafka3 = Kafka("Kafka Topic (Matched)")
    matcher = EC2("Model Matching")
    events = Dynamodb("DynamoDB: Events")
    incidents = Dynamodb("DynamoDB: Incidents")
    products = EC2("Products API")
    postgres = EC2("Postgres")
    redis = EC2("Redis")

    user >> api >> receiver >> kafka1 >> enrich >> s3 >> kafka2 >> etl >> kafka3 >> matcher >> events >> incidents
    api >> products
    products >> postgres
    products >> redis
