"""
Authentication Models
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """Request model for user signup."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)


class LoginRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Response model for auth operations."""
    user: "UserResponse"
    workspace_id: str
    message: str = "Success"


class UserResponse(BaseModel):
    """User data in responses."""
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str = "user"
    workspace_id: Optional[str] = None
    created_at: Optional[datetime] = None


class UserProfile(BaseModel):
    """Full user profile."""
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    workspace_id: str
    role: str = "user"
    subscription_status: Optional[str] = None
    plan_type: Optional[str] = None
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    """Request to update user profile."""
    full_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Request to change password."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class ResetPasswordRequest(BaseModel):
    """Request to reset password (forgot password)."""
    email: EmailStr


class GoogleAuthRequest(BaseModel):
    """Request for Google OAuth callback."""
    access_token: str


# Forward reference resolution
AuthResponse.model_rebuild()
