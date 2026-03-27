# Kafka, EKS, and ETL-Filter Scaling: Partitions, Autoscaling, and Processing

## What happens if ETL-Filter pods cannot keep up with Kafka messages?
- **Kafka Topic Backlog Grows:** Messages accumulate in Kafka topic partitions if consumers (ETL-Filter pods) cannot keep up.
- **Consumer Lag Increases:** The difference between the latest message offset and the consumer's processed offset grows (consumer lag).
- **No Immediate Data Loss:** Kafka retains messages for a configurable retention period (e.g., 7 days by default).
- **Potential for Data Loss:** If backlog exceeds retention period or storage limits, older messages are deleted and lost.
- **Scaling:** You can scale ETL-Filter pods up to the number of partitions for maximum parallelism.

## What does 'number of partitions' mean?
- A partition is a unit of parallelism in a Kafka topic.
- Each topic can have multiple partitions; each partition is an ordered sequence of messages.
- The number of partitions determines the maximum number of consumers (pods) that can process messages in parallel (one consumer per partition at a time in a consumer group).

## HPA and VPA for etl-filter deployment
- **HPA (Horizontal Pod Autoscaler):** Scales the number of pods based on CPU, memory, or custom metrics (e.g., consumer lag).
- **VPA (Vertical Pod Autoscaler):** Adjusts resource requests/limits (CPU/memory) for each pod automatically.
- **Scaling Limits:** HPA can only scale up to the number of Kafka partitions for effective parallelism. Extra pods beyond the number of partitions will be idle.

## Summary
- If ETL-Filter pods cannot keep up, consumer lag and Kafka backlog grow. No data is lost unless retention/storage limits are exceeded.
- The number of partitions sets the upper limit for parallel processing.
- HPA and VPA can automate scaling, but HPA is limited by the number of partitions.
