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

### Trace ID Propagation

Every HTTP request flowing through the system receives a `trace_id` (UUID) for end-to-end correlation:

- **Generated** at the API Gateway (from `X-Trace-Id` header or auto-generated)
- **Propagated** via Kafka record headers across all topics (`log2incident-logs` → `log2incident-filtered` → `log2incident-events` → `log2incident-incidents`)
- **Persisted** in S3/Blob (in the log JSON), DynamoDB/CosmosDB (events + incidents)
- **Logged** in every service's structured stdout logs → Elasticsearch → Kibana

To trace a request: find its `trace_id` → filter Kibana by `trace_id=<uuid>` → see every pipeline stage that processed it.

- **Frontend (Product Console)**: For product/pricing management, connects to API-Server.
- **Incident View (UI)**: For incident management, reads from Incidents Table.
- **Incident Creator** is a dedicated pod, consuming Events and producing Incidents.
- **Model Matching (EKS/Flink)**: Handles event creation based on matching logic.
- **Notification Service** and **Incident View** are decoupled from incident creation.
- **User/Operator** receives notifications via Slack, PagerDuty, or WebSocket.
- **Tagging** is part of the Log Receiver, not a separate service.
