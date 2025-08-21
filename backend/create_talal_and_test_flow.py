#!/usr/bin/env python3
"""
Create customer Talal via API and demonstrate complete workflow
"""
import asyncio
import sys
sys.path.append('/Users/hanouf/Desktop/projects/Customer-Whatsapp-agent/backend')

from app.database import db_manager
from app.models import Customer, Restaurant
from app.services.twilio_whatsapp import TwilioWhatsAppService
from sqlalchemy import select
from datetime import datetime, timedelta
import random

async def create_talal_and_demonstrate_flow():
    """Create customer Talal and show the complete workflow"""
    
    print("🎯 DEMONSTRATING COMPLETE CUSTOMER → WHATSAPP WORKFLOW")
    print("="*70)
    
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
        
        print(f"🏪 Restaurant: {restaurant.name} ({restaurant.name_arabic})")
        
        # Step 1: Create Customer
        print(f"\n📋 STEP 1: CREATE CUSTOMER")
        print("-" * 40)
        
        customer = Customer(
            customer_number="TALAL-001",
            first_name="Talal",
            last_name="Customer", 
            phone_number="+966561876440",
            restaurant_id=restaurant.id,
            preferred_language='ar',
            whatsapp_opt_in=True,
            email_opt_in=True,
            gdpr_consent=True,
            status='pending'
        )
        
        session.add(customer)
        await session.flush()  # Get customer ID
        
        print(f"✅ Customer created:")
        print(f"   • Name: {customer.first_name} {customer.last_name}")
        print(f"   • Phone: {customer.phone_number}")
        print(f"   • Customer Number: {customer.customer_number}")
        print(f"   • Restaurant: {restaurant.name}")
        print(f"   • Status: {customer.status}")
        print(f"   • WhatsApp Opt-in: {customer.whatsapp_opt_in}")
        print(f"   • AUTO-SEND WhatsApp: ❌ NO (by design)")
        
        # Step 2: Record a Visit
        print(f"\n🍽️  STEP 2: RECORD RESTAURANT VISIT")
        print("-" * 40)
        
        # Simulate a recent visit (random time in last 3 days)
        days_ago = random.randint(0, 3)
        hours_ago = random.randint(1, 12)
        visit_time = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)
        
        customer.visit_date = visit_time
        customer.party_size = random.randint(1, 4)
        customer.table_number = f"T{random.randint(10, 99)}"
        customer.status = 'visited'  # Update status after visit
        
        await session.commit()
        
        print(f"✅ Visit recorded:")
        print(f"   • Visit Date: {visit_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"   • Party Size: {customer.party_size}")
        print(f"   • Table: {customer.table_number}")
        print(f"   • Status: {customer.status}")
        print(f"   • AUTO-SEND WhatsApp: ❌ NO (still requires manual trigger)")
        
        # Step 3: Trigger WhatsApp Message
        print(f"\n📱 STEP 3: TRIGGER WHATSAPP MESSAGE (Manual Action Required)")
        print("-" * 40)
        
        print(f"💡 In real workflow, you would:")
        print(f"   1. Click 'Send WhatsApp' button in UI")
        print(f"   2. Or call API: POST /api/v1/whatsapp/send-greeting/{customer.id}")
        print(f"   3. Or run scheduled campaign")
        
        print(f"\n🚀 Triggering WhatsApp message now...")
        
        # Create personalized message using restaurant persona and customer name
        greeting = customer.get_greeting()  # Will be "مرحباً Talal" since we have name
        message = f"""
{greeting}! 🌟

نتمنى أن تكون قد استمتعت بزيارتك لمطعم {restaurant.name_arabic or restaurant.name}! 

كما تعلم، نحن في {restaurant.name} نحب أن نشارك متعة النكهات الأصيلة مع لمسة عصرية. 🍛✨

هل يمكنك مشاركتنا تجربتك على الطاولة {customer.table_number}؟ رأيك مهم جداً لنا ويساعدنا في تقديم أفضل خدمة لك ولضيوفنا الكرام.

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
        
        print(f"💬 Message Content:")
        print("="*50)
        print(message)
        print("="*50)
        
        try:
            result = await whatsapp_service.send_message(
                customer=customer,
                message_type='review_request',
                custom_message=message
            )
            
            if result.get('success', False):
                print(f"\n✅ WHATSAPP MESSAGE SENT SUCCESSFULLY!")
                print(f"   • Message SID: {result.get('message_sid')}")
                print(f"   • Status: {result.get('status')}")
                print(f"   • Sent to: {customer.phone_number}")
                print(f"   • Greeting Used: '{greeting}' (personalized with name)")
                
                # Update customer contact attempt
                customer.record_contact_attempt()
                await session.commit()
                
                print(f"\n🎯 COMPLETE WORKFLOW DEMONSTRATED:")
                print(f"="*70)
                print(f"✅ 1. Customer Created: {customer.first_name} ({customer.customer_number})")
                print(f"✅ 2. Visit Recorded: {visit_time.strftime('%Y-%m-%d %H:%M')}")
                print(f"✅ 3. WhatsApp Sent: Manual trigger required")
                print(f"✅ 4. Customer State Updated: Contact attempts = {customer.contact_attempts}")
                print(f"🔄 5. Next: Customer replies → Auto-response via webhook")
                
                print(f"\n📱 ANSWER TO YOUR QUESTION:")
                print(f"   🔸 Creating customer alone: ❌ Does NOT send WhatsApp")
                print(f"   🔸 Recording visit alone: ❌ Does NOT send WhatsApp") 
                print(f"   🔸 Manual trigger needed: ✅ Required to send WhatsApp")
                print(f"   🔸 System design: Manual control over messaging")
                
                return True
            else:
                print(f"❌ Failed to send WhatsApp message")
                print(f"   Error: {result.get('message')}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Starting complete workflow demonstration...")
    asyncio.run(create_talal_and_demonstrate_flow())