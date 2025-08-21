"""
WhatsApp webhook handler for processing incoming messages and status updates.

This module provides comprehensive webhook processing for WhatsApp Business API,
handling message delivery status, incoming messages, customer interactions,
and system notifications with proper validation and security.
"""

import asyncio
import json
import hmac
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from fastapi import Request, HTTPException

from app.core.config import settings
from app.models.whatsapp import (
    WhatsAppMessage, MessageTemplate, DeliveryReport,
    MessageStatus, MessageType, MessageDirection
)
from app.models.customer import Customer
from .exceptions import WebhookValidationError, WhatsAppAPIError
from .utils import format_phone_number, parse_webhook_timestamp, parse_interactive_response
from .rate_limiter import RateLimiter, RateLimitType


class WebhookEventType(str, Enum):
    """WhatsApp webhook event types."""
    MESSAGE = "message"
    STATUS = "status"
    TEMPLATE_STATUS = "template_status"
    ACCOUNT_UPDATE = "account_update"
    BUSINESS_CAPABILITY_UPDATE = "business_capability_update"


@dataclass
class WebhookEvent:
    """Webhook event data structure."""
    event_type: WebhookEventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    raw_payload: Dict[str, Any]


class WebhookValidator:
    """Webhook validation and security utilities."""
    
    @staticmethod
    def verify_webhook_signature(
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify webhook signature from WhatsApp.
        
        Args:
            payload: Raw webhook payload
            signature: Provided signature
            secret: Webhook secret key
            
        Returns:
            True if signature is valid
        """
        try:
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Calculate expected signature
            expected = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures using constant-time comparison
            return hmac.compare_digest(signature, expected)
            
        except Exception:
            return False
    
    @staticmethod
    def validate_webhook_structure(data: Dict[str, Any]) -> bool:
        """
        Validate basic webhook data structure.
        
        Args:
            data: Webhook payload
            
        Returns:
            True if structure is valid
        """
        try:
            # Check required top-level fields
            if not isinstance(data, dict):
                return False
            
            if 'entry' not in data:
                return False
            
            entries = data['entry']
            if not isinstance(entries, list) or len(entries) == 0:
                return False
            
            # Check each entry
            for entry in entries:
                if not isinstance(entry, dict):
                    return False
                
                if 'changes' not in entry:
                    continue
                
                changes = entry['changes']
                if not isinstance(changes, list):
                    return False
                
                for change in changes:
                    if not isinstance(change, dict):
                        return False
                    
                    if 'value' not in change:
                        return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def extract_phone_number_id(data: Dict[str, Any]) -> Optional[str]:
        """Extract phone number ID from webhook data."""
        try:
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']
            
            return value.get('metadata', {}).get('phone_number_id')
            
        except (KeyError, IndexError):
            return None
    
    @staticmethod
    def is_duplicate_event(
        data: Dict[str, Any],
        processed_events: Set[str]
    ) -> bool:
        """
        Check if webhook event has already been processed.
        
        Args:
            data: Webhook payload
            processed_events: Set of processed event IDs
            
        Returns:
            True if event is duplicate
        """
        try:
            # Generate event ID from key components
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']
            
            # Create unique ID from messages or statuses
            event_ids = []
            
            if 'messages' in value:
                for msg in value['messages']:
                    event_ids.append(f"msg_{msg.get('id')}")
            
            if 'statuses' in value:
                for status in value['statuses']:
                    event_ids.append(f"status_{status.get('id')}_{status.get('status')}")
            
            # Check if any event ID has been processed
            for event_id in event_ids:
                if event_id in processed_events:
                    return True
            
            # Add new event IDs to processed set
            processed_events.update(event_ids)
            return False
            
        except Exception:
            return False


class MessageProcessor:
    """Process incoming WhatsApp messages."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def process_incoming_message(
        self,
        message_data: Dict[str, Any],
        contact_data: Dict[str, Any]
    ) -> Optional[WhatsAppMessage]:
        """
        Process a single incoming message.
        
        Args:
            message_data: Message data from webhook
            contact_data: Contact information
            
        Returns:
            Created message record
        """
        try:
            from_number = message_data.get('from')
            message_id = message_data.get('id')
            message_type = message_data.get('type', 'text')
            timestamp = message_data.get('timestamp')
            
            # Find or create customer
            customer = await self._get_or_create_customer(from_number, contact_data)
            
            # Extract message content
            content = self._extract_message_content(message_data, message_type)
            
            # Create message record
            message_record = WhatsAppMessage(
                whatsapp_message_id=message_id,
                customer_id=customer.id,
                direction=MessageDirection.INBOUND,
                message_type=self._map_message_type(message_type),
                status=MessageStatus.DELIVERED,
                content=content.get('text'),
                media_url=content.get('media_id'),  # Store media ID for later download
                media_type=content.get('mime_type'),
                delivered_at=parse_webhook_timestamp(timestamp).isoformat(),
                webhook_payload=message_data
            )
            
            # Handle interactive message responses
            if message_type == 'interactive':
                response_data = parse_interactive_response(message_data)
                message_record.metadata = {'interactive_response': response_data}
            
            # Handle forwarded messages
            if message_data.get('context', {}).get('forwarded'):
                message_record.metadata = message_record.metadata or {}
                message_record.metadata['forwarded'] = True
            
            # Handle quoted messages
            if 'context' in message_data and 'quoted' in message_data['context']:
                quoted_message_id = message_data['context']['id']
                message_record.metadata = message_record.metadata or {}
                message_record.metadata['quoted_message_id'] = quoted_message_id
            
            self.db.add(message_record)
            self.db.commit()
            self.db.refresh(message_record)
            
            self.logger.info(
                f"Processed incoming message {message_id} from {from_number} "
                f"for customer {customer.id}"
            )
            
            return message_record
            
        except Exception as e:
            self.logger.error(f"Error processing incoming message: {str(e)}")
            self.db.rollback()
            return None
    
    async def _get_or_create_customer(
        self,
        phone_number: str,
        contact_data: Dict[str, Any]
    ) -> Customer:
        """Get existing customer or create new one."""
        formatted_phone = format_phone_number(phone_number)
        
        # Try to find existing customer
        customer = self.db.query(Customer).filter(
            Customer.phone == formatted_phone
        ).first()
        
        if customer:
            # Update customer info if we have new data
            profile = contact_data.get('profile', {})
            if profile.get('name') and not customer.whatsapp_name:
                customer.whatsapp_name = profile['name']
                if not customer.name or customer.name == 'Unknown':
                    customer.name = profile['name']
            return customer
        
        # Create new customer
        profile = contact_data.get('profile', {})
        customer = Customer(
            phone=formatted_phone,
            name=profile.get('name', 'Unknown'),
            whatsapp_name=profile.get('name'),
            language=self._detect_customer_language(contact_data),
            is_active=True
        )
        
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        
        self.logger.info(f"Created new customer {customer.id} for phone {formatted_phone}")
        return customer
    
    def _extract_message_content(
        self,
        message_data: Dict[str, Any],
        message_type: str
    ) -> Dict[str, Any]:
        """Extract content from message based on type."""
        content = {'text': None, 'media_id': None, 'mime_type': None}
        
        if message_type == 'text':
            content['text'] = message_data.get('text', {}).get('body', '')
            
        elif message_type in ['image', 'document', 'audio', 'video']:
            media_data = message_data.get(message_type, {})
            content['media_id'] = media_data.get('id')
            content['mime_type'] = media_data.get('mime_type')
            
            # Caption for images, documents, videos
            if message_type in ['image', 'document', 'video']:
                content['text'] = media_data.get('caption', '')
                
        elif message_type == 'location':
            location = message_data.get('location', {})
            lat = location.get('latitude')
            lng = location.get('longitude')
            name = location.get('name', '')
            address = location.get('address', '')
            
            location_text = f"Location: {lat}, {lng}"
            if name:
                location_text += f" ({name})"
            if address:
                location_text += f" - {address}"
                
            content['text'] = location_text
            
        elif message_type == 'contacts':
            contacts = message_data.get('contacts', [])
            if contacts:
                contact = contacts[0]  # Take first contact
                name = contact.get('name', {}).get('formatted_name', '')
                phones = contact.get('phones', [])
                phone = phones[0].get('phone', '') if phones else ''
                
                content['text'] = f"Contact: {name} ({phone})" if name else f"Phone: {phone}"
                
        elif message_type == 'interactive':
            interactive = message_data.get('interactive', {})
            if interactive.get('type') == 'button_reply':
                button_reply = interactive.get('button_reply', {})
                content['text'] = button_reply.get('title', '')
            elif interactive.get('type') == 'list_reply':
                list_reply = interactive.get('list_reply', {})
                content['text'] = list_reply.get('title', '')
                
        return content
    
    def _map_message_type(self, whatsapp_type: str) -> MessageType:
        """Map WhatsApp message type to internal enum."""
        type_mapping = {
            'text': MessageType.TEXT,
            'image': MessageType.IMAGE,
            'document': MessageType.DOCUMENT,
            'audio': MessageType.AUDIO,
            'video': MessageType.VIDEO,
            'interactive': MessageType.INTERACTIVE,
            'location': MessageType.LOCATION
        }
        return type_mapping.get(whatsapp_type, MessageType.TEXT)
    
    def _detect_customer_language(self, contact_data: Dict[str, Any]) -> str:
        """Attempt to detect customer's preferred language."""
        # This could be enhanced with more sophisticated language detection
        # For now, use default language from settings
        return settings.DEFAULT_LANGUAGE


class StatusProcessor:
    """Process message status updates."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def process_status_update(
        self,
        status_data: Dict[str, Any]
    ) -> bool:
        """
        Process a message status update.
        
        Args:
            status_data: Status data from webhook
            
        Returns:
            True if processed successfully
        """
        try:
            message_id = status_data.get('id')
            recipient_id = status_data.get('recipient_id')
            status_value = status_data.get('status')
            timestamp = status_data.get('timestamp')
            
            # Find the message record
            message = self.db.query(WhatsAppMessage).filter(
                WhatsAppMessage.whatsapp_message_id == message_id
            ).first()
            
            if not message:
                self.logger.warning(f"Message not found for status update: {message_id}")
                return False
            
            # Update message status
            old_status = message.status
            new_status = self._map_status(status_value)
            message.status = new_status
            
            # Update status timestamps
            status_timestamp = parse_webhook_timestamp(timestamp)
            
            if status_value == 'sent':
                message.sent_at = status_timestamp.isoformat()
            elif status_value == 'delivered':
                message.delivered_at = status_timestamp.isoformat()
            elif status_value == 'read':
                message.read_at = status_timestamp.isoformat()
            elif status_value == 'failed':
                message.failed_at = status_timestamp.isoformat()
                
                # Handle failure details
                if 'errors' in status_data:
                    error = status_data['errors'][0]
                    message.error_code = str(error.get('code', ''))
                    message.error_message = error.get('title', 'Message failed')
                    
                    # Check if this is a retryable error
                    if message.can_retry():
                        message.retry_count += 1
                        retry_delay = message.get_retry_delay_seconds()
                        retry_time = datetime.utcnow().timestamp() + retry_delay
                        message.next_retry_at = datetime.fromtimestamp(retry_time).isoformat()
            
            # Create delivery report
            delivery_report = DeliveryReport(
                message_id=message.id,
                status=status_value,
                timestamp=status_timestamp.isoformat(),
                whatsapp_status_id=message_id,
                webhook_payload=status_data
            )
            
            # Add error details to delivery report if failed
            if status_value == 'failed' and 'errors' in status_data:
                error = status_data['errors'][0]
                delivery_report.error_code = str(error.get('code', ''))
                delivery_report.error_title = error.get('title', '')
                delivery_report.error_message = error.get('message', '')
                delivery_report.error_details = error
            
            self.db.add(delivery_report)
            self.db.commit()
            
            self.logger.info(
                f"Updated message {message_id} status from {old_status} to {new_status}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing status update: {str(e)}")
            self.db.rollback()
            return False
    
    def _map_status(self, whatsapp_status: str) -> MessageStatus:
        """Map WhatsApp status to internal enum."""
        status_mapping = {
            'sent': MessageStatus.SENT,
            'delivered': MessageStatus.DELIVERED,
            'read': MessageStatus.READ,
            'failed': MessageStatus.FAILED
        }
        return status_mapping.get(whatsapp_status, MessageStatus.PENDING)


class WebhookHandler:
    """
    Main webhook handler for WhatsApp Business API.
    
    Processes all incoming webhooks including:
    - Message status updates
    - Incoming messages
    - System notifications
    - Template status changes
    """
    
    def __init__(
        self,
        db: Session,
        webhook_secret: Optional[str] = None,
        rate_limiter: Optional[RateLimiter] = None
    ):
        """
        Initialize webhook handler.
        
        Args:
            db: Database session
            webhook_secret: Secret for webhook validation
            rate_limiter: Rate limiter for webhook processing
        """
        self.db = db
        self.webhook_secret = webhook_secret or getattr(settings, 'WHATSAPP_WEBHOOK_SECRET', None)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.logger = logging.getLogger(__name__)
        
        # Message processors
        self.message_processor = MessageProcessor(db)
        self.status_processor = StatusProcessor(db)
        
        # Event tracking for deduplication
        self.processed_events: Set[str] = set()
        
        # Event handlers registry
        self.event_handlers: Dict[WebhookEventType, List[Callable]] = {
            WebhookEventType.MESSAGE: [],
            WebhookEventType.STATUS: [],
            WebhookEventType.TEMPLATE_STATUS: [],
            WebhookEventType.ACCOUNT_UPDATE: [],
            WebhookEventType.BUSINESS_CAPABILITY_UPDATE: []
        }
    
    async def handle_webhook(
        self,
        request: Request,
        validate_signature: bool = True
    ) -> Dict[str, Any]:
        """
        Handle incoming webhook request.
        
        Args:
            request: FastAPI request object
            validate_signature: Whether to validate webhook signature
            
        Returns:
            Processing result
            
        Raises:
            WebhookValidationError: If validation fails
            HTTPException: For HTTP-level errors
        """
        try:
            # Acquire rate limit permission
            await self.rate_limiter.acquire(RateLimitType.WEBHOOK_PROCESSING)
            
            # Get raw body for signature validation
            body = await request.body()
            
            # Validate signature if enabled
            if validate_signature and self.webhook_secret:
                signature = request.headers.get('X-Hub-Signature-256', '')
                if not WebhookValidator.verify_webhook_signature(
                    body, signature, self.webhook_secret
                ):
                    raise WebhookValidationError("Invalid webhook signature")
            
            # Parse JSON data
            try:
                data = json.loads(body)
            except json.JSONDecodeError as e:
                raise WebhookValidationError(f"Invalid JSON: {str(e)}")
            
            # Validate webhook structure
            if not WebhookValidator.validate_webhook_structure(data):
                raise WebhookValidationError("Invalid webhook structure")
            
            # Check for duplicate events
            if WebhookValidator.is_duplicate_event(data, self.processed_events):
                self.logger.info("Duplicate webhook event ignored")
                return {'status': 'ignored', 'reason': 'duplicate'}
            
            # Verify phone number ID matches our configuration
            phone_number_id = WebhookValidator.extract_phone_number_id(data)
            if (phone_number_id and 
                phone_number_id != settings.WHATSAPP_PHONE_NUMBER_ID):
                self.logger.warning(
                    f"Webhook for different phone number ID: {phone_number_id}"
                )
                return {'status': 'ignored', 'reason': 'wrong_phone_number'}
            
            # Process the webhook
            result = await self._process_webhook_data(data)
            
            self.logger.info(f"Webhook processed successfully: {result}")
            return result
            
        except WebhookValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Webhook processing error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal processing error")
    
    async def _process_webhook_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process webhook data and route to appropriate handlers."""
        results = {
            'messages_processed': 0,
            'statuses_processed': 0,
            'templates_processed': 0,
            'other_events_processed': 0,
            'errors': []
        }
        
        try:
            # Process each entry in the webhook
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    
                    # Process messages
                    if 'messages' in value:
                        await self._process_messages(
                            value['messages'],
                            value.get('contacts', [])
                        )
                        results['messages_processed'] += len(value['messages'])
                    
                    # Process status updates
                    if 'statuses' in value:
                        await self._process_statuses(value['statuses'])
                        results['statuses_processed'] += len(value['statuses'])
                    
                    # Process template status updates
                    if 'message_template_status_update' in value:
                        await self._process_template_status(
                            value['message_template_status_update']
                        )
                        results['templates_processed'] += 1
                    
                    # Process other event types
                    if 'account_update' in value:
                        await self._process_account_update(value['account_update'])
                        results['other_events_processed'] += 1
                    
                    if 'business_capability_update' in value:
                        await self._process_business_capability_update(
                            value['business_capability_update']
                        )
                        results['other_events_processed'] += 1
        
        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            results['errors'].append(error_msg)
            self.logger.error(error_msg)
        
        return results
    
    async def _process_messages(
        self,
        messages: List[Dict[str, Any]],
        contacts: List[Dict[str, Any]]
    ):
        """Process incoming messages."""
        contact_map = {
            contact.get('wa_id'): contact 
            for contact in contacts
        }
        
        for message_data in messages:
            try:
                from_number = message_data.get('from')
                contact_data = contact_map.get(from_number, {})
                
                message_record = await self.message_processor.process_incoming_message(
                    message_data, contact_data
                )
                
                if message_record:
                    # Trigger message event handlers
                    await self._trigger_event_handlers(
                        WebhookEventType.MESSAGE,
                        {
                            'message': message_record,
                            'raw_data': message_data,
                            'contact_data': contact_data
                        }
                    )
                
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")
    
    async def _process_statuses(self, statuses: List[Dict[str, Any]]):
        """Process message status updates."""
        for status_data in statuses:
            try:
                success = await self.status_processor.process_status_update(status_data)
                
                if success:
                    # Trigger status event handlers
                    await self._trigger_event_handlers(
                        WebhookEventType.STATUS,
                        {
                            'status_data': status_data,
                            'message_id': status_data.get('id'),
                            'status': status_data.get('status')
                        }
                    )
                
            except Exception as e:
                self.logger.error(f"Error processing status: {str(e)}")
    
    async def _process_template_status(self, template_status: Dict[str, Any]):
        """Process template status update."""
        try:
            template_name = template_status.get('name')
            status = template_status.get('status')
            language = template_status.get('language')
            
            # Find and update template record
            template = self.db.query(MessageTemplate).filter(
                MessageTemplate.name == template_name,
                MessageTemplate.language == language
            ).first()
            
            if template:
                template.status = status
                
                # Update status timestamps
                now = datetime.utcnow().isoformat()
                if status == 'APPROVED':
                    template.approved_at = now
                elif status == 'REJECTED':
                    template.rejected_at = now
                    template.rejection_reason = template_status.get('reason', '')
                
                self.db.commit()
                
                # Trigger template status event handlers
                await self._trigger_event_handlers(
                    WebhookEventType.TEMPLATE_STATUS,
                    {
                        'template': template,
                        'old_status': template.status,
                        'new_status': status,
                        'raw_data': template_status
                    }
                )
            
        except Exception as e:
            self.logger.error(f"Error processing template status: {str(e)}")
    
    async def _process_account_update(self, account_update: Dict[str, Any]):
        """Process account update notification."""
        try:
            # Log account updates for monitoring
            self.logger.info(f"Account update received: {account_update}")
            
            await self._trigger_event_handlers(
                WebhookEventType.ACCOUNT_UPDATE,
                {'account_update': account_update}
            )
            
        except Exception as e:
            self.logger.error(f"Error processing account update: {str(e)}")
    
    async def _process_business_capability_update(
        self,
        capability_update: Dict[str, Any]
    ):
        """Process business capability update notification."""
        try:
            # Log capability updates for monitoring
            self.logger.info(f"Business capability update: {capability_update}")
            
            await self._trigger_event_handlers(
                WebhookEventType.BUSINESS_CAPABILITY_UPDATE,
                {'capability_update': capability_update}
            )
            
        except Exception as e:
            self.logger.error(f"Error processing capability update: {str(e)}")
    
    async def _trigger_event_handlers(
        self,
        event_type: WebhookEventType,
        event_data: Dict[str, Any]
    ):
        """Trigger registered event handlers."""
        handlers = self.event_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            except Exception as e:
                self.logger.error(
                    f"Error in event handler for {event_type}: {str(e)}"
                )
    
    def register_event_handler(
        self,
        event_type: WebhookEventType,
        handler: Callable
    ):
        """
        Register an event handler for specific webhook events.
        
        Args:
            event_type: Type of event to handle
            handler: Handler function (sync or async)
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
    
    def unregister_event_handler(
        self,
        event_type: WebhookEventType,
        handler: Callable
    ):
        """Remove an event handler."""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    async def verify_webhook(
        self,
        mode: str,
        token: str,
        challenge: str,
        verify_token: str
    ) -> str:
        """
        Verify webhook subscription (used during setup).
        
        Args:
            mode: Verification mode
            token: Provided token
            challenge: Challenge string
            verify_token: Expected verification token
            
        Returns:
            Challenge string if verification successful
            
        Raises:
            HTTPException: If verification fails
        """
        if mode == "subscribe" and token == verify_token:
            self.logger.info("Webhook verification successful")
            return challenge
        else:
            self.logger.error("Webhook verification failed")
            raise HTTPException(status_code=403, detail="Verification failed")
    
    def cleanup_processed_events(self, max_age_hours: int = 24):
        """Clean up old processed event IDs to prevent memory growth."""
        # This is a simple implementation - in production you might want
        # to use a more sophisticated approach with timestamps
        if len(self.processed_events) > 10000:  # Arbitrary limit
            # Keep only the most recent half
            events_list = list(self.processed_events)
            self.processed_events = set(events_list[-5000:])
            
            self.logger.info("Cleaned up old processed event IDs")