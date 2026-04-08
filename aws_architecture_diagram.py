from diagrams import Diagram
from diagrams.aws.compute import EC2, EKS
from diagrams.aws.network import APIGateway
from diagrams.aws.storage import S3
from diagrams.aws.database import Dynamodb, RDS
from diagrams.aws.general import User
from diagrams.onprem.client import Users
from diagrams.onprem.queue import Kafka

with Diagram("AWS Log2Incident Architecture", show=False, filename="aws_architecture", outformat="png"):
    # Users and UIs
    frontend = Users("Frontend (React)")
    incident_view = Users("Incident View UI")
    operator = Users("User/Operator")

    # Core services
    api = APIGateway("API Gateway")
    auth = EKS("Auth Service (EKS)")
    receiver = EKS("Log Receiver & Enricher (EKS)")
    s3 = S3("S3 Storage")
    kafka1 = Kafka("Kafka Topic 1")
    etl = EKS("ETL Filter (EKS)")
    kafka2 = Kafka("Kafka Topic 2")
    matcher = EKS("Model Matching (EKS/Flink)")
    kafka_events = Kafka("Kafka Topic: Events")
    incident_creator = EKS("Incident Creator (EKS)")
    kafka_incidents = Kafka("Kafka Topic: Incidents")
    notification = EKS("Notification Service (EKS)")

    # Data stores
    events = Dynamodb("DynamoDB: Events")
    incidents = Dynamodb("DynamoDB: Incidents")
    event_history = Dynamodb("DynamoDB: Event History")
    products = EKS("Products API (EKS)")
    postgres = RDS("Postgres")
    redis = EC2("Redis (Cache)")

    # Flows
    frontend >> auth >> api
    api >> receiver
    receiver >> kafka1
    receiver >> s3
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
