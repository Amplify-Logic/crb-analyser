"""
Pydantic Schemas for AI Pulse
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

from .enums import (
    SourceType,
    ContentType,
    Category,
    SubscriptionStatus,
    PreferredTime,
    DigestSendStatus,
)


# ============================================================================
# User Schemas
# ============================================================================

class UserCreate(BaseModel):
    """Create user request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None
    timezone: str = "UTC"
    preferred_time: PreferredTime = PreferredTime.LUNCH


class UserUpdate(BaseModel):
    """Update user request."""
    name: Optional[str] = None
    timezone: Optional[str] = None
    preferred_time: Optional[PreferredTime] = None


class UserPreferences(BaseModel):
    """User preferences update."""
    timezone: Optional[str] = None
    preferred_time: Optional[PreferredTime] = None


class UserResponse(BaseModel):
    """User response."""
    id: str
    email: str
    name: Optional[str] = None
    timezone: str
    preferred_time: PreferredTime
    subscription_status: SubscriptionStatus
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Auth Schemas
# ============================================================================

class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    """Signup request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None
    timezone: str = "UTC"
    preferred_time: PreferredTime = PreferredTime.LUNCH


class AuthResponse(BaseModel):
    """Auth response."""
    user: UserResponse
    message: str = "Success"


# ============================================================================
# Article Schemas
# ============================================================================

class ArticleCreate(BaseModel):
    """Create article (internal use by scrapers)."""
    source_id: str
    external_id: str
    content_type: ContentType
    title: str
    description: Optional[str] = None
    url: str
    thumbnail_url: Optional[str] = None
    published_at: datetime
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None


class ArticleResponse(BaseModel):
    """Article response."""
    id: str
    source_name: str
    source_type: SourceType
    content_type: ContentType
    title: str
    description: Optional[str] = None
    url: str
    thumbnail_url: Optional[str] = None
    published_at: datetime
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    score: float
    summary: Optional[str] = None
    categories: List[str] = []

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    """Paginated article list response."""
    data: List[ArticleResponse]
    total: int
    page: int
    per_page: int
    has_more: bool


# ============================================================================
# Source Schemas
# ============================================================================

class SourceResponse(BaseModel):
    """Source response."""
    slug: str
    name: str
    source_type: SourceType
    url: str
    category: Category
    priority: int
    description: Optional[str] = None
    enabled: bool = True

    class Config:
        from_attributes = True


# ============================================================================
# Digest Schemas
# ============================================================================

class DigestResponse(BaseModel):
    """Digest response."""
    id: str
    created_at: datetime
    subject_line: str
    articles: List[ArticleResponse]
    stats: dict  # {sources_checked, items_found, items_selected}

    class Config:
        from_attributes = True


class DigestListResponse(BaseModel):
    """Paginated digest list response."""
    data: List[DigestResponse]
    total: int
    page: int
    per_page: int
    has_more: bool


# ============================================================================
# Checkout Schemas
# ============================================================================

class CheckoutRequest(BaseModel):
    """Checkout request."""
    plan: str = "monthly"  # monthly, annual
    currency: str = "USD"  # USD, EUR
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutResponse(BaseModel):
    """Checkout response."""
    checkout_url: str
    session_id: str


# ============================================================================
# Admin Schemas
# ============================================================================

class AdminStatsResponse(BaseModel):
    """Admin stats response."""
    total_users: int
    active_subscribers: int
    total_articles: int
    articles_today: int
    digests_sent_today: int
    open_rate: float  # percentage
