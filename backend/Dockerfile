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

# Start application with migrations
CMD sh -c "echo 'Running database migrations...' && \
    alembic upgrade head || echo 'Migration failed or not needed' && \
    echo 'Starting application...' && \
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"