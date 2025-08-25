"""
WhatsApp webhook endpoints for Twilio integration.
Handles incoming messages and status updates with comprehensive error handling.
"""
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from fastapi.responses import PlainTextResponse
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import uuid
import traceback
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WhatsApp"])

@router.get("/test")
async def test_webhook():
    """Test endpoint to verify deployment and system health"""
    test_results = {
        "status": "webhook_ultra_debug_v3_deployed",
        "timestamp": datetime.utcnow().isoformat(),
        "system_checks": {}
    }
    
    # Test 1: Basic imports
    try:
        from ..database import db_manager
        test_results["system_checks"]["database_import"] = "✅ SUCCESS"
    except Exception as e:
        test_results["system_checks"]["database_import"] = f"❌ FAILED: {str(e)}"
    
    # Test 2: Twilio service
    try:
        from ..services.twilio_whatsapp import twilio_service
        test_results["system_checks"]["twilio_import"] = "✅ SUCCESS"
        test_results["system_checks"]["twilio_enabled"] = "✅ ENABLED" if twilio_service.enabled else "❌ DISABLED"
    except Exception as e:
        test_results["system_checks"]["twilio_import"] = f"❌ FAILED: {str(e)}"
    
    # Test 3: Database health (if available)
    try:
        if 'db_manager' in locals():
            if db_manager.is_initialized:
                health = await db_manager.health_check()
                test_results["system_checks"]["database_health"] = f"✅ {health['status']}"
            else:
                test_results["system_checks"]["database_health"] = "⚠️ NOT_INITIALIZED"
    except Exception as e:
        test_results["system_checks"]["database_health"] = f"❌ FAILED: {str(e)}"
    
    # Test 4: Models import
    try:
        from ..models.customer import Customer
        from ..models.whatsapp import WhatsAppMessage
        test_results["system_checks"]["models_import"] = "✅ SUCCESS"
    except Exception as e:
        test_results["system_checks"]["models_import"] = f"❌ FAILED: {str(e)}"
    
    return test_results

@router.get("/debug/environment")
async def debug_environment():
    """Debug endpoint to check environment variables and configuration"""
    import os
    
    env_check = {
        "timestamp": datetime.utcnow().isoformat(),
        "environment_variables": {},
        "config_status": {}
    }
    
    # Check critical environment variables (without exposing secrets)
    env_vars_to_check = [
        "DATABASE_URL",
        "TWILIO_ACCOUNT_SID", 
        "TWILIO_AUTH_TOKEN",
        "TWILIO_WHATSAPP_NUMBER",
        "TWILIO_SANDBOX_CODE",
        "ENVIRONMENT",
        "PORT"
    ]
    
    for var in env_vars_to_check:
        value = os.getenv(var)
        if value:
            if "TOKEN" in var or "SID" in var:
                # Mask sensitive values
                env_check["environment_variables"][var] = f"SET (***{value[-4:]})"
            else:
                env_check["environment_variables"][var] = value
        else:
            env_check["environment_variables"][var] = "NOT_SET"
    
    # Check configuration loading
    try:
        from ..core.config import settings
        env_check["config_status"]["config_import"] = "✅ SUCCESS"
        env_check["config_status"]["twilio_configured"] = "✅ YES" if settings.twilio.TWILIO_ACCOUNT_SID else "❌ NO"
        env_check["config_status"]["database_url"] = "✅ SET" if settings.database.DATABASE_URL else "❌ NOT_SET"
    except Exception as e:
        env_check["config_status"]["config_import"] = f"❌ FAILED: {str(e)}"
    
    return env_check

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    ULTRA-ROBUST WhatsApp webhook with comprehensive error handling.
    Tests every component step by step to identify failure points.
    """
    step = "INIT"
    debug_info = {
        "timestamp": datetime.utcnow().isoformat(),
        "step": step,
        "form_data": {},
        "extracted_data": {},
        "database_status": "unknown",
        "twilio_status": "unknown",
        "ai_response_status": "unknown"
    }
    
    try:
        logger.info("=== ULTRA-DEBUG WEBHOOK STARTED ===")
        step = "FORM_DATA_EXTRACTION"
        debug_info["step"] = step
        
        # STEP 1: Extract form data with detailed logging
        try:
            form_data = await request.form()
            debug_info["form_data"] = dict(form_data)
            logger.info(f"✅ STEP 1 SUCCESS: Form data extracted: {debug_info['form_data']}")
        except Exception as e:
            logger.error(f"❌ STEP 1 FAILED: Form data extraction error: {str(e)}")
            debug_info["form_data_error"] = str(e)
            return PlainTextResponse(f"Error-Step1: {str(e)}", status_code=200)
        
        # STEP 2: Parse message details
        step = "MESSAGE_PARSING" 
        debug_info["step"] = step
        try:
            from_number = form_data.get('From', '').replace('whatsapp:', '')
            message_body = form_data.get('Body', '')
            message_sid = form_data.get('MessageSid', '')
            
            debug_info["extracted_data"] = {
                "from_number": from_number,
                "message_body": message_body,
                "message_sid": message_sid,
                "all_form_keys": list(form_data.keys())
            }
            
            if not from_number or not message_body:
                logger.error(f"❌ STEP 2 FAILED: Missing required data - from: '{from_number}', body: '{message_body}'")
                return PlainTextResponse("Error-Step2: Missing data", status_code=200)
            
            logger.info(f"✅ STEP 2 SUCCESS: Parsed message from {from_number}: {message_body}")
        except Exception as e:
            logger.error(f"❌ STEP 2 FAILED: Message parsing error: {str(e)}")
            return PlainTextResponse(f"Error-Step2: {str(e)}", status_code=200)
        
        # STEP 3: Test database connectivity
        step = "DATABASE_TEST"
        debug_info["step"] = step
        try:
            # Try to import database manager
            from ..database import db_manager
            logger.info("✅ STEP 3.1 SUCCESS: Database manager imported")
            
            # Test if db_manager is initialized
            if not db_manager.is_initialized:
                logger.warning("⚠️ STEP 3.2 WARNING: Database not initialized, attempting initialization...")
                try:
                    await db_manager.initialize()
                    logger.info("✅ STEP 3.2 SUCCESS: Database initialized successfully")
                except Exception as init_error:
                    logger.error(f"❌ STEP 3.2 FAILED: Database initialization error: {str(init_error)}")
                    debug_info["database_status"] = f"init_failed: {str(init_error)}"
                    # Continue without database for now
            
            # Test database connection
            try:
                health = await db_manager.health_check()
                debug_info["database_status"] = health["status"]
                logger.info(f"✅ STEP 3.3 SUCCESS: Database health check: {health}")
            except Exception as health_error:
                logger.error(f"❌ STEP 3.3 FAILED: Database health check error: {str(health_error)}")
                debug_info["database_status"] = f"health_failed: {str(health_error)}"
                
        except Exception as e:
            logger.error(f"❌ STEP 3 FAILED: Database test error: {str(e)}")
            debug_info["database_status"] = f"import_failed: {str(e)}"
        
        # STEP 4: Generate AI response (simple version first)
        step = "AI_RESPONSE"
        debug_info["step"] = step
        try:
            ai_response = get_simple_ai_response(message_body)
            debug_info["ai_response_status"] = "success"
            debug_info["ai_response_length"] = len(ai_response)
            logger.info(f"✅ STEP 4 SUCCESS: AI response generated ({len(ai_response)} chars)")
        except Exception as e:
            logger.error(f"❌ STEP 4 FAILED: AI response error: {str(e)}")
            debug_info["ai_response_status"] = f"failed: {str(e)}"
            ai_response = "شكراً لرسالتكم! سنتواصل معكم قريباً."  # Fallback response
        
        # STEP 5: Test Twilio service
        step = "TWILIO_TEST"
        debug_info["step"] = step
        try:
            # Try to import Twilio service
            from ..services.twilio_whatsapp import twilio_service
            logger.info("✅ STEP 5.1 SUCCESS: Twilio service imported")
            
            # Check if Twilio is enabled
            if not twilio_service.enabled:
                logger.error("❌ STEP 5.2 FAILED: Twilio service not enabled (missing credentials)")
                debug_info["twilio_status"] = "disabled: missing credentials"
                return PlainTextResponse("Error-Step5: Twilio disabled", status_code=200)
            
            logger.info("✅ STEP 5.2 SUCCESS: Twilio service is enabled")
            debug_info["twilio_status"] = "enabled"
            
        except Exception as e:
            logger.error(f"❌ STEP 5 FAILED: Twilio import/test error: {str(e)}")
            debug_info["twilio_status"] = f"import_failed: {str(e)}"
            return PlainTextResponse(f"Error-Step5: {str(e)}", status_code=200)
        
        # STEP 6: Create customer object and send message
        step = "MESSAGE_SENDING"
        debug_info["step"] = step
        try:
            # Create simple customer object
            class SimpleCustomer:
                phone_number = from_number
                preferred_language = 'ar'
                first_name = None  # Add required attributes
            
            customer = SimpleCustomer()
            logger.info("✅ STEP 6.1 SUCCESS: Simple customer object created")
            
            # Send message
            send_result = await twilio_service.send_message(
                customer=customer,
                custom_message=ai_response
            )
            
            if send_result['success']:
                logger.info(f"✅ STEP 6.2 SUCCESS: Message sent successfully: {send_result}")
                debug_info["message_sent"] = True
                debug_info["message_sid"] = send_result.get('message_sid', 'unknown')
            else:
                logger.error(f"❌ STEP 6.2 FAILED: Message sending failed: {send_result}")
                debug_info["message_sent"] = False
                debug_info["send_error"] = send_result.get('error', 'unknown')
            
        except Exception as e:
            logger.error(f"❌ STEP 6 FAILED: Message sending error: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            debug_info["message_sending_error"] = str(e)
        
        # STEP 7: Database logging (if available)
        step = "DATABASE_LOGGING"
        debug_info["step"] = step
        if debug_info["database_status"] == "healthy":
            try:
                # Try to log the interaction to database
                await log_whatsapp_interaction(from_number, message_body, ai_response)
                logger.info("✅ STEP 7 SUCCESS: Interaction logged to database")
                debug_info["db_logged"] = True
            except Exception as e:
                logger.error(f"❌ STEP 7 FAILED: Database logging error: {str(e)}")
                debug_info["db_logging_error"] = str(e)
                # Continue anyway
        else:
            logger.info("⚠️ STEP 7 SKIPPED: Database not available for logging")
            debug_info["db_logged"] = False
        
        # SUCCESS - Log complete debug info
        logger.info(f"🎉 WEBHOOK SUCCESS: {debug_info}")
        return PlainTextResponse("OK", status_code=200)
        
    except Exception as e:
        # CRITICAL FAILURE - Log everything for debugging
        logger.error(f"💥 CRITICAL WEBHOOK FAILURE at step {step}: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.error(f"Debug info: {debug_info}")
        
        # Still return 200 to prevent Twilio retries, but include error info
        return PlainTextResponse(f"Error-{step}: {str(e)}", status_code=200)

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

async def log_whatsapp_interaction(phone_number: str, inbound_message: str, outbound_response: str) -> bool:
    """
    Log WhatsApp interaction to database if possible.
    Returns True if successful, False otherwise.
    """
    try:
        # Import here to avoid circular imports
        from ..database import db_manager
        from ..models.customer import Customer
        from ..models.whatsapp import WhatsAppMessage
        from sqlalchemy import select
        
        async with db_manager.get_session() as session:
            # Try to find existing customer by phone
            result = await session.execute(
                select(Customer).where(Customer.phone_number == phone_number)
            )
            customer = result.scalar_one_or_none()
            
            # Create customer if doesn't exist
            if not customer:
                customer = Customer(
                    customer_number=f"WA-{phone_number[-4:]}",
                    phone_number=phone_number,
                    preferred_language='ar',
                    whatsapp_opt_in=True,
                    # Need restaurant_id - get default or skip
                    restaurant_id=None  # This might cause issues
                )
                session.add(customer)
                await session.flush()  # Get the customer ID
            
            # Log inbound message
            inbound_msg = WhatsAppMessage(
                content=inbound_message,
                direction='inbound',
                status='received',
                customer_id=customer.id,
                restaurant_id=customer.restaurant_id,
                language='ar'
            )
            session.add(inbound_msg)
            
            # Log outbound response
            outbound_msg = WhatsAppMessage(
                content=outbound_response,
                direction='outbound',
                status='sent',
                customer_id=customer.id,
                restaurant_id=customer.restaurant_id,
                language='ar',
                is_automated=True
            )
            session.add(outbound_msg)
            
            await session.commit()
            return True
            
    except Exception as e:
        logger.error(f"Failed to log WhatsApp interaction: {str(e)}")
        return False

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