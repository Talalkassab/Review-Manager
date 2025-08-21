#!/usr/bin/env python3
"""
Simple WhatsApp Conversation Testing
Tests the conversation logic without complex session management
"""
import asyncio
import sys
sys.path.append('/Users/hanouf/Desktop/projects/Customer-Whatsapp-agent/backend')

from app.database import db_manager
from app.models import Customer, Restaurant
from sqlalchemy import select

async def test_conversation_responses():
    """Test different customer response scenarios"""
    
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        # Get Naandori restaurant
        stmt = select(Restaurant).where(Restaurant.name == 'Naandori')
        result = await session.execute(stmt)
        restaurant = result.scalar_one_or_none()
        
        # Get customer
        stmt = select(Customer).where(
            Customer.phone_number == '+966561876440',
            Customer.customer_number == 'CUST-000001'
        )
        result = await session.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not restaurant or not customer:
            print("❌ Restaurant or customer not found")
            return
        
        print("🎭 WHATSAPP CONVERSATION SIMULATION")
        print("="*60)
        print(f"🏪 Restaurant: {restaurant.name} ({restaurant.name_arabic})")
        print(f"👤 Customer: {customer.display_name} ({customer.phone_number})")
        print(f"🌐 Language: {customer.preferred_language}")
        print(f"💬 Greeting: {customer.get_greeting()}")
        
        # Show initial message that was already sent
        print("\n📤 INITIAL MESSAGE SENT:")
        print("-" * 40)
        initial_message = f"""
{customer.get_greeting()}! 🌟

نتمنى أن تكون قد استمتعت بزيارتك الأمس لمطعم {restaurant.name_arabic or restaurant.name}! 

كما تعلم، نحن في {restaurant.name} نحب أن نشارك متعة النكهات الأصيلة مع لمسة عصرية. 🍛✨

هل يمكنك مشاركتنا تجربتك؟ رأيك مهم جداً لنا ويساعدنا في تقديم أفضل خدمة لك ولضيوفنا الكرام.

شكراً لك على اختيارك لنا! 🙏

فريق {restaurant.name}
📞 {restaurant.phone_number}
        """.strip()
        print(initial_message)
        
        # Test different response scenarios
        scenarios = [
            {
                "name": "📊 Rating Response (Excellent)",
                "input": "5",
                "expected": "Positive rating, Google review request"
            },
            {
                "name": "📊 Rating Response (Poor)",
                "input": "2", 
                "expected": "Negative rating, follow-up request"
            },
            {
                "name": "💬 Text Feedback (Positive)",
                "input": "كان الطعام لذيذ جداً والخدمة ممتازة!",
                "expected": "Thank you message"
            },
            {
                "name": "💬 Text Feedback (Negative)", 
                "input": "الطعام كان بارد والخدمة بطيئة",
                "expected": "Apology and follow-up"
            }
        ]
        
        print("\n🧪 TESTING CONVERSATION SCENARIOS:")
        print("="*60)
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{i}. {scenario['name']}")
            print("-" * 50)
            print(f"📥 CUSTOMER INPUT: '{scenario['input']}'")
            print(f"🎯 EXPECTED: {scenario['expected']}")
            
            # Import and test the response logic directly
            from app.api.whatsapp import process_customer_response
            
            # Create a fresh customer object for testing
            test_customer = Customer(
                customer_number=customer.customer_number,
                phone_number=customer.phone_number,
                preferred_language=customer.preferred_language,
                restaurant_id=customer.restaurant_id
            )
            
            try:
                response = await process_customer_response(
                    test_customer, 
                    scenario['input'], 
                    session
                )
                
                if response:
                    print(f"📤 BOT RESPONSE:")
                    print(response)
                    print("✅ Response generated successfully")
                else:
                    print("🔇 No automated response")
                    
                # Show updated customer state
                print(f"📊 Customer Rating: {test_customer.rating or 'Not set'}")
                print(f"😊 Sentiment: {test_customer.feedback_sentiment or 'Not set'}")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        print("\n" + "="*60)
        print("✅ CONVERSATION TESTING COMPLETED")
        print("="*60)
        
        # Show webhook URL for real testing
        print("\n🔗 FOR REAL WHATSAPP TESTING:")
        print("Configure Twilio webhook URL:")
        print("http://your-server.com/api/v1/whatsapp/webhook")
        print("\n📱 To test real conversation:")
        print(f"1. Send a message to the bot from {customer.phone_number}")
        print("2. Bot will process and respond automatically")
        print("3. Check logs for conversation flow")

if __name__ == "__main__":
    asyncio.run(test_conversation_responses())