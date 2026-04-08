# Log2Incident Complete Architecture Diagram (2026)

```mermaid
graph TD
    F[Frontend (Product Console)] -->|API| A[API-Server (EKS/AKS Pods)]
    A -->|Valid Log| B[Log Receiver, Enricher & Tagger (EKS/AKS Pods)]
    B -->|Raw Log to S3/Blob| S3[(S3/Blob Storage)]
    B -->|Enriched Log| K1((Kafka Topic 1))
    K1 --> C[ETL-Filter (EKS/AKS Pods)]
    C -->|Filtered Log| K2((Kafka Topic 2))
    K2 --> MM[Model Matching & Event Creator (EKS/Flink)]
    MM -->|Event| KE[Kafka Topic: Events]
    KE --> IC[Incident Creator (EKS/AKS Pod)]
    IC -->|Incident| KI[Kafka Topic: Incidents]
    IC -->|Incident| DDB[(DynamoDB/CosmosDB: Incidents Table)]
    KI --> NS[Notification Service (EKS/AKS Pods)]
    NS -->|Slack/PagerDuty/WebSocket| U[User/Operator]
    DDB --> IV[Incident View (UI)]
    KE --> EH[DynamoDB/CosmosDB: Event History]

    %% Filtering stages
    A -.->|Cut-1: Schema/Auth| A
    B -.->|Cut-2: Enrich/Tag/Drop| B
    C -.->|Cut-3: ETL Filter| C
```

- **Frontend (Product Console)**: For product/pricing management, connects to API-Server.
- **Incident View (UI)**: For incident management, reads from Incidents Table.
- **Incident Creator** is a dedicated pod, consuming Events and producing Incidents.
- **Model Matching (EKS/Flink)**: Handles event creation based on matching logic.
- **Notification Service** and **Incident View** are decoupled from incident creation.
- **User/Operator** receives notifications via Slack, PagerDuty, or WebSocket.
- **Tagging** is part of the Log Receiver, not a separate service.
