# Railway + Vercel Deployment Guide for WhatsApp Customer Agent

## Overview

This guide provides a complete deployment strategy for the WhatsApp Customer Agent project using:
- **Railway**: Backend FastAPI application + PostgreSQL database
- **Vercel**: Frontend Next.js application

This approach avoids the package conflicts experienced with Render (crewai-tools, Pillow, cryptography version issues).

## Table of Contents

1. [Railway Backend Deployment](#railway-backend-deployment)
2. [Vercel Frontend Deployment](#vercel-frontend-deployment)
3. [Environment Variables Configuration](#environment-variables-configuration)
4. [CORS Configuration](#cors-configuration)
5. [Deployment Process](#deployment-process)
6. [Troubleshooting](#troubleshooting)

---

## Railway Backend Deployment

### Prerequisites

1. Railway account (free tier available)
2. GitHub repository access
3. Project ready with Docker configuration

### Railway Configuration Files

Railway supports configuration through `railway.json` or `railway.toml` files.

### Recommended Project Structure

```
backend/
├── railway.json          # Railway configuration
├── Dockerfile           # Optimized for Railway
├── requirements.txt     # Dependency management
├── .dockerignore       # Exclude unnecessary files
└── app/                # Application code
```

### Database Setup

1. **Create PostgreSQL Service**:
   - Login to Railway dashboard
   - Create new project
   - Add PostgreSQL database service
   - Note the connection details (automatically provided as environment variables)

2. **Database Environment Variables** (automatically provided):
   - `PGHOST` - Database host
   - `PGPORT` - Database port  
   - `PGUSER` - Database user
   - `PGPASSWORD` - Database password
   - `PGDATABASE` - Database name

### Deployment Process

1. **Connect Repository**:
   - Link your GitHub repository to Railway
   - Select the backend directory if using monorepo

2. **Automatic Detection**:
   - Railway will detect your Dockerfile and use it automatically
   - Build process typically takes 15 seconds with optimized Docker

3. **Environment Variables**:
   - Set production environment variables in Railway dashboard
   - Include database connection variables
   - Add API keys and secrets

### Key Benefits of Railway

- Zero-configuration PostgreSQL integration
- Automatic HTTPS certificates
- Built-in monitoring and logging
- Simple scaling options
- Fast deployment times with Docker

---

## Vercel Frontend Deployment

### Prerequisites

1. Vercel account (free tier available)  
2. Next.js application ready for deployment
3. Environment variables for backend API connection

### Vercel Configuration Files

Vercel can be configured using `vercel.json` for custom routing and build settings.

### Deployment Process

1. **Connect Repository**:
   - Import project from GitHub to Vercel
   - Vercel auto-detects Next.js configuration

2. **Environment Variables**:
   - Add environment variables in Vercel dashboard
   - Use `NEXT_PUBLIC_` prefix for client-side variables
   - Configure API endpoint URLs pointing to Railway backend

3. **Build Configuration**:
   - Vercel automatically optimizes Next.js builds
   - Supports TypeScript and modern React features out of the box

### Integration with Railway Backend

Configure your Next.js app to connect to Railway backend:

```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = {
  baseURL: API_BASE_URL,
  // ... rest of configuration
};
```

---

## Environment Variables Configuration

### Railway Backend Variables

**Required Environment Variables**:
```bash
# Database (automatically provided by Railway PostgreSQL service)
DATABASE_URL=postgresql://user:password@host:port/database

# Application Settings
ENVIRONMENT=production
DEBUG=false
PORT=8000

# API Keys
OPENROUTER_API_KEY=your_openrouter_api_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_WHATSAPP_NUMBER=your_twilio_whatsapp_number

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Settings
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,https://your-custom-domain.com
```

### Vercel Frontend Variables

**Required Environment Variables**:
```bash
# API Connection
NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app
NEXT_PUBLIC_ENVIRONMENT=production

# Optional: Analytics and monitoring
NEXT_PUBLIC_GA_ID=your_google_analytics_id
```

---

## CORS Configuration

### FastAPI CORS Setup for Railway-Vercel

Update your FastAPI CORS configuration to handle Railway-Vercel integration:

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# CORS configuration for Railway-Vercel integration
origins = [
    "https://your-vercel-app.vercel.app",
    "https://your-custom-domain.com",
    "http://localhost:3000",  # For local development
]

# Add environment-based origins
if allowed_origins := os.getenv("ALLOWED_ORIGINS"):
    origins.extend(allowed_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Handle preflight requests explicitly
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return {"message": "OK"}
```

### Common CORS Issues and Solutions

1. **Preflight Request Issues**: 
   - Ensure OPTIONS method is explicitly handled
   - Railway's HTTP edge proxy forwards OPTIONS requests correctly

2. **URL Configuration Problems**:
   - Use absolute URLs for API calls from Vercel
   - Avoid relative paths that might resolve incorrectly

3. **Credential Handling**:
   - Set `allow_credentials=True` if using authentication cookies
   - Ensure frontend sends credentials with requests

---

## Deployment Process

### Step-by-Step Deployment

#### Phase 1: Railway Backend Deployment

1. **Prepare Repository**:
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push origin main
   ```

2. **Create Railway Project**:
   - Go to Railway dashboard
   - Create new project from GitHub repo
   - Select backend directory

3. **Add PostgreSQL Database**:
   - Add PostgreSQL service to project
   - Database variables are automatically configured

4. **Configure Environment Variables**:
   - Add all required environment variables
   - Test connection to database

5. **Deploy and Test**:
   - Railway automatically deploys on push
   - Check logs for successful startup
   - Test API endpoints

#### Phase 2: Vercel Frontend Deployment  

1. **Create Vercel Project**:
   - Import repository to Vercel
   - Select frontend directory
   - Configure build settings

2. **Configure Environment Variables**:
   - Set `NEXT_PUBLIC_API_URL` to Railway backend URL
   - Add other required environment variables

3. **Deploy and Test**:
   - Vercel deploys automatically
   - Test frontend-backend integration
   - Verify CORS functionality

#### Phase 3: Integration Testing

1. **End-to-End Testing**:
   - Test all API calls from frontend
   - Verify database connections
   - Test WhatsApp integration

2. **Performance Verification**:
   - Check response times
   - Monitor error rates
   - Verify scaling behavior

---

## Package Conflict Resolution

### Addressing Render Issues

The package conflicts experienced with Render (crewai-tools, Pillow, cryptography) are resolved through:

1. **Better Base Image**: Using `python:3.11-slim` instead of Alpine
2. **Improved Build Process**: Railway's Docker handling is more robust
3. **System Dependencies**: Proper handling of native dependencies

### Optimized Requirements Strategy

```txt
# requirements.txt optimized for Railway deployment

# Core FastAPI components (pinned versions)
fastapi==0.104.1
uvicorn[standard]==0.24.0

# CrewAI with compatible versions
crewai==0.5.0

# Database with tested versions  
sqlalchemy==2.0.23
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Image processing (compatible version)
Pillow==10.4.0

# Security (stable version)
cryptography==41.0.7

# Other dependencies...
```

---

## Monitoring and Maintenance

### Railway Monitoring

1. **Built-in Metrics**:
   - CPU and memory usage
   - Request/response metrics
   - Database connection health

2. **Log Management**:
   - Structured logging with timestamps
   - Error tracking and alerts
   - Performance monitoring

### Vercel Analytics

1. **Performance Monitoring**:
   - Core Web Vitals tracking
   - Build and deployment analytics
   - Error boundary monitoring

2. **User Analytics**:
   - Page view tracking
   - User interaction metrics
   - Conversion funnel analysis

---

## Troubleshooting

### Common Railway Issues

1. **Docker Build Failures**:
   - Check Dockerfile syntax
   - Verify system dependencies
   - Review build logs

2. **Database Connection Issues**:
   - Verify environment variables
   - Check network connectivity
   - Review connection string format

3. **Memory/CPU Limits**:
   - Monitor resource usage
   - Optimize application code
   - Consider upgrading plan

### Common Vercel Issues

1. **Build Failures**:
   - Check Node.js version compatibility
   - Verify package.json dependencies
   - Review build logs

2. **Environment Variable Issues**:
   - Ensure NEXT_PUBLIC_ prefix for client variables
   - Redeploy after adding variables
   - Check variable accessibility

3. **API Connection Problems**:
   - Verify CORS configuration
   - Check API endpoint URLs
   - Test network connectivity

---

## Cost Considerations

### Railway Pricing
- **Free Tier**: $0/month with usage limits
- **Pro Plan**: $20/month per user
- **Database**: Included in plans
- **Bandwidth**: Generous limits

### Vercel Pricing  
- **Hobby**: Free for personal projects
- **Pro**: $20/month per user
- **Enterprise**: Custom pricing
- **Bandwidth**: 100GB included in Pro

### Total Estimated Cost
- **Development**: Free (both platforms)
- **Production**: $40/month (both Pro plans)
- **Scale**: Variable based on usage

---

## Next Steps

1. **Follow Configuration Guides**: Use the specific configuration files provided
2. **Test Thoroughly**: Verify all functionality before production
3. **Monitor Performance**: Set up alerts and monitoring
4. **Plan Scaling**: Consider growth and resource needs
5. **Security Review**: Implement proper security measures

This deployment strategy provides a robust, scalable solution that avoids the package conflicts experienced with Render while maintaining cost-effectiveness and performance.