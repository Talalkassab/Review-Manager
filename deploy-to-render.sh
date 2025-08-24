#!/bin/bash

# Render API deployment script
API_KEY="rnd_T4CWEAYNFj2s6vGMCgy1kBrfgtSb"
REPO_URL="https://github.com/Talalkassab/Review-Manager.git"
BRANCH="main"

echo "🚀 Deploying to Render using API..."

# Create Blueprint deployment
echo "Creating blueprint deployment..."
curl -X POST https://api.render.com/v1/services/blueprints \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Restaurant WhatsApp Agent",
    "repo": "'$REPO_URL'",
    "branch": "'$BRANCH'",
    "autoDeploy": "yes"
  }'

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "📝 Next steps:"
echo "1. Go to https://dashboard.render.com to monitor deployment progress"
echo "2. Wait for all services to be deployed (5-10 minutes)"
echo "3. Update Twilio credentials in the backend service environment variables"
echo "4. Access your services:"
echo "   - Backend: https://restaurant-ai-backend.onrender.com"
echo "   - Frontend: https://restaurant-ai-frontend.onrender.com"