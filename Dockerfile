# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Expose port (Railway uses dynamic PORT)
EXPOSE 8000

# Set default port
ENV PORT=8000

# Run the application with dynamic port
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
