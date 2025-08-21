#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Create default admin user if not exists
python create_admin.py || echo "Admin user already exists"

echo "Build completed successfully!"