"""
Integration test for the vendor refresh flow.

Usage:
    cd backend
    source venv/bin/activate
    python -m src.scripts.test_refresh_flow
"""

import asyncio
import json
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

from src.config.supabase_client import get_async_supabase, init_supabase
from src.agents.research.refresh import refresh_vendors, get_stale_count
from src.agents.research.schemas import RefreshRequest, RefreshScope


async def create_test_vendor():
    """Create a test vendor with old verified_at date."""
    supabase = await get_async_supabase()

    # Check if test vendor exists
    existing = await supabase.table("vendors").select("id").eq("slug", "freshdesk-test").execute()

    if existing.data:
        print("Test vendor already exists, updating verified_at to make it stale...")
        # Update to make it stale (91 days ago)
        stale_date = (datetime.utcnow() - timedelta(days=91)).isoformat()
        await supabase.table("vendors").update({
            "verified_at": stale_date,
        }).eq("slug", "freshdesk-test").execute()
    else:
        print("Creating test vendor...")
        stale_date = (datetime.utcnow() - timedelta(days=91)).isoformat()
        await supabase.table("vendors").insert({
            "slug": "freshdesk-test",
            "name": "Freshdesk",
            "category": "customer_support",
            "website": "https://www.freshworks.com/freshdesk/",
            "pricing_url": "https://www.freshworks.com/freshdesk/pricing/",
            "status": "active",
            "verified_at": stale_date,
            "pricing": {
                "model": "subscription",
                "starting_price": 10,  # Intentionally wrong - should be 15
                "free_tier": True,
            },
        }).execute()

    print("Test vendor ready.")


async def run_refresh_test():
    """Run the refresh flow and print results."""
    print("\n" + "="*60)
    print("REFRESH FLOW TEST")
    print("="*60)

    # Check stale count
    count = await get_stale_count()
    print(f"\nStale vendors: {count}")

    if count == 0:
        print("No stale vendors to refresh.")
        return

    # Run refresh
    print("\nStarting refresh...")
    request = RefreshRequest(scope=RefreshScope.STALE)

    updates = []
    async for update in refresh_vendors(request):
        update_type = update.get("type")

        if update_type == "started":
            print(f"Scanning {update.get('total')} vendors...")
        elif update_type == "progress":
            print(f"  [{update.get('current')}/{update.get('total')}] {update.get('vendor')}")
        elif update_type == "update":
            changes = update.get("changes", [])
            print(f"\n  Found changes for {update.get('vendor_name')}:")
            for change in changes:
                print(f"    {change['field']}: {change['old_value']} -> {change['new_value']}")
            updates.append(update)
        elif update_type == "error":
            print(f"\n  Error: {update.get('vendor_name')}: {update.get('error')}")
        elif update_type == "completed":
            print(f"\nCompleted: {update.get('updates')} updates, {update.get('errors')} errors")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    if updates:
        print(f"Found {len(updates)} vendors with pricing changes")
        for u in updates:
            print(f"  - {u.get('vendor_name')}: {len(u.get('changes', []))} changes")
            if u.get('has_significant_changes'):
                print("    ⚠️  Has significant changes (needs review)")
    else:
        print("No changes detected")


async def cleanup_test_vendor():
    """Remove test vendor."""
    supabase = await get_async_supabase()
    await supabase.table("vendors").delete().eq("slug", "freshdesk-test").execute()
    print("\nTest vendor cleaned up.")


async def main():
    """Run the full test."""
    await init_supabase()

    try:
        # Setup
        await create_test_vendor()

        # Test
        await run_refresh_test()

        # Cleanup (optional - comment out to keep vendor for inspection)
        # await cleanup_test_vendor()

    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
