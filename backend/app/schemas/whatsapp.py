"""
WhatsApp-related Pydantic schemas.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import Field

from .base import BaseSchema, BaseResponse


class WhatsAppMessageCreate(BaseSchema):
    """Schema for creating a WhatsApp message."""
    
    content: str = Field(..., min_length=1, description="Message content")
    message_type: str = Field("text", description="Message type")
    template_name: Optional[str] = Field(None, description="WhatsApp template name")
    template_parameters: Optional[Dict[str, Any]] = Field(None, description="Template parameters")
    language: str = Field("ar", pattern="^(ar|en)$", description="Message language")
    direction: str = Field("outbound", pattern="^(inbound|outbound)$", description="Message direction")
    
    # Context and metadata
    context: Optional[Dict[str, Any]] = Field(None, description="Message context")
    is_automated: bool = Field(True, description="Is automated message")
    
    # Campaign association
    campaign_id: Optional[UUID] = Field(None, description="Campaign ID")
    
    # Recipients
    customer_id: UUID = Field(..., description="Customer ID")
    restaurant_id: UUID = Field(..., description="Restaurant ID")


class WhatsAppMessageResponse(BaseResponse):
    """Schema for WhatsApp message response."""
    
    whatsapp_message_id: Optional[str] = Field(None, description="WhatsApp API message ID")
    message_type: str = Field(..., description="Message type")
    content: str = Field(..., description="Message content")
    template_name: Optional[str] = Field(None, description="WhatsApp template name")
    template_parameters: Optional[Dict[str, Any]] = Field(None, description="Template parameters")
    language: str = Field(..., description="Message language")
    
    # Message direction and status
    direction: str = Field(..., description="Message direction")
    status: str = Field(..., description="Message status")
    
    # Timing
    sent_at: Optional[datetime] = Field(None, description="Sent timestamp")
    delivered_at: Optional[datetime] = Field(None, description="Delivered timestamp")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")
    failed_at: Optional[datetime] = Field(None, description="Failed timestamp")
    
    # Error handling
    error_code: Optional[str] = Field(None, description="Error code")
    error_message: Optional[str] = Field(None, description="Error message")
    retry_count: int = Field(..., description="Retry count")
    max_retries: int = Field(..., description="Max retries")
    
    # Context and metadata
    context: Optional[Dict[str, Any]] = Field(None, description="Message context")
    is_automated: bool = Field(..., description="Is automated message")
    
    # Relationships
    campaign_id: Optional[UUID] = Field(None, description="Campaign ID")
    customer_id: UUID = Field(..., description="Customer ID")
    restaurant_id: UUID = Field(..., description="Restaurant ID")
    sent_by_user_id: Optional[UUID] = Field(None, description="Sent by user ID")
    
    # Computed properties
    is_delivered: bool = Field(..., description="Is delivered")
    is_failed: bool = Field(..., description="Is failed")
    can_retry: bool = Field(..., description="Can retry")


class WhatsAppMessageUpdate(BaseSchema):
    """Schema for updating WhatsApp message status."""
    
    status: Optional[str] = Field(None, description="Message status")
    whatsapp_message_id: Optional[str] = Field(None, description="WhatsApp API message ID")
    error_code: Optional[str] = Field(None, description="Error code")
    error_message: Optional[str] = Field(None, description="Error message")
    delivered_at: Optional[datetime] = Field(None, description="Delivered timestamp")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")
    failed_at: Optional[datetime] = Field(None, description="Failed timestamp")


class ConversationThreadCreate(BaseSchema):
    """Schema for creating a conversation thread."""
    
    thread_identifier: str = Field(..., description="Thread identifier")
    subject: Optional[str] = Field(None, description="Conversation subject")
    customer_id: UUID = Field(..., description="Customer ID")
    restaurant_id: UUID = Field(..., description="Restaurant ID")
    ai_context: Optional[Dict[str, Any]] = Field(None, description="AI context")


class ConversationResponse(BaseResponse):
    """Schema for conversation thread response."""
    
    thread_identifier: str = Field(..., description="Thread identifier")
    status: str = Field(..., description="Thread status")
    subject: Optional[str] = Field(None, description="Conversation subject")
    started_at: datetime = Field(..., description="Started timestamp")
    last_message_at: Optional[datetime] = Field(None, description="Last message timestamp")
    closed_at: Optional[datetime] = Field(None, description="Closed timestamp")
    
    # AI context and sentiment
    ai_context: Optional[Dict[str, Any]] = Field(None, description="AI context")
    customer_sentiment: Optional[str] = Field(None, description="Customer sentiment")
    requires_human_intervention: bool = Field(..., description="Requires human intervention")
    
    # Relationships
    customer_id: UUID = Field(..., description="Customer ID")
    restaurant_id: UUID = Field(..., description="Restaurant ID")
    assigned_user_id: Optional[UUID] = Field(None, description="Assigned user ID")
    
    # Computed properties
    is_active: bool = Field(..., description="Is active")
    duration_minutes: float = Field(..., description="Duration in minutes")


class WhatsAppWebhook(BaseSchema):
    """Schema for WhatsApp webhook data."""
    
    object: str = Field(..., description="Webhook object type")
    entry: List[Dict[str, Any]] = Field(..., description="Webhook entry data")


class WhatsAppMessageStatus(BaseSchema):
    """Schema for WhatsApp message status update."""
    
    id: str = Field(..., description="Message ID")
    status: str = Field(..., description="Message status")
    timestamp: str = Field(..., description="Status timestamp")
    recipient_id: str = Field(..., description="Recipient ID")
    conversation: Optional[Dict[str, Any]] = Field(None, description="Conversation data")
    pricing: Optional[Dict[str, Any]] = Field(None, description="Pricing data")


class WhatsAppInboundMessage(BaseSchema):
    """Schema for inbound WhatsApp message."""
    
    from_: str = Field(..., alias="from", description="Sender phone number")
    id: str = Field(..., description="Message ID")
    timestamp: str = Field(..., description="Message timestamp")
    type: str = Field(..., description="Message type")
    text: Optional[Dict[str, str]] = Field(None, description="Text message data")
    image: Optional[Dict[str, Any]] = Field(None, description="Image message data")
    audio: Optional[Dict[str, Any]] = Field(None, description="Audio message data")
    document: Optional[Dict[str, Any]] = Field(None, description="Document message data")
    context: Optional[Dict[str, Any]] = Field(None, description="Message context")


class WhatsAppTemplate(BaseSchema):
    """Schema for WhatsApp template."""
    
    name: str = Field(..., description="Template name")
    language: str = Field(..., description="Template language")
    components: List[Dict[str, Any]] = Field(..., description="Template components")


class MessageAnalytics(BaseSchema):
    """Schema for message analytics."""
    
    total_messages: int = Field(..., description="Total messages")
    messages_sent: int = Field(..., description="Messages sent")
    messages_delivered: int = Field(..., description="Messages delivered")
    messages_read: int = Field(..., description="Messages read")
    messages_failed: int = Field(..., description="Messages failed")
    delivery_rate: float = Field(..., description="Delivery rate percentage")
    read_rate: float = Field(..., description="Read rate percentage")
    failure_rate: float = Field(..., description="Failure rate percentage")
    average_response_time: Optional[float] = Field(None, description="Average response time in hours")
    most_active_hours: List[int] = Field(..., description="Most active hours")
    message_distribution: Dict[str, int] = Field(..., description="Message type distribution")


class ConversationAnalytics(BaseSchema):
    """Schema for conversation analytics."""
    
    total_conversations: int = Field(..., description="Total conversations")
    active_conversations: int = Field(..., description="Active conversations")
    closed_conversations: int = Field(..., description="Closed conversations")
    escalated_conversations: int = Field(..., description="Escalated conversations")
    average_duration_minutes: float = Field(..., description="Average conversation duration")
    resolution_rate: float = Field(..., description="Conversation resolution rate")
    escalation_rate: float = Field(..., description="Escalation rate percentage")
    customer_satisfaction_scores: Dict[str, int] = Field(..., description="Customer satisfaction distribution")


class WhatsAppMessageListFilter(BaseSchema):
    """Schema for filtering WhatsApp messages."""
    
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    customer_id: Optional[UUID] = Field(None, description="Filter by customer")
    campaign_id: Optional[UUID] = Field(None, description="Filter by campaign")
    direction: Optional[str] = Field(None, pattern="^(inbound|outbound)$", description="Filter by direction")
    status: Optional[str] = Field(None, description="Filter by status")
    message_type: Optional[str] = Field(None, description="Filter by message type")
    language: Optional[str] = Field(None, pattern="^(ar|en)$", description="Filter by language")
    is_automated: Optional[bool] = Field(None, description="Filter by automation")
    date_from: Optional[datetime] = Field(None, description="Date from")
    date_to: Optional[datetime] = Field(None, description="Date to")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")