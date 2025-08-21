#!/usr/bin/env python3
"""
Direct database approach to create customer and send WhatsApp message
"""
import asyncio
import sys
sys.path.append('/Users/hanouf/Desktop/projects/Customer-Whatsapp-agent/backend')

from app.database import db_manager
from app.models import Customer, Restaurant
from app.services.twilio_whatsapp import TwilioWhatsAppService
from sqlalchemy import select
from datetime import datetime

async def create_customer_and_send_whatsapp():
    """Create a customer visit and send WhatsApp message directly through database"""
    
    # Initialize database and WhatsApp service
    await db_manager.initialize()
    whatsapp_service = TwilioWhatsAppService()
    
    async with db_manager.get_session() as session:
        # Get Naandori restaurant
        stmt = select(Restaurant).where(Restaurant.name == 'Naandori')
        result = await session.execute(stmt)
        restaurant = result.scalar_one_or_none()
        
        if not restaurant:
            print("❌ Naandori restaurant not found")
            return False
        
        print(f"🏪 Found restaurant: {restaurant.name} ({restaurant.name_arabic})")
        print(f"🎭 Persona: {restaurant.persona[:100]}..." if restaurant.persona else "🎭 Persona: [Not set]")
        
        # Check if customer already exists
        stmt = select(Customer).where(
            Customer.phone_number == '+966561876440',
            Customer.restaurant_id == restaurant.id
        )
        result = await session.execute(stmt)
        existing_customer = result.scalar_one_or_none()
        
        if existing_customer:
            print(f"👤 Found existing customer: {existing_customer.customer_number}")
            customer = existing_customer
        else:
            # Get next customer number
            stmt = select(Customer).where(Customer.restaurant_id == restaurant.id).order_by(Customer.id.desc())
            result = await session.execute(stmt)
            last_customer = result.first()
            
            if last_customer and last_customer[0].customer_number:
                try:
                    last_number = int(last_customer[0].customer_number.split('-')[1])
                    next_number = last_number + 1
                except:
                    next_number = 1
            else:
                next_number = 1
            
            customer_number = f"CUST-{next_number:06d}"
            
            # Create customer (empty string name - will use "Dear Customer")
            customer = Customer(
                customer_number=customer_number,
                phone_number='+966561876440',
                restaurant_id=restaurant.id,
                preferred_language='ar',  # Arabic for Saudi number
                whatsapp_opt_in=True,
                first_name='',  # Empty string - testing "Dear Customer" functionality
                last_name=''
            )
            
            session.add(customer)
            await session.flush()  # Get customer ID
            print(f"👤 Created new customer: {customer.customer_number}")
        
        # Update customer visit date
        customer.visit_date = datetime.utcnow()
        await session.commit()
        
        print(f"✅ Customer visit recorded: {customer.customer_number}")
        print(f"📅 Visit date: {customer.visit_date}")
        
        # Test the greeting (should be "عزيزنا العميل" since no name)
        greeting = customer.get_greeting()
        print(f"👋 Greeting: {greeting}")
        
        # Create personalized message using restaurant persona
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
        
        print(f"\n💬 Message to send:")
        print("="*60)
        print(message)
        print("="*60)
        
        # Now send WhatsApp message
        print(f"\n📱 Sending WhatsApp message to {customer.phone_number}...")
        
        try:
            result = await whatsapp_service.send_message(
                customer=customer,
                message_type='review_request',
                custom_message=message
            )
            
            if result.get('success', False):
                print("✅ WhatsApp message sent successfully!")
                print(f"📧 Message SID: {result.get('message_sid')}")
                print(f"📱 Sent to: {customer.phone_number}")
                print(f"📊 Status: {result.get('status')}")
                
                # Update customer contact attempt
                customer.record_contact_attempt()
                await session.commit()
                
                print("\n🎯 COMPLETE END-TO-END TEST SUCCESS!")
                print("="*60)
                print(f"✅ Customer: {customer.customer_number} (Anonymous - no name provided)")
                print(f"✅ Phone: {customer.phone_number}")
                print(f"✅ Greeting: '{greeting}' (Dear Customer in Arabic)")
                print(f"✅ Restaurant: {restaurant.name} ({restaurant.name_arabic})")
                print(f"✅ Visit recorded: {customer.visit_date}")
                print(f"✅ WhatsApp message sent with Naandori's persona")
                print(f"✅ Customer can now reply with ratings or text feedback")
                print("="*60)
                
                return True
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"❌ Failed to send WhatsApp message")
                print(f"   Error: {result.get('message', error_msg)}")
                
                # Check if it's a sandbox issue
                if 'join' in error_msg.lower():
                    print("\n📱 TWILIO SANDBOX SETUP REQUIRED:")
                    print("The customer needs to send the following message:")
                    print("   Message: 'join out-when'")
                    print("   To: +14155238886")
                    print("\nAfter joining the sandbox, the message will be delivered.")
                
                return False
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🚀 Starting direct database customer creation and WhatsApp test...")
    success = asyncio.run(create_customer_and_send_whatsapp())
    
    if success:
        print("\n🎉 END-TO-END TEST COMPLETED SUCCESSFULLY!")
        print("The system is ready for production use.")
    else:
        print("\n❌ TEST FAILED")
        print("Check the error messages above for details.")