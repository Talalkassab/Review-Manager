#!/usr/bin/env python3
"""
Create a customer visit and send WhatsApp message test
"""
import asyncio
import sys
sys.path.append('/Users/hanouf/Desktop/projects/Customer-Whatsapp-agent/backend')

from app.database import db_manager
from app.models import Customer, Restaurant, Visit
from app.services.twilio_whatsapp import TwilioWhatsAppService
from sqlalchemy import select
from datetime import datetime

async def create_visit_and_send_message():
    """Create a customer visit and send WhatsApp message"""
    
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
            return
        
        print(f"🏪 Found restaurant: {restaurant.name} ({restaurant.name_arabic})")
        
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
            # Create new customer
            # Get next customer number
            stmt = select(Customer).where(Customer.restaurant_id == restaurant.id).order_by(Customer.id.desc())
            result = await session.execute(stmt)
            last_customer = result.first()
            
            if last_customer:
                last_number = int(last_customer[0].customer_number.split('-')[1])
                next_number = last_number + 1
            else:
                next_number = 1
            
            customer_number = f"CUST-{next_number:06d}"
            
            # Create customer (no name provided - will use "Dear Customer")
            customer = Customer(
                customer_number=customer_number,
                phone_number='+966561876440',
                restaurant_id=restaurant.id,
                preferred_language='ar',  # Arabic for Saudi number
                whatsapp_opt_in=True,
                first_name=None,  # No name provided
                last_name=None
            )
            
            session.add(customer)
            await session.flush()  # Get customer ID
            print(f"👤 Created new customer: {customer.customer_number}")
        
        # Create a new visit
        visit = Visit(
            customer_id=customer.id,
            restaurant_id=restaurant.id,
            visit_date=datetime.utcnow(),
            visit_type='dine_in',
            party_size=1,
            status='completed'
        )
        
        session.add(visit)
        await session.commit()
        
        print(f"✅ Created visit for customer {customer.customer_number}")
        print(f"📅 Visit date: {visit.visit_date}")
        print(f"👥 Party size: {visit.party_size}")
        
        # Now send WhatsApp message
        print("\n🔄 Sending WhatsApp message...")
        
        # Get greeting (will be "عزيزنا العميل" since no name)
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
        
        print(f"💬 Message to send:")
        print("="*50)
        print(message)
        print("="*50)
        
        # Send via WhatsApp
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
                
                # Update customer contact attempt
                customer.record_contact_attempt()
                await session.commit()
                
                return True
            else:
                print("❌ Failed to send WhatsApp message")
                print(f"Error: {result.get('error')}")
                print(f"Message: {result.get('message')}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(create_visit_and_send_message())
    
    if success:
        print("\n🎯 TEST COMPLETED SUCCESSFULLY")
        print("The customer should receive the WhatsApp message now.")
        print("They can reply with a rating (1-4) or text feedback.")
    else:
        print("\n❌ TEST FAILED")
        print("Check the error messages above.")