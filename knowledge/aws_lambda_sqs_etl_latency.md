# AWS Lambda, SQS, and ETL Filter: Processing Latency and Monitoring

## What happens if Lambda cannot keep up with SQS message rate?
- **SQS Message Backlog Grows:** Messages accumulate in SQS if Lambda cannot process them fast enough.
- **Lambda Scaling Limits:** Lambda will scale up to its concurrency limits, but if the message rate exceeds this, backlog increases.
- **Message Retention:** SQS retains messages up to 14 days (default 4 days). Unprocessed messages are deleted after this period.
- **DLQ (Dead Letter Queue):** If a message fails processing after the max receive count, it is moved to the DLQ.
- **Potential Throttling:** Lambda may be throttled if concurrency limits are reached, further increasing backlog.
- **No Data Loss (until retention expires):** Messages are not lost unless they expire in SQS or are moved to the DLQ.

## Measuring Wait Time for Log Processing in Dashboards
- **CloudWatch:** Use the `ApproximateAgeOfOldestMessage` metric for SQS to measure the oldest message's wait time.
- **Grafana:** Visualize CloudWatch metrics (including `ApproximateAgeOfOldestMessage`) or custom metrics from your ETL/Lambda.
- **Kibana:** If logs are in Elasticsearch, store both ingestion and processing timestamps. Calculate and visualize the difference as processing latency.

## Summary
- If Lambda cannot keep up, messages pile up in SQS. They are processed as Lambda catches up, moved to DLQ after max attempts, or deleted after retention expires.
- Wait time for processing can be measured and visualized using built-in metrics or custom timestamps in CloudWatch, Grafana, or Kibana.
