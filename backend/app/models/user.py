"""
User model for authentication and authorization.
Manages restaurant staff accounts and permissions.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID

from .base import Base, UserRoleChoice
from ..core.logging import get_logger

logger = get_logger(__name__)


class User(SQLAlchemyBaseUserTableUUID, Base):
    """
    User model for restaurant staff authentication.
    Extends FastAPI-Users base model with custom fields.
    """
    
    __tablename__ = "users"
    
    # Basic info
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=True)
    preferred_language = Column(String(5), default="ar", nullable=False)
    
    # Role and permissions  
    role = Column(Enum(UserRoleChoice.SUPER_ADMIN, UserRoleChoice.RESTAURANT_OWNER, 
                      UserRoleChoice.MANAGER, UserRoleChoice.SERVER, UserRoleChoice.VIEW_ONLY, 
                      name='user_roles'), default=UserRoleChoice.VIEW_ONLY, nullable=False)
    
    # Restaurant association
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Login tracking
    last_login_at = Column(DateTime, nullable=True)
    login_count = Column(String, default="0", nullable=False)
    
    # Profile info
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="staff_members")
    created_customers = relationship(
        "Customer", 
        foreign_keys="Customer.created_by",
        back_populates="created_by_user"
    )
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self) -> str:
        """Get user's display name with Arabic/English support."""
        if self.preferred_language == "ar":
            return f"{self.last_name} {self.first_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_restaurant_owner(self) -> bool:
        """Check if user is a restaurant owner."""
        return self.role == UserRoleChoice.RESTAURANT_OWNER
    
    @property
    def is_manager(self) -> bool:
        """Check if user is a manager or higher."""
        return self.role in [UserRoleChoice.RESTAURANT_OWNER, UserRoleChoice.MANAGER]
    
    @property
    def can_manage_customers(self) -> bool:
        """Check if user can manage customer data."""
        return self.role in [
            UserRoleChoice.SUPER_ADMIN,
            UserRoleChoice.RESTAURANT_OWNER, 
            UserRoleChoice.MANAGER,
            UserRoleChoice.SERVER
        ]
    
    @property
    def can_view_analytics(self) -> bool:
        """Check if user can view analytics."""
        return self.role in [
            UserRoleChoice.SUPER_ADMIN,
            UserRoleChoice.RESTAURANT_OWNER,
            UserRoleChoice.MANAGER
        ]
    
    def record_login(self):
        """Record user login activity."""
        self.last_login_at = datetime.utcnow()
        self.login_count = str(int(self.login_count) + 1)
        logger.info(f"User login recorded: {self.email}")
    
    def can_access_restaurant(self, restaurant_id: str) -> bool:
        """Check if user can access a specific restaurant."""
        if self.is_superuser:
            return True
        return str(self.restaurant_id) == restaurant_id if self.restaurant_id else False
    
    def get_permissions(self) -> List[str]:
        """Get list of user permissions based on role."""
        permissions = []
        
        if self.role == UserRoleChoice.SUPER_ADMIN:
            return ["*"]  # All permissions
        
        if self.role == UserRoleChoice.RESTAURANT_OWNER:
            permissions.extend([
                "restaurant.manage",
                "customers.create", "customers.read", "customers.update", "customers.delete",
                "analytics.read", "analytics.export",
                "users.create", "users.read", "users.update",
                "settings.update",
                "ai.interact"
            ])
        
        elif self.role == UserRoleChoice.MANAGER:
            permissions.extend([
                "customers.create", "customers.read", "customers.update",
                "analytics.read", "analytics.export", 
                "users.read",
                "ai.interact"
            ])
        
        elif self.role == UserRoleChoice.SERVER:
            permissions.extend([
                "customers.create", "customers.read", "customers.update",
                "ai.interact"
            ])
        
        elif self.role == UserRoleChoice.VIEW_ONLY:
            permissions.extend([
                "customers.read"
            ])
        
        return permissions
    
    def __repr__(self) -> str:
        """String representation of user."""
        return f"<User(email={self.email}, role={self.role}, restaurant_id={self.restaurant_id})>"