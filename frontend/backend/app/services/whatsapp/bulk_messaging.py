"""
Bulk messaging service for WhatsApp campaigns and mass communication.

This module provides sophisticated bulk messaging capabilities for marketing
campaigns, customer notifications, and mass communications with proper
rate limiting, segmentation, and delivery tracking.
"""

import asyncio
import csv
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import uuid
from io import StringIO

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.core.config import settings
from app.models.whatsapp import (
    WhatsAppMessage, MessageTemplate, MessageStatus, MessageType, Priority
)
from app.models.customer import Customer
from .async_messaging import AsyncMessagingService, MessageTask
from .exceptions import BulkMessagingError, TemplateNotFoundError
from .rate_limiter import RateLimiter, RateLimitType
from .formatter import MessageFormatter


class CampaignStatus(str, Enum):
    """Campaign execution status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class CampaignType(str, Enum):
    """Campaign types."""
    PROMOTIONAL = "promotional"
    TRANSACTIONAL = "transactional"
    NOTIFICATION = "notification"
    SURVEY = "survey"
    REMINDER = "reminder"


class SegmentCriteria(str, Enum):
    """Customer segmentation criteria."""
    ALL = "all"
    LANGUAGE = "language"
    LOCATION = "location"
    ACTIVITY = "activity"
    CUSTOM = "custom"


@dataclass
class CampaignTarget:
    """Campaign targeting configuration."""
    segment_criteria: SegmentCriteria
    include_filters: Dict[str, Any] = field(default_factory=dict)
    exclude_filters: Dict[str, Any] = field(default_factory=dict)
    max_recipients: Optional[int] = None
    test_recipients: List[str] = field(default_factory=list)


@dataclass
class CampaignMessage:
    """Campaign message configuration."""
    message_type: MessageType
    template_name: Optional[str] = None
    template_language: Optional[str] = None
    template_parameters: Optional[Dict[str, Any]] = None
    
    # For non-template messages
    content: Optional[str] = None
    media_url: Optional[str] = None
    interactive_data: Optional[Dict[str, Any]] = None
    
    # Message customization per recipient
    personalization_enabled: bool = True
    fallback_language: str = "en"


@dataclass
class CampaignConfig:
    """Campaign configuration."""
    id: str
    name: str
    description: str
    campaign_type: CampaignType
    
    # Targeting
    target: CampaignTarget
    
    # Message configuration
    message: CampaignMessage
    
    # Scheduling
    scheduled_at: Optional[datetime] = None
    timezone: str = "UTC"
    
    # Rate limiting
    messages_per_minute: int = 60
    messages_per_hour: int = 1000
    messages_per_day: int = 10000
    
    # Delivery settings
    priority: Priority = Priority.NORMAL
    retry_failed: bool = True
    max_retries: int = 3
    
    # Tracking and analytics
    track_opens: bool = True
    track_clicks: bool = True
    track_replies: bool = True
    
    # Status
    status: CampaignStatus = CampaignStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Progress tracking
    total_recipients: int = 0
    messages_sent: int = 0
    messages_delivered: int = 0
    messages_failed: int = 0
    messages_read: int = 0
    
    # Error tracking
    error_message: Optional[str] = None
    failed_recipients: List[Dict[str, Any]] = field(default_factory=list)


class CustomerSegmenter:
    """Customer segmentation for bulk messaging."""
    
    def __init__(self, db: Session):
        """Initialize customer segmenter."""
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def segment_customers(
        self,
        target: CampaignTarget
    ) -> List[Customer]:
        """
        Segment customers based on targeting criteria.
        
        Args:
            target: Campaign targeting configuration
            
        Returns:
            List of targeted customers
        """
        try:
            # Start with base query
            query = self.db.query(Customer).filter(
                Customer.is_active == True,
                Customer.phone.isnot(None)
            )
            
            # Apply segment criteria
            if target.segment_criteria == SegmentCriteria.ALL:
                # No additional filtering needed
                pass
            
            elif target.segment_criteria == SegmentCriteria.LANGUAGE:
                if 'languages' in target.include_filters:
                    languages = target.include_filters['languages']
                    query = query.filter(Customer.language.in_(languages))
            
            elif target.segment_criteria == SegmentCriteria.LOCATION:
                if 'countries' in target.include_filters:
                    countries = target.include_filters['countries']
                    # Assume we have location data in customer model
                    # query = query.filter(Customer.country.in_(countries))
                    pass
            
            elif target.segment_criteria == SegmentCriteria.ACTIVITY:
                # Filter by activity level
                if 'min_orders' in target.include_filters:
                    min_orders = target.include_filters['min_orders']
                    # This would require a relationship to orders
                    # query = query.filter(Customer.order_count >= min_orders)
                    pass
                
                if 'last_active_days' in target.include_filters:
                    days_ago = datetime.utcnow() - timedelta(
                        days=target.include_filters['last_active_days']
                    )
                    query = query.filter(Customer.updated_at >= days_ago)
            
            elif target.segment_criteria == SegmentCriteria.CUSTOM:
                # Apply custom filters
                query = self._apply_custom_filters(query, target.include_filters)
            
            # Apply exclude filters
            if target.exclude_filters:
                query = self._apply_exclude_filters(query, target.exclude_filters)
            
            # Apply limit if specified
            if target.max_recipients:
                query = query.limit(target.max_recipients)
            
            customers = query.all()
            
            self.logger.info(f"Segmented {len(customers)} customers")
            return customers
            
        except Exception as e:
            self.logger.error(f"Customer segmentation failed: {str(e)}")
            raise BulkMessagingError(f"Segmentation failed: {str(e)}")
    
    def _apply_custom_filters(self, query, filters: Dict[str, Any]):
        """Apply custom filtering logic."""
        # Implement custom filter logic based on your customer model
        # This is a placeholder for extensible filtering
        
        for filter_key, filter_value in filters.items():
            if filter_key == 'customer_ids':
                query = query.filter(Customer.id.in_(filter_value))
            elif filter_key == 'phone_patterns':
                # Filter by phone number patterns
                for pattern in filter_value:
                    query = query.filter(Customer.phone.like(f"%{pattern}%"))
            # Add more custom filters as needed
        
        return query
    
    def _apply_exclude_filters(self, query, exclude_filters: Dict[str, Any]):
        """Apply exclusion filters."""
        if 'customer_ids' in exclude_filters:
            query = query.filter(~Customer.id.in_(exclude_filters['customer_ids']))
        
        if 'phone_patterns' in exclude_filters:
            for pattern in exclude_filters['phone_patterns']:
                query = query.filter(~Customer.phone.like(f"%{pattern}%"))
        
        return query
    
    async def get_test_recipients(
        self,
        phone_numbers: List[str]
    ) -> List[Customer]:
        """Get test recipients by phone numbers."""
        customers = self.db.query(Customer).filter(
            Customer.phone.in_(phone_numbers)
        ).all()
        
        return customers


class CampaignExecutor:
    """Executes bulk messaging campaigns."""
    
    def __init__(
        self,
        db: Session,
        async_messaging: AsyncMessagingService,
        rate_limiter: Optional[RateLimiter] = None
    ):
        """Initialize campaign executor."""
        self.db = db
        self.async_messaging = async_messaging
        self.rate_limiter = rate_limiter or RateLimiter()
        self.logger = logging.getLogger(__name__)
        self.formatter = MessageFormatter()
        
        # Active campaigns tracking
        self.active_campaigns: Dict[str, CampaignConfig] = {}
        self.campaign_tasks: Dict[str, asyncio.Task] = {}
    
    async def execute_campaign(
        self,
        campaign: CampaignConfig,
        test_mode: bool = False
    ) -> CampaignConfig:
        """
        Execute a bulk messaging campaign.
        
        Args:
            campaign: Campaign configuration
            test_mode: Whether to run in test mode
            
        Returns:
            Updated campaign configuration
        """
        try:
            self.logger.info(f"Starting campaign '{campaign.name}' (ID: {campaign.id})")
            
            # Validate campaign
            await self._validate_campaign(campaign)
            
            # Update campaign status
            campaign.status = CampaignStatus.RUNNING
            campaign.started_at = datetime.utcnow()
            self.active_campaigns[campaign.id] = campaign
            
            # Start campaign execution task
            task = asyncio.create_task(
                self._execute_campaign_async(campaign, test_mode),
                name=f"campaign_{campaign.id}"
            )
            self.campaign_tasks[campaign.id] = task
            
            return campaign
            
        except Exception as e:
            campaign.status = CampaignStatus.FAILED
            campaign.error_message = str(e)
            self.logger.error(f"Campaign '{campaign.name}' failed to start: {str(e)}")
            raise BulkMessagingError(f"Campaign execution failed: {str(e)}")
    
    async def pause_campaign(self, campaign_id: str) -> bool:
        """Pause a running campaign."""
        if campaign_id in self.active_campaigns:
            campaign = self.active_campaigns[campaign_id]
            campaign.status = CampaignStatus.PAUSED
            
            self.logger.info(f"Campaign '{campaign.name}' paused")
            return True
        
        return False
    
    async def resume_campaign(self, campaign_id: str) -> bool:
        """Resume a paused campaign."""
        if campaign_id in self.active_campaigns:
            campaign = self.active_campaigns[campaign_id]
            if campaign.status == CampaignStatus.PAUSED:
                campaign.status = CampaignStatus.RUNNING
                
                self.logger.info(f"Campaign '{campaign.name}' resumed")
                return True
        
        return False
    
    async def cancel_campaign(self, campaign_id: str) -> bool:
        """Cancel a running or paused campaign."""
        if campaign_id in self.active_campaigns:
            campaign = self.active_campaigns[campaign_id]
            campaign.status = CampaignStatus.CANCELLED
            
            # Cancel the execution task
            if campaign_id in self.campaign_tasks:
                task = self.campaign_tasks[campaign_id]
                task.cancel()
                
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
                del self.campaign_tasks[campaign_id]
            
            del self.active_campaigns[campaign_id]
            
            self.logger.info(f"Campaign '{campaign.name}' cancelled")
            return True
        
        return False
    
    async def get_campaign_status(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get campaign status and progress."""
        if campaign_id in self.active_campaigns:
            campaign = self.active_campaigns[campaign_id]
            
            progress_percentage = 0
            if campaign.total_recipients > 0:
                progress_percentage = (
                    (campaign.messages_sent + campaign.messages_failed) / 
                    campaign.total_recipients
                ) * 100
            
            return {
                'id': campaign.id,
                'name': campaign.name,
                'status': campaign.status,
                'progress_percentage': progress_percentage,
                'total_recipients': campaign.total_recipients,
                'messages_sent': campaign.messages_sent,
                'messages_delivered': campaign.messages_delivered,
                'messages_failed': campaign.messages_failed,
                'messages_read': campaign.messages_read,
                'started_at': campaign.started_at,
                'estimated_completion': self._estimate_completion_time(campaign)
            }
        
        return None
    
    async def _execute_campaign_async(
        self,
        campaign: CampaignConfig,
        test_mode: bool = False
    ):
        """Asynchronous campaign execution."""
        try:
            # Get target customers
            segmenter = CustomerSegmenter(self.db)
            
            if test_mode and campaign.target.test_recipients:
                customers = await segmenter.get_test_recipients(
                    campaign.target.test_recipients
                )
            else:
                customers = await segmenter.segment_customers(campaign.target)
            
            campaign.total_recipients = len(customers)
            
            if campaign.total_recipients == 0:
                campaign.status = CampaignStatus.COMPLETED
                campaign.completed_at = datetime.utcnow()
                self.logger.warning(f"Campaign '{campaign.name}' has no recipients")
                return
            
            self.logger.info(
                f"Campaign '{campaign.name}' targeting {campaign.total_recipients} customers"
            )
            
            # Create rate limiter for campaign
            campaign_rate_limiter = RateLimiter(
                max_requests=campaign.messages_per_minute,
                time_window=60,
                burst_limit=campaign.messages_per_hour
            )
            
            # Process customers in batches
            batch_size = min(100, campaign.messages_per_minute)
            
            for i in range(0, len(customers), batch_size):
                # Check if campaign is still running
                if campaign.status != CampaignStatus.RUNNING:
                    break
                
                batch = customers[i:i + batch_size]
                await self._process_customer_batch(
                    campaign,
                    batch,
                    campaign_rate_limiter
                )
                
                # Small delay between batches
                await asyncio.sleep(1)
            
            # Mark campaign as completed
            campaign.status = CampaignStatus.COMPLETED
            campaign.completed_at = datetime.utcnow()
            
            self.logger.info(
                f"Campaign '{campaign.name}' completed. "
                f"Sent: {campaign.messages_sent}, Failed: {campaign.messages_failed}"
            )
            
        except asyncio.CancelledError:
            campaign.status = CampaignStatus.CANCELLED
            self.logger.info(f"Campaign '{campaign.name}' was cancelled")
            
        except Exception as e:
            campaign.status = CampaignStatus.FAILED
            campaign.error_message = str(e)
            self.logger.error(f"Campaign '{campaign.name}' failed: {str(e)}")
            
        finally:
            # Clean up
            if campaign.id in self.active_campaigns:
                del self.active_campaigns[campaign.id]
            if campaign.id in self.campaign_tasks:
                del self.campaign_tasks[campaign.id]
    
    async def _process_customer_batch(
        self,
        campaign: CampaignConfig,
        customers: List[Customer],
        rate_limiter: RateLimiter
    ):
        """Process a batch of customers."""
        tasks = []
        
        for customer in customers:
            if campaign.status != CampaignStatus.RUNNING:
                break
            
            task = asyncio.create_task(
                self._send_message_to_customer(campaign, customer, rate_limiter)
            )
            tasks.append(task)
        
        # Wait for all messages in batch to be queued
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update campaign statistics
        for result in results:
            if isinstance(result, Exception):
                campaign.messages_failed += 1
                campaign.failed_recipients.append({
                    'error': str(result),
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                campaign.messages_sent += 1
    
    async def _send_message_to_customer(
        self,
        campaign: CampaignConfig,
        customer: Customer,
        rate_limiter: RateLimiter
    ):
        """Send message to individual customer."""
        try:
            # Acquire rate limit permission
            await rate_limiter.acquire(RateLimitType.MESSAGING)
            
            # Prepare message based on type
            message_data = await self._prepare_customer_message(campaign, customer)
            
            # Queue message for async sending
            if campaign.message.message_type == MessageType.TEXT:
                await self.async_messaging.send_text_message_async(
                    customer_id=customer.id,
                    phone_number=customer.phone,
                    message=message_data['content'],
                    priority=campaign.priority,
                    metadata={
                        'campaign_id': campaign.id,
                        'campaign_name': campaign.name,
                        'campaign_type': campaign.campaign_type
                    }
                )
            
            elif campaign.message.message_type == MessageType.TEMPLATE:
                await self.async_messaging.send_template_message_async(
                    customer_id=customer.id,
                    phone_number=customer.phone,
                    template_name=message_data['template_name'],
                    template_language=message_data['template_language'],
                    template_parameters=message_data.get('template_parameters'),
                    priority=campaign.priority
                )
            
            elif campaign.message.message_type in [
                MessageType.IMAGE, MessageType.DOCUMENT,
                MessageType.AUDIO, MessageType.VIDEO
            ]:
                await self.async_messaging.send_media_message_async(
                    customer_id=customer.id,
                    phone_number=customer.phone,
                    media_url=message_data['media_url'],
                    media_type=campaign.message.message_type,
                    caption=message_data.get('content'),
                    priority=campaign.priority
                )
            
        except Exception as e:
            self.logger.error(f"Failed to send message to customer {customer.id}: {str(e)}")
            raise
    
    async def _prepare_customer_message(
        self,
        campaign: CampaignConfig,
        customer: Customer
    ) -> Dict[str, Any]:
        """Prepare personalized message for customer."""
        message_data = {}
        
        # Determine customer's preferred language
        customer_language = customer.language or campaign.message.fallback_language
        
        if campaign.message.message_type == MessageType.TEMPLATE:
            message_data['template_name'] = campaign.message.template_name
            message_data['template_language'] = customer_language
            
            # Personalize template parameters
            if (campaign.message.template_parameters and 
                campaign.message.personalization_enabled):
                
                parameters = campaign.message.template_parameters.copy()
                
                # Replace customer placeholders
                for key, value in parameters.items():
                    if isinstance(value, str):
                        parameters[key] = value.format(
                            customer_name=customer.name or "Valued Customer",
                            customer_phone=customer.phone,
                            customer_language=customer_language
                        )
                
                message_data['template_parameters'] = parameters
        
        elif campaign.message.message_type == MessageType.TEXT:
            content = campaign.message.content
            
            if campaign.message.personalization_enabled and content:
                # Personalize text content
                content = content.format(
                    customer_name=customer.name or "Valued Customer",
                    customer_phone=customer.phone
                )
            
            message_data['content'] = content
        
        elif campaign.message.message_type in [
            MessageType.IMAGE, MessageType.DOCUMENT,
            MessageType.AUDIO, MessageType.VIDEO
        ]:
            message_data['media_url'] = campaign.message.media_url
            
            if campaign.message.content:
                content = campaign.message.content
                if campaign.message.personalization_enabled:
                    content = content.format(
                        customer_name=customer.name or "Valued Customer"
                    )
                message_data['content'] = content
        
        return message_data
    
    async def _validate_campaign(self, campaign: CampaignConfig):
        """Validate campaign configuration."""
        errors = []
        
        # Validate message template if using template type
        if campaign.message.message_type == MessageType.TEMPLATE:
            if not campaign.message.template_name:
                errors.append("Template name is required for template messages")
            else:
                # Check if template exists
                template = self.db.query(MessageTemplate).filter(
                    and_(
                        MessageTemplate.name == campaign.message.template_name,
                        MessageTemplate.language == campaign.message.template_language,
                        MessageTemplate.is_active == True
                    )
                ).first()
                
                if not template:
                    errors.append(
                        f"Template '{campaign.message.template_name}' not found"
                    )
                elif not template.can_be_used():
                    errors.append(
                        f"Template '{campaign.message.template_name}' is not approved"
                    )
        
        # Validate content for text messages
        elif campaign.message.message_type == MessageType.TEXT:
            if not campaign.message.content:
                errors.append("Content is required for text messages")
        
        # Validate media URL for media messages
        elif campaign.message.message_type in [
            MessageType.IMAGE, MessageType.DOCUMENT,
            MessageType.AUDIO, MessageType.VIDEO
        ]:
            if not campaign.message.media_url:
                errors.append("Media URL is required for media messages")
        
        # Validate rate limits
        if campaign.messages_per_minute > 80:  # WhatsApp API limit
            errors.append("Messages per minute cannot exceed 80")
        
        if errors:
            raise BulkMessagingError(f"Campaign validation failed: {'; '.join(errors)}")
    
    def _estimate_completion_time(self, campaign: CampaignConfig) -> Optional[str]:
        """Estimate campaign completion time."""
        if campaign.status != CampaignStatus.RUNNING:
            return None
        
        remaining_messages = campaign.total_recipients - campaign.messages_sent
        if remaining_messages <= 0:
            return None
        
        # Calculate based on rate limits
        minutes_remaining = remaining_messages / campaign.messages_per_minute
        completion_time = datetime.utcnow() + timedelta(minutes=minutes_remaining)
        
        return completion_time.isoformat()


class BulkMessagingService:
    """
    Comprehensive bulk messaging service for WhatsApp campaigns.
    
    Features:
    - Customer segmentation and targeting
    - Template-based and custom messaging
    - Rate limiting and delivery optimization
    - Campaign scheduling and management
    - Real-time progress tracking
    - Analytics and reporting
    - Test mode for campaign validation
    """
    
    def __init__(
        self,
        db: Session,
        async_messaging: AsyncMessagingService,
        rate_limiter: Optional[RateLimiter] = None
    ):
        """Initialize bulk messaging service."""
        self.db = db
        self.async_messaging = async_messaging
        self.rate_limiter = rate_limiter or RateLimiter()
        self.logger = logging.getLogger(__name__)
        
        # Campaign management
        self.campaign_executor = CampaignExecutor(db, async_messaging, rate_limiter)
        self.segmenter = CustomerSegmenter(db)
        
        # Campaign storage (in production, use proper database)
        self.campaigns: Dict[str, CampaignConfig] = {}
    
    async def create_campaign(
        self,
        name: str,
        description: str,
        campaign_type: CampaignType,
        target: CampaignTarget,
        message: CampaignMessage,
        **kwargs
    ) -> str:
        """
        Create a new bulk messaging campaign.
        
        Args:
            name: Campaign name
            description: Campaign description
            campaign_type: Type of campaign
            target: Targeting configuration
            message: Message configuration
            **kwargs: Additional campaign options
            
        Returns:
            Campaign ID
        """
        campaign_id = str(uuid.uuid4())
        
        campaign = CampaignConfig(
            id=campaign_id,
            name=name,
            description=description,
            campaign_type=campaign_type,
            target=target,
            message=message,
            **kwargs
        )
        
        self.campaigns[campaign_id] = campaign
        
        self.logger.info(f"Created campaign '{name}' with ID {campaign_id}")
        return campaign_id
    
    async def launch_campaign(
        self,
        campaign_id: str,
        test_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Launch a campaign for execution.
        
        Args:
            campaign_id: Campaign ID
            test_mode: Whether to run in test mode
            
        Returns:
            Campaign launch result
        """
        if campaign_id not in self.campaigns:
            raise BulkMessagingError(f"Campaign {campaign_id} not found")
        
        campaign = self.campaigns[campaign_id]
        
        # Check if campaign is scheduled
        if campaign.scheduled_at and campaign.scheduled_at > datetime.utcnow():
            raise BulkMessagingError("Campaign is scheduled for future execution")
        
        # Execute campaign
        updated_campaign = await self.campaign_executor.execute_campaign(
            campaign, test_mode
        )
        
        return {
            'campaign_id': campaign_id,
            'status': updated_campaign.status,
            'message': f"Campaign '{campaign.name}' launched successfully"
        }
    
    async def pause_campaign(self, campaign_id: str) -> bool:
        """Pause a running campaign."""
        return await self.campaign_executor.pause_campaign(campaign_id)
    
    async def resume_campaign(self, campaign_id: str) -> bool:
        """Resume a paused campaign."""
        return await self.campaign_executor.resume_campaign(campaign_id)
    
    async def cancel_campaign(self, campaign_id: str) -> bool:
        """Cancel a campaign."""
        success = await self.campaign_executor.cancel_campaign(campaign_id)
        
        if success and campaign_id in self.campaigns:
            del self.campaigns[campaign_id]
        
        return success
    
    async def get_campaign_details(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed campaign information."""
        if campaign_id not in self.campaigns:
            return None
        
        campaign = self.campaigns[campaign_id]
        status = await self.campaign_executor.get_campaign_status(campaign_id)
        
        return {
            'id': campaign.id,
            'name': campaign.name,
            'description': campaign.description,
            'type': campaign.campaign_type,
            'created_at': campaign.created_at.isoformat(),
            'scheduled_at': campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
            'status': status or {
                'status': campaign.status,
                'total_recipients': campaign.total_recipients,
                'messages_sent': campaign.messages_sent,
                'messages_failed': campaign.messages_failed
            }
        }
    
    async def list_campaigns(
        self,
        status_filter: Optional[CampaignStatus] = None,
        type_filter: Optional[CampaignType] = None
    ) -> List[Dict[str, Any]]:
        """List campaigns with optional filtering."""
        campaigns = []
        
        for campaign in self.campaigns.values():
            if status_filter and campaign.status != status_filter:
                continue
            
            if type_filter and campaign.campaign_type != type_filter:
                continue
            
            campaigns.append({
                'id': campaign.id,
                'name': campaign.name,
                'type': campaign.campaign_type,
                'status': campaign.status,
                'created_at': campaign.created_at.isoformat(),
                'total_recipients': campaign.total_recipients,
                'messages_sent': campaign.messages_sent
            })
        
        return sorted(campaigns, key=lambda x: x['created_at'], reverse=True)
    
    async def preview_campaign_recipients(
        self,
        target: CampaignTarget,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Preview campaign recipients for validation."""
        # Temporarily set max recipients for preview
        original_max = target.max_recipients
        target.max_recipients = limit
        
        try:
            customers = await self.segmenter.segment_customers(target)
            
            return [
                {
                    'id': customer.id,
                    'name': customer.name,
                    'phone': customer.phone,
                    'language': customer.language
                }
                for customer in customers
            ]
        
        finally:
            target.max_recipients = original_max
    
    async def export_campaign_results(
        self,
        campaign_id: str,
        format_type: str = "csv"
    ) -> str:
        """
        Export campaign results to specified format.
        
        Args:
            campaign_id: Campaign ID
            format_type: Export format (csv, json)
            
        Returns:
            Exported data as string
        """
        if campaign_id not in self.campaigns:
            raise BulkMessagingError(f"Campaign {campaign_id} not found")
        
        campaign = self.campaigns[campaign_id]
        
        # Get campaign messages from database
        messages = self.db.query(WhatsAppMessage).filter(
            WhatsAppMessage.campaign_id == campaign_id
        ).all()
        
        if format_type.lower() == "csv":
            return self._export_as_csv(campaign, messages)
        elif format_type.lower() == "json":
            return self._export_as_json(campaign, messages)
        else:
            raise BulkMessagingError(f"Unsupported export format: {format_type}")
    
    def _export_as_csv(
        self,
        campaign: CampaignConfig,
        messages: List[WhatsAppMessage]
    ) -> str:
        """Export campaign results as CSV."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Campaign ID', 'Campaign Name', 'Customer ID', 'Customer Name',
            'Phone', 'Message Type', 'Status', 'Sent At', 'Delivered At',
            'Read At', 'Error Message'
        ])
        
        # Write data rows
        for message in messages:
            writer.writerow([
                campaign.id,
                campaign.name,
                message.customer_id,
                message.customer.name if message.customer else '',
                message.customer.phone if message.customer else '',
                message.message_type,
                message.status,
                message.sent_at or '',
                message.delivered_at or '',
                message.read_at or '',
                message.error_message or ''
            ])
        
        return output.getvalue()
    
    def _export_as_json(
        self,
        campaign: CampaignConfig,
        messages: List[WhatsAppMessage]
    ) -> str:
        """Export campaign results as JSON."""
        data = {
            'campaign': {
                'id': campaign.id,
                'name': campaign.name,
                'type': campaign.campaign_type,
                'status': campaign.status,
                'created_at': campaign.created_at.isoformat(),
                'started_at': campaign.started_at.isoformat() if campaign.started_at else None,
                'completed_at': campaign.completed_at.isoformat() if campaign.completed_at else None,
                'total_recipients': campaign.total_recipients,
                'messages_sent': campaign.messages_sent,
                'messages_delivered': campaign.messages_delivered,
                'messages_failed': campaign.messages_failed
            },
            'messages': []
        }
        
        for message in messages:
            data['messages'].append({
                'id': message.id,
                'customer_id': message.customer_id,
                'customer_name': message.customer.name if message.customer else None,
                'phone': message.customer.phone if message.customer else None,
                'message_type': message.message_type,
                'status': message.status,
                'sent_at': message.sent_at,
                'delivered_at': message.delivered_at,
                'read_at': message.read_at,
                'error_message': message.error_message
            })
        
        return json.dumps(data, indent=2, default=str)
    
    async def get_campaign_analytics(
        self,
        campaign_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive campaign analytics."""
        if campaign_id not in self.campaigns:
            raise BulkMessagingError(f"Campaign {campaign_id} not found")
        
        campaign = self.campaigns[campaign_id]
        
        # Query message statistics
        message_stats = self.db.query(
            func.count(WhatsAppMessage.id).label('total'),
            func.sum(
                func.case([(WhatsAppMessage.status == MessageStatus.SENT, 1)], else_=0)
            ).label('sent'),
            func.sum(
                func.case([(WhatsAppMessage.status == MessageStatus.DELIVERED, 1)], else_=0)
            ).label('delivered'),
            func.sum(
                func.case([(WhatsAppMessage.status == MessageStatus.READ, 1)], else_=0)
            ).label('read'),
            func.sum(
                func.case([(WhatsAppMessage.status == MessageStatus.FAILED, 1)], else_=0)
            ).label('failed')
        ).filter(WhatsAppMessage.campaign_id == campaign_id).first()
        
        # Calculate rates
        total = message_stats.total or 0
        sent = message_stats.sent or 0
        delivered = message_stats.delivered or 0
        read = message_stats.read or 0
        failed = message_stats.failed or 0
        
        delivery_rate = (delivered / sent * 100) if sent > 0 else 0
        read_rate = (read / delivered * 100) if delivered > 0 else 0
        failure_rate = (failed / total * 100) if total > 0 else 0
        
        return {
            'campaign_id': campaign_id,
            'campaign_name': campaign.name,
            'statistics': {
                'total_recipients': campaign.total_recipients,
                'messages_sent': sent,
                'messages_delivered': delivered,
                'messages_read': read,
                'messages_failed': failed
            },
            'rates': {
                'delivery_rate': round(delivery_rate, 2),
                'read_rate': round(read_rate, 2),
                'failure_rate': round(failure_rate, 2)
            },
            'timeline': {
                'created_at': campaign.created_at.isoformat(),
                'started_at': campaign.started_at.isoformat() if campaign.started_at else None,
                'completed_at': campaign.completed_at.isoformat() if campaign.completed_at else None,
                'duration_seconds': (
                    (campaign.completed_at - campaign.started_at).total_seconds()
                    if campaign.started_at and campaign.completed_at else None
                )
            }
        }