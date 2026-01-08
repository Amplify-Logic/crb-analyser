"""
Fix Vendor Audit Issues

Updates vendor data based on the 2026-01-04 audit findings.

Run: cd backend && source venv/bin/activate && python -m src.scripts.fix_vendor_audit_issues
"""

import asyncio
from datetime import datetime
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.supabase_client import get_async_supabase


# Fixes based on audit findings
PRICING_FIXES = [
    {
        "slug": "nexhealth",
        "issue": "Listed as $299/mo but pricing is custom-only (no public pricing)",
        "fix": {
            "pricing": {
                "model": "custom",
                "currency": "USD",
                "starting_price": None,
                "free_tier": False,
                "custom_pricing": True,
                "notes": "Month-to-month and yearly options. No cancellation fees. Contact for custom quote."
            }
        }
    },
    {
        "slug": "ezyvet",
        "issue": "Listed as $245/mo but website shows $260.50/mo starting price",
        "fix": {
            "pricing": {
                "model": "subscription",
                "currency": "USD",
                "starting_price": 260.50,
                "free_tier": False,
                "notes": "Starting at $260.50/mo. 6-month initial term, 3-month rolling thereafter. Implementation costs separate."
            }
        }
    },
    {
        "slug": "webpt",
        "issue": "Listed as $99/mo but pricing is custom-only (no public pricing)",
        "fix": {
            "pricing": {
                "model": "custom",
                "currency": "USD",
                "starting_price": None,
                "free_tier": False,
                "custom_pricing": True,
                "notes": "Three tiers: Starter, Enhanced, Ultimate. Pricing per provider or per visit. Contact for custom quote."
            }
        }
    },
    {
        "slug": "bullhorn",
        "issue": "Listed as $99/mo but pricing is custom-only (enterprise sales)",
        "fix": {
            "pricing": {
                "model": "custom",
                "currency": "USD",
                "starting_price": None,
                "free_tier": False,
                "custom_pricing": True,
                "notes": "Enterprise pricing. Contact sales for custom quote. Established 25 years, 10,000+ customers."
            }
        }
    },
]

# Tier adjustments
TIER_ADJUSTMENTS = [
    {
        "slug": "servicetitan",
        "industry": "home-services",
        "issue": "Tier 1 but too expensive for small businesses. Should add company_size restrictions.",
        "action": "add_notes",
        "notes": "Enterprise only. Best for 10+ techs with $500K+ revenue. Not recommended for small teams on budget."
    },
    {
        "slug": "zenoti",
        "industry": "medspa",
        "issue": "Currently Tier 2 but is enterprise leader. Should be Tier 1 for multi-location.",
        "action": "promote",
        "new_tier": 1,
        "new_boost": 8,
        "notes": "Enterprise leader for multi-location. Best for 3+ locations."
    },
]


async def apply_pricing_fixes():
    """Apply pricing fixes to vendors."""
    supabase = await get_async_supabase()

    print("\n" + "="*60)
    print("APPLYING PRICING FIXES")
    print("="*60 + "\n")

    for fix in PRICING_FIXES:
        slug = fix["slug"]
        print(f"Fixing: {slug}")
        print(f"  Issue: {fix['issue']}")

        try:
            # Get current vendor data
            current = await supabase.table("vendors").select("id, pricing").eq(
                "slug", slug
            ).single().execute()

            if not current.data:
                print(f"  [SKIP] Vendor not found")
                continue

            vendor_id = current.data["id"]
            old_pricing = current.data["pricing"]

            # Update vendor
            await supabase.table("vendors").update({
                "pricing": fix["fix"]["pricing"],
                "verified_at": datetime.utcnow().isoformat(),
                "verified_by": "claude-code-audit-2026-01-04",
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("slug", slug).execute()

            # Log to audit
            await supabase.table("vendor_audit_log").insert({
                "vendor_id": vendor_id,
                "vendor_slug": slug,
                "action": "update_pricing",
                "changed_by": "claude-code-audit-2026-01-04",
                "changes": {
                    "issue": fix["issue"],
                    "old_pricing": old_pricing,
                    "new_pricing": fix["fix"]["pricing"],
                },
            }).execute()

            print(f"  [OK] Pricing updated and logged")

        except Exception as e:
            print(f"  [ERROR] {str(e)[:80]}")


async def apply_tier_adjustments():
    """Apply tier adjustments."""
    supabase = await get_async_supabase()

    print("\n" + "="*60)
    print("APPLYING TIER ADJUSTMENTS")
    print("="*60 + "\n")

    for adj in TIER_ADJUSTMENTS:
        slug = adj["slug"]
        industry = adj["industry"]
        print(f"Adjusting: {slug} for {industry}")
        print(f"  Issue: {adj['issue']}")

        try:
            # Get vendor ID
            vendor = await supabase.table("vendors").select("id").eq(
                "slug", slug
            ).single().execute()

            if not vendor.data:
                print(f"  [SKIP] Vendor not found")
                continue

            vendor_id = vendor.data["id"]

            # Get current tier
            current_tier = await supabase.table("industry_vendor_tiers").select("*").eq(
                "industry", industry
            ).eq("vendor_id", vendor_id).single().execute()

            if adj["action"] == "add_notes":
                # Just update notes
                if current_tier.data:
                    await supabase.table("industry_vendor_tiers").update({
                        "notes": adj["notes"],
                        "updated_at": datetime.utcnow().isoformat(),
                    }).eq("industry", industry).eq("vendor_id", vendor_id).execute()
                    print(f"  [OK] Notes updated: {adj['notes'][:50]}...")
                else:
                    print(f"  [SKIP] No tier assignment found")

            elif adj["action"] == "promote":
                # Upsert new tier
                await supabase.table("industry_vendor_tiers").upsert({
                    "industry": industry,
                    "vendor_id": vendor_id,
                    "tier": adj["new_tier"],
                    "boost_score": adj["new_boost"],
                    "notes": adj["notes"],
                    "updated_at": datetime.utcnow().isoformat(),
                }).execute()
                print(f"  [OK] Promoted to Tier {adj['new_tier']} with boost {adj['new_boost']}")

            # Log to audit
            await supabase.table("vendor_audit_log").insert({
                "vendor_id": vendor_id,
                "vendor_slug": slug,
                "action": "tier_adjustment",
                "changed_by": "claude-code-audit-2026-01-04",
                "changes": {
                    "issue": adj["issue"],
                    "action": adj["action"],
                    "notes": adj.get("notes"),
                    "new_tier": adj.get("new_tier"),
                },
            }).execute()

        except Exception as e:
            print(f"  [ERROR] {str(e)[:80]}")


async def main():
    """Run all fixes."""
    print("\n" + "="*70)
    print("VENDOR AUDIT FIX SCRIPT")
    print("Audit Date: 2026-01-04")
    print("="*70)

    await apply_pricing_fixes()
    await apply_tier_adjustments()

    print("\n" + "="*70)
    print("FIXES COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
