# Log2Incident

A Python-based log processing pipeline that transforms raw logs into incident views.

## Overview

The pipeline processes logs collected from endpoints or servers via AWS SQS/streams, applies model-matching to add tags, stores tagged logs in S3, and uses Flink for ETL filtering to trigger events. Incidents are created based on filters, either accumulated (multiple events) or instant (single event).

## Architecture

The system consists of two main components:

### 1. API Gateway & Log Receiver
- **API Gateway**: FastAPI-based HTTP endpoint that receives logs via REST API
- **Log Receiver**: Accepts logs and queues them to AWS SQS for processing
- Provides endpoints:
  - `POST /logs` - Submit a log entry
  - `GET /health` - Health check

### 2. Processing Pipeline
1. **Ingestion**: Consume logs from AWS SQS queue
2. **Tagging**: Apply model-matching to add tags to logs
3. **Storage**: Store tagged logs in S3 bucket
4. **ETL Filter**: Use Flink to filter logs and trigger events
5. **Events**: Create events from filtered logs
6. **Incidents**: Aggregate events into incidents (accumulated or instant)

## Installation

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Set up AWS credentials and configuration.

## Quick Start

Run the API Gateway and processing pipeline in parallel (in separate terminals):

**Terminal 1 - Start the API Gateway:**
```bash
python3 scripts/run_api_gateway.py
```
The API will be available at `http://localhost:8000`

**Terminal 2 - Start the Processing Pipeline:**
```bash
python3 scripts/run_pipeline.py
```

### Example: Send a Log

```bash
curl -X POST "http://localhost:8000/logs" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "my-app",
    "message": "Database connection failed",
    "metadata": {
      "severity": "error",
      "component": "auth-service"
    }
  }'
```

### API Documentation

Once the API Gateway is running, visit:
- Interactive docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

- Tests: `python -m pytest tests/`
- Linting: Use your preferred linter.

## Deployment

Configured for local deployment. For production, deploy to AWS EMR or Kubernetes as needed.