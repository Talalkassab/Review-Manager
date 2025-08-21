"""
WhatsApp integration models for message tracking and template management.
"""

from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Text, Boolean, JSON, Index, ForeignKey, Integer
from sqlalchemy.orm import relationship

from .base import BaseModel


class MessageStatus(str, Enum):
    """Message delivery status enum."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageType(str, Enum):
    """WhatsApp message type enum."""
    TEXT = "text"
    TEMPLATE = "template"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    INTERACTIVE = "interactive"
    LOCATION = "location"


class MessageDirection(str, Enum):
    """Message direction enum."""
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class TemplateStatus(str, Enum):
    """Template approval status enum."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISABLED = "disabled"
    PAUSED = "paused"


class Priority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class WhatsAppMessage(BaseModel):
    """Model for tracking WhatsApp messages."""
    
    __tablename__ = "whatsapp_messages"
    
    # Message identification
    whatsapp_message_id = Column(String(100), unique=True, index=True, nullable=True)  # WhatsApp's message ID
    conversation_id = Column(String(100), index=True, nullable=True)  # Conversation tracking
    
    # Customer relationship
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    customer = relationship("Customer", backref="whatsapp_messages")
    
    # Message details
    direction = Column(String(20), nullable=False, default=MessageDirection.OUTBOUND)
    message_type = Column(String(20), nullable=False, default=MessageType.TEXT)
    status = Column(String(20), nullable=False, default=MessageStatus.PENDING)
    priority = Column(String(20), nullable=False, default=Priority.NORMAL)
    
    # Message content
    content = Column(Text, nullable=True)  # Text content
    media_url = Column(String(500), nullable=True)  # Media file URL
    media_type = Column(String(50), nullable=True)  # Media MIME type
    template_name = Column(String(100), nullable=True)  # Template name if template message
    template_language = Column(String(10), nullable=True)  # Template language code
    template_parameters = Column(JSON, nullable=True)  # Template parameter values
    
    # Delivery tracking
    sent_at = Column(String(50), nullable=True)  # ISO datetime string
    delivered_at = Column(String(50), nullable=True)
    read_at = Column(String(50), nullable=True)
    failed_at = Column(String(50), nullable=True)
    
    # Error handling
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    next_retry_at = Column(String(50), nullable=True)
    
    # Metadata
    webhook_payload = Column(JSON, nullable=True)  # Original webhook data
    api_response = Column(JSON, nullable=True)  # WhatsApp API response
    metadata = Column(JSON, nullable=True)  # Additional custom metadata
    
    # Business context
    campaign_id = Column(String(100), nullable=True, index=True)  # Marketing campaign ID
    automation_id = Column(String(100), nullable=True)  # Automation flow ID
    user_id = Column(String(100), nullable=True)  # Staff member who sent message
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_message_customer', 'customer_id'),
        Index('idx_message_status', 'status'),
        Index('idx_message_type', 'message_type'),
        Index('idx_message_direction', 'direction'),
        Index('idx_message_whatsapp_id', 'whatsapp_message_id'),
        Index('idx_message_conversation', 'conversation_id'),
        Index('idx_message_campaign', 'campaign_id'),
        Index('idx_message_created', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<WhatsAppMessage(id={self.id}, type={self.message_type}, status={self.status})>"
    
    def is_failed(self) -> bool:
        """Check if message failed to send."""
        return self.status == MessageStatus.FAILED
    
    def can_retry(self) -> bool:
        """Check if message can be retried."""
        return self.is_failed() and self.retry_count < self.max_retries
    
    def is_delivered(self) -> bool:
        """Check if message was delivered."""
        return self.status in [MessageStatus.DELIVERED, MessageStatus.READ]
    
    def is_template_message(self) -> bool:
        """Check if this is a template message."""
        return self.message_type == MessageType.TEMPLATE and self.template_name is not None
    
    def get_retry_delay_seconds(self) -> int:
        """Calculate retry delay based on attempt count."""
        base_delay = 30  # 30 seconds base delay
        return base_delay * (2 ** self.retry_count)  # Exponential backoff


class MessageTemplate(BaseModel):
    """Model for managing WhatsApp message templates."""
    
    __tablename__ = "message_templates"
    
    # Template identification
    name = Column(String(100), unique=True, index=True, nullable=False)
    whatsapp_template_id = Column(String(100), nullable=True)  # WhatsApp's template ID
    
    # Template details
    language = Column(String(10), nullable=False, default="ar")  # ISO 639-1 language code
    category = Column(String(50), nullable=False)  # AUTHENTICATION, MARKETING, UTILITY
    status = Column(String(20), nullable=False, default=TemplateStatus.PENDING)
    
    # Template content
    header_text = Column(Text, nullable=True)
    body_text = Column(Text, nullable=False)
    footer_text = Column(Text, nullable=True)
    
    # Template structure
    parameters = Column(JSON, nullable=True)  # Parameter definitions
    buttons = Column(JSON, nullable=True)  # Interactive buttons
    header_type = Column(String(20), nullable=True)  # TEXT, IMAGE, VIDEO, DOCUMENT
    header_media_url = Column(String(500), nullable=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(String(50), nullable=True)
    
    # Template metadata
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags for categorization
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Approval tracking
    submitted_at = Column(String(50), nullable=True)
    approved_at = Column(String(50), nullable=True)
    rejected_at = Column(String(50), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_template_name', 'name'),
        Index('idx_template_language', 'language'),
        Index('idx_template_status', 'status'),
        Index('idx_template_category', 'category'),
        Index('idx_template_active', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<MessageTemplate(id={self.id}, name={self.name}, status={self.status})>"
    
    def is_approved(self) -> bool:
        """Check if template is approved and ready to use."""
        return self.status == TemplateStatus.APPROVED and self.is_active
    
    def can_be_used(self) -> bool:
        """Check if template can be used for sending messages."""
        return self.is_approved()
    
    def increment_usage(self) -> None:
        """Increment usage counter."""
        self.usage_count += 1
        from datetime import datetime
        self.last_used_at = datetime.utcnow().isoformat()
    
    def get_parameter_names(self) -> list:
        """Get list of parameter names defined in template."""
        if not self.parameters:
            return []
        return [param.get('name') for param in self.parameters if param.get('name')]
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate that provided parameters match template requirements."""
        if not self.parameters:
            return len(params) == 0
        
        required_params = {param['name'] for param in self.parameters if param.get('required', True)}
        provided_params = set(params.keys())
        
        return required_params.issubset(provided_params)
    
    def render_body(self, parameters: Dict[str, Any]) -> str:
        """Render template body with provided parameters."""
        if not self.body_text:
            return ""
        
        rendered = self.body_text
        for key, value in parameters.items():
            placeholder = f"{{{{{key}}}}}"  # WhatsApp uses {{parameter}} format
            rendered = rendered.replace(placeholder, str(value))
        
        return rendered


class DeliveryReport(BaseModel):
    """Model for tracking detailed delivery reports."""
    
    __tablename__ = "delivery_reports"
    
    # Message relationship
    message_id = Column(Integer, ForeignKey("whatsapp_messages.id"), nullable=False)
    message = relationship("WhatsAppMessage", backref="delivery_reports")
    
    # Report details
    status = Column(String(20), nullable=False)
    timestamp = Column(String(50), nullable=False)  # ISO datetime string
    
    # WhatsApp specific data
    whatsapp_status_id = Column(String(100), nullable=True)
    conversation_id = Column(String(100), nullable=True)
    
    # Error details (if failed)
    error_code = Column(String(50), nullable=True)
    error_title = Column(String(200), nullable=True)
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Raw webhook data
    webhook_payload = Column(JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_delivery_message', 'message_id'),
        Index('idx_delivery_status', 'status'),
        Index('idx_delivery_timestamp', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryReport(id={self.id}, status={self.status}, message_id={self.message_id})>"