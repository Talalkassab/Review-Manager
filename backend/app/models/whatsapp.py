"""
WhatsApp message and communication models.
Handles message tracking, delivery status, and conversation history.
"""
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, MessageStatusChoice, LanguageChoice
from ..core.logging import get_logger

logger = get_logger(__name__)


class WhatsAppMessage(Base):
    """
    WhatsApp message model for tracking sent and received messages.
    Handles message delivery status and conversation flow.
    """
    
    __tablename__ = "whatsapp_messages"
    
    # Message identification
    whatsapp_message_id = Column(String(255), unique=True, index=True, nullable=True)  # WhatsApp API message ID
    message_type = Column(String(20), default="text", nullable=False)  # text, image, template, interactive
    
    # Message content
    content = Column(Text, nullable=False)  # Message text content
    template_name = Column(String(100), nullable=True)  # WhatsApp template name if used
    template_parameters = Column(JSON, nullable=True)  # Template parameters
    language = Column(String(5), default=LanguageChoice.ARABIC, nullable=False)
    
    # Message direction and status
    direction = Column(String(10), nullable=False)  # inbound, outbound
    status = Column(String(20), default=MessageStatusChoice.QUEUED, nullable=False, index=True)
    
    # Timing
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Message context
    context = Column(JSON, nullable=True)  # Additional context for the message
    is_automated = Column(Boolean, default=True, nullable=False)  # True for AI-generated messages
    
    # Campaign association
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=True, index=True)
    
    # Foreign keys
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    sent_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="whatsapp_messages")
    customer = relationship("Customer", back_populates="whatsapp_messages")
    campaign = relationship("Campaign", back_populates="messages")
    sent_by_user = relationship("User", foreign_keys=[sent_by_user_id])
    
    @property
    def is_inbound(self) -> bool:
        """Check if message is inbound (from customer)."""
        return self.direction == "inbound"
    
    @property
    def is_outbound(self) -> bool:
        """Check if message is outbound (to customer)."""
        return self.direction == "outbound"
    
    @property
    def is_delivered(self) -> bool:
        """Check if message has been delivered."""
        return self.status in [MessageStatusChoice.DELIVERED, MessageStatusChoice.READ]
    
    @property
    def is_failed(self) -> bool:
        """Check if message failed to send."""
        return self.status == MessageStatusChoice.FAILED
    
    @property
    def can_retry(self) -> bool:
        """Check if message can be retried."""
        return self.is_failed and self.retry_count < self.max_retries
    
    @property
    def response_time_seconds(self) -> Optional[float]:
        """Get response time in seconds (for inbound messages after outbound)."""
        # This would need to be calculated based on conversation flow
        # Implementation depends on conversation threading logic
        return None
    
    def mark_sent(self, whatsapp_message_id: str = None):
        """Mark message as sent."""
        self.status = MessageStatusChoice.SENT
        self.sent_at = datetime.utcnow()
        if whatsapp_message_id:
            self.whatsapp_message_id = whatsapp_message_id
        logger.info(f"Message marked as sent: {self.id}")
    
    def mark_delivered(self):
        """Mark message as delivered."""
        self.status = MessageStatusChoice.DELIVERED
        self.delivered_at = datetime.utcnow()
        logger.info(f"Message marked as delivered: {self.id}")
    
    def mark_read(self):
        """Mark message as read by recipient."""
        self.status = MessageStatusChoice.READ
        self.read_at = datetime.utcnow()
        logger.info(f"Message marked as read: {self.id}")
    
    def mark_failed(self, error_code: str = None, error_message: str = None):
        """Mark message as failed."""
        self.status = MessageStatusChoice.FAILED
        self.failed_at = datetime.utcnow()
        self.error_code = error_code
        self.error_message = error_message
        logger.warning(f"Message marked as failed: {self.id}, error: {error_message}")
    
    def increment_retry(self):
        """Increment retry count."""
        self.retry_count += 1
        self.status = MessageStatusChoice.QUEUED  # Reset to queued for retry
        logger.info(f"Message retry incremented: {self.id}, retry: {self.retry_count}")
    
    def get_message_summary(self) -> Dict[str, Any]:
        """Get summary of message for analytics."""
        return {
            "id": str(self.id),
            "direction": self.direction,
            "status": self.status,
            "message_type": self.message_type,
            "language": self.language,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "is_automated": self.is_automated,
            "retry_count": self.retry_count,
            "has_error": self.is_failed
        }
    
    def __repr__(self) -> str:
        """String representation of WhatsApp message."""
        return f"<WhatsAppMessage(id={self.id}, direction={self.direction}, status={self.status})>"


class ConversationThread(Base):
    """
    Conversation thread model for grouping related WhatsApp messages.
    Helps track conversation flow and context.
    """
    
    __tablename__ = "conversation_threads"
    
    # Thread identification
    thread_identifier = Column(String(255), unique=True, index=True, nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, closed, archived
    
    # Conversation metadata
    subject = Column(String(255), nullable=True)  # Conversation subject/topic
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # AI context
    ai_context = Column(JSON, nullable=True)  # AI conversation context and memory
    customer_sentiment = Column(String(10), nullable=True)  # Current customer sentiment
    requires_human_intervention = Column(Boolean, default=False, nullable=False)
    
    # Foreign keys
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    assigned_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    restaurant = relationship("Restaurant")
    customer = relationship("Customer")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    
    @property
    def is_active(self) -> bool:
        """Check if conversation is active."""
        return self.status == "active"
    
    @property
    def duration_minutes(self) -> float:
        """Get conversation duration in minutes."""
        end_time = self.closed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds() / 60
    
    def update_last_message(self):
        """Update last message timestamp."""
        self.last_message_at = datetime.utcnow()
    
    def close_conversation(self, reason: str = None):
        """Close the conversation thread."""
        self.status = "closed"
        self.closed_at = datetime.utcnow()
        if reason:
            if not self.ai_context:
                self.ai_context = {}
            self.ai_context["close_reason"] = reason
        logger.info(f"Conversation thread closed: {self.id}")
    
    def escalate_to_human(self, user_id: str, reason: str = None):
        """Escalate conversation to human agent."""
        self.requires_human_intervention = True
        self.assigned_user_id = user_id
        if reason:
            if not self.ai_context:
                self.ai_context = {}
            self.ai_context["escalation_reason"] = reason
        logger.info(f"Conversation escalated to human: {self.id}")
    
    def __repr__(self) -> str:
        """String representation of conversation thread."""
        return f"<ConversationThread(id={self.id}, status={self.status})>"