"""
Schemas for the vendor research agent.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RefreshScope(str, Enum):
    """Scope for refresh operations."""
    STALE = "stale"
    ALL = "all"
    SPECIFIC = "specific"


class TaskStatus(str, Enum):
    """Status of a research task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Pricing Extraction
# ============================================================================

class PricingTier(BaseModel):
    """A single pricing tier extracted from vendor website."""
    name: str = Field(description="Tier name (e.g., 'Starter', 'Professional')")
    price: Optional[float] = Field(default=None, description="Monthly price, null if custom/enterprise")
    price_annual: Optional[float] = Field(default=None, description="Annual price per month if different")
    billing: Optional[str] = Field(default=None, description="Billing period: 'monthly', 'annual', 'one-time'")
    features: list[str] = Field(default_factory=list, description="Key features included")


class ExtractedPricing(BaseModel):
    """Pricing data extracted from a vendor website."""
    vendor_name: str
    pricing_model: Optional[str] = Field(default=None, description="subscription, usage, one-time, freemium")
    currency: str = Field(default="USD")
    free_tier: Optional[bool] = None
    free_trial_days: Optional[int] = None
    tiers: list[PricingTier] = Field(default_factory=list)
    enterprise_available: Optional[bool] = None
    starting_price: Optional[float] = None
    notes: Optional[str] = None


# ============================================================================
# Vendor Changes
# ============================================================================

class FieldChange(BaseModel):
    """A single field change detected during refresh."""
    field: str
    old_value: Optional[str | int | float | bool | list] = None
    new_value: Optional[str | int | float | bool | list] = None
    is_significant: bool = False  # True for large price changes, etc.


class VendorUpdate(BaseModel):
    """Update detected for a single vendor."""
    vendor_slug: str
    vendor_name: str
    source_url: str
    changes: list[FieldChange] = Field(default_factory=list)
    extracted_data: Optional[ExtractedPricing] = None
    error: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Discovery
# ============================================================================

class DiscoveredVendor(BaseModel):
    """A new vendor discovered during search."""
    name: str
    slug: str
    website: str
    description: Optional[str] = None
    category: Optional[str] = None
    sources: list[str] = Field(default_factory=list, description="Where this vendor was found")
    g2_score: Optional[float] = None
    relevance_score: float = Field(default=0.5, description="0-1 relevance to search criteria")
    pricing: Optional[ExtractedPricing] = None
    warning: Optional[str] = None  # e.g., "Low relevance", "Overlap with existing"


# ============================================================================
# Task Tracking
# ============================================================================

class ResearchTask(BaseModel):
    """A research task (refresh, discover, or scout)."""
    task_id: str
    task_type: str  # "refresh", "discover", "scout"
    status: TaskStatus = TaskStatus.PENDING
    category: Optional[str] = None
    industry: Optional[str] = None
    vendor_slugs: list[str] = Field(default_factory=list)

    # Progress
    total_items: int = 0
    processed_items: int = 0
    current_item: Optional[str] = None

    # Results
    updates: list[VendorUpdate] = Field(default_factory=list)
    discoveries: list[DiscoveredVendor] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ============================================================================
# API Request/Response
# ============================================================================

class RefreshRequest(BaseModel):
    """Request to refresh vendor data."""
    scope: RefreshScope = RefreshScope.STALE
    vendor_slugs: list[str] = Field(default_factory=list)
    category: Optional[str] = None
    industry: Optional[str] = None
    dry_run: bool = False


class DiscoverRequest(BaseModel):
    """Request to discover new vendors."""
    category: str
    industry: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=50)


class ApplyRequest(BaseModel):
    """Request to apply approved changes."""
    task_id: str
    approved_slugs: list[str]


class TaskResponse(BaseModel):
    """Response containing task info."""
    task_id: str
    status: TaskStatus
    message: str
