"""
Restaurant-related Pydantic schemas.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import Field, EmailStr, HttpUrl

from .base import BaseSchema, BaseResponse


class RestaurantCreate(BaseSchema):
    """Schema for creating a new restaurant."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Restaurant name")
    name_arabic: Optional[str] = Field(None, max_length=200, description="Restaurant name in Arabic")
    description: Optional[str] = Field(None, description="Restaurant description")
    description_arabic: Optional[str] = Field(None, description="Restaurant description in Arabic")
    
    # Branding
    logo_url: Optional[str] = Field(None, max_length=500, description="Logo URL")
    persona: Optional[str] = Field(None, description="Restaurant communication persona/style")
    
    # Contact information
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")
    website_url: Optional[HttpUrl] = Field(None, description="Website URL")
    
    # Location
    address: Optional[str] = Field(None, description="Address")
    address_arabic: Optional[str] = Field(None, description="Address in Arabic")
    city: Optional[str] = Field(None, max_length=100, description="City")
    country: str = Field("Saudi Arabia", max_length=100, description="Country")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    
    # Settings
    default_language: str = Field("ar", pattern="^(ar|en)$", description="Default language")
    timezone: str = Field("Asia/Riyadh", description="Timezone")
    currency: str = Field("SAR", max_length=3, description="Currency code")
    operating_hours: Optional[Dict[str, Any]] = Field(None, description="Operating hours")
    
    # WhatsApp settings
    whatsapp_business_phone: Optional[str] = Field(None, max_length=20, description="WhatsApp business phone")
    
    # Google Business
    google_business_id: Optional[str] = Field(None, description="Google Business ID")
    google_reviews_url: Optional[HttpUrl] = Field(None, description="Google Reviews URL")


class RestaurantUpdate(BaseSchema):
    """Schema for updating restaurant information."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Restaurant name")
    name_arabic: Optional[str] = Field(None, max_length=200, description="Restaurant name in Arabic")
    description: Optional[str] = Field(None, description="Restaurant description")
    description_arabic: Optional[str] = Field(None, description="Restaurant description in Arabic")
    
    # Branding
    logo_url: Optional[str] = Field(None, max_length=500, description="Logo URL")
    persona: Optional[str] = Field(None, description="Restaurant communication persona/style")
    
    # Contact information
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")
    website_url: Optional[HttpUrl] = Field(None, description="Website URL")
    
    # Location
    address: Optional[str] = Field(None, description="Address")
    address_arabic: Optional[str] = Field(None, description="Address in Arabic")
    city: Optional[str] = Field(None, max_length=100, description="City")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    
    # Settings
    default_language: Optional[str] = Field(None, pattern="^(ar|en)$", description="Default language")
    timezone: Optional[str] = Field(None, description="Timezone")
    currency: Optional[str] = Field(None, max_length=3, description="Currency code")
    operating_hours: Optional[Dict[str, Any]] = Field(None, description="Operating hours")
    
    # AI settings
    ai_enabled: Optional[bool] = Field(None, description="AI enabled")
    sentiment_analysis_enabled: Optional[bool] = Field(None, description="Sentiment analysis enabled")
    auto_response_enabled: Optional[bool] = Field(None, description="Auto response enabled")
    response_time_target_hours: Optional[int] = Field(None, ge=1, description="Response time target")
    review_follow_up_enabled: Optional[bool] = Field(None, description="Review follow up enabled")
    
    # WhatsApp settings
    whatsapp_business_phone: Optional[str] = Field(None, max_length=20, description="WhatsApp business phone")
    whatsapp_active: Optional[bool] = Field(None, description="WhatsApp active status")
    
    # Message templates
    message_templates: Optional[Dict[str, Any]] = Field(None, description="Message templates")
    
    # Google Business
    google_business_id: Optional[str] = Field(None, description="Google Business ID")
    google_reviews_url: Optional[HttpUrl] = Field(None, description="Google Reviews URL")


class RestaurantResponse(BaseResponse):
    """Schema for restaurant response data."""
    
    name: str = Field(..., description="Restaurant name")
    name_arabic: Optional[str] = Field(None, description="Restaurant name in Arabic")
    description: Optional[str] = Field(None, description="Restaurant description")
    description_arabic: Optional[str] = Field(None, description="Restaurant description in Arabic")
    
    # Branding
    logo_url: Optional[str] = Field(None, description="Logo URL")
    persona: Optional[str] = Field(None, description="Restaurant communication persona/style")
    
    # Contact information
    phone_number: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    website_url: Optional[str] = Field(None, description="Website URL")
    
    # Location
    address: Optional[str] = Field(None, description="Address")
    address_arabic: Optional[str] = Field(None, description="Address in Arabic")
    city: Optional[str] = Field(None, description="City")
    country: str = Field(..., description="Country")
    postal_code: Optional[str] = Field(None, description="Postal code")
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")
    
    # Settings
    default_language: str = Field(..., description="Default language")
    timezone: str = Field(..., description="Timezone")
    currency: str = Field(..., description="Currency code")
    operating_hours: Optional[Dict[str, Any]] = Field(None, description="Operating hours")
    
    # AI settings
    ai_enabled: bool = Field(..., description="AI enabled")
    sentiment_analysis_enabled: bool = Field(..., description="Sentiment analysis enabled")
    auto_response_enabled: bool = Field(..., description="Auto response enabled")
    response_time_target_hours: int = Field(..., description="Response time target")
    review_follow_up_enabled: bool = Field(..., description="Review follow up enabled")
    
    # WhatsApp settings
    whatsapp_business_phone: Optional[str] = Field(None, description="WhatsApp business phone")
    whatsapp_verified: bool = Field(..., description="WhatsApp verified")
    whatsapp_active: bool = Field(..., description="WhatsApp active")
    is_whatsapp_configured: bool = Field(..., description="WhatsApp configured status")
    
    # Business metrics
    max_customers_per_month: int = Field(..., description="Max customers per month")
    current_month_customers: int = Field(..., description="Current month customers")
    subscription_active: bool = Field(..., description="Subscription active")
    subscription_expires_at: Optional[datetime] = Field(None, description="Subscription expiration")
    
    # Status
    is_active: bool = Field(..., description="Active status")
    is_featured: bool = Field(..., description="Featured status")
    can_send_messages: bool = Field(..., description="Can send messages status")
    is_open_now: bool = Field(..., description="Currently open status")
    
    # Google Business
    google_business_id: Optional[str] = Field(None, description="Google Business ID")
    google_reviews_url: Optional[str] = Field(None, description="Google Reviews URL")
    google_review_url: Optional[str] = Field(None, description="Generated Google Review URL")
    
    # Statistics
    staff_count: Optional[int] = Field(None, description="Number of staff members")
    customer_count: Optional[int] = Field(None, description="Total customers")


class RestaurantPublicResponse(BaseSchema):
    """Schema for public restaurant information."""
    
    id: UUID = Field(..., description="Restaurant ID")
    name: str = Field(..., description="Restaurant name")
    address: Optional[str] = Field(None, description="Address")
    phone_number: Optional[str] = Field(None, description="Phone number")
    website_url: Optional[str] = Field(None, description="Website URL")
    is_open_now: bool = Field(..., description="Currently open status")
    operating_hours: Optional[Dict[str, Any]] = Field(None, description="Operating hours")
    has_whatsapp: bool = Field(..., description="Has WhatsApp support")


class RestaurantSettings(BaseSchema):
    """Schema for restaurant settings update."""
    
    ai_enabled: Optional[bool] = Field(None, description="AI enabled")
    sentiment_analysis_enabled: Optional[bool] = Field(None, description="Sentiment analysis enabled")
    auto_response_enabled: Optional[bool] = Field(None, description="Auto response enabled")
    response_time_target_hours: Optional[int] = Field(None, ge=1, description="Response time target")
    review_follow_up_enabled: Optional[bool] = Field(None, description="Review follow up enabled")
    whatsapp_active: Optional[bool] = Field(None, description="WhatsApp active status")
    message_templates: Optional[Dict[str, Any]] = Field(None, description="Message templates")


class RestaurantStats(BaseSchema):
    """Schema for restaurant statistics."""
    
    restaurant_id: UUID = Field(..., description="Restaurant ID")
    total_customers: int = Field(..., description="Total customers")
    customers_this_month: int = Field(..., description="Customers this month")
    total_messages: int = Field(..., description="Total messages sent")
    messages_this_month: int = Field(..., description="Messages this month")
    average_rating: Optional[float] = Field(None, description="Average customer rating")
    response_rate: float = Field(..., description="Customer response rate")
    positive_feedback_rate: float = Field(..., description="Positive feedback rate")
    google_reviews_generated: int = Field(..., description="Google reviews generated")
    active_campaigns: int = Field(..., description="Active campaigns count")


class OperatingHours(BaseSchema):
    """Schema for operating hours."""
    
    monday: Optional[Dict[str, str]] = Field(None, description="Monday hours")
    tuesday: Optional[Dict[str, str]] = Field(None, description="Tuesday hours")
    wednesday: Optional[Dict[str, str]] = Field(None, description="Wednesday hours")
    thursday: Optional[Dict[str, str]] = Field(None, description="Thursday hours")
    friday: Optional[Dict[str, str]] = Field(None, description="Friday hours")
    saturday: Optional[Dict[str, str]] = Field(None, description="Saturday hours")
    sunday: Optional[Dict[str, str]] = Field(None, description="Sunday hours")


class RestaurantListFilter(BaseSchema):
    """Schema for filtering restaurant lists."""
    
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search term")
    city: Optional[str] = Field(None, description="Filter by city")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    has_whatsapp: Optional[bool] = Field(None, description="Filter by WhatsApp availability")
    ai_enabled: Optional[bool] = Field(None, description="Filter by AI enabled")
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")