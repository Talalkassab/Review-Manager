# 🚀 Render Deployment Setup

## Environment Variables to Set in Render Dashboard

After deploying with the blueprint, you'll need to manually set these environment variables in the Render dashboard:

### Backend Service Environment Variables

```bash
# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid_from_console
TWILIO_AUTH_TOKEN=your_twilio_auth_token_from_console
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
TWILIO_SANDBOX_CODE=join out-when

# Get your actual credentials from: https://console.twilio.com
# Other variables are already set in render.yaml
```

## Steps After Deployment:

1. **Deploy the Blueprint** - Render will create services from `render.yaml`
2. **Update Environment Variables** - Go to each service settings and add the Twilio credentials above
3. **Restart Services** - Restart both frontend and backend services
4. **Test the Application** - Your app will be live!

## URLs After Deployment:
- **Frontend**: https://restaurant-ai-frontend.onrender.com
- **Backend**: https://restaurant-ai-backend.onrender.com
- **API Docs**: https://restaurant-ai-backend.onrender.com/docs

## Default Login:
- Email: `admin@restaurant.com`
- Password: `admin123`

**Remember to change the admin password after first login!**