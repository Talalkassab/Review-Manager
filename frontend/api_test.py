#!/usr/bin/env python3
"""
Direct API test to create customer and send WhatsApp message
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def test_customer_creation_api():
    """Test creating a customer visit via direct API calls"""
    
    base_url = "http://localhost:8000/api/v1"
    
    async with aiohttp.ClientSession() as session:
        try:
            print("🔐 Logging in to get authentication token...")
            
            # Try to register first (in case user doesn't exist)
            register_data = {
                "email": "admin@restaurant.com", 
                "password": "admin123",
                "is_active": True,
                "is_superuser": True
            }
            
            async with session.post(f"{base_url}/auth/register", json=register_data) as resp:
                if resp.status == 201:
                    print("✅ User registered successfully")
                else:
                    print(f"ℹ️  User registration status: {resp.status} (user may already exist)")
            
            # Login to get auth token
            login_data = {
                "username": "admin@restaurant.com",
                "password": "admin123"
            }
            
            async with session.post(f"{base_url}/auth/jwt/login", data=login_data) as resp:
                if resp.status == 200:
                    login_result = await resp.json()
                    token = login_result.get("access_token")
                    print(f"✅ Login successful, got token: {token[:20]}...")
                    
                    # Set authorization header for future requests
                    headers = {"Authorization": f"Bearer {token}"}
                else:
                    print(f"❌ Login failed: {resp.status}")
                    print(await resp.text())
                    return
            
            print("\n🏪 Getting restaurants...")
            async with session.get(f"{base_url}/restaurants/", headers=headers) as resp:
                if resp.status == 200:
                    restaurants = await resp.json()
                    print(f"✅ Found {len(restaurants)} restaurants")
                    
                    # Find Naandori restaurant
                    naandori = None
                    for restaurant in restaurants:
                        if restaurant.get("name") == "Naandori":
                            naandori = restaurant
                            break
                    
                    if naandori:
                        print(f"✅ Found Naandori restaurant: {naandori['id']}")
                        restaurant_id = naandori['id']
                    else:
                        print("❌ Naandori restaurant not found")
                        print("Available restaurants:")
                        for restaurant in restaurants:
                            print(f"  - {restaurant.get('name')} ({restaurant.get('id')})")
                        return
                else:
                    print(f"❌ Failed to get restaurants: {resp.status}")
                    return
            
            print(f"\n👤 Creating customer with phone +966561876440...")
            
            # Create customer data - no name to test "Dear Customer" functionality
            customer_data = {
                "phone_number": "+966561876440",
                "preferred_language": "ar",
                "restaurant_id": restaurant_id,
                "visit_date": datetime.utcnow().isoformat(),
                "party_size": 1,
                "whatsapp_opt_in": True,
                "email_opt_in": True,
                "gdpr_consent": True
            }
            
            # Generate customer number
            async with session.get(f"{base_url}/customers/", headers=headers) as resp:
                if resp.status == 200:
                    existing_customers = await resp.json()
                    customer_count = len(existing_customers) + 1
                    customer_data["customer_number"] = f"CUST-{customer_count:06d}"
                    print(f"✅ Generated customer number: {customer_data['customer_number']}")
                else:
                    print("⚠️  Using default customer number")
                    customer_data["customer_number"] = "CUST-000001"
            
            # Create the customer
            async with session.post(f"{base_url}/customers/", 
                                   json=customer_data, 
                                   headers=headers) as resp:
                if resp.status == 201:
                    customer = await resp.json()
                    customer_id = customer.get("id")
                    print(f"✅ Customer created successfully!")
                    print(f"   - ID: {customer_id}")
                    print(f"   - Number: {customer.get('customer_number')}")
                    print(f"   - Phone: {customer.get('phone_number')}")
                    print(f"   - Display Name: {customer.get('display_name')}")
                else:
                    print(f"❌ Failed to create customer: {resp.status}")
                    error_text = await resp.text()
                    print(f"   Error: {error_text}")
                    return
            
            print(f"\n📱 Sending WhatsApp message to {customer_data['phone_number']}...")
            
            # Send WhatsApp message
            whatsapp_url = f"{base_url}/whatsapp/send-greeting/{customer_id}"
            async with session.post(whatsapp_url, headers=headers) as resp:
                if resp.status == 200:
                    whatsapp_result = await resp.json()
                    print("✅ WhatsApp message sent successfully!")
                    print(f"   - Message SID: {whatsapp_result.get('message_sid')}")
                    print(f"   - Status: {whatsapp_result.get('status')}")
                    print(f"   - To: {whatsapp_result.get('to')}")
                    
                    print("\n🎯 TEST COMPLETED SUCCESSFULLY!")
                    print("="*50)
                    print(f"✅ Customer created: {customer_data['customer_number']}")
                    print(f"✅ WhatsApp message sent to: {customer_data['phone_number']}")
                    print(f"✅ Message will use greeting: 'عزيزنا العميل' (no name provided)")
                    print("="*50)
                    
                else:
                    print(f"❌ Failed to send WhatsApp message: {resp.status}")
                    error_text = await resp.text()
                    print(f"   Error: {error_text}")
                    
                    # Check if it's a sandbox issue
                    if "join" in error_text.lower():
                        print("\n📱 TWILIO SANDBOX SETUP REQUIRED:")
                        print("The customer needs to send the following message to the Twilio WhatsApp number:")
                        print("Message: 'join out-when'")
                        print("To: +14155238886")
                        print("\nAfter joining the sandbox, the message will be delivered successfully.")
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting API-based customer creation and WhatsApp test...")
    asyncio.run(test_customer_creation_api())