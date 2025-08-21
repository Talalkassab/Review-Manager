"""
WhatsApp Business Cloud API client for sending and receiving messages.

This module provides a comprehensive client for integrating with WhatsApp Business API,
supporting message sending, template management, media handling, and webhook processing.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urljoin

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.whatsapp import (
    WhatsAppMessage, MessageTemplate, DeliveryReport,
    MessageStatus, MessageType, MessageDirection, Priority
)
from app.models.customer import Customer
from .exceptions import (
    WhatsAppAPIError, RateLimitExceededError, InvalidPhoneNumberError,
    TemplateNotFoundError, MediaUploadError
)
from .utils import format_phone_number, validate_phone_number
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """
    WhatsApp Business Cloud API client with comprehensive message management.
    
    Features:
    - Async message sending with retry mechanism
    - Template message management
    - Media handling (images, documents, audio, video)
    - Delivery tracking and status updates
    - Rate limiting and queue management
    - Bulk messaging capabilities
    - Interactive messages support
    - Webhook processing
    """
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, db_session: Session):
        """Initialize WhatsApp client with database session."""
        self.db = db_session
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.business_account_id = settings.WHATSAPP_BUSINESS_ACCOUNT_ID
        
        # Rate limiter configuration
        self.rate_limiter = RateLimiter(
            max_requests=80,  # WhatsApp allows 80 requests per second
            time_window=60,   # Per minute
            burst_limit=1000  # Daily message limit
        )
        
        # HTTP client configuration
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        
        if not all([self.access_token, self.phone_number_id]):
            raise ValueError("WhatsApp credentials not configured properly")
    
    async def send_text_message(
        self,
        phone_number: str,
        message: str,
        customer_id: int,
        priority: Priority = Priority.NORMAL,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WhatsAppMessage:
        """
        Send a text message to a customer.
        
        Args:
            phone_number: Recipient's phone number
            message: Text message content
            customer_id: Customer database ID
            priority: Message priority level
            conversation_id: Optional conversation tracking ID
            metadata: Additional metadata for the message
            
        Returns:
            WhatsAppMessage: Created message record
            
        Raises:
            InvalidPhoneNumberError: If phone number format is invalid
            WhatsAppAPIError: If API request fails
        """
        # Validate and format phone number
        formatted_phone = format_phone_number(phone_number)
        if not validate_phone_number(formatted_phone):
            raise InvalidPhoneNumberError(f"Invalid phone number format: {phone_number}")
        
        # Create message record
        message_record = WhatsAppMessage(
            customer_id=customer_id,
            direction=MessageDirection.OUTBOUND,
            message_type=MessageType.TEXT,
            status=MessageStatus.PENDING,
            priority=priority,
            content=message,
            conversation_id=conversation_id,
            metadata=metadata or {}
        )
        
        self.db.add(message_record)
        self.db.commit()
        self.db.refresh(message_record)
        
        try:
            # Check rate limits
            await self.rate_limiter.acquire()
            
            # Prepare API request
            url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": formatted_phone,
                "type": "text",
                "text": {"body": message}
            }
            
            # Send message
            response = await self.client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Update message record with API response
                message_record.whatsapp_message_id = response_data["messages"][0]["id"]
                message_record.status = MessageStatus.SENT
                message_record.sent_at = datetime.utcnow().isoformat()
                message_record.api_response = response_data
                
                logger.info(f"Text message sent successfully to {formatted_phone}: {message_record.whatsapp_message_id}")
                
            else:
                # Handle API errors
                await self._handle_api_error(message_record, response)
                
        except Exception as e:
            await self._handle_send_error(message_record, e)
            
        finally:
            self.db.commit()
            
        return message_record
    
    async def send_template_message(
        self,
        phone_number: str,
        template_name: str,
        language_code: str,
        parameters: Optional[Dict[str, Any]] = None,
        customer_id: int,
        priority: Priority = Priority.NORMAL,
        conversation_id: Optional[str] = None
    ) -> WhatsAppMessage:
        """
        Send a template message to a customer.
        
        Args:
            phone_number: Recipient's phone number
            template_name: WhatsApp template name
            language_code: Template language (e.g., 'ar', 'en')
            parameters: Template parameter values
            customer_id: Customer database ID
            priority: Message priority level
            conversation_id: Optional conversation tracking ID
            
        Returns:
            WhatsAppMessage: Created message record
            
        Raises:
            TemplateNotFoundError: If template doesn't exist or isn't approved
            InvalidPhoneNumberError: If phone number format is invalid
        """
        # Validate phone number
        formatted_phone = format_phone_number(phone_number)
        if not validate_phone_number(formatted_phone):
            raise InvalidPhoneNumberError(f"Invalid phone number format: {phone_number}")
        
        # Get and validate template
        template = self.db.query(MessageTemplate).filter(
            MessageTemplate.name == template_name,
            MessageTemplate.language == language_code
        ).first()
        
        if not template or not template.can_be_used():
            raise TemplateNotFoundError(f"Template '{template_name}' not found or not approved")
        
        # Validate template parameters
        if not template.validate_parameters(parameters or {}):
            raise ValueError(f"Invalid parameters for template '{template_name}'")
        
        # Create message record
        message_record = WhatsAppMessage(
            customer_id=customer_id,
            direction=MessageDirection.OUTBOUND,
            message_type=MessageType.TEMPLATE,
            status=MessageStatus.PENDING,
            priority=priority,
            template_name=template_name,
            template_language=language_code,
            template_parameters=parameters,
            conversation_id=conversation_id
        )
        
        self.db.add(message_record)
        self.db.commit()
        self.db.refresh(message_record)
        
        try:
            # Check rate limits
            await self.rate_limiter.acquire()
            
            # Prepare template payload
            template_payload = {
                "name": template_name,
                "language": {"code": language_code}
            }
            
            # Add parameters if provided
            if parameters:
                template_payload["components"] = self._build_template_components(template, parameters)
            
            # Prepare API request
            url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": formatted_phone,
                "type": "template",
                "template": template_payload
            }
            
            # Send message
            response = await self.client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Update message record
                message_record.whatsapp_message_id = response_data["messages"][0]["id"]
                message_record.status = MessageStatus.SENT
                message_record.sent_at = datetime.utcnow().isoformat()
                message_record.api_response = response_data
                
                # Update template usage
                template.increment_usage()
                
                logger.info(f"Template message sent successfully to {formatted_phone}: {message_record.whatsapp_message_id}")
                
            else:
                await self._handle_api_error(message_record, response)
                
        except Exception as e:
            await self._handle_send_error(message_record, e)
            
        finally:
            self.db.commit()
            
        return message_record
    
    async def send_media_message(
        self,
        phone_number: str,
        media_url: str,
        media_type: MessageType,
        customer_id: int,
        caption: Optional[str] = None,
        priority: Priority = Priority.NORMAL,
        conversation_id: Optional[str] = None
    ) -> WhatsAppMessage:
        """
        Send a media message (image, document, audio, video).
        
        Args:
            phone_number: Recipient's phone number
            media_url: URL of the media file
            media_type: Type of media (IMAGE, DOCUMENT, AUDIO, VIDEO)
            customer_id: Customer database ID
            caption: Optional media caption
            priority: Message priority level
            conversation_id: Optional conversation tracking ID
            
        Returns:
            WhatsAppMessage: Created message record
        """
        # Validate phone number
        formatted_phone = format_phone_number(phone_number)
        if not validate_phone_number(formatted_phone):
            raise InvalidPhoneNumberError(f"Invalid phone number format: {phone_number}")
        
        # Validate media type
        if media_type not in [MessageType.IMAGE, MessageType.DOCUMENT, MessageType.AUDIO, MessageType.VIDEO]:
            raise ValueError(f"Invalid media type: {media_type}")
        
        # Create message record
        message_record = WhatsAppMessage(
            customer_id=customer_id,
            direction=MessageDirection.OUTBOUND,
            message_type=media_type,
            status=MessageStatus.PENDING,
            priority=priority,
            media_url=media_url,
            content=caption,
            conversation_id=conversation_id
        )
        
        self.db.add(message_record)
        self.db.commit()
        self.db.refresh(message_record)
        
        try:
            # Check rate limits
            await self.rate_limiter.acquire()
            
            # Prepare media payload
            media_payload = {"link": media_url}
            if caption and media_type in [MessageType.IMAGE, MessageType.DOCUMENT, MessageType.VIDEO]:
                media_payload["caption"] = caption
            
            # Prepare API request
            url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": formatted_phone,
                "type": media_type.value,
                media_type.value: media_payload
            }
            
            # Send message
            response = await self.client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Update message record
                message_record.whatsapp_message_id = response_data["messages"][0]["id"]
                message_record.status = MessageStatus.SENT
                message_record.sent_at = datetime.utcnow().isoformat()
                message_record.api_response = response_data
                
                logger.info(f"Media message sent successfully to {formatted_phone}: {message_record.whatsapp_message_id}")
                
            else:
                await self._handle_api_error(message_record, response)
                
        except Exception as e:
            await self._handle_send_error(message_record, e)
            
        finally:
            self.db.commit()
            
        return message_record
    
    async def send_interactive_message(
        self,
        phone_number: str,
        interactive_type: str,
        header_text: Optional[str],
        body_text: str,
        footer_text: Optional[str],
        buttons: List[Dict[str, Any]],
        customer_id: int,
        priority: Priority = Priority.NORMAL,
        conversation_id: Optional[str] = None
    ) -> WhatsAppMessage:
        """
        Send an interactive message with buttons or lists.
        
        Args:
            phone_number: Recipient's phone number
            interactive_type: Type of interactive message ('button' or 'list')
            header_text: Optional header text
            body_text: Main message body
            footer_text: Optional footer text
            buttons: List of interactive buttons/options
            customer_id: Customer database ID
            priority: Message priority level
            conversation_id: Optional conversation tracking ID
            
        Returns:
            WhatsAppMessage: Created message record
        """
        # Validate phone number
        formatted_phone = format_phone_number(phone_number)
        if not validate_phone_number(formatted_phone):
            raise InvalidPhoneNumberError(f"Invalid phone number format: {phone_number}")
        
        # Create message record
        message_record = WhatsAppMessage(
            customer_id=customer_id,
            direction=MessageDirection.OUTBOUND,
            message_type=MessageType.INTERACTIVE,
            status=MessageStatus.PENDING,
            priority=priority,
            content=body_text,
            conversation_id=conversation_id,
            metadata={"interactive_type": interactive_type, "buttons": buttons}
        )
        
        self.db.add(message_record)
        self.db.commit()
        self.db.refresh(message_record)
        
        try:
            # Check rate limits
            await self.rate_limiter.acquire()
            
            # Prepare interactive payload
            interactive_payload = {
                "type": interactive_type,
                "body": {"text": body_text}
            }
            
            if header_text:
                interactive_payload["header"] = {"type": "text", "text": header_text}
            
            if footer_text:
                interactive_payload["footer"] = {"text": footer_text}
            
            # Add buttons based on type
            if interactive_type == "button":
                interactive_payload["action"] = {"buttons": buttons}
            elif interactive_type == "list":
                interactive_payload["action"] = {"sections": buttons}
            
            # Prepare API request
            url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": formatted_phone,
                "type": "interactive",
                "interactive": interactive_payload
            }
            
            # Send message
            response = await self.client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Update message record
                message_record.whatsapp_message_id = response_data["messages"][0]["id"]
                message_record.status = MessageStatus.SENT
                message_record.sent_at = datetime.utcnow().isoformat()
                message_record.api_response = response_data
                
                logger.info(f"Interactive message sent successfully to {formatted_phone}: {message_record.whatsapp_message_id}")
                
            else:
                await self._handle_api_error(message_record, response)
                
        except Exception as e:
            await self._handle_send_error(message_record, e)
            
        finally:
            self.db.commit()
            
        return message_record
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Optional[WhatsAppMessage]:
        """
        Process incoming webhook from WhatsApp.
        
        Args:
            webhook_data: Webhook payload from WhatsApp
            
        Returns:
            WhatsAppMessage: Processed message record if applicable
        """
        try:
            if not self._is_valid_webhook(webhook_data):
                logger.warning("Invalid webhook data received")
                return None
            
            # Extract message data
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            # Handle message status updates
            if "statuses" in value:
                await self._process_status_updates(value["statuses"])
            
            # Handle incoming messages
            if "messages" in value:
                return await self._process_incoming_messages(value["messages"], value.get("contacts", []))
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            logger.error(f"Webhook data: {json.dumps(webhook_data, indent=2)}")
        
        return None
    
    def _build_template_components(self, template: MessageTemplate, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build template components with parameters."""
        components = []
        
        # Header component
        if template.header_text and template.parameters:
            header_params = [p for p in template.parameters if p.get('component') == 'header']
            if header_params:
                components.append({
                    "type": "header",
                    "parameters": [{"type": "text", "text": str(parameters.get(p['name'], ''))} for p in header_params]
                })
        
        # Body component
        body_params = [p for p in template.parameters or [] if p.get('component') == 'body']
        if body_params:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": str(parameters.get(p['name'], ''))} for p in body_params]
            })
        
        return components
    
    async def _handle_api_error(self, message_record: WhatsAppMessage, response: httpx.Response):
        """Handle API error responses."""
        try:
            error_data = response.json()
            error_info = error_data.get("error", {})
            
            message_record.status = MessageStatus.FAILED
            message_record.failed_at = datetime.utcnow().isoformat()
            message_record.error_code = str(error_info.get("code", response.status_code))
            message_record.error_message = error_info.get("message", "Unknown API error")
            message_record.api_response = error_data
            
            # Handle rate limiting
            if response.status_code == 429:
                raise RateLimitExceededError("WhatsApp API rate limit exceeded")
            
            logger.error(f"WhatsApp API error: {message_record.error_code} - {message_record.error_message}")
            
        except (json.JSONDecodeError, KeyError):
            message_record.status = MessageStatus.FAILED
            message_record.failed_at = datetime.utcnow().isoformat()
            message_record.error_code = str(response.status_code)
            message_record.error_message = f"HTTP {response.status_code}: {response.text}"
    
    async def _handle_send_error(self, message_record: WhatsAppMessage, error: Exception):
        """Handle general sending errors."""
        message_record.status = MessageStatus.FAILED
        message_record.failed_at = datetime.utcnow().isoformat()
        message_record.error_message = str(error)
        message_record.retry_count += 1
        
        # Schedule retry if within limits
        if message_record.can_retry():
            delay_seconds = message_record.get_retry_delay_seconds()
            retry_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
            message_record.next_retry_at = retry_time.isoformat()
        
        logger.error(f"Message send error: {str(error)}")
    
    def _is_valid_webhook(self, data: Dict[str, Any]) -> bool:
        """Validate webhook data structure."""
        return (
            isinstance(data, dict) and
            "entry" in data and
            isinstance(data["entry"], list) and
            len(data["entry"]) > 0
        )
    
    async def _process_status_updates(self, statuses: List[Dict[str, Any]]):
        """Process message status updates from webhooks."""
        for status in statuses:
            message_id = status.get("id")
            recipient_id = status.get("recipient_id")
            status_value = status.get("status")
            timestamp = status.get("timestamp")
            
            # Find message record
            message = self.db.query(WhatsAppMessage).filter(
                WhatsAppMessage.whatsapp_message_id == message_id
            ).first()
            
            if message:
                # Update message status
                old_status = message.status
                message.status = self._map_webhook_status(status_value)
                
                # Update timestamps
                if status_value == "delivered":
                    message.delivered_at = datetime.fromtimestamp(int(timestamp)).isoformat()
                elif status_value == "read":
                    message.read_at = datetime.fromtimestamp(int(timestamp)).isoformat()
                elif status_value == "failed":
                    message.failed_at = datetime.fromtimestamp(int(timestamp)).isoformat()
                    if "errors" in status:
                        error = status["errors"][0]
                        message.error_code = str(error.get("code"))
                        message.error_message = error.get("title", "Unknown error")
                
                # Create delivery report
                delivery_report = DeliveryReport(
                    message_id=message.id,
                    status=status_value,
                    timestamp=datetime.fromtimestamp(int(timestamp)).isoformat(),
                    whatsapp_status_id=message_id,
                    webhook_payload=status
                )
                
                self.db.add(delivery_report)
                
                logger.info(f"Message status updated: {message_id} from {old_status} to {message.status}")
        
        self.db.commit()
    
    async def _process_incoming_messages(self, messages: List[Dict[str, Any]], contacts: List[Dict[str, Any]]) -> Optional[WhatsAppMessage]:
        """Process incoming messages from customers."""
        for msg_data in messages:
            try:
                from_number = msg_data.get("from")
                message_id = msg_data.get("id")
                message_type = msg_data.get("type", "text")
                timestamp = msg_data.get("timestamp")
                
                # Find or create customer
                customer = self.db.query(Customer).filter(
                    Customer.phone == format_phone_number(from_number)
                ).first()
                
                if not customer:
                    # Create new customer from contact info
                    contact_info = next((c for c in contacts if c.get("wa_id") == from_number), {})
                    customer = Customer(
                        phone=format_phone_number(from_number),
                        name=contact_info.get("profile", {}).get("name", "Unknown"),
                        whatsapp_name=contact_info.get("profile", {}).get("name")
                    )
                    self.db.add(customer)
                    self.db.commit()
                    self.db.refresh(customer)
                
                # Extract message content
                content = self._extract_message_content(msg_data, message_type)
                
                # Create message record
                message_record = WhatsAppMessage(
                    whatsapp_message_id=message_id,
                    customer_id=customer.id,
                    direction=MessageDirection.INBOUND,
                    message_type=self._map_message_type(message_type),
                    status=MessageStatus.DELIVERED,  # Incoming messages are already delivered
                    content=content.get("text"),
                    media_url=content.get("media_url"),
                    media_type=content.get("media_type"),
                    delivered_at=datetime.fromtimestamp(int(timestamp)).isoformat(),
                    webhook_payload=msg_data
                )
                
                self.db.add(message_record)
                self.db.commit()
                self.db.refresh(message_record)
                
                logger.info(f"Incoming message processed: {message_id} from {from_number}")
                return message_record
                
            except Exception as e:
                logger.error(f"Error processing incoming message: {str(e)}")
                continue
        
        return None
    
    def _map_webhook_status(self, status: str) -> MessageStatus:
        """Map webhook status to internal status enum."""
        status_mapping = {
            "sent": MessageStatus.SENT,
            "delivered": MessageStatus.DELIVERED,
            "read": MessageStatus.READ,
            "failed": MessageStatus.FAILED
        }
        return status_mapping.get(status, MessageStatus.PENDING)
    
    def _map_message_type(self, whatsapp_type: str) -> MessageType:
        """Map WhatsApp message type to internal type enum."""
        type_mapping = {
            "text": MessageType.TEXT,
            "image": MessageType.IMAGE,
            "document": MessageType.DOCUMENT,
            "audio": MessageType.AUDIO,
            "video": MessageType.VIDEO,
            "interactive": MessageType.INTERACTIVE,
            "location": MessageType.LOCATION
        }
        return type_mapping.get(whatsapp_type, MessageType.TEXT)
    
    def _extract_message_content(self, message_data: Dict[str, Any], message_type: str) -> Dict[str, Any]:
        """Extract content from incoming message data."""
        content = {"text": None, "media_url": None, "media_type": None}
        
        if message_type == "text":
            content["text"] = message_data.get("text", {}).get("body")
        elif message_type in ["image", "document", "audio", "video"]:
            media_data = message_data.get(message_type, {})
            content["media_url"] = media_data.get("id")  # Media ID for download
            content["media_type"] = media_data.get("mime_type")
            if message_type in ["image", "document", "video"]:
                content["text"] = media_data.get("caption")
        elif message_type == "interactive":
            interactive_data = message_data.get("interactive", {})
            if interactive_data.get("type") == "button_reply":
                content["text"] = interactive_data.get("button_reply", {}).get("title")
            elif interactive_data.get("type") == "list_reply":
                content["text"] = interactive_data.get("list_reply", {}).get("title")
        elif message_type == "location":
            location_data = message_data.get("location", {})
            content["text"] = f"Location: {location_data.get('latitude')}, {location_data.get('longitude')}"
        
        return content
    
    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()
    
    def __del__(self):
        """Ensure HTTP client is closed on destruction."""
        try:
            if hasattr(self, 'client'):
                asyncio.create_task(self.client.aclose())
        except Exception:
            pass