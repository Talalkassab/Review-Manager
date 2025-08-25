#!/bin/bash
set -e

echo "🚀 Starting Railway build process..."

# Navigate to backend directory
cd backend

echo "📦 Installing Python dependencies..."
pip install --upgrade pip setuptools wheel

# Install packages strategically to avoid conflicts
pip install --no-cache-dir cryptography==41.0.7 Pillow==10.4.0
pip install --no-cache-dir fastapi==0.104.1 uvicorn[standard]==0.24.0 sqlalchemy==2.0.23
pip install --no-cache-dir -r requirements.txt

echo "✅ Build completed successfully!"