"""
Main WhatsApp Business integration service.

This module provides the main WhatsApp service that integrates all components
including messaging, templates, media handling, webhooks, and bulk messaging.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.whatsapp import (
    WhatsAppMessage, MessageTemplate, MessageStatus, MessageType, Priority
)
from app.models.customer import Customer

from .client import WhatsAppClient
from .formatter import MessageFormatter
from .media import WhatsAppMediaHandler
from .webhook import WebhookHandler
from .template_manager import TemplateManager
from .async_messaging import AsyncMessagingService
from .bulk_messaging import BulkMessagingService, CampaignConfig
from .rate_limiter import RateLimiter
from .exceptions import WhatsAppError, ConfigurationError


class WhatsAppService:
    """
    Comprehensive WhatsApp Business API integration service.
    
    This is the main service class that provides a unified interface to all
    WhatsApp functionality including:
    
    - Message sending (text, template, media, interactive)
    - Webhook processing
    - Template management
    - Media handling
    - Bulk messaging and campaigns
    - Rate limiting and queue management
    - Delivery tracking and analytics
    """
    
    def __init__(
        self,
        db_session: Session,
        media_storage_path: str = "media",
        webhook_secret: Optional[str] = None,
        rate_limiter_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize WhatsApp service with all components.
        
        Args:
            db_session: Database session
            media_storage_path: Path for media file storage
            webhook_secret: Secret for webhook validation
            rate_limiter_config: Custom rate limiter configuration
        """
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration
        self._validate_config()
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(**(rate_limiter_config or {}))
        
        # Initialize core components
        self.client = WhatsAppClient(db_session)
        self.formatter = MessageFormatter()
        self.media_handler = WhatsAppMediaHandler(media_storage_path)
        self.template_manager = TemplateManager(db_session)
        
        # Initialize advanced services
        self.async_messaging = AsyncMessagingService(
            db_session, self.client, self.rate_limiter
        )
        self.bulk_messaging = BulkMessagingService(
            db_session, self.async_messaging, self.rate_limiter
        )
        
        # Initialize webhook handler
        self.webhook_handler = WebhookHandler(
            db_session, webhook_secret, self.rate_limiter
        )
        
        # Service state
        self._initialized = False
        self._running = False
    
    async def initialize(self):
        """Initialize the service and start background workers."""
        if self._initialized:
            return
        
        try:
            self.logger.info("Initializing WhatsApp service...")
            
            # Start async messaging workers
            await self.async_messaging.start_workers()
            
            # Initialize restaurant templates if they don't exist
            await self._initialize_restaurant_templates()
            
            self._initialized = True
            self._running = True
            
            self.logger.info("WhatsApp service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WhatsApp service: {str(e)}")
            raise ConfigurationError(f"Service initialization failed: {str(e)}")
    
    async def shutdown(self):
        """Shutdown the service and clean up resources."""
        if not self._running:
            return
        
        self.logger.info("Shutting down WhatsApp service...")
        
        try:
            # Stop background workers
            await self.async_messaging.stop_workers()
            
            # Close HTTP clients
            await self.client.close()
            await self.media_handler.close()
            await self.template_manager.close()
            
            self._running = False
            
            self.logger.info("WhatsApp service shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Error during service shutdown: {str(e)}")
    
    # Message Sending Methods
    
    async def send_text_message(
        self,
        phone_number: str,
        message: str,
        customer_id: int,
        priority: Priority = Priority.NORMAL,
        use_async: bool = True,
        **kwargs
    ) -> Union[WhatsAppMessage, str]:
        """
        Send a text message.
        
        Args:
            phone_number: Recipient phone number
            message: Text message content
            customer_id: Customer database ID
            priority: Message priority
            use_async: Whether to use async messaging queue
            **kwargs: Additional parameters
            
        Returns:
            WhatsAppMessage record or task ID if async
        """
        if use_async:
            return await self.async_messaging.send_text_message_async(
                customer_id=customer_id,
                phone_number=phone_number,
                message=message,
                priority=priority,
                **kwargs
            )
        else:
            return await self.client.send_text_message(
                phone_number=phone_number,
                message=message,
                customer_id=customer_id,
                priority=priority,
                **kwargs
            )
    
    async def send_template_message(
        self,
        phone_number: str,
        template_name: str,
        language_code: str,
        parameters: Optional[Dict[str, Any]] = None,
        customer_id: int,
        priority: Priority = Priority.NORMAL,
        use_async: bool = True,
        **kwargs
    ) -> Union[WhatsAppMessage, str]:
        """
        Send a template message.
        
        Args:
            phone_number: Recipient phone number
            template_name: Template name
            language_code: Template language
            parameters: Template parameters
            customer_id: Customer database ID
            priority: Message priority
            use_async: Whether to use async messaging queue
            **kwargs: Additional parameters
            
        Returns:
            WhatsAppMessage record or task ID if async
        """
        if use_async:
            return await self.async_messaging.send_template_message_async(
                customer_id=customer_id,
                phone_number=phone_number,
                template_name=template_name,
                template_language=language_code,
                template_parameters=parameters,
                priority=priority,
                **kwargs
            )
        else:
            return await self.client.send_template_message(
                phone_number=phone_number,
                template_name=template_name,
                language_code=language_code,
                parameters=parameters,
                customer_id=customer_id,
                priority=priority,
                **kwargs
            )
    
    async def send_media_message(
        self,
        phone_number: str,
        media_url: str,
        media_type: MessageType,
        customer_id: int,
        caption: Optional[str] = None,
        priority: Priority = Priority.NORMAL,
        use_async: bool = True,
        **kwargs
    ) -> Union[WhatsAppMessage, str]:
        """
        Send a media message.
        
        Args:
            phone_number: Recipient phone number
            media_url: Media file URL
            media_type: Type of media
            customer_id: Customer database ID
            caption: Optional media caption
            priority: Message priority
            use_async: Whether to use async messaging queue
            **kwargs: Additional parameters
            
        Returns:
            WhatsAppMessage record or task ID if async
        """
        if use_async:
            return await self.async_messaging.send_media_message_async(
                customer_id=customer_id,
                phone_number=phone_number,
                media_url=media_url,
                media_type=media_type,
                caption=caption,
                priority=priority,
                **kwargs
            )
        else:
            return await self.client.send_media_message(
                phone_number=phone_number,
                media_url=media_url,
                media_type=media_type,
                customer_id=customer_id,
                caption=caption,
                priority=priority,
                **kwargs
            )
    
    # Convenience Methods for Restaurant Use Cases
    
    async def send_welcome_message(
        self,
        customer: Customer,
        restaurant_name: str = None,
        language: str = None
    ) -> Union[WhatsAppMessage, str]:
        """Send personalized welcome message to customer."""
        restaurant_name = restaurant_name or settings.RESTAURANT_NAME
        language = language or customer.language or settings.DEFAULT_LANGUAGE
        
        welcome_message = self.formatter.create_welcome_message(
            customer_name=customer.name or "Valued Customer",
            restaurant_name=restaurant_name,
            language=language
        )
        
        return await self.send_text_message(
            phone_number=customer.phone,
            message=welcome_message,
            customer_id=customer.id,
            priority=Priority.HIGH
        )
    
    async def send_order_confirmation(
        self,
        customer: Customer,
        order_number: str,
        items: List[Dict[str, Any]],
        total_amount: float,
        currency: str = "SAR",
        language: str = None
    ) -> Union[WhatsAppMessage, str]:
        """Send order confirmation message."""
        language = language or customer.language or settings.DEFAULT_LANGUAGE
        
        confirmation_message = self.formatter.create_order_confirmation(
            customer_name=customer.name or "Valued Customer",
            order_number=order_number,
            items=items,
            total_amount=total_amount,
            currency=currency,
            language=language
        )
        
        return await self.send_text_message(
            phone_number=customer.phone,
            message=confirmation_message,
            customer_id=customer.id,
            priority=Priority.HIGH
        )
    
    async def send_delivery_update(
        self,
        customer: Customer,
        order_number: str,
        status: str,
        estimated_time: Optional[str] = None,
        language: str = None
    ) -> Union[WhatsAppMessage, str]:
        """Send delivery status update."""
        language = language or customer.language or settings.DEFAULT_LANGUAGE
        
        update_message = self.formatter.create_delivery_update(
            customer_name=customer.name or "Valued Customer",
            order_number=order_number,
            status=status,
            estimated_time=estimated_time,
            language=language
        )
        
        return await self.send_text_message(
            phone_number=customer.phone,
            message=update_message,
            customer_id=customer.id,
            priority=Priority.HIGH
        )
    
    async def send_feedback_request(
        self,
        customer: Customer,
        order_number: str,
        language: str = None
    ) -> Union[WhatsAppMessage, str]:
        """Send feedback request message."""
        language = language or customer.language or settings.DEFAULT_LANGUAGE
        
        feedback_message = self.formatter.create_feedback_request(
            customer_name=customer.name or "Valued Customer",
            order_number=order_number,
            language=language
        )
        
        return await self.send_text_message(
            phone_number=customer.phone,
            message=feedback_message,
            customer_id=customer.id,
            priority=Priority.NORMAL
        )
    
    # Template Management
    
    async def create_template(
        self,
        template_data: Dict[str, Any],
        submit_to_whatsapp: bool = True
    ) -> MessageTemplate:
        """Create a new message template."""
        return await self.template_manager.create_template(
            template_data, submit_to_whatsapp
        )
    
    async def get_template(
        self,
        name: str,
        language: str = None
    ) -> Optional[MessageTemplate]:
        """Get template by name and language."""
        return self.template_manager.get_template(name, language)
    
    async def list_templates(
        self,
        language: Optional[str] = None,
        **filters
    ) -> List[MessageTemplate]:
        """List available templates."""
        return self.template_manager.list_templates(language=language, **filters)
    
    async def sync_templates_from_whatsapp(self) -> Dict[str, int]:
        """Sync templates from WhatsApp servers."""
        return await self.template_manager.sync_templates_from_whatsapp()
    
    # Media Handling
    
    async def upload_media(
        self,
        file_path: str,
        media_type: str = None,
        optimize: bool = True
    ) -> Dict[str, Any]:
        """Upload media file to WhatsApp."""
        return await self.media_handler.upload_media(
            file_path, media_type, optimize
        )
    
    async def download_media(
        self,
        media_id: str,
        download_path: str = None
    ) -> Dict[str, Any]:
        """Download media file from WhatsApp."""
        return await self.media_handler.download_media(media_id, download_path)
    
    # Bulk Messaging and Campaigns
    
    async def create_campaign(
        self,
        name: str,
        description: str,
        campaign_type,
        target,
        message,
        **kwargs
    ) -> str:
        """Create a bulk messaging campaign."""
        return await self.bulk_messaging.create_campaign(
            name, description, campaign_type, target, message, **kwargs
        )
    
    async def launch_campaign(
        self,
        campaign_id: str,
        test_mode: bool = False
    ) -> Dict[str, Any]:
        """Launch a campaign."""
        return await self.bulk_messaging.launch_campaign(campaign_id, test_mode)
    
    async def get_campaign_status(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get campaign status and progress."""
        return await self.bulk_messaging.get_campaign_details(campaign_id)
    
    # Webhook Processing
    
    async def process_webhook(
        self,
        request,
        validate_signature: bool = True
    ) -> Dict[str, Any]:
        """Process incoming webhook."""
        return await self.webhook_handler.handle_webhook(request, validate_signature)
    
    async def verify_webhook(
        self,
        mode: str,
        token: str,
        challenge: str,
        verify_token: str
    ) -> str:
        """Verify webhook during setup."""
        return await self.webhook_handler.verify_webhook(
            mode, token, challenge, verify_token
        )
    
    def register_webhook_handler(self, event_type, handler):
        """Register custom webhook event handler."""
        self.webhook_handler.register_event_handler(event_type, handler)
    
    # Analytics and Reporting
    
    def get_message_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get message statistics for specified period."""
        query = self.db.query(WhatsAppMessage).filter(
            WhatsAppMessage.created_at.between(
                start_date.isoformat(),
                end_date.isoformat()
            )
        )
        
        # Apply filters
        if filters:
            if 'customer_id' in filters:
                query = query.filter(WhatsAppMessage.customer_id == filters['customer_id'])
            
            if 'message_type' in filters:
                query = query.filter(WhatsAppMessage.message_type == filters['message_type'])
            
            if 'status' in filters:
                query = query.filter(WhatsAppMessage.status == filters['status'])
        
        messages = query.all()
        
        # Calculate statistics
        total = len(messages)
        sent = len([m for m in messages if m.status == MessageStatus.SENT])
        delivered = len([m for m in messages if m.status == MessageStatus.DELIVERED])
        read = len([m for m in messages if m.status == MessageStatus.READ])
        failed = len([m for m in messages if m.status == MessageStatus.FAILED])
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'totals': {
                'total_messages': total,
                'sent': sent,
                'delivered': delivered,
                'read': read,
                'failed': failed
            },
            'rates': {
                'delivery_rate': (delivered / sent * 100) if sent > 0 else 0,
                'read_rate': (read / delivered * 100) if delivered > 0 else 0,
                'failure_rate': (failed / total * 100) if total > 0 else 0
            }
        }
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get service health status."""
        return {
            'service_status': 'healthy' if self._running else 'stopped',
            'initialized': self._initialized,
            'components': {
                'async_messaging': self.async_messaging.get_service_stats(),
                'rate_limiter': self.rate_limiter.get_current_status(),
                'database': 'connected' if self.db else 'disconnected'
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # Private Methods
    
    def _validate_config(self):
        """Validate service configuration."""
        required_settings = [
            'WHATSAPP_ACCESS_TOKEN',
            'WHATSAPP_PHONE_NUMBER_ID',
            'WHATSAPP_BUSINESS_ACCOUNT_ID'
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not getattr(settings, setting, None):
                missing_settings.append(setting)
        
        if missing_settings:
            raise ConfigurationError(
                f"Missing required WhatsApp configuration: {', '.join(missing_settings)}"
            )
    
    async def _initialize_restaurant_templates(self):
        """Initialize default restaurant templates."""
        try:
            # Check if templates already exist
            existing_templates = self.template_manager.list_templates()
            
            if len(existing_templates) == 0:
                self.logger.info("Creating default restaurant templates...")
                
                # Create restaurant-specific templates
                created_templates = await self.template_manager.create_restaurant_templates()
                
                total_created = sum(len(templates) for templates in created_templates.values())
                self.logger.info(f"Created {total_created} restaurant templates")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize restaurant templates: {str(e)}")
            # Don't fail initialization if template creation fails
    
    # Context Manager Support
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()


# Convenience function for creating service instance
def create_whatsapp_service(
    db_session: Session,
    **kwargs
) -> WhatsAppService:
    """
    Create and configure a WhatsApp service instance.
    
    Args:
        db_session: Database session
        **kwargs: Additional configuration options
        
    Returns:
        Configured WhatsApp service instance
    """
    return WhatsAppService(db_session, **kwargs)