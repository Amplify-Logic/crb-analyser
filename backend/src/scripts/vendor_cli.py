"""
Vendor CLI

Command-line helper for managing the vendor database from Claude Code.

Usage:
    python -m backend.src.scripts.vendor_cli add "https://vendor.com"
    python -m backend.src.scripts.vendor_cli refresh "vendor-slug"
    python -m backend.src.scripts.vendor_cli list-stale
    python -m backend.src.scripts.vendor_cli set-tier "vendor-slug" "dental" 1
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Optional

# Add project root to path for imports
sys.path.insert(0, "/Users/larsmusic/CRB Analyser/crb-analyser/backend")

from src.config.supabase_client import get_async_supabase


# =============================================================================
# VENDOR OPERATIONS
# =============================================================================

async def list_stale_vendors(days: int = 90) -> None:
    """List vendors that haven't been verified in X days."""
    supabase = await get_async_supabase()

    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

    result = await supabase.table("vendors").select(
        "slug, name, category, verified_at"
    ).or_(
        f"verified_at.is.null,verified_at.lt.{cutoff}"
    ).eq("status", "active").order("verified_at", nullsfirst=True).execute()

    vendors = result.data or []

    print(f"\n📋 Stale Vendors (not verified in {days}+ days)")
    print("=" * 60)

    if not vendors:
        print("No stale vendors found!")
        return

    for v in vendors:
        verified = v.get("verified_at", "Never")
        if verified and verified != "Never":
            verified = verified[:10]  # Just the date
        print(f"  {v['slug']:<30} | {v['category']:<20} | Verified: {verified}")

    print(f"\nTotal: {len(vendors)} vendors")


async def get_vendor_by_slug(slug: str) -> Optional[dict]:
    """Get a vendor by slug."""
    supabase = await get_async_supabase()
    result = await supabase.table("vendors").select("*").eq("slug", slug).single().execute()
    return result.data


async def create_vendor(data: dict) -> dict:
    """Create a new vendor."""
    supabase = await get_async_supabase()

    data["created_at"] = datetime.utcnow().isoformat()
    data["updated_at"] = datetime.utcnow().isoformat()
    data["status"] = "active"

    result = await supabase.table("vendors").insert(data).execute()

    if result.data:
        # Log audit
        await supabase.table("vendor_audit_log").insert({
            "vendor_id": result.data[0]["id"],
            "vendor_slug": data["slug"],
            "action": "create",
            "changed_by": "claude-code-cli",
            "changes": {"created": data},
        }).execute()

    return result.data[0] if result.data else {}


async def update_vendor(slug: str, data: dict) -> dict:
    """Update an existing vendor."""
    supabase = await get_async_supabase()

    # Get existing
    existing = await get_vendor_by_slug(slug)
    if not existing:
        raise ValueError(f"Vendor '{slug}' not found")

    data["updated_at"] = datetime.utcnow().isoformat()

    result = await supabase.table("vendors").update(data).eq("slug", slug).execute()

    if result.data:
        # Build changes log
        changes = {}
        for key, new_value in data.items():
            if key != "updated_at":
                old_value = existing.get(key)
                if old_value != new_value:
                    changes[key] = {"old": old_value, "new": new_value}

        if changes:
            await supabase.table("vendor_audit_log").insert({
                "vendor_id": result.data[0]["id"],
                "vendor_slug": slug,
                "action": "update",
                "changed_by": "claude-code-cli",
                "changes": changes,
            }).execute()

    return result.data[0] if result.data else {}


async def set_vendor_tier(slug: str, industry: str, tier: int, boost: int = 0) -> None:
    """Set a vendor's tier for an industry."""
    supabase = await get_async_supabase()

    # Get vendor ID
    vendor = await get_vendor_by_slug(slug)
    if not vendor:
        print(f"❌ Vendor '{slug}' not found")
        return

    vendor_id = vendor["id"]

    # Upsert tier assignment
    await supabase.table("industry_vendor_tiers").upsert({
        "industry": industry,
        "vendor_id": vendor_id,
        "tier": tier,
        "boost_score": boost,
        "updated_at": datetime.utcnow().isoformat(),
    }, on_conflict="industry,vendor_id").execute()

    print(f"✅ Set {slug} as Tier {tier} for {industry}")


async def remove_vendor_tier(slug: str, industry: str) -> None:
    """Remove a vendor from an industry's tiers."""
    supabase = await get_async_supabase()

    # Get vendor ID
    vendor = await get_vendor_by_slug(slug)
    if not vendor:
        print(f"❌ Vendor '{slug}' not found")
        return

    await supabase.table("industry_vendor_tiers").delete().eq(
        "vendor_id", vendor["id"]
    ).eq("industry", industry).execute()

    print(f"✅ Removed {slug} from {industry} tiers")


async def verify_vendor(slug: str) -> None:
    """Mark a vendor as verified."""
    supabase = await get_async_supabase()

    now = datetime.utcnow().isoformat()

    result = await supabase.table("vendors").update({
        "verified_at": now,
        "verified_by": "claude-code-cli",
        "updated_at": now,
    }).eq("slug", slug).execute()

    if result.data:
        print(f"✅ Verified: {slug}")
    else:
        print(f"❌ Vendor '{slug}' not found")


async def get_vendor_stats() -> None:
    """Print vendor database statistics."""
    supabase = await get_async_supabase()

    # Total by status
    vendors_result = await supabase.table("vendors").select("status").execute()
    vendors = vendors_result.data or []

    status_counts = {"active": 0, "deprecated": 0, "needs_review": 0}
    for v in vendors:
        status = v.get("status", "active")
        status_counts[status] = status_counts.get(status, 0) + 1

    # By category
    category_result = await supabase.table("vendors").select("category").neq("status", "deprecated").execute()
    category_counts = {}
    for v in category_result.data or []:
        cat = v.get("category")
        if cat:
            category_counts[cat] = category_counts.get(cat, 0) + 1

    # Industry tier counts
    tiers_result = await supabase.table("industry_vendor_tiers").select("industry, tier").execute()
    tier_counts = {}
    for t in tiers_result.data or []:
        industry = t["industry"]
        if industry not in tier_counts:
            tier_counts[industry] = {"t1": 0, "t2": 0, "t3": 0}
        tier_counts[industry][f"t{t['tier']}"] += 1

    print("\n📊 Vendor Database Statistics")
    print("=" * 50)
    print(f"\nTotal Vendors: {len(vendors)}")
    print(f"  Active: {status_counts['active']}")
    print(f"  Deprecated: {status_counts['deprecated']}")
    print(f"  Needs Review: {status_counts['needs_review']}")

    print("\nBy Category:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:<25} {count}")

    print("\nIndustry Tier Assignments:")
    for industry, counts in sorted(tier_counts.items()):
        print(f"  {industry:<20} T1:{counts['t1']} T2:{counts['t2']} T3:{counts['t3']}")


async def list_vendors(category: Optional[str] = None, industry: Optional[str] = None) -> None:
    """List vendors with optional filters."""
    supabase = await get_async_supabase()

    query = supabase.table("vendors").select(
        "slug, name, category, our_rating, verified_at"
    ).neq("status", "deprecated").order("name")

    if category:
        query = query.eq("category", category)

    if industry:
        query = query.contains("industries", [industry])

    result = await query.execute()
    vendors = result.data or []

    print(f"\n📋 Vendors" + (f" ({category})" if category else "") + (f" [{industry}]" if industry else ""))
    print("=" * 80)

    for v in vendors:
        rating = f"★{v['our_rating']}" if v.get('our_rating') else "   "
        verified = "✓" if v.get("verified_at") else " "
        print(f"  {verified} {v['slug']:<35} | {v['category']:<20} | {rating}")

    print(f"\nTotal: {len(vendors)}")


# =============================================================================
# CLI COMMANDS
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Vendor Database CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m backend.src.scripts.vendor_cli stats
  python -m backend.src.scripts.vendor_cli list --category crm
  python -m backend.src.scripts.vendor_cli list-stale --days 90
  python -m backend.src.scripts.vendor_cli verify hubspot
  python -m backend.src.scripts.vendor_cli set-tier forethought dental 1
  python -m backend.src.scripts.vendor_cli remove-tier forethought dental
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # stats
    subparsers.add_parser("stats", help="Show vendor database statistics")

    # list
    list_parser = subparsers.add_parser("list", help="List vendors")
    list_parser.add_argument("--category", "-c", help="Filter by category")
    list_parser.add_argument("--industry", "-i", help="Filter by industry")

    # list-stale
    stale_parser = subparsers.add_parser("list-stale", help="List stale vendors")
    stale_parser.add_argument("--days", "-d", type=int, default=90, help="Days threshold")

    # verify
    verify_parser = subparsers.add_parser("verify", help="Mark vendor as verified")
    verify_parser.add_argument("slug", help="Vendor slug")

    # set-tier
    tier_parser = subparsers.add_parser("set-tier", help="Set vendor tier for industry")
    tier_parser.add_argument("slug", help="Vendor slug")
    tier_parser.add_argument("industry", help="Industry name")
    tier_parser.add_argument("tier", type=int, choices=[1, 2, 3], help="Tier (1-3)")
    tier_parser.add_argument("--boost", "-b", type=int, default=0, help="Extra boost score")

    # remove-tier
    rm_tier_parser = subparsers.add_parser("remove-tier", help="Remove vendor from industry tiers")
    rm_tier_parser.add_argument("slug", help="Vendor slug")
    rm_tier_parser.add_argument("industry", help="Industry name")

    # get
    get_parser = subparsers.add_parser("get", help="Get vendor details")
    get_parser.add_argument("slug", help="Vendor slug")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Run async command
    if args.command == "stats":
        asyncio.run(get_vendor_stats())

    elif args.command == "list":
        asyncio.run(list_vendors(args.category, args.industry))

    elif args.command == "list-stale":
        asyncio.run(list_stale_vendors(args.days))

    elif args.command == "verify":
        asyncio.run(verify_vendor(args.slug))

    elif args.command == "set-tier":
        asyncio.run(set_vendor_tier(args.slug, args.industry, args.tier, args.boost))

    elif args.command == "remove-tier":
        asyncio.run(remove_vendor_tier(args.slug, args.industry))

    elif args.command == "get":
        vendor = asyncio.run(get_vendor_by_slug(args.slug))
        if vendor:
            print(json.dumps(vendor, indent=2, default=str))
        else:
            print(f"❌ Vendor '{args.slug}' not found")


if __name__ == "__main__":
    main()
