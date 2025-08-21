"""
User-related Pydantic schemas for authentication and user management.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import Field, EmailStr

from .base import BaseSchema, BaseResponse


class UserCreate(BaseSchema):
    """Schema for creating a new user."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    preferred_language: str = Field("ar", pattern="^(ar|en)$", description="Preferred language")
    role: str = Field("view_only", description="User role")
    restaurant_id: Optional[UUID] = Field(None, description="Restaurant ID")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")


class UserUpdate(BaseSchema):
    """Schema for updating user information."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Last name")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    preferred_language: Optional[str] = Field(None, pattern="^(ar|en)$", description="Preferred language")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar URL")


class UserResponse(BaseResponse):
    """Schema for user response data."""
    
    email: EmailStr = Field(..., description="User email address")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    phone_number: Optional[str] = Field(None, description="Phone number")
    preferred_language: str = Field(..., description="Preferred language")
    role: str = Field(..., description="User role")
    restaurant_id: Optional[UUID] = Field(None, description="Restaurant ID")
    is_active: bool = Field(..., description="Account active status")
    is_verified: bool = Field(..., description="Email verification status")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    login_count: str = Field(..., description="Login count")
    bio: Optional[str] = Field(None, description="User bio")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    full_name: str = Field(..., description="Full name")
    display_name: str = Field(..., description="Display name")
    permissions: List[str] = Field(..., description="User permissions")


class UserLogin(BaseSchema):
    """Schema for user login request."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(False, description="Remember login")


class UserLoginResponse(BaseSchema):
    """Schema for login response."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: UserResponse = Field(..., description="User information")


class TokenResponse(BaseSchema):
    """Schema for token response."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token") 
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class PasswordChangeRequest(BaseSchema):
    """Schema for password change request."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")


class PasswordResetRequest(BaseSchema):
    """Schema for password reset request."""
    
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseSchema):
    """Schema for password reset confirmation."""
    
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")


class EmailVerificationRequest(BaseSchema):
    """Schema for email verification request."""
    
    email: EmailStr = Field(..., description="Email to verify")


class EmailVerificationConfirm(BaseSchema):
    """Schema for email verification confirmation."""
    
    token: str = Field(..., description="Verification token")


class UserProfileUpdate(BaseSchema):
    """Schema for user profile updates."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Last name")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    preferred_language: Optional[str] = Field(None, pattern="^(ar|en)$", description="Preferred language")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")


class UserRoleUpdate(BaseSchema):
    """Schema for updating user role (admin only)."""
    
    role: str = Field(..., description="New user role")
    restaurant_id: Optional[UUID] = Field(None, description="Restaurant ID")


class UserPermissionsResponse(BaseSchema):
    """Schema for user permissions response."""
    
    user_id: UUID = Field(..., description="User ID")
    permissions: List[str] = Field(..., description="User permissions")
    role: str = Field(..., description="User role")
    can_manage_users: bool = Field(..., description="Can manage users")
    can_manage_customers: bool = Field(..., description="Can manage customers")
    can_view_analytics: bool = Field(..., description="Can view analytics")
    can_access_ai: bool = Field(..., description="Can access AI features")


class UserActivitySummary(BaseSchema):
    """Schema for user activity summary."""
    
    user_id: UUID = Field(..., description="User ID")
    login_count: int = Field(..., description="Total logins")
    last_login_at: Optional[datetime] = Field(None, description="Last login")
    customers_created: int = Field(..., description="Customers created count")
    messages_sent: int = Field(..., description="Messages sent count")
    campaigns_created: int = Field(..., description="Campaigns created count")
    activity_score: float = Field(..., description="Activity score (0-100)")


class UserListFilter(BaseSchema):
    """Schema for filtering user lists."""
    
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search term")
    role: Optional[str] = Field(None, description="Filter by role")
    restaurant_id: Optional[UUID] = Field(None, description="Filter by restaurant")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")