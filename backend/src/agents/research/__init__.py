"""
Vendor Research Agent

Automated discovery and refresh of vendor data.

Usage:
    from src.agents.research import refresh_vendors, discover_vendors

    # Refresh stale vendors
    async for update in refresh_vendors(RefreshRequest(scope="stale")):
        print(update)

    # Discover new vendors
    async for candidate in discover_vendors(DiscoverRequest(category="crm")):
        print(candidate)
"""

from .schemas import (
    RefreshRequest,
    RefreshScope,
    DiscoverRequest,
    ApplyRequest,
    TaskResponse,
    VendorUpdate,
    DiscoveredVendor,
    ExtractedPricing,
)
from .refresh import (
    refresh_vendors,
    get_stale_vendors,
    get_stale_count,
    apply_vendor_updates,
)
from .discover import (
    discover_vendors,
    add_discovered_vendor,
    add_multiple_vendors,
)

__all__ = [
    # Schemas
    "RefreshRequest",
    "RefreshScope",
    "DiscoverRequest",
    "ApplyRequest",
    "TaskResponse",
    "VendorUpdate",
    "DiscoveredVendor",
    "ExtractedPricing",
    # Refresh
    "refresh_vendors",
    "get_stale_vendors",
    "get_stale_count",
    "apply_vendor_updates",
    # Discover
    "discover_vendors",
    "add_discovered_vendor",
    "add_multiple_vendors",
]
