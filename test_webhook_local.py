#!/usr/bin/env python3
"""
Test WhatsApp webhook locally to verify AI integration
"""
import requests
import json

def test_webhook():
    """Test the WhatsApp webhook with sample data"""
    
    # Try different Railway URLs
    possible_urls = [
        "https://customer-whatsapp-agent-production-5e03.up.railway.app",
        "https://customer-whatsapp-agent-production.up.railway.app",
        "https://web-production-5e03.up.railway.app"
    ]
    
    # Sample WhatsApp webhook data
    test_data = {
        'From': 'whatsapp:+966501234567',
        'Body': 'أيش أحسن طبق عندكم؟',  # What's your best dish?
        'MessageSid': 'test_message_' + str(int(time.time()) if 'time' in dir() else 12345),
        'To': 'whatsapp:+14155238886'
    }
    
    print("🧪 Testing WhatsApp Webhook with AI Agent...")
    print("=" * 60)
    print(f"📤 Test Message: {test_data['Body']}")
    print("=" * 60)
    
    for url in possible_urls:
        webhook_url = f"{url}/api/v1/whatsapp/webhook"
        test_url = f"{url}/api/v1/whatsapp/test"
        
        print(f"\n🔗 Trying: {url}")
        
        # First try the test endpoint
        try:
            response = requests.get(test_url, timeout=10)
            if response.status_code == 200:
                print(f"✅ Test endpoint working: {response.status_code}")
                test_result = response.json()
                
                # Check if AI system is available
                if 'system_checks' in test_result:
                    for check, status in test_result['system_checks'].items():
                        print(f"   {check}: {status}")
                
                # Now test the webhook
                print(f"\n📨 Testing webhook...")
                webhook_response = requests.post(webhook_url, data=test_data, timeout=15)
                print(f"📨 Webhook Response ({webhook_response.status_code}): {webhook_response.text}")
                
                if webhook_response.status_code == 200 and "Error" not in webhook_response.text:
                    print("🎉 Webhook test successful!")
                    return True
                else:
                    print("⚠️ Webhook returned error")
                    
            else:
                print(f"❌ Test endpoint failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection failed: {str(e)}")
            continue
    
    print("\n❌ All webhook tests failed")
    return False

if __name__ == "__main__":
    import time
    test_webhook()