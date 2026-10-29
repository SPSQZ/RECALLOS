# Minimal lightweight container image for Nebius Serverless Jobs
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy serverless worker script
COPY batch_benchmark_job.py .

# Output mount directory
RUN mkdir -p /app/job_artifacts

ENV PYTHONUNBUFFERED=1
ENV OUTPUT_DIR=/app/job_artifacts

ENTRYPOINT ["python", "batch_benchmark_job.py"]

