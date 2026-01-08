"""
Vendor refresh service.

Handles:
- Finding stale vendors
- Scraping updated pricing
- Detecting changes
- Applying updates to database
"""

import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator, Optional

import structlog

from src.config.supabase_client import get_async_supabase

from .schemas import (
    FieldChange,
    RefreshRequest,
    RefreshScope,
    ResearchTask,
    TaskStatus,
    VendorUpdate,
)
from .sources import scrape_vendor_pricing

logger = structlog.get_logger()

# Stale threshold in days
STALE_THRESHOLD_DAYS = 90

# Price change threshold for warnings
SIGNIFICANT_PRICE_CHANGE_PERCENT = 50


async def get_stale_vendors(
    category: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """
    Get vendors that haven't been verified in STALE_THRESHOLD_DAYS.

    Returns list of vendor dicts with id, slug, name, website, pricing_url, verified_at
    """
    supabase = await get_async_supabase()

    stale_date = datetime.utcnow() - timedelta(days=STALE_THRESHOLD_DAYS)

    query = (
        supabase.table("vendors")
        .select("id, slug, name, website, pricing_url, verified_at, pricing")
        .eq("status", "active")
        .or_(f"verified_at.is.null,verified_at.lt.{stale_date.isoformat()}")
        .limit(limit)
    )

    if category:
        query = query.eq("category", category)

    if industry:
        query = query.contains("industries", [industry])

    result = await query.execute()
    return result.data or []


async def get_stale_count(
    category: Optional[str] = None,
    industry: Optional[str] = None,
) -> int:
    """Get count of stale vendors matching filters."""
    supabase = await get_async_supabase()

    stale_date = datetime.utcnow() - timedelta(days=STALE_THRESHOLD_DAYS)

    query = (
        supabase.table("vendors")
        .select("id", count="exact")
        .eq("status", "active")
        .or_(f"verified_at.is.null,verified_at.lt.{stale_date.isoformat()}")
    )

    if category:
        query = query.eq("category", category)

    if industry:
        query = query.contains("industries", [industry])

    result = await query.execute()
    return result.count or 0


async def refresh_vendors(
    request: RefreshRequest,
) -> AsyncGenerator[dict, None]:
    """
    Refresh vendor data based on request.

    Yields progress updates as dict:
    - {"type": "started", "task_id": str, "total": int}
    - {"type": "progress", "current": int, "total": int, "vendor": str}
    - {"type": "update", "vendor_slug": str, "changes": list, ...}
    - {"type": "completed", "task_id": str, "updates": int, "errors": int}
    """
    task_id = str(uuid.uuid4())
    logger.info("refresh_started", task_id=task_id, scope=request.scope)

    # Get vendors to refresh
    if request.scope == RefreshScope.SPECIFIC:
        vendors = await _get_vendors_by_slugs(request.vendor_slugs)
    elif request.scope == RefreshScope.STALE:
        vendors = await get_stale_vendors(request.category, request.industry)
    else:  # ALL
        vendors = await _get_all_active_vendors(request.category, request.industry)

    total = len(vendors)
    yield {"type": "started", "task_id": task_id, "total": total}

    updates = []
    errors = []

    for i, vendor in enumerate(vendors):
        slug = vendor["slug"]
        name = vendor["name"]

        yield {
            "type": "progress",
            "current": i + 1,
            "total": total,
            "vendor": name,
        }

        # Determine URL to scrape
        url = vendor.get("pricing_url") or vendor.get("website")
        if not url:
            errors.append(f"{slug}: No URL")
            continue

        # Add /pricing if needed
        if not any(p in url.lower() for p in ["pricing", "plans", "price"]):
            url = url.rstrip("/") + "/pricing"

        # Scrape the vendor
        result = await scrape_vendor_pricing(url, name)

        if not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            errors.append(f"{slug}: {error_msg}")
            yield {
                "type": "error",
                "vendor_slug": slug,
                "vendor_name": name,
                "error": error_msg,
            }
            continue

        # Compare with existing data
        extracted = result.get("data", {})
        changes = _detect_changes(vendor, extracted)

        update = VendorUpdate(
            vendor_slug=slug,
            vendor_name=name,
            source_url=url,
            changes=changes,
            extracted_data=extracted,
        )
        updates.append(update)

        yield {
            "type": "update",
            "vendor_slug": slug,
            "vendor_name": name,
            "changes": [c.model_dump() for c in changes],
            "has_significant_changes": any(c.is_significant for c in changes),
            "extracted_data": extracted,
        }

    yield {
        "type": "completed",
        "task_id": task_id,
        "total": total,
        "updates": len(updates),
        "errors": len(errors),
        "error_details": errors,
    }

    logger.info(
        "refresh_completed",
        task_id=task_id,
        total=total,
        updates=len(updates),
        errors=len(errors),
    )


def _detect_changes(existing: dict, extracted: dict) -> list[FieldChange]:
    """Detect changes between existing vendor data and extracted data."""
    changes = []

    existing_pricing = existing.get("pricing") or {}

    # Check starting_price
    old_price = existing_pricing.get("starting_price")
    new_price = extracted.get("starting_price")
    if old_price != new_price and (old_price or new_price):
        is_significant = False
        if old_price and new_price and old_price > 0:
            change_percent = abs(new_price - old_price) / old_price * 100
            is_significant = change_percent > SIGNIFICANT_PRICE_CHANGE_PERCENT

        changes.append(FieldChange(
            field="starting_price",
            old_value=old_price,
            new_value=new_price,
            is_significant=is_significant,
        ))

    # Check free_tier
    old_free = existing_pricing.get("free_tier")
    new_free = extracted.get("free_tier")
    if old_free != new_free and new_free is not None:
        changes.append(FieldChange(
            field="free_tier",
            old_value=old_free,
            new_value=new_free,
            is_significant=old_free is True and new_free is False,  # Removing free tier is significant
        ))

    # Check free_trial_days
    old_trial = existing_pricing.get("free_trial_days")
    new_trial = extracted.get("free_trial_days")
    if old_trial != new_trial and new_trial is not None:
        changes.append(FieldChange(
            field="free_trial_days",
            old_value=old_trial,
            new_value=new_trial,
            is_significant=False,
        ))

    # Check tier count
    old_tiers = len(existing_pricing.get("tiers") or [])
    new_tiers = len(extracted.get("tiers") or [])
    if old_tiers != new_tiers:
        changes.append(FieldChange(
            field="tier_count",
            old_value=old_tiers,
            new_value=new_tiers,
            is_significant=False,
        ))

    # Check pricing_model
    old_model = existing_pricing.get("model")
    new_model = extracted.get("pricing_model")
    if old_model != new_model and new_model:
        changes.append(FieldChange(
            field="pricing_model",
            old_value=old_model,
            new_value=new_model,
            is_significant=False,
        ))

    return changes


async def apply_vendor_updates(
    task_id: str,
    approved_slugs: list[str],
    updates: list[VendorUpdate],
) -> dict:
    """
    Apply approved updates to the database.

    Returns summary of applied changes.
    """
    supabase = await get_async_supabase()
    applied = []
    errors = []

    for update in updates:
        if update.vendor_slug not in approved_slugs:
            continue

        if not update.extracted_data:
            continue

        try:
            # Build pricing update
            pricing_data = {
                "model": update.extracted_data.get("pricing_model"),
                "currency": update.extracted_data.get("currency", "USD"),
                "free_tier": update.extracted_data.get("free_tier"),
                "free_trial_days": update.extracted_data.get("free_trial_days"),
                "starting_price": update.extracted_data.get("starting_price"),
                "tiers": update.extracted_data.get("tiers", []),
            }

            # Update vendor
            await (
                supabase.table("vendors")
                .update({
                    "pricing": pricing_data,
                    "verified_at": datetime.utcnow().isoformat(),
                    "verified_by": "research-agent-v1",
                })
                .eq("slug", update.vendor_slug)
                .execute()
            )

            # Log to audit table
            await (
                supabase.table("vendor_audit_log")
                .insert({
                    "vendor_slug": update.vendor_slug,
                    "action": "update",
                    "changed_by": "research-agent-v1",
                    "changes": {c.field: {"old": c.old_value, "new": c.new_value} for c in update.changes},
                })
                .execute()
            )

            applied.append(update.vendor_slug)
            logger.info("vendor_updated", slug=update.vendor_slug, changes=len(update.changes))

        except Exception as e:
            errors.append(f"{update.vendor_slug}: {str(e)}")
            logger.exception("update_failed", slug=update.vendor_slug, error=str(e))

    return {
        "applied": applied,
        "applied_count": len(applied),
        "errors": errors,
    }


async def _get_vendors_by_slugs(slugs: list[str]) -> list[dict]:
    """Get vendors by their slugs."""
    if not slugs:
        return []

    supabase = await get_async_supabase()
    result = await (
        supabase.table("vendors")
        .select("id, slug, name, website, pricing_url, verified_at, pricing")
        .in_("slug", slugs)
        .execute()
    )
    return result.data or []


async def _get_all_active_vendors(
    category: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    """Get all active vendors matching filters."""
    supabase = await get_async_supabase()

    query = (
        supabase.table("vendors")
        .select("id, slug, name, website, pricing_url, verified_at, pricing")
        .eq("status", "active")
        .limit(limit)
    )

    if category:
        query = query.eq("category", category)

    if industry:
        query = query.contains("industries", [industry])

    result = await query.execute()
    return result.data or []
