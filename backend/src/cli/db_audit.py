"""
Database hygiene audit for CRB Analyser.

Checks all tables for invalid/stale industry references, orphaned records,
and data quality issues. Optionally cleans up invalid data.

Usage:
    cd backend
    source venv/bin/activate

    # Full audit (read-only)
    python -m src.cli.db_audit

    # Audit with JSON output (for cron/logging)
    python -m src.cli.db_audit --output json

    # Audit + clean up invalid industry data
    python -m src.cli.db_audit --fix

    # Dry run (show what --fix would do, without doing it)
    python -m src.cli.db_audit --fix --dry-run
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

load_dotenv()

import structlog

logger = structlog.get_logger()

# The only supported industries
SUPPORTED_INDUSTRIES = [
    "professional-services",
    "dental",
    "ecommerce",
    "b2b-platforms",
]


# =============================================================================
# AUDIT CHECKS
# =============================================================================

async def audit_supported_industries_table(supabase: Any) -> dict:
    """Check the supported_industries reference table matches our 4 industries."""
    result = await supabase.table("supported_industries").select("*").execute()
    rows = result.data or []

    valid = []
    invalid = []
    missing = list(SUPPORTED_INDUSTRIES)

    for row in rows:
        slug = row.get("slug")
        if slug in SUPPORTED_INDUSTRIES:
            valid.append(slug)
            if slug in missing:
                missing.remove(slug)
        else:
            invalid.append({
                "slug": slug,
                "name": row.get("name"),
                "priority": row.get("priority"),
            })

    return {
        "table": "supported_industries",
        "total_rows": len(rows),
        "valid": valid,
        "invalid": invalid,
        "missing": missing,
        "status": "clean" if not invalid and not missing else "dirty",
    }


async def audit_vendors_table(supabase: Any) -> dict:
    """Check vendors.industries[] for invalid industry references."""
    result = await supabase.table("vendors").select(
        "id, slug, name, industries"
    ).execute()
    rows = result.data or []

    clean = 0
    dirty_rows = []

    for row in rows:
        industries = row.get("industries") or []
        # Vendors with ["*"] are cross-industry — valid but should be normalized
        if industries == ["*"]:
            # Cross-industry vendors: set to all 4
            dirty_rows.append({
                "id": row["id"],
                "slug": row.get("slug"),
                "name": row.get("name"),
                "current_industries": industries,
                "invalid_industries": ["*"],
                "valid_industries": list(SUPPORTED_INDUSTRIES),
            })
            continue

        invalid = [i for i in industries if i not in SUPPORTED_INDUSTRIES]
        if invalid:
            dirty_rows.append({
                "id": row["id"],
                "slug": row.get("slug"),
                "name": row.get("name"),
                "current_industries": industries,
                "invalid_industries": invalid,
                "valid_industries": [i for i in industries if i in SUPPORTED_INDUSTRIES],
            })
        else:
            clean += 1

    return {
        "table": "vendors",
        "total_rows": len(rows),
        "clean": clean,
        "dirty": len(dirty_rows),
        "dirty_rows": dirty_rows,
        "status": "clean" if not dirty_rows else "dirty",
    }


async def audit_industry_vendor_tiers(supabase: Any) -> dict:
    """Check industry_vendor_tiers for invalid industry values."""
    result = await supabase.table("industry_vendor_tiers").select(
        "id, industry, vendor_id, tier"
    ).execute()
    rows = result.data or []

    clean = 0
    invalid_rows = []

    for row in rows:
        industry = row.get("industry")
        if industry not in SUPPORTED_INDUSTRIES:
            invalid_rows.append({
                "id": row["id"],
                "industry": industry,
                "vendor_id": row.get("vendor_id"),
                "tier": row.get("tier"),
            })
        else:
            clean += 1

    return {
        "table": "industry_vendor_tiers",
        "total_rows": len(rows),
        "clean": clean,
        "invalid": len(invalid_rows),
        "invalid_rows": invalid_rows,
        "status": "clean" if not invalid_rows else "dirty",
    }


async def audit_workflow_templates(supabase: Any) -> dict:
    """Check workflow_templates for invalid industry values."""
    result = await supabase.table("workflow_templates").select(
        "id, slug, industry, name"
    ).execute()
    rows = result.data or []

    clean = 0
    invalid_rows = []

    for row in rows:
        industry = row.get("industry")
        if industry not in SUPPORTED_INDUSTRIES:
            invalid_rows.append({
                "id": row["id"],
                "slug": row.get("slug"),
                "industry": industry,
                "name": row.get("name"),
            })
        else:
            clean += 1

    return {
        "table": "workflow_templates",
        "total_rows": len(rows),
        "clean": clean,
        "invalid": len(invalid_rows),
        "invalid_rows": invalid_rows,
        "status": "clean" if not invalid_rows else "dirty",
    }


async def audit_knowledge_embeddings(supabase: Any) -> dict:
    """Check knowledge_embeddings for invalid industry references."""
    result = await supabase.table("knowledge_embeddings").select(
        "id, content_type, industry, source_file"
    ).not_.is_("industry", "null").execute()
    rows = result.data or []

    clean = 0
    invalid_rows = []

    for row in rows:
        industry = row.get("industry")
        if industry not in SUPPORTED_INDUSTRIES:
            invalid_rows.append({
                "id": row["id"],
                "content_type": row.get("content_type"),
                "industry": industry,
                "source_file": row.get("source_file"),
            })
        else:
            clean += 1

    return {
        "table": "knowledge_embeddings",
        "total_rows": len(rows),
        "clean": clean,
        "invalid": len(invalid_rows),
        "invalid_rows": invalid_rows,  # Full list needed for fix operations
        "status": "clean" if not invalid_rows else "dirty",
    }


async def audit_quiz_sessions(supabase: Any) -> dict:
    """Check quiz_sessions for industry values in JSONB answers."""
    result = await supabase.table("quiz_sessions").select(
        "id, answers, created_at"
    ).execute()
    rows = result.data or []

    industry_counts: dict[str, int] = {}
    invalid_sessions = []

    for row in rows:
        answers = row.get("answers") or {}
        industry = answers.get("industry") or answers.get("industry_slug")
        if industry:
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
            if industry not in SUPPORTED_INDUSTRIES:
                invalid_sessions.append({
                    "id": row["id"],
                    "industry": industry,
                    "created_at": row.get("created_at"),
                })

    return {
        "table": "quiz_sessions",
        "total_rows": len(rows),
        "industry_distribution": industry_counts,
        "invalid_industry_sessions": len(invalid_sessions),
        "invalid_samples": invalid_sessions[:10],  # Sample
        "status": "clean" if not invalid_sessions else "has_legacy_data",
    }


async def audit_reports(supabase: Any) -> dict:
    """Check reports for industry values in JSONB fields."""
    result = await supabase.table("reports").select(
        "id, agent_context, created_at, status"
    ).execute()
    rows = result.data or []

    industry_counts: dict[str, int] = {}
    invalid_reports = []

    for row in rows:
        ctx = row.get("agent_context") or {}
        industry = ctx.get("industry")
        if industry:
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
            if industry not in SUPPORTED_INDUSTRIES:
                invalid_reports.append({
                    "id": row["id"],
                    "industry": industry,
                    "status": row.get("status"),
                    "created_at": row.get("created_at"),
                })

    return {
        "table": "reports",
        "total_rows": len(rows),
        "industry_distribution": industry_counts,
        "invalid_industry_reports": len(invalid_reports),
        "invalid_samples": invalid_reports[:10],
        "status": "clean" if not invalid_reports else "has_legacy_data",
    }


# =============================================================================
# NORMALIZATION HELPERS
# =============================================================================

# Map display names / legacy values to supported slugs
_INDUSTRY_NORMALIZATION: dict[str, str | None] = {
    # Direct matches
    "professional-services": "professional-services",
    "dental": "dental",
    "ecommerce": "ecommerce",
    "b2b-platforms": "b2b-platforms",
    # Display name variants
    "e-commerce": "ecommerce",
    "E-commerce": "ecommerce",
    "Professional Services": "professional-services",
    "Dental": "dental",
    "B2B Platforms": "b2b-platforms",
    # Broad/cross-industry — these vendors serve our industries
    "*": None,  # Will be handled specially (set to all 4)
    "SaaS": "b2b-platforms",
    "B2B SaaS": "b2b-platforms",
    "Enterprise SaaS": "b2b-platforms",
    "Technology": "b2b-platforms",
    "Telecommunications": "b2b-platforms",
    "Financial Services": "professional-services",
    "Healthcare": "dental",
    "Retail": "ecommerce",
    "Manufacturing": "b2b-platforms",
    "Agencies": "professional-services",
    # Sub-industries that map to our 4
    "accounting": "professional-services",
    "consulting": "professional-services",
    "finance": "professional-services",
    "it-services": "b2b-platforms",
    "legal": "professional-services",
    # Not our focus — drop
    "Education": None,
    "Non-profits": None,
    "Media": None,
    "Hospitality": None,
    "Real Estate": None,
    "Construction": None,
    "Government": None,
    # Legacy industries — drop
    "home-services": None,
    "home_services": None,
    "recruiting": None,
    "coaching": None,
    "veterinary": None,
    "physical-therapy": None,
    "medspa": None,
    "marketing-agencies": None,
    "tech-companies": None,
    "music-studios": None,
    "general": None,
}


def _normalize_vendor_industry(value: str) -> str | None:
    """Normalize a vendor industry value to a supported slug, or None to drop."""
    if value == "*":
        return None  # Cross-industry vendor — industries will be set to None (all)
    return _INDUSTRY_NORMALIZATION.get(value)


# =============================================================================
# FIX OPERATIONS
# =============================================================================

async def fix_supported_industries(supabase: Any, audit: dict, dry_run: bool) -> dict:
    """Update supported_industries table to match our 4 industries."""
    actions = []

    # Delete invalid entries
    for entry in audit.get("invalid", []):
        slug = entry["slug"]
        if dry_run:
            actions.append(f"[DRY RUN] DELETE supported_industries WHERE slug='{slug}'")
        else:
            await supabase.table("supported_industries").delete().eq("slug", slug).execute()
            actions.append(f"DELETED supported_industries WHERE slug='{slug}'")

    # Insert missing entries
    display_names = {
        "professional-services": "Professional Services",
        "dental": "Dental Practices",
        "ecommerce": "E-commerce",
        "b2b-platforms": "B2B Platforms",
    }
    for slug in audit.get("missing", []):
        if dry_run:
            actions.append(f"[DRY RUN] INSERT supported_industries slug='{slug}'")
        else:
            await supabase.table("supported_industries").insert({
                "slug": slug,
                "name": display_names.get(slug, slug),
                "priority": "primary",
            }).execute()
            actions.append(f"INSERTED supported_industries slug='{slug}'")

    return {"actions": actions, "count": len(actions)}


async def fix_vendors(supabase: Any, audit: dict, dry_run: bool) -> dict:
    """Normalize vendor industries to supported slugs."""
    actions = []

    for row in audit.get("dirty_rows", []):
        vendor_id = row["id"]
        slug = row.get("slug")
        current = row["current_industries"]

        # Cross-industry vendors: set to all supported industries
        if current == ["*"]:
            new_industries = list(SUPPORTED_INDUSTRIES)
        else:
            # Normalize display names to slugs
            normalized = set()
            for ind in current:
                mapped = _normalize_vendor_industry(ind)
                if mapped:
                    normalized.add(mapped)
            new_industries = sorted(normalized) if normalized else []

        if dry_run:
            actions.append(
                f"[DRY RUN] UPDATE vendors SET industries={new_industries} "
                f"WHERE slug='{slug}' (was: {current})"
            )
        else:
            await supabase.table("vendors").update(
                {"industries": new_industries}
            ).eq("id", vendor_id).execute()
            actions.append(
                f"UPDATED vendors.industries={new_industries} WHERE slug='{slug}'"
            )

    return {"actions": actions, "count": len(actions)}


async def fix_industry_vendor_tiers(supabase: Any, audit: dict, dry_run: bool) -> dict:
    """Normalize industry_vendor_tiers display names to slugs, delete unmappable or dupes."""
    actions = []

    # Build set of existing valid (industry, vendor_id) pairs to detect duplicates
    all_rows = await supabase.table("industry_vendor_tiers").select(
        "id, industry, vendor_id"
    ).execute()
    existing_pairs: set[tuple[str, str]] = set()
    for r in (all_rows.data or []):
        if r["industry"] in SUPPORTED_INDUSTRIES:
            existing_pairs.add((r["industry"], r["vendor_id"]))

    for row in audit.get("invalid_rows", []):
        tier_id = row["id"]
        industry = row["industry"]
        vendor_id = row["vendor_id"]
        normalized = _INDUSTRY_NORMALIZATION.get(industry)

        if normalized and (normalized, vendor_id) not in existing_pairs:
            # Normalizable and no duplicate — update
            if dry_run:
                actions.append(
                    f"[DRY RUN] UPDATE industry_vendor_tiers SET industry='{normalized}' "
                    f"WHERE id='{tier_id}' (was: '{industry}')"
                )
            else:
                await supabase.table("industry_vendor_tiers").update(
                    {"industry": normalized}
                ).eq("id", tier_id).execute()
                actions.append(
                    f"UPDATED industry_vendor_tiers SET industry='{normalized}' "
                    f"(was: '{industry}')"
                )
            # Track newly created pair to prevent dupes within this batch
            existing_pairs.add((normalized, vendor_id))
        else:
            # Can't normalize or would create duplicate — delete
            reason = "duplicate" if normalized else "no mapping"
            if dry_run:
                actions.append(
                    f"[DRY RUN] DELETE industry_vendor_tiers WHERE id='{tier_id}' "
                    f"(industry='{industry}' — {reason})"
                )
            else:
                await supabase.table("industry_vendor_tiers").delete().eq(
                    "id", tier_id
                ).execute()
                actions.append(
                    f"DELETED industry_vendor_tiers WHERE industry='{industry}' — {reason}"
                )

    return {"actions": actions, "count": len(actions)}


async def fix_workflow_templates(supabase: Any, audit: dict, dry_run: bool) -> dict:
    """Delete workflow_templates for unsupported industries."""
    actions = []

    for row in audit.get("invalid_rows", []):
        wf_id = row["id"]
        industry = row["industry"]
        slug = row.get("slug")

        if dry_run:
            actions.append(
                f"[DRY RUN] DELETE workflow_templates WHERE id='{wf_id}' "
                f"(industry='{industry}', slug='{slug}')"
            )
        else:
            await supabase.table("workflow_templates").delete().eq(
                "id", wf_id
            ).execute()
            actions.append(
                f"DELETED workflow_templates WHERE slug='{slug}' (industry='{industry}')"
            )

    return {"actions": actions, "count": len(actions)}


async def fix_knowledge_embeddings(supabase: Any, audit: dict, dry_run: bool) -> dict:
    """Delete knowledge_embeddings for unsupported industries."""
    actions = []

    for row in audit.get("invalid_rows", []):
        emb_id = row["id"]
        industry = row["industry"]

        if dry_run:
            actions.append(
                f"[DRY RUN] DELETE knowledge_embeddings WHERE id='{emb_id}' "
                f"(industry='{industry}')"
            )
        else:
            await supabase.table("knowledge_embeddings").delete().eq(
                "id", emb_id
            ).execute()
            actions.append(
                f"DELETED knowledge_embeddings WHERE industry='{industry}'"
            )

    return {"actions": actions, "count": len(actions)}


# =============================================================================
# MAIN AUDIT PIPELINE
# =============================================================================

async def run_audit(fix: bool = False, dry_run: bool = False) -> dict:
    """Run full database audit."""
    from src.config.supabase_client import get_async_supabase

    supabase = await get_async_supabase()

    results: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "supported_industries": SUPPORTED_INDUSTRIES,
        "audits": {},
        "fixes": {},
        "summary": {
            "tables_audited": 0,
            "tables_clean": 0,
            "tables_dirty": 0,
            "total_invalid_rows": 0,
        },
    }

    # Run all audits
    audit_funcs = [
        ("supported_industries", audit_supported_industries_table),
        ("vendors", audit_vendors_table),
        ("industry_vendor_tiers", audit_industry_vendor_tiers),
        ("workflow_templates", audit_workflow_templates),
        ("knowledge_embeddings", audit_knowledge_embeddings),
        ("quiz_sessions", audit_quiz_sessions),
        ("reports", audit_reports),
    ]

    for name, func in audit_funcs:
        try:
            audit_result = await func(supabase)
            results["audits"][name] = audit_result
            results["summary"]["tables_audited"] += 1

            status = audit_result.get("status", "unknown")
            if status == "clean":
                results["summary"]["tables_clean"] += 1
            elif status == "has_legacy_data":
                # Legacy data is historical — acknowledged, not actionable
                results["summary"]["tables_clean"] += 1
            elif status == "dirty":
                results["summary"]["tables_dirty"] += 1
                # Count invalid rows
                invalid_count = (
                    audit_result.get("invalid", 0)
                    if isinstance(audit_result.get("invalid"), int)
                    else len(audit_result.get("invalid", audit_result.get("invalid_rows", [])))
                )
                dirty_count = audit_result.get("dirty", 0)
                results["summary"]["total_invalid_rows"] += invalid_count + dirty_count

        except Exception as e:
            logger.error("audit_failed", table=name, error=str(e))
            results["audits"][name] = {"error": str(e), "status": "error"}

    # Run fixes if requested
    if fix:
        fix_funcs = [
            ("supported_industries", fix_supported_industries, "supported_industries"),
            ("vendors", fix_vendors, "vendors"),
            ("industry_vendor_tiers", fix_industry_vendor_tiers, "industry_vendor_tiers"),
            ("workflow_templates", fix_workflow_templates, "workflow_templates"),
            ("knowledge_embeddings", fix_knowledge_embeddings, "knowledge_embeddings"),
        ]

        total_fixes = 0
        for name, func, audit_key in fix_funcs:
            audit_data = results["audits"].get(audit_key, {})
            if audit_data.get("status") in ("dirty",):
                try:
                    fix_result = await func(supabase, audit_data, dry_run)
                    results["fixes"][name] = fix_result
                    total_fixes += fix_result.get("count", 0)
                except Exception as e:
                    logger.error("fix_failed", table=name, error=str(e))
                    results["fixes"][name] = {"error": str(e)}

        results["summary"]["fixes_applied"] = total_fixes
        results["summary"]["dry_run"] = dry_run

    # Overall health
    if results["summary"]["tables_dirty"] == 0:
        results["health"] = "clean"
    elif results["summary"]["total_invalid_rows"] > 50:
        results["health"] = "critical"
    elif results["summary"]["total_invalid_rows"] > 10:
        results["health"] = "needs_cleanup"
    else:
        results["health"] = "minor_issues"

    return results


# =============================================================================
# OUTPUT FORMATTING
# =============================================================================

def print_result(result: dict, output_format: str = "text") -> None:
    """Print audit results."""
    if output_format == "json":
        print(json.dumps(result, indent=2, default=str))
        return

    print("=" * 60)
    print("DATABASE HYGIENE AUDIT")
    print(f"Timestamp: {result.get('timestamp', 'unknown')}")
    print(f"Supported industries: {', '.join(result.get('supported_industries', []))}")
    print("=" * 60)

    for table_name, audit in result.get("audits", {}).items():
        status = audit.get("status", "unknown")
        icon = "OK" if status == "clean" else "!!" if status == "dirty" else "~~" if status == "has_legacy_data" else "??"
        total = audit.get("total_rows", "?")

        print(f"\n[{icon}] {table_name} ({total} rows) — {status.upper()}")

        if status == "dirty":
            # Show invalid counts
            invalid_count = audit.get("dirty", audit.get("invalid", 0))
            if isinstance(invalid_count, list):
                invalid_count = len(invalid_count)
            print(f"     Invalid rows: {invalid_count}")

            # Show sample invalid data (capped for display)
            samples = (
                audit.get("dirty_rows", [])
                or audit.get("invalid_rows", [])
                or audit.get("invalid", [])
            )
            for row in (samples[:5] if isinstance(samples, list) else []):
                if isinstance(row, dict):
                    slug = row.get("slug", row.get("name", row.get("id", "?")))
                    industry = row.get("industry", row.get("invalid_industries", "?"))
                    print(f"       - {slug}: {industry}")

        elif status == "has_legacy_data":
            invalid_count = audit.get("invalid_industry_sessions", 0) + audit.get("invalid_industry_reports", 0)
            print(f"     Legacy industry rows: {invalid_count}")
            dist = audit.get("industry_distribution", {})
            if dist:
                print(f"     Distribution: {dict(sorted(dist.items(), key=lambda x: -x[1]))}")

    # Fixes
    fixes = result.get("fixes", {})
    if fixes:
        print("\n" + "=" * 60)
        print("FIXES APPLIED")
        print("=" * 60)
        for name, fix in fixes.items():
            count = fix.get("count", 0)
            print(f"\n  {name}: {count} actions")
            for action in fix.get("actions", [])[:10]:
                print(f"    {action}")

    # Summary
    summary = result.get("summary", {})
    print("\n" + "=" * 60)
    print(f"HEALTH: {result.get('health', 'unknown').upper()}")
    print(f"Tables audited: {summary.get('tables_audited', 0)}")
    print(f"Tables clean: {summary.get('tables_clean', 0)}")
    print(f"Tables with issues: {summary.get('tables_dirty', 0)}")
    print(f"Total invalid rows: {summary.get('total_invalid_rows', 0)}")
    if "fixes_applied" in summary:
        dry = " (DRY RUN)" if summary.get("dry_run") else ""
        print(f"Fixes applied: {summary['fixes_applied']}{dry}")
    print("=" * 60)


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="CRB Database Hygiene Audit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli.db_audit                    # Audit only
  python -m src.cli.db_audit --output json      # JSON output
  python -m src.cli.db_audit --fix --dry-run    # Preview fixes
  python -m src.cli.db_audit --fix              # Audit + fix
        """,
    )

    parser.add_argument(
        "--fix", action="store_true",
        help="Fix invalid data (delete/update rows with unsupported industries)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what --fix would do without making changes",
    )
    parser.add_argument(
        "--output", choices=["text", "json"], default="text",
        help="Output format",
    )

    args = parser.parse_args()

    result = asyncio.run(run_audit(fix=args.fix, dry_run=args.dry_run))
    print_result(result, args.output)

    # Exit code based on health
    health = result.get("health", "unknown")
    if health == "critical":
        sys.exit(2)
    elif health in ("needs_cleanup", "minor_issues"):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
