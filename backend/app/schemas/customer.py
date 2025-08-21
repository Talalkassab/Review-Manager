"""
Customer-related Pydantic schemas.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import Field, EmailStr

from .base import BaseSchema, BaseResponse


class CustomerCreate(BaseSchema):
    """Schema for creating a new customer."""
    
    customer_number: str = Field(..., min_length=1, max_length=50, description="Customer number/identifier")
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name (optional)")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    phone_number: str = Field(..., max_length=20, description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")
    preferred_language: str = Field("ar", pattern="^(ar|en)$", description="Preferred language")
    
    # Visit information
    visit_date: Optional[datetime] = Field(None, description="Visit date")
    table_number: Optional[str] = Field(None, max_length=10, description="Table number")
    server_name: Optional[str] = Field(None, max_length=100, description="Server name")
    party_size: int = Field(1, ge=1, le=20, description="Party size")
    
    # Order information
    order_details: Optional[Dict[str, Any]] = Field(None, description="Order details")
    order_total: Optional[float] = Field(None, ge=0, description="Order total amount")
    special_requests: Optional[str] = Field(None, description="Special requests")
    
    # Communication preferences
    whatsapp_opt_in: bool = Field(True, description="WhatsApp opt-in status")
    email_opt_in: bool = Field(True, description="Email opt-in status")
    
    # Privacy
    gdpr_consent: bool = Field(True, description="GDPR consent")
    
    # Restaurant association
    restaurant_id: UUID = Field(..., description="Restaurant ID")


class CustomerUpdate(BaseSchema):
    """Schema for updating customer information."""
    
    customer_number: Optional[str] = Field(None, min_length=1, max_length=50, description="Customer number/identifier")
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")
    preferred_language: Optional[str] = Field(None, pattern="^(ar|en)$", description="Preferred language")
    
    # Visit information
    table_number: Optional[str] = Field(None, max_length=10, description="Table number")
    server_name: Optional[str] = Field(None, max_length=100, description="Server name")
    party_size: Optional[int] = Field(None, ge=1, le=20, description="Party size")
    
    # Order information
    order_details: Optional[Dict[str, Any]] = Field(None, description="Order details")
    order_total: Optional[float] = Field(None, ge=0, description="Order total amount")
    special_requests: Optional[str] = Field(None, description="Special requests")
    
    # Communication preferences
    whatsapp_opt_in: Optional[bool] = Field(None, description="WhatsApp opt-in status")
    email_opt_in: Optional[bool] = Field(None, description="Email opt-in status")
    
    # Follow-up
    follow_up_notes: Optional[str] = Field(None, description="Follow-up notes")
    requires_follow_up: Optional[bool] = Field(None, description="Requires follow-up")
    max_contact_attempts: Optional[int] = Field(None, ge=1, le=10, description="Max contact attempts")


class CustomerResponse(BaseResponse):
    """Schema for customer response data."""
    
    customer_number: Optional[str] = Field(None, description="Customer number/identifier")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    phone_number: str = Field(..., description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    preferred_language: str = Field(..., description="Preferred language")
    
    # Visit information
    visit_date: datetime = Field(..., description="Visit date")
    table_number: Optional[str] = Field(None, description="Table number")
    server_name: Optional[str] = Field(None, description="Server name")
    party_size: int = Field(..., description="Party size")
    
    # Order information
    order_details: Optional[Dict[str, Any]] = Field(None, description="Order details")
    order_total: Optional[float] = Field(None, description="Order total amount")
    special_requests: Optional[str] = Field(None, description="Special requests")
    
    # Communication status
    status: str = Field(..., description="Customer status")
    last_contacted_at: Optional[datetime] = Field(None, description="Last contacted timestamp")
    contact_attempts: int = Field(..., description="Contact attempts count")
    max_contact_attempts: int = Field(..., description="Max contact attempts")
    
    # Communication preferences
    whatsapp_opt_in: bool = Field(..., description="WhatsApp opt-in status")
    email_opt_in: bool = Field(..., description="Email opt-in status")
    
    # Feedback information
    feedback_received_at: Optional[datetime] = Field(None, description="Feedback received timestamp")
    feedback_text: Optional[str] = Field(None, description="Feedback text")
    feedback_sentiment: Optional[str] = Field(None, description="Feedback sentiment")
    feedback_confidence_score: Optional[float] = Field(None, description="Sentiment confidence score")
    rating: Optional[int] = Field(None, description="Customer rating (1-5)")
    
    # Review tracking
    google_review_requested_at: Optional[datetime] = Field(None, description="Google review requested timestamp")
    google_review_link_sent: bool = Field(..., description="Google review link sent")
    google_review_completed: bool = Field(..., description="Google review completed")
    google_review_url: Optional[str] = Field(None, description="Google review URL")
    
    # Follow-up and resolution
    requires_follow_up: bool = Field(..., description="Requires follow-up")
    follow_up_notes: Optional[str] = Field(None, description="Follow-up notes")
    issue_resolved: bool = Field(..., description="Issue resolved status")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")
    
    # Customer metadata
    is_repeat_customer: bool = Field(..., description="Is repeat customer")
    visit_count: int = Field(..., description="Visit count")
    first_visit_date: Optional[datetime] = Field(None, description="First visit date")
    last_visit_date: Optional[datetime] = Field(None, description="Last visit date")
    
    # Privacy and GDPR
    gdpr_consent: bool = Field(..., description="GDPR consent")
    data_retention_date: Optional[datetime] = Field(None, description="Data retention date")
    
    # Relationships
    restaurant_id: UUID = Field(..., description="Restaurant ID")
    created_by: Optional[UUID] = Field(None, description="Created by user ID")
    
    # Computed properties
    full_name: str = Field(..., description="Full name")
    display_name: str = Field(..., description="Display name")
    masked_phone_number: str = Field(..., description="Masked phone number")
    time_since_visit_hours: float = Field(..., description="Hours since visit")
    is_recent_visit: bool = Field(..., description="Is recent visit")
    can_be_contacted: bool = Field(..., description="Can be contacted")
    sentiment_emoji: str = Field(..., description="Sentiment emoji")


class CustomerFeedbackUpdate(BaseSchema):
    """Schema for updating customer feedback."""
    
    feedback_text: str = Field(..., min_length=1, description="Feedback text")
    sentiment: Optional[str] = Field(None, pattern="^(positive|negative|neutral)$", description="Sentiment")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence score")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating (1-5)")
    requires_follow_up: Optional[bool] = Field(None, description="Requires follow-up")
    issue_resolved: Optional[bool] = Field(None, description="Issue resolved")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")


class CustomerInteractionSummary(BaseSchema):
    """Schema for customer interaction summary."""
    
    customer_id: UUID = Field(..., description="Customer ID")
    name: str = Field(..., description="Customer name")
    phone: str = Field(..., description="Masked phone number")
    visit_date: datetime = Field(..., description="Visit date")
    status: str = Field(..., description="Interaction status")
    contact_attempts: int = Field(..., description="Contact attempts")
    has_feedback: bool = Field(..., description="Has feedback")
    sentiment: Optional[str] = Field(None, description="Feedback sentiment")
    rating: Optional[int] = Field(None, description="Customer rating")
    requires_follow_up: bool = Field(..., description="Requires follow-up")
    google_review_sent: bool = Field(..., description="Google review sent")
    google_review_completed: bool = Field(..., description="Google review completed")


class CustomerStats(BaseSchema):
    """Schema for customer statistics."""
    
    total_customers: int = Field(..., description="Total customers")
    customers_today: int = Field(..., description="Customers today")
    customers_this_week: int = Field(..., description="Customers this week")
    customers_this_month: int = Field(..., description="Customers this month")
    pending_contact: int = Field(..., description="Pending contact")
    contacted: int = Field(..., description="Contacted")
    responded: int = Field(..., description="Responded")
    completed: int = Field(..., description="Completed")
    failed: int = Field(..., description="Failed")
    response_rate: float = Field(..., description="Response rate percentage")
    positive_feedback_rate: float = Field(..., description="Positive feedback rate")
    average_rating: Optional[float] = Field(None, description="Average rating")
    google_reviews_generated: int = Field(..., description="Google reviews generated")


class CustomerBulkUpdate(BaseSchema):
    """Schema for bulk customer updates."""
    
    customer_ids: List[UUID] = Field(..., min_items=1, max_items=100, description="Customer IDs")
    status: Optional[str] = Field(None, description="New status")
    requires_follow_up: Optional[bool] = Field(None, description="Requires follow-up")
    follow_up_notes: Optional[str] = Field(None, description="Follow-up notes")
    max_contact_attempts: Optional[int] = Field(None, ge=1, le=10, description="Max contact attempts")


class CustomerListFilter(BaseSchema):
    """Schema for filtering customer lists."""
    
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search term")
    status: Optional[str] = Field(None, description="Filter by status")
    sentiment: Optional[str] = Field(None, pattern="^(positive|negative|neutral)$", description="Filter by sentiment")
    has_feedback: Optional[bool] = Field(None, description="Filter by feedback presence")
    requires_follow_up: Optional[bool] = Field(None, description="Filter by follow-up requirement")
    visit_date_from: Optional[datetime] = Field(None, description="Visit date from")
    visit_date_to: Optional[datetime] = Field(None, description="Visit date to")
    rating_min: Optional[int] = Field(None, ge=1, le=5, description="Minimum rating")
    rating_max: Optional[int] = Field(None, ge=1, le=5, description="Maximum rating")
    is_repeat_customer: Optional[bool] = Field(None, description="Filter by repeat customer")
    google_review_completed: Optional[bool] = Field(None, description="Filter by Google review status")
    sort_by: Optional[str] = Field("visit_date", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")


class CustomerExport(BaseSchema):
    """Schema for customer data export."""
    
    format: str = Field("csv", pattern="^(csv|xlsx|json)$", description="Export format")
    include_personal_data: bool = Field(False, description="Include personal data")
    date_range_start: Optional[datetime] = Field(None, description="Date range start")
    date_range_end: Optional[datetime] = Field(None, description="Date range end")
    filters: Optional[CustomerListFilter] = Field(None, description="Export filters")


class CustomerAnalytics(BaseSchema):
    """Schema for customer analytics data."""
    
    period: str = Field(..., description="Analytics period")
    customer_acquisition: Dict[str, int] = Field(..., description="Customer acquisition data")
    response_rates: Dict[str, float] = Field(..., description="Response rates")
    sentiment_distribution: Dict[str, int] = Field(..., description="Sentiment distribution")
    rating_distribution: Dict[str, int] = Field(..., description="Rating distribution")
    feedback_trends: List[Dict[str, Any]] = Field(..., description="Feedback trends")
    top_issues: List[Dict[str, Any]] = Field(..., description="Top customer issues")
    resolution_times: Dict[str, float] = Field(..., description="Issue resolution times")