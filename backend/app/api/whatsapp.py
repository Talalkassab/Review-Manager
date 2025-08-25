"""
WhatsApp webhook endpoints for Twilio integration.
Handles incoming messages and status updates.
"""
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from fastapi.responses import PlainTextResponse
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import uuid

from ..services.twilio_whatsapp import twilio_service, send_automated_greeting
from ..models.customer import Customer
from ..models.whatsapp import WhatsAppMessage
from ..database import db_manager
from .auth import current_active_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WhatsApp"])

@router.get("/test")
async def test_webhook():
    """Test endpoint to verify deployment"""
    return {"status": "webhook_v2_deployed", "timestamp": "2025-08-25-10:27"}

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Handle incoming WhatsApp messages from Twilio.
    Process customer responses and trigger appropriate actions.
    """
    try:
        logger.info("=== WEBHOOK CALLED ===")
        
        # Get form data from Twilio
        form_data = await request.form()
        
        # Extract message details
        from_number = form_data.get('From', '').replace('whatsapp:', '')
        message_body = form_data.get('Body', '')
        
        logger.info(f"Message from {from_number}: {message_body}")
        
        # Generate simple AI response without database
        ai_response = get_simple_ai_response(message_body)
        
        # Send response using Twilio
        try:
            from ..services.twilio_whatsapp import twilio_service
            
            # Create minimal customer object
            class SimpleCustomer:
                phone_number = from_number
                preferred_language = 'ar'
            
            customer = SimpleCustomer()
            
            await twilio_service.send_message(
                customer=customer,
                custom_message=ai_response
            )
            
            logger.info(f"Sent response to {from_number}")
            
        except Exception as send_error:
            logger.error(f"Error sending message: {send_error}")
            # Still return OK to Twilio
        
        return PlainTextResponse("OK", status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")
        # Still return 200 to prevent Twilio retries
        return PlainTextResponse("Error", status_code=200)

@router.post("/status")
async def whatsapp_status_webhook(request: Request):
    """Handle message status updates from Twilio."""
    try:
        form_data = await request.form()
        message_sid = form_data.get('MessageSid', '')
        status = form_data.get('MessageStatus', '')
        
        logger.info(f"Message {message_sid} status: {status}")
        
        # Update message status in database
        async with db_manager.get_session() as session:
            result = await session.execute(
                select(WhatsAppMessage).where(
                    WhatsAppMessage.whatsapp_message_id == message_sid
                )
            )
            message = result.scalar_one_or_none()
            
            if message:
                if status == 'delivered':
                    message.mark_delivered()
                elif status == 'read':
                    message.mark_read()
                elif status == 'failed':
                    message.mark_failed()
                
                await session.commit()
        
        return PlainTextResponse("OK", status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing status webhook: {str(e)}")
        return PlainTextResponse("Error", status_code=200)

def get_simple_ai_response(message: str) -> str:
    """Generate simple AI response without database dependencies"""
    message_lower = message.lower().strip()
    
    # Greeting
    if any(word in message_lower for word in ['مرحبا', 'السلام', 'أهلا', 'hello', 'hi']):
        return """مرحباً بكم في مطعمنا! 🌟

كيف يمكنني مساعدتكم؟
• حجز طاولة  
• قائمة الطعام
• تقييم الخدمة

نحن هنا لخدمتكم! 😊"""

    # Booking
    elif any(word in message_lower for word in ['حجز', 'طاولة', 'book']):
        return """ممتاز! لحجز طاولة 🪑

أخبرونا:
📅 التاريخ؟
🕐 الوقت؟  
👥 كم شخص؟

يمكنكم الاتصال بنا للحجز المباشر!"""

    # Menu
    elif any(word in message_lower for word in ['منيو', 'طعام', 'menu']):
        return """قائمة طعامنا 🍽️

🥙 أطباق رئيسية
🍲 شوربات ومقبلات
🥗 سلطات طازجة
🧃 مشروبات
🍰 حلويات

ماذا تفضلون؟"""

    # Thanks
    elif any(word in message_lower for word in ['شكرا', 'شكراً', 'thank']):
        return """العفو! يسعدنا خدمتكم 🙏

نتطلع لاستقبالكم قريباً! ✨"""

    # Default
    else:
        return """شكراً لتواصلكم! 📱

يمكنكم كتابة:
🔹 "حجز" للحجوزات
🔹 "منيو" لقائمة الطعام
🔹 "مرحبا" للترحيب

كيف يمكنني مساعدتكم؟ 😊"""

async def generate_ai_response(customer: Customer, message: str, session: AsyncSession) -> Optional[str]:
    """Generate intelligent AI response based on customer message"""
    try:
        # Simple pattern matching for now
        message_lower = message.lower().strip()
        
        # Greeting responses
        if any(word in message_lower for word in ['مرحبا', 'السلام', 'أهلا', 'hello', 'hi']):
            return """مرحباً بكم في مطعمنا! 🌟

كيف يمكنني مساعدتكم اليوم؟
• للحجز: اكتبوا "حجز"  
• لآراءكم: اكتبوا "تقييم"
• للاستفسار: اكتبوا "استفسار"

نحن هنا لخدمتكم! 😊"""

        # Booking requests
        elif any(word in message_lower for word in ['حجز', 'طاولة', 'book', 'reservation']):
            return """ممتاز! سنساعدكم في حجز طاولة 🪑

يرجى إخبارنا بالتفاصيل التالية:
📅 التاريخ المطلوب
🕐 الوقت المفضل  
👥 عدد الأشخاص

يمكنكم أيضاً الاتصال بنا مباشرة للحجز السريع!"""

        # Feedback/Rating
        elif any(word in message_lower for word in ['تقييم', 'رأي', 'feedback', 'review']):
            return """نشكركم لاهتمامكم بتقييم خدمتنا! ⭐

كيف كانت تجربتكم معنا؟
من 1 إلى 5:
1️⃣ غير راض  
2️⃣ مقبول
3️⃣ جيد
4️⃣ ممتاز  
5️⃣ استثنائي

رأيكم مهم جداً لنا! 💝"""

        # Menu inquiry
        elif any(word in message_lower for word in ['منيو', 'طعام', 'أطباق', 'menu', 'food']):
            return """قائمة طعامنا الشهية! 🍽️

🥙 الأطباق الرئيسية
🍲 الشوربات والمقبلات
🥗 السلطات الطازجة
🧃 المشروبات والعصائر
🍰 الحلويات

أي نوع من الأطباق تفضلون؟"""

        # Thanks message
        elif any(word in message_lower for word in ['شكرا', 'شكراً', 'thank', 'thanks']):
            return """العفو! يسعدنا خدمتكم دائماً 🙏

إذا كان لديكم أي استفسار آخر أو تحتاجون مساعدة، لا تترددوا في التواصل معنا.

نتطلع لاستقبالكم قريباً! ✨"""

        # Default intelligent response
        else:
            return """شكراً لتواصلكم معنا! 📱

لم أفهم طلبكم تماماً، لكن يمكنكم:

🔹 كتابة "حجز" للحجوزات
🔹 كتابة "منيو" لقائمة الطعام  
🔹 كتابة "تقييم" لتقييم الخدمة
🔹 الاتصال بنا مباشرة للمساعدة

كيف يمكنني مساعدتكم؟ 😊"""

    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        return "شكراً لرسالتكم! سنتواصل معكم قريباً 🙏"

async def process_customer_response(
    customer: Customer, 
    message: str, 
    session: AsyncSession
) -> Optional[str]:
    """
    Process customer response and generate appropriate reply.
    
    Returns:
        Response message to send back to customer, or None
    """
    # Normalize message
    message = message.strip().lower()
    
    # Check for rating responses (1-4)
    if message in ['1', '2', '3', '4']:
        rating = int(message)
        
        # Update customer feedback
        customer.rating = rating
        customer.feedback_received_at = datetime.utcnow()
        
        # Set sentiment based on rating
        if rating >= 4:
            customer.feedback_sentiment = 'positive'
            sentiment_emoji = '😊'
        elif rating == 3:
            customer.feedback_sentiment = 'neutral'
            sentiment_emoji = '😐'
        else:
            customer.feedback_sentiment = 'negative'
            sentiment_emoji = '😔'
        
        # Generate response based on rating
        if customer.preferred_language == 'ar':
            if rating >= 4:
                response = """رائع! يسعدنا أن تجربتكم كانت ممتازة! 🌟

هل يمكنكم مساعدتنا بمشاركة تجربتكم الإيجابية على Google؟ 
تقييمكم يساعدنا كثيراً.

https://g.page/r/YOUR_GOOGLE_REVIEW_LINK

شكراً لكم ونتطلع لرؤيتكم قريباً! 🙏"""
            elif rating == 3:
                response = """شكراً لتقييمكم! نسعى دائماً للتحسين. 

هل يمكنكم مشاركة المزيد عن تجربتكم؟ 
ما الذي يمكننا تحسينه لجعل زيارتكم القادمة أفضل؟"""
            else:
                response = """نأسف لسماع ذلك. رأيكم مهم جداً لنا. 😔

هل يمكنكم مشاركتنا المزيد عن تجربتكم؟ 
ما الذي يمكننا تحسينه؟

مديرنا سيتواصل معكم شخصياً لحل أي مشكلة.
نقدر صراحتكم ونعدكم بتحسين خدماتنا. 🙏"""
        else:
            if rating >= 4:
                response = """Wonderful! We're thrilled you had an excellent experience! 🌟

Would you mind sharing your positive experience on Google? 
Your review helps us greatly.

https://g.page/r/YOUR_GOOGLE_REVIEW_LINK

Thank you and we look forward to seeing you again! 🙏"""
            elif rating == 3:
                response = """Thank you for your feedback! We're always looking to improve.

Could you share more about your experience? 
What can we do better for your next visit?"""
            else:
                response = """We're sorry to hear that. Your feedback is very important to us. 😔

Could you please share more about your experience? 
What can we improve?

Our manager will contact you personally to resolve any issues.
We appreciate your honesty and promise to improve. 🙏"""
        
        # Mark customer as needing follow-up if negative
        if rating <= 2:
            customer.requires_follow_up = True
            customer.follow_up_notes = f"Customer rated experience as {rating}/4"
        
        # Request Google review if positive
        if rating >= 4:
            customer.google_review_requested_at = datetime.utcnow()
            customer.google_review_link_sent = True
        
        return response
    
    # Check for other keywords
    elif any(word in message for word in ['شكرا', 'thank', 'مشكور', 'تمام', 'ok']):
        if customer.preferred_language == 'ar':
            return "عفواً! نتمنى لكم يوماً سعيداً 🌟"
        else:
            return "You're welcome! Have a wonderful day! 🌟"
    
    # Store as general feedback if not a rating
    else:
        customer.feedback_text = message
        customer.feedback_received_at = datetime.utcnow()
        
        # Simple sentiment detection
        negative_words = ['سيء', 'bad', 'poor', 'terrible', 'horrible', 'worst']
        positive_words = ['ممتاز', 'رائع', 'excellent', 'great', 'amazing', 'wonderful']
        
        if any(word in message for word in negative_words):
            customer.feedback_sentiment = 'negative'
            customer.requires_follow_up = True
        elif any(word in message for word in positive_words):
            customer.feedback_sentiment = 'positive'
        
        if customer.preferred_language == 'ar':
            return "شكراً لملاحظاتكم القيمة! سنحرص على الاستفادة منها لتحسين خدماتنا. 🙏"
        else:
            return "Thank you for your valuable feedback! We'll use it to improve our services. 🙏"
    
    return None

@router.post("/send-test")
async def send_test_message(
    phone_number: str,
    current_user = Depends(current_active_user)
):
    """
    Send a test WhatsApp message to verify integration.
    Requires authentication.
    """
    result = await twilio_service.send_test_message(phone_number)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result

@router.get("/sandbox-info")
async def get_sandbox_info():
    """Get Twilio WhatsApp sandbox joining instructions."""
    return twilio_service.get_sandbox_instructions()

@router.post("/send-greeting/{customer_id}")
async def send_greeting_message(
    customer_id: str,
    background_tasks: BackgroundTasks,
    delay_hours: float = 0,
    current_user = Depends(current_active_user)
):
    """
    Send greeting message to a specific customer.
    Can be immediate or delayed.
    """
    if delay_hours > 0:
        # Schedule for later
        background_tasks.add_task(
            send_automated_greeting,
            customer_id=customer_id,
            delay_hours=delay_hours
        )
        return {
            "message": f"Greeting scheduled to be sent in {delay_hours} hours",
            "customer_id": customer_id
        }
    else:
        # Send immediately
        async with db_manager.get_session() as session:
            # Handle UUID conversion - try direct string first, then UUID conversion
            try:
                if len(customer_id) == 32:  # UUID without hyphens
                    # Convert to UUID with hyphens for SQLAlchemy
                    uuid_str = f"{customer_id[:8]}-{customer_id[8:12]}-{customer_id[12:16]}-{customer_id[16:20]}-{customer_id[20:]}"
                    customer_uuid = uuid.UUID(uuid_str)
                else:
                    customer_uuid = uuid.UUID(customer_id)
                
                customer = await session.get(Customer, customer_uuid)
            except (ValueError, TypeError):
                # Try direct string lookup if UUID conversion fails
                result = await session.execute(
                    select(Customer).where(Customer.id == customer_id)
                )
                customer = result.scalar_one_or_none()
            
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            result = await twilio_service.send_message(customer, 'greeting')
            
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['message'])
            
            return result

@router.post("/test-greeting/{customer_id}")
async def test_send_greeting_message(
    customer_id: str
):
    """
    Test endpoint to send greeting message without authentication.
    For testing purposes only.
    """
    async with db_manager.get_session() as session:
        # Handle UUID conversion - try direct string first, then UUID conversion
        try:
            if len(customer_id) == 32:  # UUID without hyphens
                # Convert to UUID with hyphens for SQLAlchemy
                uuid_str = f"{customer_id[:8]}-{customer_id[8:12]}-{customer_id[12:16]}-{customer_id[16:20]}-{customer_id[20:]}"
                customer_uuid = uuid.UUID(uuid_str)
            else:
                customer_uuid = uuid.UUID(customer_id)
            
            customer = await session.get(Customer, customer_uuid)
        except (ValueError, TypeError):
            # Try direct string lookup if UUID conversion fails
            result = await session.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        result = await twilio_service.send_message(customer, 'greeting')
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        return result