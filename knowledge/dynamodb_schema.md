# DynamoDB Schema and Indexing for Events/Incidents

## Table Schema
- **Partition Key:** `id` (string)
- **Sort Key:** `timestamp` (string, ISO8601 format recommended)
- **Global Secondary Index (GSI):**
  - Name: `TimestampIndex`
  - Partition Key: `timestamp`
  - Sort Key: `id`
  - Purpose: Efficient time-based queries (e.g., last 7/30 days)

## Implementation Notes
- Both events and incidents tables use this schema for efficient time-range queries.
- The GSI allows querying by timestamp directly, supporting user queries like last 24 hours, 7 days, etc.
- If you use Redis for caching, cache frequent or recent queries to reduce DynamoDB load.

## References
- See `scripts/create_dynamodb_tables.py` for table creation script.
- Models: `log2incident/models.py`
- Storage logic: `log2incident/storage/event_incident_store.py`

## Best Practices
- Store timestamps in ISO8601 string format for correct sorting.
- Use the GSI for all time-based queries to avoid full table scans.
- Monitor and tune read/write capacity as needed.
