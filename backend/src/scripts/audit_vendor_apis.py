"""
Audit Vendor API Capabilities

This script helps identify vendors that need API openness scores
and provides utilities for populating the new API fields.

Usage:
    python -m src.scripts.audit_vendor_apis list-unrated
    python -m src.scripts.audit_vendor_apis rate-vendor <slug> <score>
    python -m src.scripts.audit_vendor_apis bulk-update
"""

import asyncio
import sys
from typing import Optional

# Well-known API openness scores for common vendors
KNOWN_API_SCORES = {
    # Score 5: Full REST API + Webhooks + OAuth
    "stripe": {
        "api_openness_score": 5,
        "api_type": "REST",
        "has_webhooks": True,
        "has_oauth": True,
        "zapier_integration": True,
        "make_integration": True,
        "n8n_integration": True,
        "api_rate_limits": "100/sec",
        "custom_tool_examples": [
            "Automated payment reconciliation",
            "Subscription lifecycle management",
            "Revenue analytics dashboards",
        ],
    },
    "twilio": {
        "api_openness_score": 5,
        "api_type": "REST",
        "has_webhooks": True,
        "has_oauth": True,
        "zapier_integration": True,
        "make_integration": True,
        "n8n_integration": True,
        "api_rate_limits": "100/sec",
        "custom_tool_examples": [
            "AI-powered SMS appointment reminders",
            "Voice call transcription and analysis",
            "Automated customer outreach sequences",
        ],
    },
    "hubspot": {
        "api_openness_score": 5,
        "api_type": "REST",
        "has_webhooks": True,
        "has_oauth": True,
        "zapier_integration": True,
        "make_integration": True,
        "n8n_integration": True,
        "api_rate_limits": "100/10sec",
        "custom_tool_examples": [
            "Lead scoring with AI analysis",
            "Automated deal stage progression",
            "Custom reporting dashboards",
        ],
    },
    "intercom": {
        "api_openness_score": 5,
        "api_type": "REST",
        "has_webhooks": True,
        "has_oauth": True,
        "zapier_integration": True,
        "make_integration": True,
        "n8n_integration": True,
        "api_rate_limits": "1000/min",
        "custom_tool_examples": [
            "AI ticket categorization and routing",
            "Automated customer health scoring",
            "Proactive support triggers",
        ],
    },
    "zendesk": {
        "api_openness_score": 4,
        "api_type": "REST",
        "has_webhooks": True,
        "has_oauth": True,
        "zapier_integration": True,
        "make_integration": True,
        "n8n_integration": True,
        "api_rate_limits": "700/min",
        "custom_tool_examples": [
            "Smart ticket routing with AI",
            "Automated response suggestions",
            "Customer sentiment analysis",
        ],
    },
    "salesforce": {
        "api_openness_score": 4,
        "api_type": "REST",
        "has_webhooks": True,
        "has_oauth": True,
        "zapier_integration": True,
        "make_integration": True,
        "n8n_integration": True,
        "api_rate_limits": "1000/day per user",
        "custom_tool_examples": [
            "AI-powered opportunity scoring",
            "Automated data enrichment",
            "Custom workflow automation",
        ],
    },
    "slack": {
        "api_openness_score": 5,
        "api_type": "REST",
        "has_webhooks": True,
        "has_oauth": True,
        "zapier_integration": True,
        "make_integration": True,
        "n8n_integration": True,
        "api_rate_limits": "1/sec per method",
        "custom_tool_examples": [
            "AI-powered notification routing",
            "Automated standup summaries",
            "Smart channel management",
        ],
    },
    "notion": {
        "api_openness_score": 4,
        "api_type": "REST",
        "has_webhooks": False,
        "has_oauth": True,
        "zapier_integration": True,
        "make_integration": True,
        "n8n_integration": True,
        "api_rate_limits": "3 req/sec",
        "custom_tool_examples": [
            "Automated documentation from code",
            "Meeting notes to action items",
            "Project status dashboards",
        ],
    },
    "airtable": {
        "api_openness_score": 4,
        "api_type": "REST",
        "has_webhooks": True,
        "has_oauth": True,
        "zapier_integration": True,
        "make_integration": True,
        "n8n_integration": True,
        "api_rate_limits": "5 req/sec",
        "custom_tool_examples": [
            "Automated data pipelines",
            "Custom CRM workflows",
            "Inventory management automation",
        ],
    },
    "calendly": {
        "api_openness_score": 4,
        "api_type": "REST",
        "has_webhooks": True,
        "has_oauth": True,
        "zapier_integration": True,
        "make_integration": True,
        "n8n_integration": True,
        "api_rate_limits": "unlimited",
        "custom_tool_examples": [
            "Pre-meeting AI research",
            "Smart scheduling optimization",
            "Automated follow-up sequences",
        ],
    },
    # Score 3: Basic API
    "freshdesk": {
        "api_openness_score": 4,
        "api_type": "REST",
        "has_webhooks": True,
        "has_oauth": False,
        "zapier_integration": True,
        "make_integration": True,
        "n8n_integration": True,
        "api_rate_limits": "1000/min",
    },
    "pipedrive": {
        "api_openness_score": 4,
        "api_type": "REST",
        "has_webhooks": True,
        "has_oauth": True,
        "zapier_integration": True,
        "make_integration": True,
        "n8n_integration": True,
        "api_rate_limits": "100/10sec",
    },
    # Automation platforms themselves (score 5)
    "zapier": {
        "api_openness_score": 5,
        "api_type": "REST",
        "has_webhooks": True,
        "has_oauth": True,
        "zapier_integration": True,
        "make_integration": False,
        "n8n_integration": False,
    },
    "make": {
        "api_openness_score": 5,
        "api_type": "REST",
        "has_webhooks": True,
        "has_oauth": True,
        "zapier_integration": False,
        "make_integration": True,
        "n8n_integration": False,
    },
    "n8n": {
        "api_openness_score": 5,
        "api_type": "REST",
        "has_webhooks": True,
        "has_oauth": True,
        "zapier_integration": False,
        "make_integration": False,
        "n8n_integration": True,
    },
}


async def list_unrated_vendors() -> None:
    """List vendors without API openness scores."""
    from src.services.vendor_service import vendor_service

    vendors = await vendor_service.get_vendors_needing_api_audit(limit=100)

    if not vendors:
        print("All vendors have API openness scores!")
        return

    print(f"\n{len(vendors)} vendors need API openness scores:\n")
    print("-" * 60)

    for v in vendors:
        api_status = "Has API" if v.get("api_available") else "No API"
        docs = v.get("api_docs_url") or "No docs"
        print(f"  {v['slug']:<30} {v['category']:<20} {api_status}")
        if docs != "No docs":
            print(f"    └─ {docs}")

    print("-" * 60)
    print(f"\nTo rate a vendor: python -m src.scripts.audit_vendor_apis rate <slug> <score>")


async def rate_vendor(
    slug: str,
    score: int,
    has_webhooks: bool = False,
    has_oauth: bool = False,
    zapier: bool = False,
    make: bool = False,
    n8n: bool = False,
) -> None:
    """Set API openness score for a vendor."""
    from src.services.vendor_service import vendor_service

    result = await vendor_service.update_vendor_api_info(
        slug=slug,
        api_openness_score=score,
        has_webhooks=has_webhooks,
        has_oauth=has_oauth,
        zapier_integration=zapier,
        make_integration=make,
        n8n_integration=n8n,
    )

    if result:
        print(f"Updated {slug} with API openness score: {score}")
    else:
        print(f"Failed to update {slug} - vendor not found?")


async def bulk_update_known_vendors() -> None:
    """Update vendors with known API scores."""
    from src.services.vendor_service import vendor_service

    updated = 0
    failed = 0

    for slug, data in KNOWN_API_SCORES.items():
        result = await vendor_service.update_vendor_api_info(
            slug=slug,
            api_openness_score=data["api_openness_score"],
            has_webhooks=data.get("has_webhooks", False),
            has_oauth=data.get("has_oauth", False),
            zapier_integration=data.get("zapier_integration", False),
            make_integration=data.get("make_integration", False),
            n8n_integration=data.get("n8n_integration", False),
            api_rate_limits=data.get("api_rate_limits"),
            custom_tool_examples=data.get("custom_tool_examples"),
        )

        if result:
            print(f"  ✓ {slug}: score {data['api_openness_score']}")
            updated += 1
        else:
            print(f"  ✗ {slug}: not found in database")
            failed += 1

    print(f"\nUpdated {updated} vendors, {failed} not found")


async def show_stats() -> None:
    """Show API openness statistics."""
    from src.config.supabase_client import get_async_supabase

    supabase = await get_async_supabase()

    # Get total counts
    result = await supabase.table("vendors").select(
        "api_openness_score", count="exact"
    ).eq("status", "active").execute()

    total = result.count or 0

    # Count by score
    score_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, None: 0}

    for vendor in result.data or []:
        score = vendor.get("api_openness_score")
        if score in score_counts:
            score_counts[score] += 1
        else:
            score_counts[None] += 1

    print("\nAPI Openness Score Distribution:")
    print("-" * 40)
    print(f"  Score 5 (Fully Open):    {score_counts[5]:>4} vendors")
    print(f"  Score 4 (Good API):      {score_counts[4]:>4} vendors")
    print(f"  Score 3 (Basic API):     {score_counts[3]:>4} vendors")
    print(f"  Score 2 (Integrations):  {score_counts[2]:>4} vendors")
    print(f"  Score 1 (Closed):        {score_counts[1]:>4} vendors")
    print(f"  Not Rated:               {score_counts[None]:>4} vendors")
    print("-" * 40)
    print(f"  Total Active:            {total:>4} vendors")

    rated = total - score_counts[None]
    pct = (rated / total * 100) if total > 0 else 0
    print(f"\n  Coverage: {rated}/{total} ({pct:.1f}%)")


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m src.scripts.audit_vendor_apis list      # List unrated vendors")
        print("  python -m src.scripts.audit_vendor_apis stats     # Show statistics")
        print("  python -m src.scripts.audit_vendor_apis bulk      # Update known vendors")
        print("  python -m src.scripts.audit_vendor_apis rate <slug> <score>  # Rate vendor")
        return

    command = sys.argv[1]

    if command == "list":
        asyncio.run(list_unrated_vendors())
    elif command == "stats":
        asyncio.run(show_stats())
    elif command == "bulk":
        asyncio.run(bulk_update_known_vendors())
    elif command == "rate":
        if len(sys.argv) < 4:
            print("Usage: python -m src.scripts.audit_vendor_apis rate <slug> <score>")
            return
        slug = sys.argv[2]
        try:
            score = int(sys.argv[3])
            if score < 1 or score > 5:
                raise ValueError("Score must be 1-5")
        except ValueError as e:
            print(f"Error: {e}")
            return
        asyncio.run(rate_vendor(slug, score))
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
