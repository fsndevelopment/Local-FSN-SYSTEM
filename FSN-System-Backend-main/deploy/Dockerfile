# FSN APPIUM Production Dockerfile
# Builds production-ready Instagram automation system with all 9 working actions

FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libusb-1.0-0 \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ .
COPY deploy/production_config.py .

# Create directories for data persistence
RUN mkdir -p /app/logs /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose the API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/real-device/test-status || exit 1

# Start the production server
CMD ["python", "-c", "import uvicorn; from production_config import production_config; uvicorn.run('main:app', **production_config.get_uvicorn_config())"]
