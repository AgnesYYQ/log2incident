from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from log2incident.log_receiver.receiver import LogReceiver
from log2incident.auth.service import AuthService
from log2incident.products.store import ProductStore
from config.config import get_frontend_origin
from psycopg import Error as PsycopgError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize log receiver
log_receiver = LogReceiver()
auth_service = AuthService()
product_store = ProductStore()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize product schema without blocking API startup if infra is down."""
    try:
        product_store.ensure_schema()
        logger.info("Product schema ready")
    except Exception as exc:
        logger.warning(f"Product schema initialization skipped: {exc}")
    yield


# Initialize FastAPI app
app = FastAPI(
    title="Log2Incident API Gateway",
    description="API Gateway for receiving logs, authenticating users, and managing products",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_frontend_origin()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    wrong_password_attempts: int = 0


class UsernameValidationResponse(BaseModel):
    exists: bool
    message: str


class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    updated_at: str


class ProductPriceUpdateRequest(BaseModel):
    price: float


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "log2incident-api-gateway",
        "features": ["log-ingestion", "auth", "products-cache"]
    }


@app.get("/auth/validate-username", response_model=UsernameValidationResponse)
async def validate_username(username: str = Query(..., min_length=1)):
    exists = auth_service.username_exists(username)
    if exists:
        return UsernameValidationResponse(exists=True, message="Username looks good")
    return UsernameValidationResponse(exists=False, message="Unknown username")


@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    success, error, attempts = auth_service.login(request.username, request.password)

    if success:
        return LoginResponse(
            success=True,
            message="Login successful",
            wrong_password_attempts=0,
        )

    status = 404 if error == "Unknown username" else 401
    raise HTTPException(
        status_code=status,
        detail={
            "success": False,
            "message": error,
            "wrong_password_attempts": attempts,
        },
    )


@app.get("/products", response_model=List[ProductResponse])
async def list_products():
    try:
        return product_store.list_products()
    except PsycopgError as exc:
        logger.error(f"Unable to list products: {exc}")
        raise HTTPException(status_code=503, detail="Product database unavailable")


@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    try:
        product = product_store.get_product(product_id)
    except PsycopgError as exc:
        logger.error(f"Unable to fetch product {product_id}: {exc}")
        raise HTTPException(status_code=503, detail="Product database unavailable")

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.patch("/products/{product_id}/price", response_model=ProductResponse)
async def update_product_price(product_id: str, request: ProductPriceUpdateRequest):
    if request.price < 0:
        raise HTTPException(status_code=400, detail="Price must be non-negative")

    try:
        product = product_store.update_price(product_id, request.price)
    except PsycopgError as exc:
        logger.error(f"Unable to update product {product_id}: {exc}")
        raise HTTPException(status_code=503, detail="Product database unavailable")

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


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
