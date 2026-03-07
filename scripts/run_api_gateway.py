#!/usr/bin/env python3
"""
Run the Log2Incident API Gateway.

The API Gateway receives logs via HTTP and queues them for processing
by the pipeline consumer.

Usage:
    python3 scripts/run_api_gateway.py
    
The API will be available at:
    http://localhost:8000
    
Interactive API documentation:
    http://localhost:8000/docs
    http://localhost:8000/redoc
"""

import uvicorn
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log2incident.api_gateway.app import app


def main():
    print("Starting Log2Incident API Gateway...")
    print("API will be available at http://localhost:8000")
    print("Interactive docs at http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
