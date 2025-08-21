#!/usr/bin/env python3
"""
Test script to send WhatsApp message for customer review
"""
import asyncio
import sys
sys.path.append('/Users/hanouf/Desktop/projects/Customer-Whatsapp-agent/backend')

from app.database import db_manager
from app.models import Customer, Restaurant
from app.services.twilio_whatsapp import TwilioWhatsAppService
from sqlalchemy import select

async def send_review_message():
    """Send WhatsApp message to customer for review"""
    
    # Initialize WhatsApp service
    whatsapp_service = TwilioWhatsAppService()
    
    # Initialize database manager
    await db_manager.initialize()
    
    async with db_manager.get_session() as session:
        # Get the Naandori restaurant first
        stmt = select(Restaurant).where(Restaurant.name == 'Naandori')
        result = await session.execute(stmt)
        restaurant = result.scalar_one_or_none()
        
        if not restaurant:
            print("❌ Restaurant not found")
            return
            
        # Get the customer for this restaurant (use customer_number to identify the Naandori customer)
        stmt = select(Customer).where(
            Customer.phone_number == '+966561876440',
            Customer.customer_number == 'CUST-000001'
        )
        result = await session.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not customer:
            print("❌ Customer not found")
            return
        
        if not restaurant:
            print("❌ Restaurant not found")
            return
            
        print(f"📱 Customer: {customer.customer_number} ({customer.phone_number})")
        print(f"🏪 Restaurant: {restaurant.name} ({restaurant.name_arabic})")
        print(f"🎭 Persona: {restaurant.persona[:100]}...")
        
        # Get greeting based on customer's language preference
        greeting = customer.get_greeting()
        print(f"👋 Greeting: {greeting}")
        
        # Create a personalized review message using the restaurant's persona
        if customer.preferred_language == 'ar':
            message = f"""
{greeting}! 🌟

نتمنى أن تكون قد استمتعت بزيارتك الأمس لمطعم {restaurant.name_arabic or restaurant.name}! 

كما تعلم، نحن في {restaurant.name} نحب أن نشارك متعة النكهات الأصيلة مع لمسة عصرية. 🍛✨

هل يمكنك مشاركتنا تجربتك؟ رأيك مهم جداً لنا ويساعدنا في تقديم أفضل خدمة لك ولضيوفنا الكرام.

شكراً لك على اختيارك لنا! 🙏

فريق {restaurant.name}
📞 {restaurant.phone_number}
""".strip()
        else:
            message = f"""
{greeting}! 🌟

We hope you enjoyed your visit to {restaurant.name} last night!

As you know, we at {restaurant.name} love sharing the joy of authentic flavors with a modern twist. 🍛✨

Could you please share your experience with us? Your feedback is incredibly important to us and helps us provide the best service for you and all our valued guests.

Thank you for choosing us! 🙏

The {restaurant.name} Team
📞 {restaurant.phone_number}
""".strip()
        
        print(f"💬 Message to send:")
        print(f"---")
        print(message)
        print(f"---")
        
        # Send the message
        try:
            result = await whatsapp_service.send_message(
                customer=customer,
                message_type='review_request',
                custom_message=message
            )
            
            success = result.get('success', False)
            
            if success:
                print("✅ WhatsApp message sent successfully!")
                
                # Update customer status
                customer.record_contact_attempt()
                await session.commit()
                print("✅ Customer contact attempt recorded")
            else:
                print("❌ Failed to send WhatsApp message")
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")

if __name__ == "__main__":
    asyncio.run(send_review_message())