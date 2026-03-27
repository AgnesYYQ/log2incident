# Log2Incident Architecture: Key Design Decisions and Implementation Notes

## AWS Lambda, SQS, and ETL Filter (Legacy)
- Used Lambda functions to process logs from SQS queues, with Dead Letter Queues (DLQ) for failed messages.
- If Lambda could not keep up with SQS message rate:
  - Messages accumulated in SQS (backlog grew).
  - Lambda scaled up to concurrency limits, but backlog increased if limits were reached.
  - SQS retained messages up to 14 days (default 4 days). Unprocessed messages were deleted after this period.
  - Messages failing max receive attempts were moved to DLQ.
  - No data loss unless messages expired or were moved to DLQ.
- Processing wait time was measured using CloudWatch's `ApproximateAgeOfOldestMessage` metric, and visualized in Grafana or Kibana.

## Migration to EKS and Kafka
- Moved ETL-Filter to run as pods on EKS, consuming from Kafka topics.
- Kafka provides higher throughput, better parallelism, and configurable retention.
- If ETL-Filter pods cannot keep up with Kafka:
  - Messages accumulate in Kafka partitions (backlog grows).
  - Consumer lag increases (difference between latest offset and processed offset).
  - No data loss unless retention period or storage limits are exceeded.
  - Scaling is possible up to the number of partitions.
- HPA (Horizontal Pod Autoscaler) and VPA (Vertical Pod Autoscaler) are used for automatic scaling of ETL-Filter pods.
  - HPA scales pod count based on metrics (CPU, memory, or consumer lag).
  - VPA adjusts resource requests/limits for each pod.
  - HPA scaling is limited by the number of Kafka partitions (one consumer per partition).

## Monitoring and Observability
- CloudWatch, Grafana, and Kibana are used for monitoring:
  - SQS: `ApproximateAgeOfOldestMessage` for backlog/wait time.
  - Kafka: Consumer lag metrics for backlog/wait time.
  - Custom metrics and logs are used for deeper observability.

## Summary
- The architecture evolved from Lambda/SQS to EKS/Kafka for better scalability and throughput.
- Autoscaling and observability are key to handling variable log volumes and ensuring reliability.
- Knowledge base files provide details on each architecture component and operational best practices.
