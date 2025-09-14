"""
Authentication schemas for request/response models.
"""
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    """JWT token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token."""
    refresh_token: str


class LoginRequest(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserProfileResponse(BaseModel):
    """User profile information response."""
    id: str
    email: str
    full_name: str
    role: str
    restaurant_id: Optional[str] = None
    is_active: bool
    is_verified: bool
    permissions: List[str]
    last_login_at: Optional[str] = None

    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

    def validate_passwords_match(self):
        """Validate that new passwords match."""
        if self.new_password != self.confirm_password:
            raise ValueError("New passwords do not match")
        return self


class TokenVerificationResponse(BaseModel):
    """Token verification response."""
    valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None