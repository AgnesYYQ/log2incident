FROM python:3.10-slim
WORKDIR /app
COPY ../../.. /app
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "-m", "log2incident.incident_creator.incident_creator_service"]
