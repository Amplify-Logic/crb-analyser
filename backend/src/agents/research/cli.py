"""
CLI for the vendor research agent.

Usage:
    cd backend
    source venv/bin/activate

    # Refresh stale vendors
    python -m src.agents.research.cli refresh --stale
    python -m src.agents.research.cli refresh --stale --category crm --industry dental

    # Refresh specific vendors
    python -m src.agents.research.cli refresh --vendor hubspot --vendor salesforce

    # Discover new vendors
    python -m src.agents.research.cli discover --category crm --industry dental

    # Dry run (no database updates)
    python -m src.agents.research.cli refresh --stale --dry-run

    # JSON output for scripting
    python -m src.agents.research.cli refresh --stale --output json
"""

import argparse
import asyncio
import json
import sys
from typing import Optional

from dotenv import load_dotenv

# Load env before imports that need settings
load_dotenv()

from src.agents.research.schemas import RefreshRequest, RefreshScope, DiscoverRequest
from src.agents.research.refresh import refresh_vendors, get_stale_count, apply_vendor_updates
from src.agents.research.discover import discover_vendors, add_multiple_vendors, DiscoveredVendor


def print_progress(update: dict, output_format: str = "text"):
    """Print a progress update."""
    if output_format == "json":
        print(json.dumps(update))
        return

    update_type = update.get("type")

    if update_type == "started":
        print(f"\n{'='*60}")
        print(f"Task ID: {update.get('task_id')}")
        print(f"Total items: {update.get('total')}")
        print("="*60)

    elif update_type == "progress":
        current = update.get("current", 0)
        total = update.get("total", 0)
        vendor = update.get("vendor", "")
        pct = (current / total * 100) if total > 0 else 0
        print(f"[{current}/{total}] {pct:.0f}% - {vendor}")

    elif update_type == "update":
        vendor = update.get("vendor_name", update.get("vendor_slug"))
        changes = update.get("changes", [])
        significant = update.get("has_significant_changes", False)

        if changes:
            icon = "⚠️ " if significant else "  "
            print(f"{icon}{vendor}:")
            for change in changes:
                field = change.get("field", "")
                old = change.get("old_value", "null")
                new = change.get("new_value", "null")
                sig = " ⚠️" if change.get("is_significant") else ""
                print(f"    {field}: {old} → {new}{sig}")
        else:
            print(f"  {vendor}: no changes")

    elif update_type == "error":
        vendor = update.get("vendor_name", update.get("vendor_slug"))
        error = update.get("error", "Unknown error")
        print(f"✗ {vendor}: {error}")

    elif update_type == "candidate":
        vendor = update.get("vendor", {})
        name = vendor.get("name", "Unknown")
        website = vendor.get("website", "")
        score = vendor.get("relevance_score", 0)
        warning = vendor.get("warning")
        icon = "⚠️ " if warning else "  "
        print(f"{icon}{name} ({website}) - {score:.0%} relevance")
        if warning:
            print(f"    Warning: {warning}")

    elif update_type == "completed":
        print("\n" + "="*60)
        print("COMPLETED")
        print(f"Total: {update.get('total', 0)}")
        if "updates" in update:
            print(f"Updates found: {update.get('updates', 0)}")
        if "candidates" in update:
            print(f"Candidates found: {update.get('candidates', 0)}")
        if "errors" in update:
            print(f"Errors: {update.get('errors', 0)}")
        print("="*60)


async def cmd_refresh(args):
    """Handle refresh command."""
    # Determine scope
    if args.vendor:
        scope = RefreshScope.SPECIFIC
        vendor_slugs = args.vendor
    elif args.all:
        scope = RefreshScope.ALL
        vendor_slugs = []
    else:
        scope = RefreshScope.STALE
        vendor_slugs = []

    # Show stale count first
    if scope == RefreshScope.STALE:
        count = await get_stale_count(category=args.category, industry=args.industry)
        print(f"Found {count} stale vendors")
        if count == 0:
            print("Nothing to refresh.")
            return

    request = RefreshRequest(
        scope=scope,
        vendor_slugs=vendor_slugs,
        category=args.category,
        industry=args.industry,
        dry_run=args.dry_run,
    )

    updates = []
    async for update in refresh_vendors(request):
        print_progress(update, args.output)
        if update.get("type") == "update":
            updates.append(update)

    # If not dry run, prompt for approval
    if not args.dry_run and updates and not args.auto_approve:
        print("\nApply changes? [Y/n/select]: ", end="")
        sys.stdout.flush()
        try:
            response = input().strip().lower()
        except EOFError:
            response = "n"

        if response in ("", "y", "yes"):
            # Apply all
            slugs = [u.get("vendor_slug") for u in updates]
            print(f"Applying {len(slugs)} updates...")
            # Note: In CLI we'd need to reconstruct VendorUpdate objects
            # For now, print what would be applied
            print(f"Would apply updates to: {', '.join(slugs)}")
            print("(Full apply requires running through API)")
        else:
            print("Changes not applied.")

    elif args.auto_approve and updates:
        # Auto-approve non-significant changes
        non_significant = [u for u in updates if not u.get("has_significant_changes")]
        if non_significant:
            slugs = [u.get("vendor_slug") for u in non_significant]
            print(f"\nAuto-approving {len(slugs)} non-significant updates...")
            print(f"Would apply to: {', '.join(slugs)}")
            print("(Full apply requires running through API)")

        significant = [u for u in updates if u.get("has_significant_changes")]
        if significant:
            print(f"\nSkipped {len(significant)} updates with significant changes (require manual review)")


async def cmd_discover(args):
    """Handle discover command."""
    if not args.category:
        print("Error: --category is required for discovery")
        sys.exit(1)

    request = DiscoverRequest(
        category=args.category,
        industry=args.industry,
        limit=args.limit,
    )

    candidates = []
    async for update in discover_vendors(request):
        print_progress(update, args.output)
        if update.get("type") == "candidate":
            candidates.append(update.get("vendor"))

    if candidates:
        print(f"\nFound {len(candidates)} new vendor candidates.")
        print("Use the admin UI to review and add them.")


async def cmd_stale_count(args):
    """Show count of stale vendors."""
    count = await get_stale_count(category=args.category, industry=args.industry)

    if args.output == "json":
        print(json.dumps({"count": count, "category": args.category, "industry": args.industry}))
    else:
        filters = []
        if args.category:
            filters.append(f"category={args.category}")
        if args.industry:
            filters.append(f"industry={args.industry}")
        filter_str = f" ({', '.join(filters)})" if filters else ""
        print(f"Stale vendors{filter_str}: {count}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Vendor Research Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Refresh command
    refresh_parser = subparsers.add_parser("refresh", help="Refresh vendor data")
    refresh_parser.add_argument("--stale", action="store_true", help="Refresh stale vendors only (default)")
    refresh_parser.add_argument("--all", action="store_true", help="Refresh all vendors")
    refresh_parser.add_argument("--vendor", action="append", help="Refresh specific vendor(s) by slug")
    refresh_parser.add_argument("--category", help="Filter by category")
    refresh_parser.add_argument("--industry", help="Filter by industry")
    refresh_parser.add_argument("--dry-run", action="store_true", help="Preview without applying")
    refresh_parser.add_argument("--auto-approve", action="store_true", help="Auto-approve non-significant changes")
    refresh_parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")

    # Discover command
    discover_parser = subparsers.add_parser("discover", help="Discover new vendors")
    discover_parser.add_argument("--category", required=True, help="Category to search")
    discover_parser.add_argument("--industry", help="Industry to search")
    discover_parser.add_argument("--limit", type=int, default=20, help="Max candidates to return")
    discover_parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")

    # Stale count command
    stale_parser = subparsers.add_parser("stale-count", help="Show count of stale vendors")
    stale_parser.add_argument("--category", help="Filter by category")
    stale_parser.add_argument("--industry", help="Filter by industry")
    stale_parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Run the appropriate command
    if args.command == "refresh":
        asyncio.run(cmd_refresh(args))
    elif args.command == "discover":
        asyncio.run(cmd_discover(args))
    elif args.command == "stale-count":
        asyncio.run(cmd_stale_count(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
