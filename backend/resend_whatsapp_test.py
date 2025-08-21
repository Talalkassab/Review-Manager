#!/usr/bin/env python3
"""
Resend WhatsApp message after sandbox setup
"""
import asyncio
import sys
sys.path.append('/Users/hanouf/Desktop/projects/Customer-Whatsapp-agent/backend')

from app.database import db_manager
from app.models import Customer, Restaurant
from app.services.twilio_whatsapp import TwilioWhatsAppService
from sqlalchemy import select

async def resend_whatsapp_message():
    """Resend WhatsApp message to existing customer"""
    
    await db_manager.initialize()
    whatsapp_service = TwilioWhatsAppService()
    
    async with db_manager.get_session() as session:
        # Get the most recent customer with this phone number
        stmt = select(Customer).where(
            Customer.phone_number == '+966561876440'
        ).order_by(Customer.created_at.desc())
        result = await session.execute(stmt)
        customer = result.scalars().first()
        
        if not customer:
            print("❌ Customer not found")
            return False
        
        print(f"👤 Found customer: {customer.customer_number}")
        print(f"📱 Phone: {customer.phone_number}")
        print(f"👋 Greeting: {customer.get_greeting()}")
        
        # Get restaurant
        stmt = select(Restaurant).where(Restaurant.name == 'Naandori')
        result = await session.execute(stmt)
        restaurant = result.scalar_one_or_none()
        
        if not restaurant:
            print("❌ Restaurant not found")
            return False
        
        print(f"🏪 Restaurant: {restaurant.name} ({restaurant.name_arabic})")
        
        # Create message
        greeting = customer.get_greeting()
        message = f"""
{greeting}! 🌟

نتمنى أن تكون قد استمتعت بزيارتك اليوم لمطعم {restaurant.name_arabic or restaurant.name}! 

كما تعلم، نحن في {restaurant.name} نحب أن نشارك متعة النكهات الأصيلة مع لمسة عصرية. 🍛✨

هل يمكنك مشاركتنا تجربتك؟ رأيك مهم جداً لنا ويساعدنا في تقديم أفضل خدمة لك ولضيوفنا الكرام.

يمكنك الرد بتقييم من 1 إلى 4:
1️⃣ ضعيف
2️⃣ متوسط  
3️⃣ جيد
4️⃣ ممتاز

أو مشاركة تعليقاتك مباشرة.

شكراً لك على اختيارك لنا! 🙏

فريق {restaurant.name}
📞 {restaurant.phone_number}
        """.strip()
        
        print(f"\n📤 Resending WhatsApp message...")
        
        try:
            result = await whatsapp_service.send_message(
                customer=customer,
                message_type='review_request',
                custom_message=message
            )
            
            if result.get('success', False):
                print("✅ WhatsApp message sent successfully!")
                print(f"📧 Message SID: {result.get('message_sid')}")
                print(f"📊 Status: {result.get('status')}")
                print(f"\n🎯 Message sent to +966561876440")
                print("📱 You should receive the message on WhatsApp now!")
                return True
            else:
                error_msg = result.get('message', 'Unknown error')
                print(f"❌ Failed to send: {error_msg}")
                
                if 'join' in error_msg.lower():
                    print("\n📱 SANDBOX SETUP STILL NEEDED:")
                    print("1. Send 'join out-when' to +14155238886")
                    print("2. Wait for confirmation")
                    print("3. Then run this script again")
                
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    print("🔄 Resending WhatsApp message after sandbox setup...")
    success = asyncio.run(resend_whatsapp_message())
    
    if success:
        print("\n✅ Message sent! Check your WhatsApp.")
    else:
        print("\n❌ Message failed. Please check sandbox setup.")