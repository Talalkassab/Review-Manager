# Simplified Dockerfile for Render deployment
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p logs uploads

# Skip database setup in Docker build - will run at startup
# RUN python create_admin.py || true

# Expose port
EXPOSE 8000

# Create startup script
RUN echo '#!/bin/sh\n\
echo "Running database migrations..."\n\
alembic upgrade head || echo "Migration failed or not needed"\n\
echo "Starting application..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}' > /app/start.sh && \
    chmod +x /app/start.sh

# Start application
CMD ["/app/start.sh"]