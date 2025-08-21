"""
Twilio WhatsApp service for sending automated customer feedback messages.
Uses Twilio's WhatsApp Business API for reliable message delivery.
"""
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging

from ..core.config import settings
from ..models.customer import Customer
from ..models.whatsapp import WhatsAppMessage
from ..database import db_manager

logger = logging.getLogger(__name__)

class TwilioWhatsAppService:
    """Service for sending WhatsApp messages via Twilio."""
    
    def __init__(self):
        """Initialize Twilio client with credentials."""
        # Twilio credentials from settings
        self.account_sid = settings.twilio.TWILIO_ACCOUNT_SID or ''
        self.auth_token = settings.twilio.TWILIO_AUTH_TOKEN or ''
        self.whatsapp_number = settings.twilio.TWILIO_WHATSAPP_NUMBER or "whatsapp:+14155238886"
        # Extract sandbox code properly
        sandbox_env = settings.twilio.TWILIO_SANDBOX_CODE or ''
        logger.info(f"Loaded environment variables - SID: {self.account_sid[:10] + '...' if self.account_sid else 'None'}, Sandbox: '{sandbox_env}'")
        if sandbox_env.startswith('join '):
            self.sandbox_code = sandbox_env.replace('join ', '').strip()
        else:
            self.sandbox_code = sandbox_env.strip()
        
        # Initialize Twilio client if credentials exist
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            self.enabled = True
            logger.info("Twilio WhatsApp service initialized successfully")
        else:
            self.client = None
            self.enabled = False
            logger.warning("Twilio WhatsApp service disabled - missing credentials")
    
    def format_phone_number(self, phone: str) -> str:
        """Format phone number for WhatsApp (must include country code)."""
        # Remove any spaces or special characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Add country code if not present (assuming Saudi Arabia +966)
        if not phone.startswith('966') and not phone.startswith('+'):
            phone = '966' + phone
        
        # Ensure + prefix
        if not phone.startswith('+'):
            phone = '+' + phone
            
        return f"whatsapp:{phone}"
    
    def get_greeting_message(self, customer: Customer, language: str = 'ar') -> str:
        """Generate personalized greeting message based on language."""
        
        if language == 'ar':
            # Arabic message
            name = customer.first_name or "عميلنا العزيز"
            message = f"""مرحباً {name}! 👋

شكراً لزيارتكم مطعم الأصالة اليوم. نأمل أن تكون تجربتكم معنا مميزة.

نود أن نسمع رأيكم الكريم عن زيارتكم. هل يمكنكم مشاركتنا تجربتكم؟

1️⃣ ممتازة 😊
2️⃣ جيدة 👍
3️⃣ متوسطة 😐
4️⃣ تحتاج تحسين 😔

يرجى الرد برقم اختياركم."""
        else:
            # English message
            name = customer.first_name or "Valued Guest"
            message = f"""Hello {name}! 👋

Thank you for visiting Al Asala Restaurant today. We hope you had a wonderful experience.

We'd love to hear your feedback about your visit. How was your experience?

1️⃣ Excellent 😊
2️⃣ Good 👍
3️⃣ Average 😐
4️⃣ Needs Improvement 😔

Please reply with your choice number."""
        
        return message
    
    async def send_message(
        self, 
        customer: Customer, 
        message_type: str = 'greeting',
        custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp message to customer.
        
        Args:
            customer: Customer object with phone number
            message_type: Type of message (greeting, follow_up, thank_you)
            custom_message: Optional custom message to send
            
        Returns:
            Dict with status and message details
        """
        if not self.enabled:
            logger.error("Twilio WhatsApp service is not enabled")
            return {
                'success': False,
                'error': 'WhatsApp service not configured',
                'message': 'Please configure Twilio credentials in .env file'
            }
        
        try:
            # Format recipient phone number
            to_number = self.format_phone_number(customer.phone_number)
            
            # Get message content
            if custom_message:
                message_body = custom_message
            elif message_type == 'greeting':
                message_body = self.get_greeting_message(
                    customer, 
                    customer.preferred_language or 'ar'
                )
            else:
                message_body = "Thank you for visiting our restaurant!"
            
            # Send message via Twilio
            message = self.client.messages.create(
                body=message_body,
                from_=self.whatsapp_number,
                to=to_number
            )
            
            logger.info(f"WhatsApp message sent successfully to {customer.phone_number}")
            
            # Save message to database
            await self._save_message_record(
                customer=customer,
                message_body=message_body,
                twilio_sid=message.sid,
                status='sent'
            )
            
            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status,
                'to': customer.phone_number,
                'message': 'Message sent successfully'
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio error sending message: {str(e)}")
            
            # Common error handling
            error_message = str(e)
            if "join" in error_message.lower():
                return {
                    'success': False,
                    'error': 'sandbox_not_joined',
                    'message': f'Customer needs to join sandbox first. Send "join {self.sandbox_code}" to {self.whatsapp_number.replace("whatsapp:", "")}'
                }
            
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to send WhatsApp message'
            }
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp message: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'An unexpected error occurred'
            }
    
    async def _save_message_record(
        self,
        customer: Customer,
        message_body: str,
        twilio_sid: str,
        status: str
    ):
        """Save message record to database."""
        try:
            async with db_manager.get_session() as session:
                message = WhatsAppMessage(
                    whatsapp_message_id=twilio_sid,
                    message_type='text',
                    content=message_body,
                    language=customer.preferred_language or 'ar',
                    direction='outbound',
                    status=status,
                    sent_at=datetime.utcnow(),
                    is_automated=True,
                    restaurant_id=customer.restaurant_id,
                    customer_id=customer.id,
                    context={'service': 'twilio', 'type': 'greeting'}
                )
                session.add(message)
                await session.commit()
                logger.info(f"Message record saved for customer {customer.id}")
        except Exception as e:
            logger.error(f"Failed to save message record: {str(e)}")
    
    def get_sandbox_instructions(self) -> Dict[str, str]:
        """Get instructions for joining Twilio WhatsApp sandbox."""
        return {
            'sandbox_number': self.whatsapp_number.replace('whatsapp:', ''),
            'join_code': f"join {self.sandbox_code}",
            'instructions': {
                'en': f"To test WhatsApp messages, customer must first send 'join {self.sandbox_code}' to {self.whatsapp_number.replace('whatsapp:', '')}",
                'ar': f"للاختبار، يجب على العميل أولاً إرسال 'join {self.sandbox_code}' إلى {self.whatsapp_number.replace('whatsapp:', '')}"
            }
        }
    
    async def send_test_message(self, phone_number: str) -> Dict[str, Any]:
        """Send a test message to verify setup."""
        test_customer = Customer(
            first_name="Test",
            last_name="User",
            phone_number=phone_number,
            preferred_language='en'
        )
        
        test_message = """🔧 Test Message from Restaurant AI Agent

This is a test message to confirm WhatsApp integration is working.

If you received this message, the setup is successful! ✅

Reply with 'OK' to confirm receipt."""
        
        return await self.send_message(
            customer=test_customer,
            custom_message=test_message
        )

# Global service instance
twilio_service = TwilioWhatsAppService()

async def send_automated_greeting(customer_id: str, delay_hours: float = 2.0):
    """
    Send automated greeting message after a delay.
    
    Args:
        customer_id: Customer ID to send message to
        delay_hours: Hours to wait before sending (default 2 hours)
    """
    # Wait for specified delay
    await asyncio.sleep(delay_hours * 3600)
    
    # Get customer from database
    async with db_manager.get_session() as session:
        customer = await session.get(Customer, customer_id)
        if customer and customer.whatsapp_opt_in:
            result = await twilio_service.send_message(customer, 'greeting')
            if result['success']:
                logger.info(f"Automated greeting sent to customer {customer_id}")
            else:
                logger.error(f"Failed to send automated greeting: {result['error']}")