"""
Campaign-related Pydantic schemas.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import Field

from .base import BaseSchema, BaseResponse


class CampaignCreate(BaseSchema):
    """Schema for creating a new campaign."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Campaign name")
    description: Optional[str] = Field(None, description="Campaign description")
    campaign_type: str = Field(..., description="Campaign type")
    
    # Targeting configuration
    targeting_config: Dict[str, Any] = Field(..., description="Targeting configuration")
    
    # Message configuration
    message_variants: List[Dict[str, Any]] = Field(..., min_items=1, description="Message variants")
    default_language: str = Field("ar", pattern="^(ar|en)$", description="Default language")
    
    # Scheduling
    scheduled_start_at: Optional[datetime] = Field(None, description="Scheduled start time")
    scheduled_end_at: Optional[datetime] = Field(None, description="Scheduled end time")
    scheduling_config: Optional[Dict[str, Any]] = Field(None, description="Scheduling configuration")
    
    # Performance settings
    max_recipients: Optional[int] = Field(None, gt=0, description="Maximum recipients")
    send_rate_per_hour: int = Field(100, gt=0, description="Send rate per hour")
    
    # Budget
    budget_limit_usd: Optional[float] = Field(None, gt=0, description="Budget limit USD")
    
    # A/B testing
    is_ab_test: bool = Field(False, description="Is A/B test")
    ab_test_config: Optional[Dict[str, Any]] = Field(None, description="A/B test configuration")
    
    # Restaurant association
    restaurant_id: UUID = Field(..., description="Restaurant ID")


class CampaignUpdate(BaseSchema):
    """Schema for updating campaign information."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Campaign name")
    description: Optional[str] = Field(None, description="Campaign description")
    
    # Message configuration
    message_variants: Optional[List[Dict[str, Any]]] = Field(None, min_items=1, description="Message variants")
    
    # Scheduling
    scheduled_start_at: Optional[datetime] = Field(None, description="Scheduled start time")
    scheduled_end_at: Optional[datetime] = Field(None, description="Scheduled end time")
    scheduling_config: Optional[Dict[str, Any]] = Field(None, description="Scheduling configuration")
    
    # Performance settings
    max_recipients: Optional[int] = Field(None, gt=0, description="Maximum recipients")
    send_rate_per_hour: Optional[int] = Field(None, gt=0, description="Send rate per hour")
    
    # Budget
    budget_limit_usd: Optional[float] = Field(None, gt=0, description="Budget limit USD")
    
    # A/B testing
    ab_test_config: Optional[Dict[str, Any]] = Field(None, description="A/B test configuration")


class CampaignResponse(BaseResponse):
    """Schema for campaign response data."""
    
    name: str = Field(..., description="Campaign name")
    description: Optional[str] = Field(None, description="Campaign description")
    campaign_type: str = Field(..., description="Campaign type")
    status: str = Field(..., description="Campaign status")
    
    # Scheduling
    scheduled_start_at: Optional[datetime] = Field(None, description="Scheduled start time")
    scheduled_end_at: Optional[datetime] = Field(None, description="Scheduled end time")
    started_at: Optional[datetime] = Field(None, description="Started timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completed timestamp")
    
    # Targeting and messaging
    targeting_config: Dict[str, Any] = Field(..., description="Targeting configuration")
    message_variants: List[Dict[str, Any]] = Field(..., description="Message variants")
    default_language: str = Field(..., description="Default language")
    scheduling_config: Optional[Dict[str, Any]] = Field(None, description="Scheduling configuration")
    
    # Performance settings
    max_recipients: Optional[int] = Field(None, description="Maximum recipients")
    send_rate_per_hour: int = Field(..., description="Send rate per hour")
    
    # Budget and costs
    budget_limit_usd: Optional[float] = Field(None, description="Budget limit USD")
    estimated_cost_usd: Optional[float] = Field(None, description="Estimated cost USD")
    actual_cost_usd: float = Field(..., description="Actual cost USD")
    
    # Performance metrics
    recipients_count: int = Field(..., description="Recipients count")
    messages_sent: int = Field(..., description="Messages sent")
    messages_delivered: int = Field(..., description="Messages delivered")
    messages_read: int = Field(..., description="Messages read")
    messages_failed: int = Field(..., description="Messages failed")
    responses_received: int = Field(..., description="Responses received")
    
    # A/B testing
    is_ab_test: bool = Field(..., description="Is A/B test")
    ab_test_config: Optional[Dict[str, Any]] = Field(None, description="A/B test configuration")
    
    # Relationships
    restaurant_id: UUID = Field(..., description="Restaurant ID")
    created_by_user_id: UUID = Field(..., description="Created by user ID")
    
    # Computed properties
    delivery_rate: float = Field(..., description="Delivery rate percentage")
    read_rate: float = Field(..., description="Read rate percentage")
    response_rate: float = Field(..., description="Response rate percentage")
    failure_rate: float = Field(..., description="Failure rate percentage")
    estimated_completion_time: Optional[datetime] = Field(None, description="Estimated completion time")
    can_be_started: bool = Field(..., description="Can be started")
    is_running: bool = Field(..., description="Is running")
    is_completed: bool = Field(..., description="Is completed")


class CampaignRecipientCreate(BaseSchema):
    """Schema for creating campaign recipients."""
    
    customer_ids: List[UUID] = Field(..., min_items=1, description="Customer IDs")
    campaign_id: UUID = Field(..., description="Campaign ID")
    variant_assignments: Optional[Dict[UUID, str]] = Field(None, description="Variant assignments per customer")
    personalization_data: Optional[Dict[UUID, Dict[str, Any]]] = Field(None, description="Personalization data per customer")
    scheduled_send_times: Optional[Dict[UUID, datetime]] = Field(None, description="Scheduled send times per customer")


class CampaignRecipientResponse(BaseResponse):
    """Schema for campaign recipient response."""
    
    status: str = Field(..., description="Recipient status")
    variant_id: Optional[str] = Field(None, description="Assigned variant ID")
    personalization_data: Optional[Dict[str, Any]] = Field(None, description="Personalization data")
    
    # Timing
    scheduled_send_time: Optional[datetime] = Field(None, description="Scheduled send time")
    sent_at: Optional[datetime] = Field(None, description="Sent timestamp")
    delivered_at: Optional[datetime] = Field(None, description="Delivered timestamp")
    responded_at: Optional[datetime] = Field(None, description="Responded timestamp")
    
    # Response tracking
    response_text: Optional[str] = Field(None, description="Response text")
    response_sentiment: Optional[str] = Field(None, description="Response sentiment")
    
    # Relationships
    campaign_id: UUID = Field(..., description="Campaign ID")
    customer_id: UUID = Field(..., description="Customer ID")
    message_id: Optional[UUID] = Field(None, description="Message ID")
    
    # Computed properties
    is_pending: bool = Field(..., description="Is pending")
    is_sent: bool = Field(..., description="Is sent")
    has_responded: bool = Field(..., description="Has responded")


class CampaignAction(BaseSchema):
    """Schema for campaign actions."""
    
    action: str = Field(..., description="Action to perform")
    reason: Optional[str] = Field(None, description="Action reason")


class CampaignStats(BaseSchema):
    """Schema for campaign statistics."""
    
    campaign_id: UUID = Field(..., description="Campaign ID")
    performance_summary: Dict[str, Any] = Field(..., description="Performance summary")
    targeting_summary: Dict[str, Any] = Field(..., description="Targeting summary")
    hourly_breakdown: List[Dict[str, Any]] = Field(..., description="Hourly performance breakdown")
    variant_performance: Optional[List[Dict[str, Any]]] = Field(None, description="Variant performance comparison")
    top_performing_times: List[Dict[str, Any]] = Field(..., description="Top performing send times")
    customer_segments: Dict[str, Any] = Field(..., description="Customer segment performance")


class CampaignAnalytics(BaseSchema):
    """Schema for campaign analytics."""
    
    period: str = Field(..., description="Analytics period")
    total_campaigns: int = Field(..., description="Total campaigns")
    active_campaigns: int = Field(..., description="Active campaigns")
    completed_campaigns: int = Field(..., description="Completed campaigns")
    cancelled_campaigns: int = Field(..., description="Cancelled campaigns")
    total_messages_sent: int = Field(..., description="Total messages sent")
    average_delivery_rate: float = Field(..., description="Average delivery rate")
    average_response_rate: float = Field(..., description="Average response rate")
    total_cost_usd: float = Field(..., description="Total cost USD")
    roi_metrics: Dict[str, float] = Field(..., description="ROI metrics")
    best_performing_types: List[Dict[str, Any]] = Field(..., description="Best performing campaign types")
    optimal_send_times: List[Dict[str, Any]] = Field(..., description="Optimal send times")


class CampaignTemplate(BaseSchema):
    """Schema for campaign templates."""
    
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    campaign_type: str = Field(..., description="Campaign type")
    default_targeting: Dict[str, Any] = Field(..., description="Default targeting configuration")
    default_messages: List[Dict[str, Any]] = Field(..., description="Default message variants")
    default_scheduling: Dict[str, Any] = Field(..., description="Default scheduling configuration")
    is_system_template: bool = Field(False, description="Is system template")


class BulkCampaignOperation(BaseSchema):
    """Schema for bulk campaign operations."""
    
    campaign_ids: List[UUID] = Field(..., min_items=1, max_items=50, description="Campaign IDs")
    operation: str = Field(..., description="Operation to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Operation parameters")


class CampaignListFilter(BaseSchema):
    """Schema for filtering campaign lists."""
    
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search term")
    campaign_type: Optional[str] = Field(None, description="Filter by campaign type")
    status: Optional[str] = Field(None, description="Filter by status")
    created_by: Optional[UUID] = Field(None, description="Filter by creator")
    is_ab_test: Optional[bool] = Field(None, description="Filter by A/B test status")
    created_from: Optional[datetime] = Field(None, description="Created from date")
    created_to: Optional[datetime] = Field(None, description="Created to date")
    has_budget_limit: Optional[bool] = Field(None, description="Filter by budget limit")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")


class ABTestResults(BaseSchema):
    """Schema for A/B test results."""
    
    campaign_id: UUID = Field(..., description="Campaign ID")
    test_duration_hours: float = Field(..., description="Test duration in hours")
    variants: List[Dict[str, Any]] = Field(..., description="Variant performance data")
    winner: Optional[str] = Field(None, description="Winning variant ID")
    confidence_level: Optional[float] = Field(None, description="Statistical confidence level")
    statistical_significance: bool = Field(..., description="Is statistically significant")
    recommendations: List[str] = Field(..., description="Recommendations based on results")
    key_metrics: Dict[str, Any] = Field(..., description="Key performance metrics")
    conversion_uplift: Optional[float] = Field(None, description="Conversion uplift percentage")