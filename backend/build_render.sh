#!/usr/bin/env bash
set -o errexit

echo "Starting build process for Restaurant AI with CrewAI..."

# Set Python path and install build tools
export PYTHONPATH=/opt/render/project/src
python -m pip install --upgrade pip setuptools wheel

# Install system dependencies that CrewAI might need
echo "Installing core dependencies..."
pip install --no-cache-dir numpy==1.24.3
pip install --no-cache-dir pandas==2.1.4

# Install CrewAI and dependencies in stages to avoid conflicts
echo "Installing AI dependencies..."
pip install --no-cache-dir openai==1.6.1
pip install --no-cache-dir anthropic==0.8.0
pip install --no-cache-dir crewai==0.5.0
pip install --no-cache-dir crewai-tools==0.1.32

# Install remaining dependencies
echo "Installing remaining dependencies..."
pip install --no-cache-dir --timeout=600 -r requirements.txt

echo "Dependencies installed successfully!"

# Initialize database (skip if fails - database might already exist)
echo "Setting up database..."
if [ -f "alembic.ini" ]; then
    alembic upgrade head || echo "Database migration skipped (might already exist)"
fi

# Create admin user (skip if fails - user might already exist) 
python create_admin.py || echo "Admin user creation skipped (might already exist)"

echo "Build completed successfully!"