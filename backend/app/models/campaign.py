"""
Campaign models for managing bulk messaging and targeted customer outreach.
Handles campaign creation, targeting, scheduling, and performance tracking.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, LanguageChoice
from ..core.logging import get_logger

logger = get_logger(__name__)


class Campaign(Base):
    """
    Campaign model for managing bulk messaging campaigns.
    Supports advanced targeting, A/B testing, and performance analytics.
    """
    
    __tablename__ = "campaigns"
    
    # Basic campaign information
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    campaign_type = Column(String(50), nullable=False)  # bulk_feedback, promotion, satisfaction_survey, etc.
    
    # Campaign status
    status = Column(String(20), default="draft", nullable=False, index=True)  # draft, scheduled, running, paused, completed, cancelled
    
    # Scheduling
    scheduled_start_at = Column(DateTime, nullable=True)
    scheduled_end_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Targeting configuration
    targeting_config = Column(JSON, nullable=False)  # Demographics, behavioral, geographic targeting
    
    # Message configuration
    message_variants = Column(JSON, nullable=False)  # Array of message variants for A/B testing
    default_language = Column(String(5), default=LanguageChoice.ARABIC, nullable=False)
    
    # Scheduling rules
    scheduling_config = Column(JSON, nullable=True)  # Timing rules, cultural considerations, optimal timing
    
    # Performance settings
    max_recipients = Column(Integer, nullable=True)  # Maximum number of recipients
    send_rate_per_hour = Column(Integer, default=100, nullable=False)  # Rate limiting
    
    # Budget and limits
    budget_limit_usd = Column(Float, nullable=True)
    estimated_cost_usd = Column(Float, nullable=True)
    actual_cost_usd = Column(Float, default=0.0, nullable=False)
    
    # Performance metrics (updated as campaign runs)
    recipients_count = Column(Integer, default=0, nullable=False)
    messages_sent = Column(Integer, default=0, nullable=False)
    messages_delivered = Column(Integer, default=0, nullable=False)
    messages_read = Column(Integer, default=0, nullable=False)
    messages_failed = Column(Integer, default=0, nullable=False)
    responses_received = Column(Integer, default=0, nullable=False)
    
    # A/B testing
    is_ab_test = Column(Boolean, default=False, nullable=False)
    ab_test_config = Column(JSON, nullable=True)  # A/B test configuration and results
    
    # Foreign keys
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False, index=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    restaurant = relationship("Restaurant")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    messages = relationship("WhatsAppMessage", back_populates="campaign")
    campaign_recipients = relationship("CampaignRecipient", back_populates="campaign")
    
    @property
    def is_draft(self) -> bool:
        """Check if campaign is in draft status."""
        return self.status == "draft"
    
    @property
    def is_running(self) -> bool:
        """Check if campaign is currently running."""
        return self.status == "running"
    
    @property
    def is_completed(self) -> bool:
        """Check if campaign is completed."""
        return self.status == "completed"
    
    @property
    def can_be_started(self) -> bool:
        """Check if campaign can be started."""
        return self.status in ["draft", "scheduled"] and bool(self.message_variants)
    
    @property
    def delivery_rate(self) -> float:
        """Calculate message delivery rate."""
        if self.messages_sent == 0:
            return 0.0
        return (self.messages_delivered / self.messages_sent) * 100
    
    @property
    def read_rate(self) -> float:
        """Calculate message read rate."""
        if self.messages_delivered == 0:
            return 0.0
        return (self.messages_read / self.messages_delivered) * 100
    
    @property
    def response_rate(self) -> float:
        """Calculate customer response rate."""
        if self.messages_delivered == 0:
            return 0.0
        return (self.responses_received / self.messages_delivered) * 100
    
    @property
    def failure_rate(self) -> float:
        """Calculate message failure rate."""
        if self.messages_sent == 0:
            return 0.0
        return (self.messages_failed / self.messages_sent) * 100
    
    @property
    def estimated_completion_time(self) -> Optional[datetime]:
        """Estimate when campaign will complete based on current rate."""
        if not self.is_running or self.recipients_count == 0:
            return None
        
        remaining_messages = self.recipients_count - self.messages_sent
        if remaining_messages <= 0:
            return datetime.utcnow()
        
        hours_remaining = remaining_messages / self.send_rate_per_hour
        return datetime.utcnow() + timedelta(hours=hours_remaining)
    
    @property
    def roi_estimate(self) -> Optional[float]:
        """Calculate estimated ROI if applicable."""
        # This would be implemented based on business metrics
        # For now, return None as it requires additional context
        return None
    
    def start_campaign(self):
        """Start the campaign."""
        if not self.can_be_started:
            raise ValueError(f"Campaign {self.id} cannot be started in current status: {self.status}")
        
        self.status = "running"
        self.started_at = datetime.utcnow()
        logger.info(f"Campaign started: {self.id} - {self.name}")
    
    def pause_campaign(self):
        """Pause the running campaign."""
        if not self.is_running:
            raise ValueError(f"Cannot pause campaign {self.id} - not running")
        
        self.status = "paused"
        logger.info(f"Campaign paused: {self.id} - {self.name}")
    
    def resume_campaign(self):
        """Resume a paused campaign."""
        if self.status != "paused":
            raise ValueError(f"Cannot resume campaign {self.id} - not paused")
        
        self.status = "running"
        logger.info(f"Campaign resumed: {self.id} - {self.name}")
    
    def complete_campaign(self):
        """Mark campaign as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        logger.info(f"Campaign completed: {self.id} - {self.name}")
    
    def cancel_campaign(self, reason: str = None):
        """Cancel the campaign."""
        self.status = "cancelled"
        if reason and not hasattr(self, 'cancellation_reason'):
            # Store cancellation reason in targeting_config for now
            if not self.targeting_config:
                self.targeting_config = {}
            self.targeting_config["cancellation_reason"] = reason
        logger.info(f"Campaign cancelled: {self.id} - {self.name}, reason: {reason}")
    
    def update_metrics(self, sent: int = 0, delivered: int = 0, read: int = 0, failed: int = 0, responses: int = 0):
        """Update campaign performance metrics."""
        self.messages_sent += sent
        self.messages_delivered += delivered
        self.messages_read += read
        self.messages_failed += failed
        self.responses_received += responses
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get campaign performance summary."""
        return {
            "campaign_id": str(self.id),
            "name": self.name,
            "status": self.status,
            "recipients_count": self.recipients_count,
            "messages_sent": self.messages_sent,
            "messages_delivered": self.messages_delivered,
            "messages_read": self.messages_read,
            "messages_failed": self.messages_failed,
            "responses_received": self.responses_received,
            "delivery_rate": round(self.delivery_rate, 2),
            "read_rate": round(self.read_rate, 2),
            "response_rate": round(self.response_rate, 2),
            "failure_rate": round(self.failure_rate, 2),
            "actual_cost_usd": self.actual_cost_usd,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "estimated_completion": self.estimated_completion_time.isoformat() if self.estimated_completion_time else None
        }
    
    def get_targeting_summary(self) -> Dict[str, Any]:
        """Get campaign targeting configuration summary."""
        return {
            "campaign_type": self.campaign_type,
            "targeting_config": self.targeting_config,
            "max_recipients": self.max_recipients,
            "is_ab_test": self.is_ab_test,
            "message_variants_count": len(self.message_variants) if self.message_variants else 0
        }
    
    def __repr__(self) -> str:
        """String representation of campaign."""
        return f"<Campaign(name={self.name}, status={self.status}, recipients={self.recipients_count})>"


class CampaignRecipient(Base):
    """
    Campaign recipient model for tracking individual customer targeting and delivery.
    Links campaigns to specific customers with personalization data.
    """
    
    __tablename__ = "campaign_recipients"
    
    # Recipient status
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, sent, delivered, read, failed, responded
    
    # Variant assignment (for A/B testing)
    variant_id = Column(String(50), nullable=True, index=True)  # Which message variant was assigned
    
    # Personalization data
    personalization_data = Column(JSON, nullable=True)  # Customer-specific variables for message templating
    
    # Timing
    scheduled_send_time = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    
    # Response tracking
    response_text = Column(Text, nullable=True)
    response_sentiment = Column(String(10), nullable=True)  # positive, negative, neutral
    
    # Foreign keys
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("whatsapp_messages.id"), nullable=True)  # Linked message
    
    # Relationships
    campaign = relationship("Campaign", back_populates="campaign_recipients")
    customer = relationship("Customer")
    message = relationship("WhatsAppMessage")
    
    @property
    def is_pending(self) -> bool:
        """Check if recipient is pending message send."""
        return self.status == "pending"
    
    @property
    def is_sent(self) -> bool:
        """Check if message was sent to recipient."""
        return self.status in ["sent", "delivered", "read", "responded"]
    
    @property
    def has_responded(self) -> bool:
        """Check if recipient has responded."""
        return self.status == "responded"
    
    def mark_sent(self, message_id: str = None):
        """Mark message as sent to recipient."""
        self.status = "sent"
        self.sent_at = datetime.utcnow()
        if message_id:
            self.message_id = message_id
        logger.info(f"Campaign recipient marked as sent: {self.id}")
    
    def mark_delivered(self):
        """Mark message as delivered to recipient."""
        self.status = "delivered"
        self.delivered_at = datetime.utcnow()
        logger.info(f"Campaign recipient marked as delivered: {self.id}")
    
    def mark_responded(self, response_text: str, sentiment: str = None):
        """Mark recipient as responded."""
        self.status = "responded"
        self.responded_at = datetime.utcnow()
        self.response_text = response_text
        self.response_sentiment = sentiment
        logger.info(f"Campaign recipient marked as responded: {self.id}")
    
    def get_recipient_summary(self) -> Dict[str, Any]:
        """Get recipient summary for analytics."""
        return {
            "recipient_id": str(self.id),
            "customer_id": str(self.customer_id),
            "status": self.status,
            "variant_id": self.variant_id,
            "scheduled_send_time": self.scheduled_send_time.isoformat() if self.scheduled_send_time else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "has_responded": self.has_responded,
            "response_sentiment": self.response_sentiment
        }
    
    def __repr__(self) -> str:
        """String representation of campaign recipient."""
        return f"<CampaignRecipient(campaign_id={self.campaign_id}, customer_id={self.customer_id}, status={self.status})>"