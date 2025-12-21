"""
Vendor Models

Pydantic models for vendor data.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel


class VendorPricingTier(BaseModel):
    """A pricing tier for a vendor."""
    name: str
    price: float
    per: Optional[str] = None  # "month", "user/month", "year"
    features: Optional[List[str]] = None
    limits: Optional[str] = None


class VendorPricing(BaseModel):
    """Vendor pricing information."""
    model: str  # "per_seat", "flat", "usage", "custom"
    currency: str = "EUR"
    tiers: List[VendorPricingTier] = []
    custom_pricing: bool = False
    free_trial_days: Optional[int] = None
    pricing_url: Optional[str] = None


class VendorCreate(BaseModel):
    """Request to create a new vendor."""
    slug: str
    name: str
    category: str
    subcategory: Optional[str] = None
    pricing: Optional[VendorPricing] = None
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    best_for: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    avoid_if: Optional[List[str]] = None
    avg_implementation_weeks: Optional[int] = None
    implementation_cost_range: Optional[Dict[str, int]] = None
    requires_developer: bool = False
    g2_rating: Optional[float] = None
    g2_reviews: Optional[int] = None
    capterra_rating: Optional[float] = None
    our_rating: Optional[float] = None
    integrations: Optional[List[str]] = None
    api_available: bool = True


class VendorUpdate(BaseModel):
    """Request to update a vendor."""
    name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    pricing: Optional[VendorPricing] = None
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    best_for: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    avoid_if: Optional[List[str]] = None
    avg_implementation_weeks: Optional[int] = None
    implementation_cost_range: Optional[Dict[str, int]] = None
    requires_developer: Optional[bool] = None
    g2_rating: Optional[float] = None
    g2_reviews: Optional[int] = None
    capterra_rating: Optional[float] = None
    our_rating: Optional[float] = None
    integrations: Optional[List[str]] = None
    api_available: Optional[bool] = None
    auto_refresh_enabled: Optional[bool] = None


class VendorResponse(BaseModel):
    """Vendor data response."""
    id: str
    slug: str
    name: str
    category: str
    subcategory: Optional[str] = None
    pricing: Optional[Dict[str, Any]] = None
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    best_for: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    avoid_if: Optional[List[str]] = None
    avg_implementation_weeks: Optional[int] = None
    implementation_cost_range: Optional[Dict[str, int]] = None
    requires_developer: bool = False
    g2_rating: Optional[float] = None
    g2_reviews: Optional[int] = None
    capterra_rating: Optional[float] = None
    our_rating: Optional[float] = None
    integrations: Optional[List[str]] = None
    api_available: bool = True
    pricing_verified_at: Optional[datetime] = None
    auto_refresh_enabled: bool = True
    created_at: datetime
    updated_at: datetime


class VendorListResponse(BaseModel):
    """Paginated vendor list response."""
    vendors: List[VendorResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class VendorCompareRequest(BaseModel):
    """Request to compare vendors."""
    vendor_ids: List[str]  # List of vendor IDs or slugs


class VendorCompareResponse(BaseModel):
    """Vendor comparison response."""
    vendors: List[VendorResponse]
    comparison: Dict[str, Any]


class CategoryResponse(BaseModel):
    """Vendor category response."""
    category: str
    description: Optional[str] = None
    vendor_count: int


class RefreshResult(BaseModel):
    """Result of a vendor pricing refresh."""
    vendor_slug: str
    success: bool
    changed: bool = False
    old_pricing: Optional[Dict[str, Any]] = None
    new_pricing: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
