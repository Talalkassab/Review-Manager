# Render Deployment Checklist

## Pre-Deployment Verification ✅

### 1. Docker Configuration Status
- [x] **Backend Dockerfile**: Optimized with startup script for migrations
- [x] **Frontend Dockerfile**: Configured for Next.js production build
- [x] **Docker ignore files**: Created to exclude unnecessary files
- [x] **render.yaml**: Updated to use Docker runtime

### 2. Files Included in Docker Containers

#### Backend Container Includes:
- ✅ Python application code (`app/` directory)
- ✅ Requirements.txt with all dependencies
- ✅ Alembic migration files
- ✅ Startup script for database migrations
- ❌ Excluded: Test files, screenshots, .env files, development scripts

#### Frontend Container Includes:
- ✅ Next.js application code (`src/` directory)
- ✅ Package.json and package-lock.json
- ✅ Public assets
- ✅ Production build configuration
- ❌ Excluded: Test files, .env files, development scripts

### 3. Environment Variables Configuration

#### Backend Required Variables:
```yaml
DATABASE_URL         # ✅ Auto-configured from Render database
SECRET_KEY          # ✅ Auto-generated
TWILIO_ACCOUNT_SID  # ⚠️ MANUAL: Update after deployment
TWILIO_AUTH_TOKEN   # ⚠️ MANUAL: Update after deployment
TWILIO_WHATSAPP_NUMBER  # ✅ Pre-configured for sandbox
BACKEND_CORS_ORIGINS    # ✅ Pre-configured
```

#### Frontend Variables:
```yaml
NEXT_PUBLIC_API_URL  # ✅ Points to backend service
NODE_ENV            # ✅ Set to production
PORT               # ✅ Set to 3000
```

## Deployment Steps

### 1. Initial Deployment
```bash
# Option 1: Deploy via GitHub integration
1. Push code to GitHub
2. Connect repository in Render Dashboard
3. Deploy using render.yaml blueprint

# Option 2: Deploy via Render CLI
render blueprint deploy
```

### 2. Post-Deployment Actions

#### Critical Actions:
1. **Update Twilio Credentials**
   - Go to Render Dashboard → Backend Service → Environment
   - Update `TWILIO_ACCOUNT_SID` with your actual SID
   - Update `TWILIO_AUTH_TOKEN` with your actual token
   - Restart service

2. **Verify Database Connection**
   - Check backend logs for successful migration
   - Confirm "Database connected" message

3. **Test WhatsApp Integration**
   - Send test message to sandbox number
   - Verify webhook receives messages

#### Optional Actions:
1. Set up custom domain
2. Configure monitoring alerts
3. Set up log aggregation

## Service Health Checks

### Backend Service
- **Health Endpoint**: `https://restaurant-ai-backend.onrender.com/docs`
- **Expected Response**: FastAPI documentation page
- **Database Check**: `/api/v1/health` endpoint

### Frontend Service
- **Health Check**: `https://restaurant-ai-frontend.onrender.com`
- **Expected Response**: Login page or dashboard

## Common Issues & Solutions

### Issue 1: Database Connection Failed
**Solution**: 
- Verify DATABASE_URL is properly set
- Check if database service is running
- Review migration logs in build output

### Issue 2: CORS Errors
**Solution**:
- Verify BACKEND_CORS_ORIGINS includes frontend URL
- Check both services are using HTTPS

### Issue 3: WhatsApp Messages Not Received
**Solution**:
- Verify Twilio credentials are updated
- Check webhook URL in Twilio console
- Review backend logs for webhook errors

### Issue 4: Build Timeout
**Solution**:
- Render free tier has 15-minute build limit
- Consider upgrading if builds exceed limit
- Optimize Docker layers for caching

## Monitoring & Logs

### View Logs:
1. **Backend Logs**: 
   - Render Dashboard → restaurant-ai-backend → Logs
   - Look for: Database connection, API requests, WhatsApp webhooks

2. **Frontend Logs**:
   - Render Dashboard → restaurant-ai-frontend → Logs
   - Look for: Build output, Next.js startup, API connection

### Key Metrics to Monitor:
- Response time (should be < 1s for API calls)
- Memory usage (free tier: 512MB limit)
- Database connections (free tier: 5 connection limit)
- Build duration (should be < 10 minutes)

## Rollback Procedure

If deployment fails:
1. Go to Render Dashboard → Service → Deploys
2. Find last successful deployment
3. Click "Rollback to this deploy"
4. Investigate issues in failed deployment logs

## Security Checklist

- [x] No secrets in Dockerfiles
- [x] Environment variables used for sensitive data
- [x] HTTPS enforced for all services
- [x] Database credentials managed by Render
- [ ] Update default admin password after deployment
- [ ] Review and restrict CORS origins for production

## Performance Optimization

### Current Optimizations:
- ✅ Multi-stage builds avoided (using slim images)
- ✅ Docker layer caching optimized
- ✅ Static assets served by CDN (frontend)
- ✅ Database connection pooling configured

### Future Optimizations:
- Consider Redis for caching (Render Redis service)
- Implement CDN for API responses
- Add horizontal scaling for high traffic

## Deployment Validation

After deployment, verify:
1. [ ] Both services show "Live" status
2. [ ] Database migrations completed successfully
3. [ ] Frontend can communicate with backend
4. [ ] WhatsApp webhook is accessible
5. [ ] Admin login works
6. [ ] Customer creation works
7. [ ] WhatsApp messages are received and processed

## Support Resources

- **Render Documentation**: https://render.com/docs
- **Render Status Page**: https://status.render.com
- **Project Issues**: GitHub repository issues
- **Twilio Console**: https://console.twilio.com

---

## Deployment Status: READY ✅

Your WhatsApp Customer Agent project is fully prepared for Render deployment. All Docker configurations follow best practices, environment variables are properly configured, and the deployment process is streamlined.

**Next Step**: Deploy via Render Dashboard or CLI, then complete post-deployment actions.