from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from log2incident.log_receiver.receiver import LogReceiver
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Log2Incident API Gateway",
    description="API Gateway for receiving and processing logs",
    version="1.0.0"
)

# Initialize log receiver
log_receiver = LogReceiver()


class LogRequest(BaseModel):
    """Schema for incoming log requests."""
    source: str
    message: str
    id: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LogResponse(BaseModel):
    """Schema for log submission response."""
    success: bool
    message_id: str
    log_id: str


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "log2incident-api-gateway"
    }


@app.post("/logs", response_model=LogResponse)
async def receive_log(log: LogRequest):
    """
    Receive a log entry and queue it for processing.
    
    - **source**: The source of the log (e.g., 'application', 'system')
    - **message**: The log message content
    - **id**: (Optional) Custom log ID; auto-generated if not provided
    - **timestamp**: (Optional) Log timestamp in ISO format; uses current time if not provided
    - **metadata**: (Optional) Additional metadata as key-value pairs
    """
    try:
        log_data = {
            "source": log.source,
            "message": log.message,
            "id": log.id,
            "timestamp": log.timestamp,
            "metadata": log.metadata or {}
        }
        
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        # Send log to queue
        message_id = log_receiver.receive_and_queue_log(log_data)
        
        logger.info(f"Log received and queued: {log_data.get('id', 'generated_id')}")
        
        return LogResponse(
            success=True,
            message_id=message_id,
            log_id=log_data.get('id')
        )
    except Exception as e:
        logger.error(f"Error processing log: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing log: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
