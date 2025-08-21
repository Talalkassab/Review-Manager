"""
Customer model for contact management.
"""

from typing import Optional, List
from sqlalchemy import Column, String, Boolean, Text, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import BaseModel


class Customer(BaseModel):
    """Customer model for managing restaurant customer contacts and preferences."""
    
    __tablename__ = "customers"
    
    # Basic Information
    phone_number = Column(String(20), unique=True, index=True, nullable=False)  # E.164 format
    whatsapp_id = Column(String(50), unique=True, index=True, nullable=True)  # WhatsApp user ID
    name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    
    # Preferences
    preferred_language = Column(String(2), default="ar", nullable=False)  # ISO 639-1 codes (ar, en)
    timezone = Column(String(50), default="Asia/Riyadh", nullable=False)
    
    # WhatsApp specific settings
    whatsapp_opt_in = Column(Boolean, default=True, nullable=False)  # Consent for WhatsApp messaging
    marketing_opt_in = Column(Boolean, default=False, nullable=False)  # Marketing messages consent
    
    # Customer profile data
    dietary_preferences = Column(JSON, nullable=True)  # Vegetarian, halal, allergies, etc.
    favorite_dishes = Column(JSON, nullable=True)  # Array of favorite menu items
    visit_frequency = Column(String(20), nullable=True)  # weekly, monthly, occasional
    average_order_value = Column(String(20), nullable=True)  # low, medium, high
    
    # Contact history and status
    last_message_at = Column(String(50), nullable=True)  # ISO datetime string
    total_messages_sent = Column(String(10), default="0", nullable=False)
    total_messages_received = Column(String(10), default="0", nullable=False)
    
    # Customer satisfaction tracking
    last_feedback_score = Column(String(5), nullable=True)  # 1-10 scale
    feedback_count = Column(String(10), default="0", nullable=False)
    average_satisfaction = Column(String(5), nullable=True)  # Calculated average
    
    # Notes and tags
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of custom tags
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)  # Blocked from messaging
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_customer_phone', 'phone_number'),
        Index('idx_customer_whatsapp', 'whatsapp_id'),
        Index('idx_customer_active', 'is_active'),
        Index('idx_customer_language', 'preferred_language'),
    )
    
    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, phone={self.phone_number}, name={self.name})>"
    
    def to_dict(self) -> dict:
        """Convert customer to dictionary with safe data types."""
        data = super().to_dict()
        
        # Convert JSON fields safely
        if self.dietary_preferences:
            data['dietary_preferences'] = self.dietary_preferences
        if self.favorite_dishes:
            data['favorite_dishes'] = self.favorite_dishes
        if self.tags:
            data['tags'] = self.tags
            
        return data
    
    def get_display_name(self) -> str:
        """Get customer display name or fallback to phone number."""
        return self.name or self.phone_number
    
    def can_receive_marketing(self) -> bool:
        """Check if customer can receive marketing messages."""
        return self.is_active and not self.is_blocked and self.marketing_opt_in
    
    def can_receive_messages(self) -> bool:
        """Check if customer can receive any WhatsApp messages."""
        return self.is_active and not self.is_blocked and self.whatsapp_opt_in
    
    def increment_messages_sent(self) -> None:
        """Increment the sent message counter."""
        current = int(self.total_messages_sent) if self.total_messages_sent.isdigit() else 0
        self.total_messages_sent = str(current + 1)
    
    def increment_messages_received(self) -> None:
        """Increment the received message counter."""
        current = int(self.total_messages_received) if self.total_messages_received.isdigit() else 0
        self.total_messages_received = str(current + 1)
    
    def update_feedback_score(self, score: int) -> None:
        """Update customer feedback score and calculate new average."""
        if not (1 <= score <= 10):
            raise ValueError("Feedback score must be between 1 and 10")
        
        self.last_feedback_score = str(score)
        feedback_count = int(self.feedback_count) if self.feedback_count.isdigit() else 0
        
        if self.average_satisfaction and self.average_satisfaction.replace('.', '').isdigit():
            current_avg = float(self.average_satisfaction)
            new_avg = ((current_avg * feedback_count) + score) / (feedback_count + 1)
        else:
            new_avg = float(score)
        
        self.average_satisfaction = f"{new_avg:.1f}"
        self.feedback_count = str(feedback_count + 1)
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to customer."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from customer."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def has_tag(self, tag: str) -> bool:
        """Check if customer has a specific tag."""
        return self.tags and tag in self.tags