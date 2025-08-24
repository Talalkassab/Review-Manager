# Railway + Vercel Deployment Verification Guide

## Overview

This guide provides comprehensive testing and verification procedures for your WhatsApp Customer Agent deployment on Railway (backend) and Vercel (frontend).

## Pre-Deployment Checklist

### Backend (Railway) Pre-Deployment

- [ ] All environment variables configured in Railway dashboard
- [ ] PostgreSQL database service added to Railway project
- [ ] `railway.json` configuration file in place
- [ ] Optimized `Dockerfile.railway` ready for deployment
- [ ] CORS origins include Vercel frontend URLs
- [ ] Requirements file optimized for Railway (`requirements-railway.txt`)
- [ ] Database migrations ready (`alembic upgrade head`)

### Frontend (Vercel) Pre-Deployment

- [ ] Repository connected to Vercel
- [ ] Build command configured: `npm run build`
- [ ] Environment variables set in Vercel dashboard
- [ ] `NEXT_PUBLIC_API_URL` points to Railway backend
- [ ] `vercel.json` configuration file in place
- [ ] Node.js version specified in package.json engines

## Deployment Process

### Phase 1: Railway Backend Deployment

#### Step 1: Deploy Backend to Railway

1. **Create Railway Project**:
   ```bash
   # Login to Railway (if not already)
   railway login
   
   # Create new project
   railway new
   
   # Link to existing repository
   railway link
   ```

2. **Add PostgreSQL Database**:
   ```bash
   # Add PostgreSQL service
   railway add postgresql
   
   # Generate database if needed
   railway run python -c "from app.database import create_tables; create_tables()"
   ```

3. **Configure Environment Variables**:
   ```bash
   # Set environment variables via CLI or dashboard
   railway vars set SECRET_KEY="your-secret-key-here"
   railway vars set OPENROUTER_API_KEY="your-api-key"
   railway vars set TWILIO_ACCOUNT_SID="your-twilio-sid"
   railway vars set TWILIO_AUTH_TOKEN="your-twilio-token"
   railway vars set ALLOWED_ORIGINS="https://your-vercel-app.vercel.app"
   ```

4. **Deploy**:
   ```bash
   # Deploy to Railway
   railway up
   
   # Check deployment status
   railway status
   
   # View logs
   railway logs
   ```

#### Step 2: Verify Backend Deployment

1. **Health Check Test**:
   ```bash
   curl https://your-railway-app.railway.app/health
   
   # Expected response:
   # {
   #   "status": "healthy",
   #   "timestamp": ...,
   #   "version": "1.0.0",
   #   "environment": "production"
   # }
   ```

2. **Database Connection Test**:
   ```bash
   curl https://your-railway-app.railway.app/api/v1/restaurants
   
   # Should return empty array or existing restaurants
   ```

3. **CORS Test**:
   ```bash
   curl -H "Origin: https://your-vercel-app.vercel.app" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: Content-Type" \
        -X OPTIONS \
        https://your-railway-app.railway.app/api/v1/health
   
   # Check for CORS headers in response
   ```

### Phase 2: Vercel Frontend Deployment

#### Step 1: Deploy Frontend to Vercel

1. **Connect Repository to Vercel**:
   - Go to Vercel dashboard
   - Import project from GitHub
   - Select frontend directory if using monorepo

2. **Configure Build Settings**:
   ```json
   {
     "buildCommand": "npm run build",
     "outputDirectory": ".next",
     "installCommand": "npm ci",
     "framework": "nextjs"
   }
   ```

3. **Set Environment Variables**:
   ```bash
   # Via Vercel CLI or dashboard
   vercel env add NEXT_PUBLIC_API_URL
   # Enter: https://your-railway-app.railway.app
   
   vercel env add NEXT_PUBLIC_ENVIRONMENT
   # Enter: production
   ```

4. **Deploy**:
   ```bash
   # Deploy to Vercel
   vercel --prod
   
   # Or push to main branch for automatic deployment
   git push origin main
   ```

#### Step 2: Verify Frontend Deployment

1. **Build Success Check**:
   - Verify build completed without errors in Vercel dashboard
   - Check build logs for any warnings or issues

2. **Environment Variables Check**:
   ```javascript
   // Test in browser console
   console.log(process.env.NEXT_PUBLIC_API_URL);
   // Should output your Railway backend URL
   ```

3. **API Connection Test**:
   ```javascript
   // Test API connection from browser
   fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`)
     .then(response => response.json())
     .then(data => console.log('Backend health:', data))
     .catch(error => console.error('Connection failed:', error));
   ```

## Integration Testing

### End-to-End Testing Scripts

#### Backend API Testing

Create `tests/api-integration-test.js`:

```javascript
const axios = require('axios');

const API_BASE_URL = process.env.API_URL || 'https://your-railway-app.railway.app';

async function testBackendAPI() {
  console.log('🧪 Starting Backend API Tests...\n');
  
  try {
    // Test 1: Health Check
    console.log('1. Testing Health Check...');
    const healthResponse = await axios.get(`${API_BASE_URL}/health`);
    console.log('✅ Health check passed:', healthResponse.data);
    
    // Test 2: API V1 Endpoints
    console.log('\n2. Testing API V1 endpoints...');
    
    // Test restaurants endpoint
    const restaurantsResponse = await axios.get(`${API_BASE_URL}/api/v1/restaurants`);
    console.log('✅ Restaurants endpoint accessible:', restaurantsResponse.status);
    
    // Test customers endpoint
    const customersResponse = await axios.get(`${API_BASE_URL}/api/v1/customers`);
    console.log('✅ Customers endpoint accessible:', customersResponse.status);
    
    // Test 3: CORS Headers
    console.log('\n3. Testing CORS configuration...');
    const corsResponse = await axios.options(`${API_BASE_URL}/api/v1/health`, {
      headers: {
        'Origin': 'https://your-vercel-app.vercel.app',
        'Access-Control-Request-Method': 'GET'
      }
    });
    console.log('✅ CORS headers present:', corsResponse.headers['access-control-allow-origin']);
    
    console.log('\n🎉 All backend tests passed!');
    
  } catch (error) {
    console.error('❌ Backend test failed:', error.response?.data || error.message);
    process.exit(1);
  }
}

testBackendAPI();
```

#### Frontend Integration Testing

Create `tests/frontend-integration-test.js`:

```javascript
const axios = require('axios');

const FRONTEND_URL = process.env.FRONTEND_URL || 'https://your-vercel-app.vercel.app';
const API_URL = process.env.API_URL || 'https://your-railway-app.railway.app';

async function testFrontendIntegration() {
  console.log('🧪 Starting Frontend Integration Tests...\n');
  
  try {
    // Test 1: Frontend Accessibility
    console.log('1. Testing frontend accessibility...');
    const frontendResponse = await axios.get(FRONTEND_URL);
    console.log('✅ Frontend accessible:', frontendResponse.status);
    
    // Test 2: API Integration from Frontend Context
    console.log('\n2. Testing API integration...');
    
    // Simulate frontend API call with proper headers
    const apiResponse = await axios.get(`${API_URL}/api/v1/health`, {
      headers: {
        'Origin': FRONTEND_URL,
        'Content-Type': 'application/json'
      }
    });
    console.log('✅ Frontend-Backend integration working:', apiResponse.data);
    
    // Test 3: Authentication Flow (if applicable)
    console.log('\n3. Testing authentication endpoints...');
    try {
      const authResponse = await axios.post(`${API_URL}/api/v1/auth/login`, {
        username: 'test',
        password: 'test'
      }, {
        headers: {
          'Origin': FRONTEND_URL,
          'Content-Type': 'application/json'
        }
      });
      console.log('✅ Auth endpoint accessible');
    } catch (authError) {
      if (authError.response?.status === 401 || authError.response?.status === 422) {
        console.log('✅ Auth endpoint accessible (expected auth failure)');
      } else {
        throw authError;
      }
    }
    
    console.log('\n🎉 All integration tests passed!');
    
  } catch (error) {
    console.error('❌ Integration test failed:', error.response?.data || error.message);
    process.exit(1);
  }
}

testFrontendIntegration();
```

### Automated Testing with GitHub Actions

Create `.github/workflows/deploy-test.yml`:

```yaml
name: Deployment Testing

on:
  deployment_status

jobs:
  test-deployment:
    if: github.event.deployment_status.state == 'success'
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: npm install axios
    
    - name: Test Backend API
      env:
        API_URL: ${{ secrets.RAILWAY_API_URL }}
      run: node tests/api-integration-test.js
    
    - name: Test Frontend Integration
      env:
        FRONTEND_URL: ${{ secrets.VERCEL_URL }}
        API_URL: ${{ secrets.RAILWAY_API_URL }}
      run: node tests/frontend-integration-test.js
    
    - name: Notify on Success
      if: success()
      run: echo "🎉 Deployment verification successful!"
    
    - name: Notify on Failure
      if: failure()
      run: echo "❌ Deployment verification failed!"
```

## Performance Testing

### Load Testing Script

Create `tests/load-test.js`:

```javascript
const axios = require('axios');

async function performanceTest() {
  const API_URL = process.env.API_URL || 'https://your-railway-app.railway.app';
  const CONCURRENT_REQUESTS = 10;
  const TOTAL_REQUESTS = 100;
  
  console.log(`🚀 Starting load test: ${TOTAL_REQUESTS} requests with ${CONCURRENT_REQUESTS} concurrent`);
  
  const startTime = Date.now();
  const results = [];
  
  for (let i = 0; i < TOTAL_REQUESTS; i += CONCURRENT_REQUESTS) {
    const batch = Array.from({ length: Math.min(CONCURRENT_REQUESTS, TOTAL_REQUESTS - i) }, 
      (_, index) => testSingleRequest(API_URL, i + index));
    
    const batchResults = await Promise.allSettled(batch);
    results.push(...batchResults);
    
    // Small delay between batches
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  const endTime = Date.now();
  const totalTime = endTime - startTime;
  
  const successful = results.filter(r => r.status === 'fulfilled').length;
  const failed = results.filter(r => r.status === 'rejected').length;
  
  console.log(`\n📊 Load Test Results:`);
  console.log(`Total time: ${totalTime}ms`);
  console.log(`Successful requests: ${successful}`);
  console.log(`Failed requests: ${failed}`);
  console.log(`Success rate: ${(successful/TOTAL_REQUESTS*100).toFixed(2)}%`);
  console.log(`Average response time: ${(totalTime/TOTAL_REQUESTS).toFixed(2)}ms`);
}

async function testSingleRequest(baseUrl, requestId) {
  const start = Date.now();
  try {
    await axios.get(`${baseUrl}/health`);
    return { requestId, time: Date.now() - start, success: true };
  } catch (error) {
    return { requestId, time: Date.now() - start, success: false, error: error.message };
  }
}

performanceTest();
```

## Monitoring Setup

### Health Check Monitoring

Create `monitoring/health-check.js`:

```javascript
const axios = require('axios');

async function continuousHealthCheck() {
  const API_URL = process.env.API_URL || 'https://your-railway-app.railway.app';
  const FRONTEND_URL = process.env.FRONTEND_URL || 'https://your-vercel-app.vercel.app';
  const CHECK_INTERVAL = 5 * 60 * 1000; // 5 minutes
  
  console.log('🔍 Starting continuous health monitoring...');
  
  setInterval(async () => {
    try {
      // Check backend health
      const backendStart = Date.now();
      const backendResponse = await axios.get(`${API_URL}/health`, { timeout: 10000 });
      const backendTime = Date.now() - backendStart;
      
      // Check frontend accessibility
      const frontendStart = Date.now();
      const frontendResponse = await axios.get(FRONTEND_URL, { timeout: 10000 });
      const frontendTime = Date.now() - frontendStart;
      
      console.log(`✅ [${new Date().toISOString()}] Health Check Passed`);
      console.log(`   Backend: ${backendTime}ms (${backendResponse.status})`);
      console.log(`   Frontend: ${frontendTime}ms (${frontendResponse.status})`);
      
      // Alert if response times are too high
      if (backendTime > 5000 || frontendTime > 5000) {
        console.log('⚠️  WARNING: High response times detected!');
      }
      
    } catch (error) {
      console.error(`❌ [${new Date().toISOString()}] Health Check Failed:`, error.message);
      
      // Here you could integrate with alerting services
      // await sendAlert(error);
    }
  }, CHECK_INTERVAL);
}

continuousHealthCheck();
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Backend Deployment Issues

**Issue**: `ModuleNotFoundError` during Railway build
```
Solution: 
- Check requirements-railway.txt for missing dependencies
- Verify Python version compatibility (3.11)
- Check for system dependencies in Dockerfile.railway
```

**Issue**: Database connection fails
```
Solution:
- Verify PostgreSQL service is added to Railway project
- Check DATABASE_URL environment variable
- Ensure database migrations ran successfully
```

**Issue**: CORS errors from frontend
```
Solution:
- Verify ALLOWED_ORIGINS includes Vercel URL
- Check CORS middleware configuration
- Test with curl/Postman first
```

#### 2. Frontend Deployment Issues

**Issue**: Build fails on Vercel
```
Solution:
- Check Node.js version in package.json engines
- Verify all dependencies in package.json
- Check build logs for specific errors
```

**Issue**: Environment variables not available
```
Solution:
- Ensure NEXT_PUBLIC_ prefix for client-side variables
- Redeploy after adding environment variables
- Check Vercel environment variable settings
```

**Issue**: API calls fail from frontend
```
Solution:
- Verify NEXT_PUBLIC_API_URL is correct
- Check network tab for actual request URLs
- Test API endpoints directly
```

### Debug Commands

```bash
# Railway debugging
railway logs --tail
railway vars
railway status
railway shell

# Vercel debugging  
vercel logs
vercel env ls
vercel inspect

# Local testing
npm run build
npm run start
curl http://localhost:3000/api/health
```

## Final Verification Checklist

### Production Readiness Checklist

- [ ] Backend responds to health checks consistently
- [ ] Database connections are stable and performant
- [ ] All API endpoints accessible from frontend
- [ ] Authentication flow works end-to-end
- [ ] CORS configuration allows frontend requests
- [ ] Error handling works properly
- [ ] Log aggregation is functional
- [ ] Performance is within acceptable ranges
- [ ] Security headers are configured
- [ ] SSL/HTTPS is working correctly

### Performance Benchmarks

- [ ] Backend response time < 500ms (95th percentile)
- [ ] Frontend initial load < 3 seconds
- [ ] API requests complete < 2 seconds
- [ ] Database queries < 100ms (average)
- [ ] No memory leaks under load
- [ ] Concurrent user handling verified

### Security Verification

- [ ] No sensitive data in logs
- [ ] Environment variables properly secured
- [ ] HTTPS enforced on all endpoints
- [ ] Authentication tokens working correctly
- [ ] Rate limiting functional
- [ ] Input validation working

This comprehensive verification process ensures your Railway + Vercel deployment is production-ready and performing optimally.