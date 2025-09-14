"""
WhatsApp Service Layer
Handles WhatsApp messaging and webhook processing business logic.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID
import logging
import traceback

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models import Customer, WhatsAppMessage, Restaurant
from ..services.twilio_whatsapp import twilio_service
from ..core.logging import get_logger

logger = get_logger(__name__)


class WhatsAppService:
    """Service class for WhatsApp-related business logic."""

    def __init__(self, session: AsyncSession):
        """Initialize the service with a database session."""
        self.session = session
        self.twilio_service = twilio_service

    async def process_incoming_message(
        self,
        message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process an incoming WhatsApp message."""
        try:
            # Extract message details
            from_number = message_data.get('From', '').replace('whatsapp:', '')
            to_number = message_data.get('To', '').replace('whatsapp:', '')
            message_body = message_data.get('Body', '')
            message_sid = message_data.get('MessageSid', '')

            # Find or create customer
            customer = await self._find_or_create_customer(from_number)

            # Save message to database
            message = await self._save_message(
                customer_id=customer.id if customer else None,
                from_number=from_number,
                to_number=to_number,
                message_body=message_body,
                message_sid=message_sid,
                direction='inbound',
                raw_data=message_data
            )

            # Process message based on content
            response = await self._generate_response(customer, message_body)

            # Send response if generated
            if response:
                await self.send_message(
                    to_number=from_number,
                    message_body=response,
                    customer_id=customer.id if customer else None
                )

            return {
                "status": "processed",
                "message_id": str(message.id) if message else None,
                "customer_id": str(customer.id) if customer else None,
                "response_sent": bool(response)
            }

        except Exception as e:
            logger.error(f"Error processing incoming message: {str(e)}\n{traceback.format_exc()}")
            raise

    async def process_status_update(
        self,
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a WhatsApp message status update."""
        try:
            message_sid = status_data.get('MessageSid', '')
            status = status_data.get('MessageStatus', '')

            # Update message status in database
            stmt = select(WhatsAppMessage).where(
                WhatsAppMessage.twilio_sid == message_sid
            )
            result = await self.session.execute(stmt)
            message = result.scalar_one_or_none()

            if message:
                message.status = status
                message.updated_at = datetime.utcnow()

                # Add status history
                if not message.status_history:
                    message.status_history = []

                message.status_history.append({
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat(),
                    "raw_data": status_data
                })

                await self.session.commit()

                logger.info(f"Updated message {message_sid} status to {status}")

            return {
                "status": "processed",
                "message_sid": message_sid,
                "new_status": status
            }

        except Exception as e:
            logger.error(f"Error processing status update: {str(e)}\n{traceback.format_exc()}")
            raise

    async def send_message(
        self,
        to_number: str,
        message_body: str,
        customer_id: Optional[UUID] = None,
        template_data: Optional[Dict] = None
    ) -> WhatsAppMessage:
        """Send a WhatsApp message."""
        try:
            # Format the recipient number
            formatted_to = self._format_phone_number(to_number)

            # Send via Twilio
            if self.twilio_service.enabled:
                twilio_response = await self.twilio_service.send_whatsapp_message(
                    to_number=formatted_to,
                    message_body=message_body,
                    template_data=template_data
                )
                message_sid = twilio_response.get('sid') if twilio_response else None
            else:
                logger.warning("Twilio service is disabled, message not sent")
                message_sid = None

            # Save message to database
            message = await self._save_message(
                customer_id=customer_id,
                from_number=self.twilio_service.whatsapp_number if self.twilio_service.enabled else None,
                to_number=to_number,
                message_body=message_body,
                message_sid=message_sid,
                direction='outbound',
                template_data=template_data
            )

            return message

        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}\n{traceback.format_exc()}")
            raise

    async def send_bulk_messages(
        self,
        customer_ids: List[UUID],
        message_template: str,
        personalize: bool = True
    ) -> Dict[str, Any]:
        """Send bulk WhatsApp messages to multiple customers."""
        results = {
            "total": len(customer_ids),
            "successful": 0,
            "failed": 0,
            "errors": []
        }

        for customer_id in customer_ids:
            try:
                # Get customer
                customer = await self._get_customer(customer_id)
                if not customer:
                    results["failed"] += 1
                    results["errors"].append({
                        "customer_id": str(customer_id),
                        "error": "Customer not found"
                    })
                    continue

                # Personalize message if requested
                if personalize:
                    message_body = self._personalize_message(message_template, customer)
                else:
                    message_body = message_template

                # Send message
                await self.send_message(
                    to_number=customer.phone_number,
                    message_body=message_body,
                    customer_id=customer.id
                )

                results["successful"] += 1

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "customer_id": str(customer_id),
                    "error": str(e)
                })
                logger.error(f"Error sending message to customer {customer_id}: {str(e)}")

        return results

    async def get_conversation_history(
        self,
        customer_id: UUID,
        limit: int = 50
    ) -> List[WhatsAppMessage]:
        """Get conversation history for a customer."""
        stmt = select(WhatsAppMessage).where(
            WhatsAppMessage.customer_id == customer_id
        ).order_by(
            WhatsAppMessage.created_at.desc()
        ).limit(limit)

        result = await self.session.execute(stmt)
        messages = result.scalars().all()

        return messages

    # Private helper methods
    async def _find_or_create_customer(self, phone_number: str) -> Optional[Customer]:
        """Find existing customer or create a placeholder."""
        # Clean phone number
        clean_phone = self._clean_phone_number(phone_number)

        # Try to find existing customer
        stmt = select(Customer).where(
            and_(
                Customer.phone_number == clean_phone,
                Customer.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        customer = result.scalar_one_or_none()

        if not customer:
            # Create placeholder customer
            customer = Customer(
                phone_number=clean_phone,
                name=f"WhatsApp User {clean_phone[-4:]}",
                status="pending",
                visit_date=datetime.utcnow()
            )
            self.session.add(customer)
            await self.session.commit()
            await self.session.refresh(customer)

            logger.info(f"Created placeholder customer for phone: {clean_phone}")

        return customer

    async def _get_customer(self, customer_id: UUID) -> Optional[Customer]:
        """Get customer by ID."""
        stmt = select(Customer).where(Customer.id == customer_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _save_message(
        self,
        customer_id: Optional[UUID],
        from_number: str,
        to_number: str,
        message_body: str,
        message_sid: Optional[str],
        direction: str,
        raw_data: Optional[Dict] = None,
        template_data: Optional[Dict] = None
    ) -> WhatsAppMessage:
        """Save WhatsApp message to database."""
        message = WhatsAppMessage(
            customer_id=customer_id,
            from_number=from_number,
            to_number=to_number,
            message_body=message_body,
            twilio_sid=message_sid,
            direction=direction,
            status="sent" if direction == "outbound" else "received",
            raw_data=raw_data,
            template_data=template_data
        )

        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)

        logger.info(f"Saved {direction} message: {message.id}")
        return message

    async def _generate_response(
        self,
        customer: Optional[Customer],
        message_body: str
    ) -> Optional[str]:
        """Generate automated response based on message content."""
        # This is a placeholder for AI-based response generation
        # Will be enhanced with AI service integration

        message_lower = message_body.lower()

        # Basic keyword-based responses
        if any(keyword in message_lower for keyword in ['hello', 'hi', 'hey']):
            return f"Hello! Thank you for contacting us. How can we help you today?"

        if any(keyword in message_lower for keyword in ['menu', 'food', 'dishes']):
            return "You can view our menu at our website. Would you like to make a reservation?"

        if any(keyword in message_lower for keyword in ['reservation', 'book', 'table']):
            return "To make a reservation, please visit our website or call us directly. What date were you thinking of?"

        if any(keyword in message_lower for keyword in ['hours', 'open', 'close']):
            return "We're open Monday-Friday 11:00 AM - 10:00 PM, and Saturday-Sunday 10:00 AM - 11:00 PM."

        # Default response
        return None

    def _format_phone_number(self, phone_number: str) -> str:
        """Format phone number for WhatsApp."""
        # Remove any whatsapp: prefix
        clean = phone_number.replace('whatsapp:', '')

        # Add whatsapp: prefix if not present
        if not clean.startswith('whatsapp:'):
            clean = f'whatsapp:{clean}'

        return clean

    def _clean_phone_number(self, phone_number: str) -> str:
        """Clean phone number for storage."""
        # Remove whatsapp: prefix and any non-digit characters
        clean = phone_number.replace('whatsapp:', '')
        clean = ''.join(filter(str.isdigit, clean))

        # Add country code if missing (assuming US)
        if len(clean) == 10:
            clean = f'1{clean}'

        return f'+{clean}'

    def _personalize_message(self, template: str, customer: Customer) -> str:
        """Personalize message template with customer data."""
        return template.format(
            name=customer.name or "Valued Customer",
            phone=customer.phone_number,
            restaurant=customer.restaurant.name if customer.restaurant else "our restaurant"
        )