# Railway-Vercel CORS Configuration Guide

## Overview

This guide provides the complete CORS (Cross-Origin Resource Sharing) configuration needed for seamless integration between your Railway backend and Vercel frontend deployment.

## Common CORS Issues with Railway-Vercel

### 1. Preflight Request Failures
- Railway's HTTP edge proxy properly forwards OPTIONS requests
- Ensure explicit handling of OPTIONS method in FastAPI
- Configure proper CORS headers for preflight responses

### 2. URL Configuration Problems
- Use absolute URLs for API calls from Vercel
- Avoid relative paths that resolve incorrectly across domains
- Ensure consistent protocol (HTTPS) in production

### 3. Credential and Cookie Issues
- Configure `allow_credentials=True` for authenticated requests
- Ensure frontend sends credentials with requests when needed
- Handle authentication tokens properly across domains

## FastAPI CORS Configuration (Railway Backend)

### Optimized Configuration

Update your `backend/app/main.py` CORS configuration:

```python
from fastapi.middleware.cors import CORSMiddleware
import os

# CORS configuration optimized for Railway-Vercel integration
def get_cors_origins():
    """Get CORS origins from environment with sensible defaults."""
    origins = [
        "http://localhost:3000",      # Local development
        "http://localhost:3001", 
        "https://localhost:3000",     # Local HTTPS development
    ]
    
    # Add production origins from environment
    if allowed_origins := os.getenv("ALLOWED_ORIGINS"):
        production_origins = [origin.strip() for origin in allowed_origins.split(",")]
        origins.extend(production_origins)
    
    # Add Vercel preview domains (for preview deployments)
    if vercel_url := os.getenv("VERCEL_URL"):
        origins.append(f"https://{vercel_url}")
    
    return origins

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,  # Enable if using authentication cookies
    allow_methods=[
        "GET", 
        "POST", 
        "PUT", 
        "DELETE", 
        "PATCH", 
        "OPTIONS", 
        "HEAD"
    ],
    allow_headers=[
        "*",  # Allow all headers, or specify: ["Content-Type", "Authorization", "X-Requested-With"]
    ],
    expose_headers=[
        "Content-Range", 
        "X-Content-Range", 
        "X-Total-Count",
        "Authorization"  # If you need to expose auth headers
    ],
    max_age=86400,  # Cache preflight responses for 24 hours
)

# Explicit OPTIONS handler for problematic endpoints
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle preflight OPTIONS requests explicitly."""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",  # Or specific origin
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Max-Age": "86400",
        }
    )
```

### Enhanced Configuration with Origin Validation

For production security, implement origin validation:

```python
def validate_origin(origin: str) -> bool:
    """Validate if origin is allowed."""
    allowed_patterns = [
        r"^https://.*\.vercel\.app$",        # Vercel deployments
        r"^https://.*\.railway\.app$",       # Railway deployments  
        r"^https://your-domain\.com$",       # Your custom domain
        r"^http://localhost:\d+$",           # Local development
    ]
    
    import re
    return any(re.match(pattern, origin) for pattern in allowed_patterns)

# Custom CORS middleware with validation
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    """Custom CORS middleware with origin validation."""
    origin = request.headers.get("origin")
    
    # Process the request
    response = await call_next(request)
    
    # Add CORS headers if origin is valid
    if origin and validate_origin(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        response.headers["Access-Control-Expose-Headers"] = "Content-Range, X-Content-Range, X-Total-Count"
    
    return response
```

## Environment Configuration

### Railway Backend Environment Variables

```bash
# CORS Configuration for Railway
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,https://your-custom-domain.com

# Optional: Enable CORS debugging
CORS_DEBUG=true
ENVIRONMENT=production
```

### Vercel Frontend Configuration

Update your API client configuration:

```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  withCredentials: true,  // Include credentials (cookies/auth) in requests
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request interceptor for auth tokens
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export { apiClient };
```

### Next.js Configuration Updates

Update `next.config.ts` for better API integration:

```typescript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // API rewrites for development
  async rewrites() {
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
      ];
    }
    return [];
  },
  
  // Headers for CORS and security
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
    ];
  },
  
  // Environment variables validation
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
};

export default nextConfig;
```

## Testing CORS Configuration

### 1. Development Testing

Test CORS during development:

```bash
# Test from browser console on your Vercel preview
fetch('https://your-railway-app.railway.app/api/v1/health', {
  method: 'GET',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
  },
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('CORS Error:', error));
```

### 2. Automated CORS Testing

Create a test script for CORS validation:

```javascript
// tests/cors-test.js
const axios = require('axios');

async function testCORS() {
  const backendUrl = process.env.BACKEND_URL || 'https://your-railway-app.railway.app';
  const frontendUrl = process.env.FRONTEND_URL || 'https://your-vercel-app.vercel.app';
  
  try {
    // Test preflight request
    const preflightResponse = await axios({
      method: 'OPTIONS',
      url: `${backendUrl}/api/v1/health`,
      headers: {
        'Origin': frontendUrl,
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type',
      },
    });
    
    console.log('Preflight Response Headers:', preflightResponse.headers);
    
    // Test actual request
    const response = await axios({
      method: 'GET',
      url: `${backendUrl}/api/v1/health`,
      headers: {
        'Origin': frontendUrl,
      },
    });
    
    console.log('Request successful:', response.data);
    
  } catch (error) {
    console.error('CORS Test Failed:', error.response?.data || error.message);
  }
}

testCORS();
```

## Common Issues and Solutions

### Issue 1: "Access to fetch blocked by CORS policy"

**Solution**: Ensure your backend includes the frontend domain in allowed origins:

```python
# In Railway environment variables
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,https://preview-123.your-vercel-app.vercel.app
```

### Issue 2: "Preflight request doesn't pass access control check"

**Solution**: Add explicit OPTIONS handler:

```python
@app.options("/{path:path}")
async def handle_options(path: str):
    return Response(status_code=200)
```

### Issue 3: "Credentials not included in CORS request"

**Solution**: Configure both frontend and backend for credentials:

```python
# Backend
allow_credentials=True

# Frontend
withCredentials: true  // in axios config
```

### Issue 4: "Custom headers not allowed"

**Solution**: Add custom headers to CORS config:

```python
allow_headers=["Content-Type", "Authorization", "X-Custom-Header"]
```

## Production Deployment Checklist

### Railway Backend
- [ ] Environment variable `ALLOWED_ORIGINS` set with Vercel URL
- [ ] CORS middleware configured with proper origins
- [ ] OPTIONS endpoints handled explicitly
- [ ] Health check endpoint responds correctly
- [ ] HTTPS enforced in production

### Vercel Frontend  
- [ ] `NEXT_PUBLIC_API_URL` points to Railway backend
- [ ] API client configured with proper headers
- [ ] Credentials handling configured if needed
- [ ] Error handling for network failures implemented
- [ ] Build successful with environment variables

### Integration Testing
- [ ] Frontend can reach backend health check
- [ ] Authentication flow works end-to-end
- [ ] API calls succeed from production frontend
- [ ] CORS preflight requests pass
- [ ] Error responses handled properly

## Performance Considerations

### 1. Preflight Caching
Set appropriate `max_age` for preflight responses to reduce unnecessary OPTIONS requests:

```python
# Cache preflight responses for 24 hours
max_age=86400
```

### 2. Origin Validation Optimization
Use compiled regex patterns for origin validation:

```python
import re
COMPILED_PATTERNS = [re.compile(pattern) for pattern in allowed_patterns]
```

### 3. Response Header Optimization
Only expose necessary headers to reduce response size:

```python
expose_headers=["Content-Length", "X-Total-Count"]  # Only what you need
```

## Security Best Practices

### 1. Specific Origins in Production
Never use `"*"` for origins in production:

```python
# Development only
allow_origins=["*"] if DEBUG else specific_origins
```

### 2. Header Restrictions
Be specific about allowed headers:

```python
allow_headers=["Content-Type", "Authorization"] # Don't use "*" in production
```

### 3. Method Restrictions
Only allow necessary HTTP methods:

```python
allow_methods=["GET", "POST", "PUT", "DELETE"] # Don't include unnecessary methods
```

This configuration ensures seamless Railway-Vercel integration while maintaining security and performance best practices.