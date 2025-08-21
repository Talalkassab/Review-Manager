#!/usr/bin/env python3
"""
Monitor WhatsApp conversation in real-time
"""
import asyncio
import sys
sys.path.append('/Users/hanouf/Desktop/projects/Customer-Whatsapp-agent/backend')

from app.database import db_manager
from app.models import Customer, WhatsAppMessage
from sqlalchemy import select
from datetime import datetime
import time

async def monitor_whatsapp_conversation():
    """Monitor for new WhatsApp messages and responses"""
    
    print("🔄 Starting WhatsApp conversation monitor...")
    print("📱 Waiting for customer responses from +966561876440...")
    print("=" * 60)
    
    await db_manager.initialize()
    
    # Get customer
    async with db_manager.get_session() as session:
        stmt = select(Customer).where(Customer.phone_number == '+966561876440').order_by(Customer.created_at.desc())
        result = await session.execute(stmt)
        customer = result.scalars().first()
        
        if not customer:
            print("❌ Customer not found")
            return
        
        print(f"👤 Monitoring customer: {customer.customer_number}")
        print(f"📞 Phone: {customer.phone_number}")
        print(f"👋 Will use greeting: '{customer.get_greeting()}'")
        print("=" * 60)
    
    last_message_count = 0
    start_time = datetime.utcnow()
    
    print("⏰ Monitor started at:", start_time.strftime("%Y-%m-%d %H:%M:%S"))
    print("🎯 Send your WhatsApp response now!")
    print("💬 You can reply with:")
    print("   • Rating: 1, 2, 3, or 4")
    print("   • Text feedback: Any message about your experience")
    print("   • Thank you: شكرا, thank you, etc.")
    print("=" * 60)
    
    try:
        while True:
            async with db_manager.get_session() as session:
                # Check for new messages
                stmt = select(WhatsAppMessage).where(
                    WhatsAppMessage.customer_id == customer.id
                ).order_by(WhatsAppMessage.created_at.desc())
                result = await session.execute(stmt)
                messages = result.scalars().all()
                
                if len(messages) > last_message_count:
                    print(f"\n📨 Found {len(messages)} total messages (was {last_message_count})")
                    
                    # Show new messages
                    new_messages = messages[:len(messages) - last_message_count]
                    for msg in reversed(new_messages):  # Show in chronological order
                        timestamp = msg.created_at.strftime("%H:%M:%S")
                        direction = "📤 RESTAURANT → CUSTOMER" if msg.direction == 'outbound' else "📥 CUSTOMER → RESTAURANT"
                        
                        print(f"\n[{timestamp}] {direction}")
                        print(f"📱 Content: {msg.content}")
                        print(f"🔄 Status: {msg.status}")
                        print(f"🤖 Auto: {msg.is_automated}")
                        
                        if msg.direction == 'inbound':
                            print("🎯 CUSTOMER RESPONSE RECEIVED!")
                            
                            # Process the response to generate bot reply
                            from app.api.whatsapp import process_customer_response
                            
                            # Refresh customer to get latest state
                            await session.refresh(customer)
                            
                            try:
                                bot_response = await process_customer_response(
                                    customer, msg.content, session
                                )
                                
                                await session.commit()
                                
                                if bot_response:
                                    print(f"🤖 BOT RESPONSE GENERATED:")
                                    print(f"📝 Message: {bot_response}")
                                    
                                    # Send the bot response
                                    from app.services.twilio_whatsapp import TwilioWhatsAppService
                                    whatsapp_service = TwilioWhatsAppService()
                                    
                                    send_result = await whatsapp_service.send_message(
                                        customer=customer,
                                        custom_message=bot_response
                                    )
                                    
                                    if send_result.get('success'):
                                        print(f"✅ Bot response sent! SID: {send_result.get('message_sid')}")
                                    else:
                                        print(f"❌ Failed to send bot response: {send_result.get('message')}")
                                else:
                                    print("🔇 No automated response generated")
                                
                                # Show updated customer state
                                print(f"\n📊 UPDATED CUSTOMER STATE:")
                                print(f"   Rating: {customer.rating or 'Not set'}")
                                print(f"   Sentiment: {customer.feedback_sentiment or 'Not set'}")
                                print(f"   Feedback: {customer.feedback_text or 'None'}")
                                print(f"   Status: {customer.status}")
                                print(f"   Contact Attempts: {customer.contact_attempts}")
                                print(f"   Requires Follow-up: {customer.requires_follow_up}")
                                
                            except Exception as e:
                                print(f"❌ Error processing response: {e}")
                                import traceback
                                traceback.print_exc()
                    
                    last_message_count = len(messages)
                    print(f"\n{'='*60}")
                    print("🔄 Continuing to monitor for more messages...")
                    print("⏰ Current time:", datetime.utcnow().strftime("%H:%M:%S"))
                
                # Check if we should continue monitoring
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed > 300:  # 5 minutes timeout
                    print(f"\n⏰ Monitor timeout after {elapsed/60:.1f} minutes")
                    break
                
                # Wait before next check
                await asyncio.sleep(3)
                
    except KeyboardInterrupt:
        print("\n🛑 Monitor stopped by user")
    except Exception as e:
        print(f"\n❌ Monitor error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎯 CONVERSATION MONITORING COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(monitor_whatsapp_conversation())