"""
Restaurant model for managing restaurant information and settings.
Handles multi-location restaurant chains and individual restaurants.
"""
from typing import List, Optional, Dict, Any

from sqlalchemy import Column, String, Boolean, Text, JSON, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, LanguageChoice
from ..core.logging import get_logger

logger = get_logger(__name__)


class Restaurant(Base):
    """
    Restaurant model for managing restaurant information.
    Supports both single locations and multi-location chains.
    """
    
    __tablename__ = "restaurants"
    
    # Basic information
    name = Column(String(200), nullable=False, index=True)
    name_arabic = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    description_arabic = Column(Text, nullable=True)
    
    # Branding
    logo_url = Column(String(500), nullable=True)
    persona = Column(Text, nullable=True)  # Restaurant's communication persona/style
    
    # Contact information
    phone_number = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    website_url = Column(String(500), nullable=True)
    
    # Location
    address = Column(Text, nullable=True)
    address_arabic = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), default="Saudi Arabia", nullable=False)
    postal_code = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Business settings
    default_language = Column(String(5), default=LanguageChoice.ARABIC, nullable=False)
    timezone = Column(String(50), default="Asia/Riyadh", nullable=False)
    currency = Column(String(3), default="SAR", nullable=False)
    
    # Operating hours (JSON format)
    operating_hours = Column(JSON, nullable=True)  # {"monday": {"open": "09:00", "close": "23:00"}, ...}
    
    # WhatsApp settings
    whatsapp_business_phone = Column(String(20), nullable=True)
    whatsapp_verified = Column(Boolean, default=False, nullable=False)
    whatsapp_active = Column(Boolean, default=True, nullable=False)
    
    # AI settings
    ai_enabled = Column(Boolean, default=True, nullable=False)
    sentiment_analysis_enabled = Column(Boolean, default=True, nullable=False)
    auto_response_enabled = Column(Boolean, default=True, nullable=False)
    
    # Message templates (JSON format)
    message_templates = Column(JSON, nullable=True)
    
    # Business metrics settings
    response_time_target_hours = Column(Integer, default=24, nullable=False)
    review_follow_up_enabled = Column(Boolean, default=True, nullable=False)
    
    # Subscription and limits
    max_customers_per_month = Column(Integer, default=1000, nullable=False)
    current_month_customers = Column(Integer, default=0, nullable=False)
    subscription_active = Column(Boolean, default=True, nullable=False)
    subscription_expires_at = Column(DateTime, nullable=True)
    
    # Status and visibility
    is_active = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Google Business settings
    google_business_id = Column(String(255), nullable=True)
    google_reviews_url = Column(String(500), nullable=True)
    
    # Relationships
    staff_members = relationship("User", back_populates="restaurant")
    customers = relationship("Customer", back_populates="restaurant")
    whatsapp_messages = relationship("WhatsAppMessage", back_populates="restaurant")
    ai_interactions = relationship("AIInteraction", back_populates="restaurant")
    
    @property
    def display_name(self, language: str = None) -> str:
        """Get restaurant display name in specified language."""
        if language == LanguageChoice.ARABIC and self.name_arabic:
            return self.name_arabic
        return self.name
    
    @property
    def display_address(self, language: str = None) -> str:
        """Get restaurant address in specified language."""
        if language == LanguageChoice.ARABIC and self.address_arabic:
            return self.address_arabic
        return self.address or ""
    
    @property
    def has_location(self) -> bool:
        """Check if restaurant has location coordinates."""
        return self.latitude is not None and self.longitude is not None
    
    @property
    def is_whatsapp_configured(self) -> bool:
        """Check if WhatsApp is properly configured."""
        return (
            self.whatsapp_business_phone is not None and
            self.whatsapp_verified and
            self.whatsapp_active
        )
    
    @property
    def can_send_messages(self) -> bool:
        """Check if restaurant can send WhatsApp messages."""
        return (
            self.is_whatsapp_configured and
            self.subscription_active and
            self.current_month_customers < self.max_customers_per_month
        )
    
    def get_operating_hours_for_day(self, day: str) -> Optional[Dict[str, str]]:
        """Get operating hours for a specific day."""
        if not self.operating_hours:
            return None
        return self.operating_hours.get(day.lower())
    
    def is_open_now(self) -> bool:
        """Check if restaurant is currently open."""
        from datetime import datetime
        import pytz
        
        # Get current time in restaurant timezone
        tz = pytz.timezone(self.timezone)
        current_time = datetime.now(tz)
        current_day = current_time.strftime("%A").lower()
        
        hours = self.get_operating_hours_for_day(current_day)
        if not hours:
            return False
        
        open_time = datetime.strptime(hours["open"], "%H:%M").time()
        close_time = datetime.strptime(hours["close"], "%H:%M").time()
        current_time_only = current_time.time()
        
        if close_time < open_time:  # Crosses midnight
            return current_time_only >= open_time or current_time_only <= close_time
        else:
            return open_time <= current_time_only <= close_time
    
    def get_default_message_template(self, template_type: str, language: str = None) -> Optional[str]:
        """Get default message template for a specific type and language."""
        if not self.message_templates:
            return None
        
        lang = language or self.default_language
        templates = self.message_templates.get(lang, {})
        return templates.get(template_type)
    
    def increment_monthly_customers(self) -> bool:
        """Increment monthly customer count and check limits."""
        if self.current_month_customers >= self.max_customers_per_month:
            logger.warning(f"Restaurant {self.id} reached monthly customer limit")
            return False
        
        self.current_month_customers += 1
        logger.info(f"Restaurant {self.id} monthly customers: {self.current_month_customers}")
        return True
    
    def reset_monthly_counters(self):
        """Reset monthly counters (called by scheduled task)."""
        self.current_month_customers = 0
        logger.info(f"Reset monthly counters for restaurant {self.id}")
    
    def get_google_review_url(self) -> Optional[str]:
        """Generate Google review URL for this restaurant."""
        if self.google_business_id:
            return f"https://search.google.com/local/writereview?placeid={self.google_business_id}"
        return self.google_reviews_url
    
    def to_dict_public(self, language: str = None) -> Dict[str, Any]:
        """Get public information about the restaurant."""
        return {
            "id": str(self.id),
            "name": self.display_name(language),
            "address": self.display_address(language),
            "phone_number": self.phone_number,
            "website_url": self.website_url,
            "is_open_now": self.is_open_now(),
            "operating_hours": self.operating_hours,
            "has_whatsapp": self.is_whatsapp_configured
        }
    
    def __repr__(self) -> str:
        """String representation of restaurant."""
        return f"<Restaurant(name={self.name}, city={self.city}, active={self.is_active})>"