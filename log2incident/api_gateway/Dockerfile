# Dockerfile for API Gateway
FROM python:3.11-slim
WORKDIR /app
COPY log2incident/api_gateway /app/api_gateway
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "-m", "api_gateway.app"]
