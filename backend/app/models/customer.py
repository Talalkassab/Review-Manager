"""
Customer model for managing restaurant customer information and interactions.
Tracks visits, communications, and feedback.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, LanguageChoice, CustomerStatusChoice, SentimentChoice
from ..core.logging import get_logger

logger = get_logger(__name__)


class Customer(Base):
    """
    Customer model for tracking restaurant customers and their interactions.
    Manages contact information, visit history, and feedback.
    """
    
    __tablename__ = "customers"
    
    # Basic information
    customer_number = Column(String(50), nullable=False, index=True)  # Primary identifier
    first_name = Column(String(100), nullable=True)  # Now optional
    last_name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    
    # Language and communication preferences
    preferred_language = Column(String(5), default=LanguageChoice.ARABIC, nullable=False)
    whatsapp_opt_in = Column(Boolean, default=True, nullable=False)
    email_opt_in = Column(Boolean, default=True, nullable=False)
    
    # Visit information
    visit_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    table_number = Column(String(10), nullable=True)
    server_name = Column(String(100), nullable=True)
    party_size = Column(Integer, default=1, nullable=False)
    
    # Order information (optional)
    order_details = Column(JSON, nullable=True)  # {"items": [...], "total": 150.00, "notes": "..."}
    order_total = Column(Float, nullable=True)
    special_requests = Column(Text, nullable=True)
    
    # Communication status
    status = Column(String(20), default=CustomerStatusChoice.PENDING, nullable=False, index=True)
    last_contacted_at = Column(DateTime, nullable=True)
    contact_attempts = Column(Integer, default=0, nullable=False)
    max_contact_attempts = Column(Integer, default=3, nullable=False)
    
    # Feedback information
    feedback_received_at = Column(DateTime, nullable=True)
    feedback_text = Column(Text, nullable=True)
    feedback_sentiment = Column(String(10), nullable=True)  # positive, negative, neutral
    feedback_confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Rating (1-5 stars equivalent)
    rating = Column(Integer, nullable=True)  # 1, 2, 3, 4, 5
    
    # Review tracking
    google_review_requested_at = Column(DateTime, nullable=True)
    google_review_link_sent = Column(Boolean, default=False, nullable=False)
    google_review_completed = Column(Boolean, default=False, nullable=False)
    google_review_url = Column(String(500), nullable=True)
    
    # Follow-up and resolution
    requires_follow_up = Column(Boolean, default=False, nullable=False)
    follow_up_notes = Column(Text, nullable=True)
    issue_resolved = Column(Boolean, default=True, nullable=False)
    resolution_notes = Column(Text, nullable=True)
    
    # Customer metadata
    is_repeat_customer = Column(Boolean, default=False, nullable=False)
    visit_count = Column(Integer, default=1, nullable=False)
    first_visit_date = Column(DateTime, nullable=True)
    last_visit_date = Column(DateTime, nullable=True)
    
    # Privacy and GDPR
    data_retention_date = Column(DateTime, nullable=True)  # When to delete customer data
    gdpr_consent = Column(Boolean, default=True, nullable=False)
    
    # Foreign keys
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="customers")
    created_by_user = relationship("User", foreign_keys=[created_by], back_populates="created_customers")
    whatsapp_messages = relationship("WhatsAppMessage", back_populates="customer")
    ai_interactions = relationship("AIInteraction", back_populates="customer")
    
    @property
    def full_name(self) -> str:
        """Get customer's full name."""
        if not self.first_name:
            return f"Customer #{self.customer_number}"
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    
    @property
    def display_name(self) -> str:
        """Get customer's display name with language support."""
        if not self.first_name:
            if self.preferred_language == LanguageChoice.ARABIC:
                return f"العميل #{self.customer_number}"
            return f"Customer #{self.customer_number}"
        if self.preferred_language == LanguageChoice.ARABIC and self.last_name:
            return f"{self.last_name} {self.first_name}"
        return self.full_name
    
    @property
    def masked_phone_number(self) -> str:
        """Get masked phone number for privacy."""
        if len(self.phone_number) > 6:
            return self.phone_number[:3] + "*" * (len(self.phone_number) - 6) + self.phone_number[-3:]
        return "*" * len(self.phone_number)
    
    @property
    def is_pending_contact(self) -> bool:
        """Check if customer is pending initial contact."""
        return self.status == CustomerStatusChoice.PENDING
    
    @property
    def is_contacted(self) -> bool:
        """Check if customer has been contacted."""
        return self.status in [CustomerStatusChoice.CONTACTED, CustomerStatusChoice.RESPONDED, CustomerStatusChoice.COMPLETED]
    
    @property
    def has_responded(self) -> bool:
        """Check if customer has provided feedback."""
        return self.status in [CustomerStatusChoice.RESPONDED, CustomerStatusChoice.COMPLETED]
    
    @property
    def is_completed(self) -> bool:
        """Check if customer interaction is completed."""
        return self.status == CustomerStatusChoice.COMPLETED
    
    @property
    def can_be_contacted(self) -> bool:
        """Check if customer can be contacted again."""
        if not self.whatsapp_opt_in:
            return False
        if self.contact_attempts >= self.max_contact_attempts:
            return False
        if self.status in [CustomerStatusChoice.COMPLETED, CustomerStatusChoice.FAILED]:
            return False
        return True
    
    @property
    def time_since_visit_hours(self) -> float:
        """Get hours since customer visit."""
        return (datetime.utcnow() - self.visit_date).total_seconds() / 3600
    
    @property
    def is_recent_visit(self, hours: int = 48) -> bool:
        """Check if visit was recent (within specified hours)."""
        return self.time_since_visit_hours <= hours
    
    @property
    def sentiment_emoji(self) -> str:
        """Get emoji representation of sentiment."""
        if self.feedback_sentiment == SentimentChoice.POSITIVE:
            return "😊"
        elif self.feedback_sentiment == SentimentChoice.NEGATIVE:
            return "😞"
        elif self.feedback_sentiment == SentimentChoice.NEUTRAL:
            return "😐"
        return "❓"
    
    def record_contact_attempt(self):
        """Record a contact attempt."""
        self.contact_attempts += 1
        self.last_contacted_at = datetime.utcnow()
        if self.status == CustomerStatusChoice.PENDING:
            self.status = CustomerStatusChoice.CONTACTED
        logger.info(f"Contact attempt recorded for customer {self.id}: {self.contact_attempts}")
    
    def record_feedback(self, feedback_text: str, sentiment: str = None, 
                       confidence_score: float = None, rating: int = None):
        """Record customer feedback."""
        self.feedback_text = feedback_text
        self.feedback_sentiment = sentiment
        self.feedback_confidence_score = confidence_score
        self.rating = rating
        self.feedback_received_at = datetime.utcnow()
        self.status = CustomerStatusChoice.RESPONDED
        
        # Determine if follow-up is needed
        if sentiment == SentimentChoice.NEGATIVE or (rating and rating <= 2):
            self.requires_follow_up = True
            self.issue_resolved = False
        
        logger.info(f"Feedback recorded for customer {self.id}: sentiment={sentiment}, rating={rating}")
    
    def mark_completed(self, notes: str = None):
        """Mark customer interaction as completed."""
        self.status = CustomerStatusChoice.COMPLETED
        if notes:
            self.resolution_notes = notes
        logger.info(f"Customer interaction completed: {self.id}")
    
    def mark_failed(self, reason: str = None):
        """Mark customer interaction as failed."""
        self.status = CustomerStatusChoice.FAILED
        if reason:
            self.follow_up_notes = f"Failed: {reason}"
        logger.warning(f"Customer interaction failed: {self.id}, reason: {reason}")
    
    def request_google_review(self) -> bool:
        """Mark that Google review was requested."""
        if self.feedback_sentiment != SentimentChoice.POSITIVE:
            logger.warning(f"Google review requested for non-positive feedback: {self.id}")
            return False
        
        self.google_review_requested_at = datetime.utcnow()
        self.google_review_link_sent = True
        logger.info(f"Google review requested for customer {self.id}")
        return True
    
    def mark_google_review_completed(self, review_url: str = None):
        """Mark Google review as completed."""
        self.google_review_completed = True
        if review_url:
            self.google_review_url = review_url
        logger.info(f"Google review completed for customer {self.id}")
    
    def should_be_deleted(self, retention_days: int = 365) -> bool:
        """Check if customer data should be deleted for GDPR compliance."""
        if not self.gdpr_consent:
            return True
        if self.data_retention_date and datetime.utcnow() > self.data_retention_date:
            return True
        if self.visit_date < datetime.utcnow() - timedelta(days=retention_days):
            return True
        return False
    
    def update_visit_history(self):
        """Update visit history for repeat customers."""
        # This would be called when creating a new visit for existing customer
        self.visit_count += 1
        self.last_visit_date = self.visit_date
        self.is_repeat_customer = True
        if not self.first_visit_date:
            self.first_visit_date = self.visit_date
    
    def get_greeting(self) -> str:
        """Get appropriate greeting for the customer."""
        if self.first_name and self.first_name.strip():
            if self.preferred_language == LanguageChoice.ARABIC:
                return f"مرحباً {self.first_name}"
            return f"Hello {self.first_name}"
        else:
            if self.preferred_language == LanguageChoice.ARABIC:
                return "عزيزنا العميل"
            return "Dear Customer"
    
    def get_interaction_summary(self) -> Dict[str, Any]:
        """Get summary of customer interactions."""
        return {
            "customer_id": str(self.id),
            "name": self.display_name,
            "phone": self.masked_phone_number,
            "visit_date": self.visit_date.isoformat(),
            "status": self.status,
            "contact_attempts": self.contact_attempts,
            "has_feedback": self.feedback_text is not None,
            "sentiment": self.feedback_sentiment,
            "rating": self.rating,
            "requires_follow_up": self.requires_follow_up,
            "google_review_sent": self.google_review_link_sent,
            "google_review_completed": self.google_review_completed
        }
    
    def __repr__(self) -> str:
        """String representation of customer."""
        return f"<Customer(number={self.customer_number}, name={self.full_name}, phone={self.masked_phone_number}, status={self.status})>"