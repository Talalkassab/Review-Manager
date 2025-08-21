# 📱 Twilio WhatsApp Setup Guide

This guide will help you set up Twilio WhatsApp for testing the Restaurant AI Customer Feedback Agent.

## 🚀 Quick Setup (5 Minutes)

### Step 1: Create Twilio Account
1. Go to [Twilio.com](https://www.twilio.com/try-twilio)
2. Sign up for a free account
3. Verify your email and phone number
4. You'll receive $15 free credit for testing

### Step 2: Get Your Credentials
1. Go to [Twilio Console](https://console.twilio.com)
2. Find your **Account SID** and **Auth Token** on the dashboard
3. Copy these values - you'll need them for the .env file

### Step 3: Activate WhatsApp Sandbox
1. In Twilio Console, go to **Messaging** → **Try it out** → **Send a WhatsApp message**
2. Or directly visit: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
3. You'll see the sandbox number: **+1 415 523 8886**
4. You'll see your unique join code like: `join example-code`

### Step 4: Join the Sandbox
**Important**: Each phone that will receive messages must join the sandbox first!

1. From your WhatsApp, send the message: `join your-sandbox-code`
2. Send it to: **+1 415 523 8886**
3. You'll receive confirmation: "Twilio Sandbox: ✅ You are all set!"

### Step 5: Configure Environment Variables
Update your `/backend/.env` file:

```env
# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token-here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
TWILIO_SANDBOX_CODE=your-sandbox-code
```

### Step 6: Install Twilio Python SDK
```bash
cd backend
pip install twilio
```

### Step 7: Configure Webhook (Optional for receiving replies)
If you want to receive customer responses:

1. Install ngrok for local testing:
   ```bash
   brew install ngrok  # macOS
   # or download from https://ngrok.com
   ```

2. Start ngrok:
   ```bash
   ngrok http 8000
   ```

3. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

4. In Twilio Console:
   - Go to **Messaging** → **Settings** → **WhatsApp sandbox settings**
   - Set webhook URL: `https://abc123.ngrok.io/api/v1/whatsapp/webhook`
   - Set status callback URL: `https://abc123.ngrok.io/api/v1/whatsapp/status`
   - Save the configuration

## 🧪 Testing the Integration

### Test 1: Send Test Message via API
```bash
# Login first
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/jwt/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@restaurant.com&password=Admin123!" \
  | jq -r '.access_token')

# Send test message (replace with your WhatsApp number)
curl -X POST "http://localhost:8000/api/v1/whatsapp/send-test" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+966501234567"}'
```

### Test 2: Send Greeting to Customer
```bash
# Get a customer ID
CUSTOMER_ID=$(curl -X GET "http://localhost:8000/api/v1/customers/" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.items[0].id')

# Send greeting immediately
curl -X POST "http://localhost:8000/api/v1/whatsapp/send-greeting/$CUSTOMER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"delay_hours": 0}'
```

### Test 3: Schedule Delayed Message
```bash
# Schedule greeting for 2 hours later
curl -X POST "http://localhost:8000/api/v1/whatsapp/send-greeting/$CUSTOMER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"delay_hours": 2}'
```

## 📝 Message Flow Testing

### Customer Journey Test:
1. **Add Customer** via UI with your WhatsApp number
2. **Receive Greeting** (immediately or after delay)
3. **Reply with Rating** (1-4)
4. **Receive Response** based on your rating:
   - Rating 4: Google review request
   - Rating 1-2: Manager follow-up promise
5. **Check Database** for updated feedback

## 🔍 Debugging Tips

### Check Sandbox Info:
```bash
curl http://localhost:8000/api/v1/whatsapp/sandbox-info
```

### Common Issues:

**"User has not joined sandbox"**
- Solution: Send `join your-code` to +14155238886 from WhatsApp

**"Invalid phone number"**
- Solution: Include country code (+966 for Saudi Arabia)

**"Authentication token is invalid"**
- Solution: Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env

**Message not received**
- Check Twilio Console logs: https://console.twilio.com/us1/monitor/logs/messages
- Verify phone number format includes country code
- Ensure sandbox is active (expires after 3 days of inactivity)

## 💰 Costs for Production

### Twilio WhatsApp Pricing:
- **Session Messages** (24-hour window): $0.005 per message
- **Template Messages** (outside 24 hours): $0.0085 per message
- **Saudi Arabia**: ~$0.02 per message

### Monthly Estimate:
- 1000 customers × 2 messages = 2000 messages
- Cost: ~$40/month

## 🚀 Moving to Production

When ready for production:

1. **Apply for WhatsApp Business Account**:
   - Submit business verification to Meta
   - Takes 2-7 business days

2. **Get Dedicated Number**:
   - Purchase Twilio phone number
   - Register with WhatsApp Business

3. **Create Message Templates**:
   - Submit templates for Meta approval
   - Takes 24-48 hours

4. **Update Configuration**:
   ```env
   TWILIO_WHATSAPP_NUMBER=whatsapp:+966501234567  # Your business number
   ENABLE_WHATSAPP=true
   ```

## ✅ Current Implementation Features

- ✅ Send personalized greetings (Arabic/English)
- ✅ Receive and process customer responses
- ✅ Sentiment analysis based on ratings
- ✅ Automatic follow-up for negative feedback
- ✅ Google review requests for positive feedback
- ✅ Message status tracking (sent, delivered, read)
- ✅ Database logging of all interactions
- ✅ Scheduled message sending
- ✅ Webhook for receiving replies

## 📚 Resources

- [Twilio WhatsApp Documentation](https://www.twilio.com/docs/whatsapp)
- [Twilio Python SDK](https://www.twilio.com/docs/libraries/python)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Twilio Console](https://console.twilio.com)

---

**Note**: The sandbox is perfect for testing but has limitations:
- Messages must include "Twilio Sandbox" prefix
- Expires after 3 days of inactivity
- Recipients must join sandbox first

For production, you'll need a verified WhatsApp Business Account.