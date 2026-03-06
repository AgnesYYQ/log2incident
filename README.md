# Log2Incident

A Python-based log processing pipeline that transforms raw logs into incident views.

## Overview

The pipeline processes logs collected from endpoints or servers via AWS SQS/streams, applies model-matching to add tags, stores tagged logs in S3, and uses Flink for ETL filtering to trigger events. Incidents are created based on filters, either accumulated (multiple events) or instant (single event).

## Architecture

1. **Ingestion**: Collect raw logs from AWS SQS/streams.
2. **Tagging**: Apply model-matching to add tags to logs.
3. **Storage**: Store tagged logs in S3 bucket.
4. **ETL Filter**: Use Flink to filter logs and trigger events.
5. **Events**: Create events from filtered logs.
6. **Incidents**: Aggregate events into incidents (accumulated or instant).

## Installation

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Set up AWS credentials and configuration.

## Usage

Run the pipeline components as needed. See scripts/ for examples.

## Development

- Tests: `python -m pytest tests/`
- Linting: Use your preferred linter.

## Deployment

Configured for local deployment. For production, deploy to AWS EMR or Kubernetes as needed.