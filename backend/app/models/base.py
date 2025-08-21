"""
Base database models and common functionality.
Provides shared model behaviors and utilities.
"""
import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr

from ..core.logging import get_logger

logger = get_logger(__name__)


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UUIDMixin:
    """Mixin for UUID primary key."""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    def soft_delete(self):
        """Mark the record as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        logger.info(f"Soft deleted {self.__class__.__name__} with id: {self.id}")
    
    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        logger.info(f"Restored {self.__class__.__name__} with id: {self.id}")


class AuditMixin:
    """Mixin for audit trail functionality."""
    
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    
    @declared_attr
    def created_by_user(cls):
        """Relationship to the user who created this record."""
        return cls.metadata.tables.get('users')  # Will be defined later
    
    @declared_attr  
    def updated_by_user(cls):
        """Relationship to the user who last updated this record."""
        return cls.metadata.tables.get('users')  # Will be defined later


class BaseModel(UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    Base model class with common functionality.
    All models should inherit from this class.
    """
    
    def to_dict(self, exclude_none: bool = True) -> Dict[str, Any]:
        """Convert model to dictionary representation."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if exclude_none and value is None:
                continue
            # Convert datetime to ISO string
            if isinstance(value, datetime):
                value = value.isoformat()
            # Convert UUID to string
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude_keys: list = None) -> None:
        """Update model attributes from dictionary."""
        exclude_keys = exclude_keys or ['id', 'created_at', 'updated_at']
        
        for key, value in data.items():
            if key in exclude_keys:
                continue
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"Updated {self.__class__.__name__}.{key} to {value}")
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


# Create the base class
Base = declarative_base(cls=BaseModel)


class LanguageChoice:
    """Language choices for the application."""
    ARABIC = "ar"
    ENGLISH = "en"
    
    CHOICES = [
        (ARABIC, "Arabic"),
        (ENGLISH, "English")
    ]


class SentimentChoice:
    """Sentiment analysis choices."""
    POSITIVE = "positive"
    NEGATIVE = "negative" 
    NEUTRAL = "neutral"
    
    CHOICES = [
        (POSITIVE, "Positive"),
        (NEGATIVE, "Negative"),
        (NEUTRAL, "Neutral")
    ]


class CustomerStatusChoice:
    """Customer interaction status choices."""
    PENDING = "pending"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    COMPLETED = "completed"
    FAILED = "failed"
    
    CHOICES = [
        (PENDING, "Pending"),
        (CONTACTED, "Contacted"), 
        (RESPONDED, "Responded"),
        (COMPLETED, "Completed"),
        (FAILED, "Failed")
    ]


class MessageStatusChoice:
    """WhatsApp message status choices."""
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    
    CHOICES = [
        (QUEUED, "Queued"),
        (SENT, "Sent"),
        (DELIVERED, "Delivered"),
        (READ, "Read"),
        (FAILED, "Failed")
    ]


class UserRoleChoice:
    """User role choices."""
    SUPER_ADMIN = "super_admin"
    RESTAURANT_OWNER = "restaurant_owner"
    MANAGER = "manager"
    SERVER = "server"
    VIEW_ONLY = "view_only"
    
    CHOICES = [
        (SUPER_ADMIN, "Super Admin"),
        (RESTAURANT_OWNER, "Restaurant Owner"),
        (MANAGER, "Manager"),
        (SERVER, "Server"),
        (VIEW_ONLY, "View Only")
    ]