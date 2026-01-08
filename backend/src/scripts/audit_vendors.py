"""
Vendor Database Audit Script

Queries all vendors and their tier assignments from Supabase.
Run: cd backend && source venv/bin/activate && python -m src.scripts.audit_vendors
"""

import asyncio
import json
from datetime import datetime

import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.supabase_client import get_async_supabase


async def get_all_vendors():
    """Get all vendors from Supabase."""
    supabase = await get_async_supabase()

    # Get all vendors
    result = await supabase.table("vendors").select("*").order("industries").execute()
    return result.data


async def get_all_tier_assignments():
    """Get all tier assignments."""
    supabase = await get_async_supabase()

    result = await supabase.table("industry_vendor_tiers").select("*").execute()
    return result.data


async def get_vendor_summary():
    """Get summary by industry."""
    supabase = await get_async_supabase()

    # This gets vendors grouped conceptually
    result = await supabase.table("vendors").select("slug, name, industries, pricing, g2_score, capterra_score, website, verified_at, status").order("name").execute()
    return result.data


async def main():
    """Main audit function."""
    print("\n" + "="*80)
    print("VENDOR DATABASE AUDIT")
    print("="*80)
    print(f"Audit Date: {datetime.now().isoformat()}")
    print("="*80 + "\n")

    # Get all vendors
    vendors = await get_all_vendors()
    tiers = await get_all_tier_assignments()

    # Create tier lookup
    tier_lookup = {}  # vendor_id -> {industry: tier, boost}
    for t in tiers:
        vid = t.get("vendor_id")
        if vid not in tier_lookup:
            tier_lookup[vid] = {}
        tier_lookup[vid][t.get("industry")] = {
            "tier": t.get("tier"),
            "boost": t.get("boost_score"),
            "notes": t.get("notes")
        }

    # Count by industry
    industry_counts = {}
    for v in vendors:
        industries = v.get("industries", [])
        if isinstance(industries, str):
            industries = [industries]
        for ind in industries:
            industry_counts[ind] = industry_counts.get(ind, 0) + 1

    print("VENDOR COUNT BY INDUSTRY:")
    print("-" * 40)
    total = 0
    for ind, count in sorted(industry_counts.items()):
        print(f"  {ind}: {count}")
        total += count
    print(f"  TOTAL: {len(vendors)} vendors ({total} industry assignments)")
    print()

    # Count by tier
    tier_counts = {"1": 0, "2": 0, "3": 0, "unassigned": 0}
    for v in vendors:
        vid = v.get("id")
        if vid in tier_lookup:
            # Get the first tier assignment
            for ind, tdata in tier_lookup[vid].items():
                t = str(tdata.get("tier", ""))
                if t in tier_counts:
                    tier_counts[t] += 1
                break
        else:
            tier_counts["unassigned"] += 1

    print("VENDOR COUNT BY TIER:")
    print("-" * 40)
    for t, count in tier_counts.items():
        print(f"  Tier {t}: {count}")
    print()

    # List all vendors with details
    print("\n" + "="*80)
    print("ALL VENDORS (by industry)")
    print("="*80 + "\n")

    # Group by primary industry
    by_industry = {}
    for v in vendors:
        industries = v.get("industries", ["unknown"])
        if isinstance(industries, str):
            industries = [industries]
        primary_ind = industries[0] if industries else "unknown"
        if primary_ind not in by_industry:
            by_industry[primary_ind] = []
        by_industry[primary_ind].append(v)

    for industry in sorted(by_industry.keys()):
        print(f"\n### {industry.upper()} ###")
        print("-" * 60)

        vlist = by_industry[industry]
        for v in sorted(vlist, key=lambda x: x.get("name", "")):
            vid = v.get("id")
            slug = v.get("slug", "")
            name = v.get("name", "")
            website = v.get("website", "N/A")
            g2 = v.get("g2_score", "N/A")
            capterra = v.get("capterra_score", "N/A")
            pricing = v.get("pricing") or {}
            if isinstance(pricing, str):
                try:
                    pricing = json.loads(pricing)
                except:
                    pricing = {}
            starting_price = pricing.get("starting_price", "Custom") if pricing else "Custom"
            pricing_model = pricing.get("model", "N/A")
            verified = v.get("verified_at", "Never")[:10] if v.get("verified_at") else "Never"

            # Get tier info
            tier_info = "No tier"
            if vid in tier_lookup:
                for ind, tdata in tier_lookup[vid].items():
                    if ind == industry:
                        tier_info = f"Tier {tdata.get('tier')} (boost: {tdata.get('boost', 0)})"
                        break

            print(f"\n  {name} ({slug})")
            print(f"    Website: {website}")
            print(f"    Pricing: ${starting_price}/mo ({pricing_model})")
            print(f"    Ratings: G2={g2}, Capterra={capterra}")
            print(f"    Tier: {tier_info}")
            print(f"    Verified: {verified}")

    # Output JSON for programmatic use
    output = {
        "audit_date": datetime.now().isoformat(),
        "total_vendors": len(vendors),
        "industry_counts": industry_counts,
        "tier_counts": tier_counts,
        "vendors": []
    }

    for v in vendors:
        vid = v.get("id")
        tier_data = tier_lookup.get(vid, {})
        output["vendors"].append({
            "slug": v.get("slug"),
            "name": v.get("name"),
            "website": v.get("website"),
            "industries": v.get("industries"),
            "pricing": v.get("pricing"),
            "g2_score": v.get("g2_score"),
            "capterra_score": v.get("capterra_score"),
            "verified_at": v.get("verified_at"),
            "tiers": tier_data
        })

    # Write JSON output
    with open("vendor_audit_output.json", "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n\n{'='*80}")
    print("Audit complete. JSON output: vendor_audit_output.json")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
