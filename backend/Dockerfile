# Backend Dockerfile for AI Research Processor Web API

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/backend/

# Copy source code from parent directory
# (This assumes docker build context is the project root)
COPY src/ /app/src/
COPY config/ /app/config/

# Create necessary directories
RUN mkdir -p /app/temp_sessions /app/logs /app/data

# Set Python path
ENV PYTHONPATH=/app

# Default API port (can be overridden via environment variable)
ENV API_PORT=8000

# Expose port (note: this is documentation only, actual port is set at runtime)
EXPOSE ${API_PORT}

# Run the application with configurable port
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${API_PORT}"]

