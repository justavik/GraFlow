# Use Python slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY pipeline_orchestrator.py .
COPY settings_fast.yaml .
COPY validate_setup.py .
COPY graphrag_output/ ./graphrag_output/
COPY .env.template .

# Create input directory for PDFs
RUN mkdir -p /app/input

# Copy the streamlined startup script
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Expose port for any web interface (future use)
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# Default command
ENTRYPOINT ["./docker-entrypoint.sh"]
