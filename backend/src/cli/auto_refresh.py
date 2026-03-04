"""
Automated data refresh pipeline.

Handles scheduled updates for:
- Vendor pricing refresh (stale vendors)
- Knowledge base freshness auditing
- Expertise store health checking

Usage:
    cd backend
    source venv/bin/activate

    # Full refresh cycle (vendor refresh + KB audit + expertise health)
    python -m src.cli.auto_refresh all

    # Individual commands
    python -m src.cli.auto_refresh vendors --auto-approve
    python -m src.cli.auto_refresh kb-audit
    python -m src.cli.auto_refresh expertise-health

    # Cron-friendly: JSON output, auto-approve non-significant changes
    python -m src.cli.auto_refresh all --output json --auto-approve

    # Dry run
    python -m src.cli.auto_refresh vendors --dry-run
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

import structlog

logger = structlog.get_logger()

# Paths
BACKEND_ROOT = Path(__file__).parent.parent.parent
EXPERTISE_DIR = BACKEND_ROOT / "src" / "expertise" / "data"
KNOWLEDGE_DIR = BACKEND_ROOT / "src" / "knowledge"

# Thresholds
KB_STALE_DAYS = 90
KB_AGING_DAYS = 30
VENDOR_STALE_DAYS = 90


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# =============================================================================
# VENDOR REFRESH
# =============================================================================

async def cmd_vendors(args) -> dict:
    """Refresh stale vendors using research agent."""
    from src.agents.research.schemas import RefreshRequest, RefreshScope
    from src.agents.research.refresh import refresh_vendors, get_stale_count, apply_vendor_updates

    result = {
        "command": "vendors",
        "timestamp": _now_iso(),
        "stale_count": 0,
        "refreshed": 0,
        "updates_found": 0,
        "errors": 0,
        "significant_changes": [],
    }

    # Check stale count
    stale_count = await get_stale_count()
    result["stale_count"] = stale_count

    if stale_count == 0:
        result["status"] = "ok"
        result["message"] = "No stale vendors found"
        return result

    # Run refresh
    request = RefreshRequest(
        scope=RefreshScope.STALE,
        dry_run=args.dry_run,
    )

    updates = []
    async for update in refresh_vendors(request):
        update_type = update.get("type")

        if update_type == "started":
            result["total"] = update.get("total", 0)

        elif update_type == "update":
            updates.append(update)
            if update.get("has_significant_changes"):
                result["significant_changes"].append({
                    "vendor": update.get("vendor_name"),
                    "slug": update.get("vendor_slug"),
                    "changes": update.get("changes", []),
                })

        elif update_type == "error":
            result["errors"] += 1

        elif update_type == "completed":
            result["refreshed"] = update.get("total", 0)
            result["updates_found"] = update.get("updates", 0)

    # Auto-approve non-significant if requested and persist changes
    if args.auto_approve and not args.dry_run and updates:
        non_significant = [u for u in updates if not u.get("has_significant_changes")]
        result["auto_approved"] = len(non_significant)
        result["requires_review"] = len(result["significant_changes"])

        # Actually persist non-significant changes
        if non_significant:
            approved_slugs = [u.get("vendor_slug") for u in non_significant if u.get("vendor_slug")]
            if approved_slugs:
                try:
                    # Reconstruct VendorUpdate objects for apply
                    from src.agents.research.schemas import VendorUpdate, FieldChange
                    vendor_updates = []
                    for u in non_significant:
                        changes = [
                            FieldChange(**c) if isinstance(c, dict) else c
                            for c in u.get("changes", [])
                        ]
                        vendor_updates.append(VendorUpdate(
                            vendor_slug=u.get("vendor_slug", ""),
                            vendor_name=u.get("vendor_name", ""),
                            source_url="auto-refresh",
                            changes=changes,
                            extracted_data=u.get("extracted_data"),
                        ))
                    applied = await apply_vendor_updates(
                        task_id="auto-refresh",
                        approved_slugs=approved_slugs,
                        updates=vendor_updates,
                    )
                    result["applied"] = applied
                    logger.info(
                        "auto_refresh_applied",
                        count=applied.get("applied_count", 0),
                        errors=len(applied.get("errors", [])),
                    )
                except Exception as e:
                    logger.error("auto_refresh_apply_failed", error=str(e))
                    result["apply_error"] = str(e)
    else:
        result["auto_approved"] = 0
        result["requires_review"] = len(updates)

    result["status"] = "ok" if result["errors"] == 0 else "warning"
    return result


# =============================================================================
# KNOWLEDGE BASE AUDIT
# =============================================================================

def cmd_kb_audit(args) -> dict:
    """Audit knowledge base freshness across all industries."""
    result = {
        "command": "kb-audit",
        "timestamp": _now_iso(),
        "industries": {},
        "vendor_categories": {},
        "summary": {
            "total_files": 0,
            "fresh": 0,
            "current": 0,
            "aging": 0,
            "stale": 0,
            "no_date": 0,
        },
    }

    # Audit industry knowledge files
    industries = ["dental", "ecommerce", "professional-services", "b2b-platforms"]
    data_types = ["benchmarks", "opportunities", "processes", "vendors"]

    for industry in industries:
        result["industries"][industry] = {}
        for data_type in data_types:
            file_path = KNOWLEDGE_DIR / industry / f"{data_type}.json"
            audit = _audit_file(file_path)
            result["industries"][industry][data_type] = audit
            result["summary"]["total_files"] += 1
            result["summary"][audit["freshness"]] += 1

    # Audit vendor category files
    vendor_dir = KNOWLEDGE_DIR / "vendors"
    if vendor_dir.exists():
        for vendor_file in sorted(vendor_dir.glob("*.json")):
            audit = _audit_file(vendor_file)
            category = vendor_file.stem
            result["vendor_categories"][category] = audit
            result["summary"]["total_files"] += 1
            result["summary"][audit["freshness"]] += 1

    # Audit curated insights
    insights_dir = KNOWLEDGE_DIR / "insights" / "curated"
    if insights_dir.exists():
        result["curated_insights"] = {}
        for insight_file in sorted(insights_dir.glob("*.json")):
            audit = _audit_file(insight_file)
            result["curated_insights"][insight_file.stem] = audit
            result["summary"]["total_files"] += 1
            result["summary"][audit["freshness"]] += 1

    # Overall health
    stale_pct = (
        result["summary"]["stale"] / max(result["summary"]["total_files"], 1)
    ) * 100
    if stale_pct > 50:
        result["health"] = "critical"
    elif stale_pct > 25:
        result["health"] = "warning"
    elif result["summary"]["aging"] > result["summary"]["fresh"]:
        result["health"] = "aging"
    else:
        result["health"] = "healthy"

    return result


def _audit_file(file_path: Path) -> dict:
    """Audit a single knowledge base file for freshness."""
    if not file_path.exists():
        return {
            "exists": False,
            "freshness": "no_date",
            "message": "File not found",
        }

    try:
        with open(file_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {
            "exists": True,
            "freshness": "no_date",
            "message": "Failed to parse",
        }

    # Extract last_updated from various formats
    last_updated = (
        data.get("last_updated")
        or data.get("verified_date")
        or data.get("extracted_at")
    )

    if not last_updated:
        return {
            "exists": True,
            "freshness": "no_date",
            "message": "No date metadata",
            "entry_count": _count_entries(data),
        }

    # Parse date
    try:
        if len(str(last_updated)) <= 10:
            # Handle "2025-12" or "2025-12-27" format
            if len(str(last_updated)) == 7:
                updated_date = datetime.strptime(str(last_updated), "%Y-%m")
            else:
                updated_date = datetime.strptime(str(last_updated), "%Y-%m-%d")
        else:
            updated_date = datetime.fromisoformat(
                str(last_updated).replace("Z", "+00:00").replace("+00:00", "")
            )
    except (ValueError, TypeError):
        return {
            "exists": True,
            "freshness": "no_date",
            "message": f"Unparseable date: {last_updated}",
            "entry_count": _count_entries(data),
        }

    days_old = (datetime.now(timezone.utc) - updated_date).days

    if days_old <= 7:
        freshness = "fresh"
    elif days_old <= KB_AGING_DAYS:
        freshness = "current"
    elif days_old <= KB_STALE_DAYS:
        freshness = "aging"
    else:
        freshness = "stale"

    return {
        "exists": True,
        "freshness": freshness,
        "last_updated": str(last_updated),
        "days_old": days_old,
        "entry_count": _count_entries(data),
        "verification_status": data.get("verification_status"),
    }


def _count_entries(data: dict) -> int:
    """Count meaningful entries in a knowledge base file."""
    count = 0
    for key in ["vendors", "ai_opportunities", "common_processes", "benchmarks",
                 "pain_points", "vendor_categories", "categories"]:
        value = data.get(key)
        if isinstance(value, list):
            count += len(value)
        elif isinstance(value, dict):
            count += len(value)
    return count


# =============================================================================
# EXPERTISE STORE HEALTH
# =============================================================================

def cmd_expertise_health(args) -> dict:
    """Check health of the self-improving expertise store."""
    result = {
        "command": "expertise-health",
        "timestamp": _now_iso(),
        "industries": {},
        "vendors": {},
        "execution": {},
        "records": {},
    }

    # Check industry expertise files
    industries_dir = EXPERTISE_DIR / "industries"
    if industries_dir.exists():
        for industry_file in sorted(industries_dir.glob("*.json")):
            try:
                with open(industry_file) as f:
                    data = json.load(f)

                industry = industry_file.stem
                pain_points = data.get("pain_points", {})
                processes = data.get("processes", {})
                patterns = data.get("effective_patterns", [])
                anti_patterns = data.get("anti_patterns", [])

                result["industries"][industry] = {
                    "total_analyses": data.get("total_analyses", 0),
                    "confidence": data.get("confidence", "unknown"),
                    "last_updated": data.get("last_updated"),
                    "pain_points_count": len(pain_points),
                    "processes_count": len(processes),
                    "patterns_count": len(patterns),
                    "anti_patterns_count": len(anti_patterns),
                    "size_segments": list(data.get("size_specific", {}).keys()),
                    "avg_readiness": data.get("avg_ai_readiness"),
                    "avg_savings": data.get("avg_potential_savings"),
                    "has_tech_stacks": bool(data.get("common_tech_stacks")),
                    "health": _assess_industry_health(data),
                }
            except (json.JSONDecodeError, OSError) as e:
                result["industries"][industry_file.stem] = {"error": str(e)}

    # Check vendor expertise
    vendors_file = EXPERTISE_DIR / "vendors.json"
    if vendors_file.exists():
        try:
            with open(vendors_file) as f:
                data = json.load(f)
            result["vendors"] = {
                "last_updated": data.get("last_updated"),
                "total_recommendations": data.get("total_recommendations", 0),
                "vendor_count": len(data.get("vendors", {})),
                "category_insights_count": len(data.get("category_insights", {})),
                "health": "empty" if not data.get("vendors") else "populated",
            }
        except (json.JSONDecodeError, OSError) as e:
            result["vendors"] = {"error": str(e)}

    # Check execution metrics
    execution_file = EXPERTISE_DIR / "execution.json"
    if execution_file.exists():
        try:
            with open(execution_file) as f:
                data = json.load(f)
            result["execution"] = {
                "last_updated": data.get("last_updated"),
                "total_executions": data.get("total_executions", 0),
                "tools_tracked": len(data.get("tool_success_rates", {})),
                "phase_insights": len(data.get("phase_insights", {})),
                "failure_patterns": len(data.get("failure_patterns", [])),
            }
        except (json.JSONDecodeError, OSError) as e:
            result["execution"] = {"error": str(e)}

    # Count analysis records
    records_dir = EXPERTISE_DIR / "records"
    if records_dir.exists():
        record_files = list(records_dir.glob("*.json"))
        result["records"] = {
            "total_records": len(record_files),
        }

    return result


def _assess_industry_health(data: dict) -> str:
    """Assess overall health of an industry expertise entry."""
    analyses = data.get("total_analyses", 0)
    pain_points = len(data.get("pain_points", {}))
    processes = len(data.get("processes", {}))

    if analyses == 0:
        return "empty"
    if pain_points == 0 or processes == 0:
        return "incomplete"
    if analyses < 5:
        return "low_confidence"
    if analyses < 20:
        return "growing"
    return "mature"


# =============================================================================
# COMBINED PIPELINE
# =============================================================================

async def cmd_all(args) -> dict:
    """Run full refresh pipeline with auto-action triggers."""
    results = {
        "command": "all",
        "timestamp": _now_iso(),
        "pipeline": [],
        "auto_actions": [],
    }

    # 1. KB audit first (informs which vendors need refresh)
    print("=" * 60)
    print("STEP 1: Knowledge Base Audit")
    print("=" * 60)
    kb_result = cmd_kb_audit(args)
    results["pipeline"].append(kb_result)

    # 2. Vendor refresh
    print("\n" + "=" * 60)
    print("STEP 2: Vendor Refresh")
    print("=" * 60)
    vendor_result = await cmd_vendors(args)
    results["pipeline"].append(vendor_result)

    # 3. Expertise health
    print("\n" + "=" * 60)
    print("STEP 3: Expertise Store Health")
    print("=" * 60)
    expertise_result = cmd_expertise_health(args)
    results["pipeline"].append(expertise_result)

    # 4. Database hygiene audit
    print("\n" + "=" * 60)
    print("STEP 4: Database Hygiene Audit")
    print("=" * 60)
    try:
        from src.cli.db_audit import run_audit as run_db_audit
        db_result = await run_db_audit(fix=False)
        results["pipeline"].append({"command": "db-audit", **db_result.get("summary", {})})
        db_health = db_result.get("health", "unknown")
        print(f"  Health: {db_health.upper()}")
        print(f"  Tables: {db_result['summary']['tables_audited']} audited, "
              f"{db_result['summary']['tables_clean']} clean, "
              f"{db_result['summary']['tables_dirty']} with issues")
        if db_result["summary"]["total_invalid_rows"] > 0:
            print(f"  Invalid rows: {db_result['summary']['total_invalid_rows']}")
            print(f"  Run: make db-audit-fix  to clean up")
    except Exception as e:
        logger.error("db_audit_failed", error=str(e))
        print(f"  DB audit failed: {e}")

    # 5. Auto-action triggers based on audit results
    auto_actions = _evaluate_auto_actions(kb_result, vendor_result, expertise_result)
    results["auto_actions"] = auto_actions

    if auto_actions:
        print("\n" + "=" * 60)
        print("STEP 5: Auto-Actions Triggered")
        print("=" * 60)
        for action in auto_actions:
            print(f"  [{action['severity']}] {action['action']}: {action['reason']}")

    # Summary
    results["overall_health"] = _overall_health(vendor_result, kb_result, expertise_result)

    # Write refresh log
    _write_refresh_log(results)

    return results


def _evaluate_auto_actions(
    kb_result: dict, vendor_result: dict, expertise_result: dict
) -> list:
    """Evaluate audit results and determine what auto-actions to trigger."""
    actions = []

    # KB health triggers
    kb_health = kb_result.get("health", "healthy")
    if kb_health in ("critical", "warning"):
        # Find which industries have stale data
        stale_industries = []
        for industry, types in kb_result.get("industries", {}).items():
            stale_types = [
                t for t, info in types.items()
                if isinstance(info, dict) and info.get("freshness") in ("stale",)
            ]
            if stale_types:
                stale_industries.append({"industry": industry, "stale_types": stale_types})

        if stale_industries:
            actions.append({
                "severity": "high",
                "action": "kb_refresh_needed",
                "reason": f"KB health is {kb_health}. Stale: {', '.join(i['industry'] for i in stale_industries)}",
                "details": stale_industries,
            })

    # Vendor health triggers
    stale_count = vendor_result.get("stale_count", 0)
    if stale_count > 20:
        actions.append({
            "severity": "high",
            "action": "vendor_bulk_refresh",
            "reason": f"{stale_count} stale vendors — consider full vendor discovery cycle",
        })

    significant_changes = vendor_result.get("significant_changes", [])
    if significant_changes:
        actions.append({
            "severity": "medium",
            "action": "review_significant_changes",
            "reason": f"{len(significant_changes)} vendors have significant price/feature changes",
            "details": [c["vendor"] for c in significant_changes],
        })

    # Expertise health triggers
    for industry, data in expertise_result.get("industries", {}).items():
        if not isinstance(data, dict):
            continue
        health = data.get("health", "unknown")
        if health in ("empty", "incomplete"):
            actions.append({
                "severity": "critical" if health == "empty" else "high",
                "action": "expertise_populate",
                "reason": f"{industry} expertise is {health} — needs data population",
                "details": {"industry": industry, "analyses": data.get("total_analyses", 0)},
            })

    vendor_expertise_health = expertise_result.get("vendors", {}).get("health", "unknown")
    if vendor_expertise_health == "empty":
        actions.append({
            "severity": "critical",
            "action": "vendor_expertise_seed",
            "reason": "Vendor expertise store is empty — self-improvement loop not working",
        })

    return actions


REFRESH_LOG_PATH = BACKEND_ROOT / "src" / "data" / "refresh_log.json"


def _write_refresh_log(results: dict) -> None:
    """Append to the refresh log for historical tracking."""
    log_entry = {
        "timestamp": results.get("timestamp", _now_iso()),
        "overall_health": results.get("overall_health", "unknown"),
        "auto_actions_count": len(results.get("auto_actions", [])),
        "vendor_stale": 0,
        "vendor_refreshed": 0,
        "kb_health": "unknown",
        "expertise_health": {},
    }

    # Extract key metrics from pipeline
    for step in results.get("pipeline", []):
        cmd = step.get("command")
        if cmd == "vendors":
            log_entry["vendor_stale"] = step.get("stale_count", 0)
            log_entry["vendor_refreshed"] = step.get("refreshed", 0)
        elif cmd == "kb-audit":
            log_entry["kb_health"] = step.get("health", "unknown")
        elif cmd == "expertise-health":
            for ind, data in step.get("industries", {}).items():
                if isinstance(data, dict):
                    log_entry["expertise_health"][ind] = data.get("health", "unknown")

    # Read existing log or create new
    log_data = {"entries": []}
    if REFRESH_LOG_PATH.exists():
        try:
            with open(REFRESH_LOG_PATH) as f:
                log_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    log_data["entries"].append(log_entry)
    # Keep last 100 entries
    log_data["entries"] = log_data["entries"][-100:]
    log_data["last_run"] = log_entry["timestamp"]

    REFRESH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REFRESH_LOG_PATH, "w") as f:
        json.dump(log_data, f, indent=2, default=str)


def _overall_health(vendor_result: dict, kb_result: dict, expertise_result: dict) -> str:
    """Calculate overall system health."""
    issues = []

    if vendor_result.get("stale_count", 0) > 10:
        issues.append("many_stale_vendors")
    if kb_result.get("health") in ("critical", "warning"):
        issues.append("kb_stale")
    for ind, data in expertise_result.get("industries", {}).items():
        if isinstance(data, dict) and data.get("health") in ("empty", "incomplete"):
            issues.append(f"{ind}_incomplete")
    if expertise_result.get("vendors", {}).get("health") == "empty":
        issues.append("vendor_expertise_empty")

    if len(issues) > 3:
        return "critical"
    elif len(issues) > 1:
        return "needs_attention"
    elif issues:
        return "minor_issues"
    return "healthy"


# =============================================================================
# OUTPUT FORMATTING
# =============================================================================

def print_result(result: dict, output_format: str = "text"):
    """Print results in requested format."""
    if output_format == "json":
        print(json.dumps(result, indent=2, default=str))
        return

    command = result.get("command", "unknown")

    if command == "vendors":
        _print_vendor_result(result)
    elif command == "kb-audit":
        _print_kb_result(result)
    elif command == "expertise-health":
        _print_expertise_result(result)
    elif command == "all":
        for step in result.get("pipeline", []):
            print_result(step, output_format)
            print()
        print(f"\nOverall Health: {result.get('overall_health', 'unknown').upper()}")


def _print_vendor_result(result: dict):
    """Print vendor refresh results."""
    print(f"Stale vendors: {result.get('stale_count', 0)}")
    print(f"Refreshed: {result.get('refreshed', 0)}")
    print(f"Updates found: {result.get('updates_found', 0)}")
    print(f"Errors: {result.get('errors', 0)}")

    significant = result.get("significant_changes", [])
    if significant:
        print(f"\nSignificant changes ({len(significant)}):")
        for change in significant:
            print(f"  {change['vendor']}: {len(change.get('changes', []))} changes")


def _print_kb_result(result: dict):
    """Print KB audit results."""
    summary = result.get("summary", {})
    print(f"Knowledge Base Health: {result.get('health', 'unknown').upper()}")
    print(f"Total files: {summary.get('total_files', 0)}")
    print(f"  Fresh:   {summary.get('fresh', 0)}")
    print(f"  Current: {summary.get('current', 0)}")
    print(f"  Aging:   {summary.get('aging', 0)}")
    print(f"  Stale:   {summary.get('stale', 0)}")
    print(f"  No date: {summary.get('no_date', 0)}")

    # Show stale/aging files
    for industry, types in result.get("industries", {}).items():
        stale_types = [
            t for t, info in types.items()
            if isinstance(info, dict) and info.get("freshness") in ("stale", "aging")
        ]
        if stale_types:
            print(f"\n  {industry}: {', '.join(stale_types)} need refresh")


def _print_expertise_result(result: dict):
    """Print expertise health results."""
    print("Expertise Store Health:")
    for industry, data in result.get("industries", {}).items():
        if isinstance(data, dict) and "health" in data:
            print(
                f"  {industry}: {data['health']} "
                f"(analyses={data.get('total_analyses', 0)}, "
                f"pain_points={data.get('pain_points_count', 0)}, "
                f"processes={data.get('processes_count', 0)})"
            )

    vendor_health = result.get("vendors", {}).get("health", "unknown")
    print(f"  Vendor patterns: {vendor_health}")

    records = result.get("records", {}).get("total_records", 0)
    print(f"  Analysis records: {records}")


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CRB Data Intelligence Auto-Refresh Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli.auto_refresh all                    # Full pipeline
  python -m src.cli.auto_refresh vendors --auto-approve # Refresh stale vendors
  python -m src.cli.auto_refresh kb-audit               # Audit KB freshness
  python -m src.cli.auto_refresh expertise-health       # Check expertise store

Cron setup (weekly):
  0 3 * * 1 cd /path/to/backend && source venv/bin/activate && \\
    python -m src.cli.auto_refresh all --auto-approve --output json \\
    >> /var/log/crb-refresh.log 2>&1
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # All command
    all_parser = subparsers.add_parser("all", help="Run full refresh pipeline")
    all_parser.add_argument("--dry-run", action="store_true")
    all_parser.add_argument("--auto-approve", action="store_true")
    all_parser.add_argument("--output", choices=["text", "json"], default="text")

    # Vendors command
    vendor_parser = subparsers.add_parser("vendors", help="Refresh stale vendors")
    vendor_parser.add_argument("--dry-run", action="store_true")
    vendor_parser.add_argument("--auto-approve", action="store_true")
    vendor_parser.add_argument("--output", choices=["text", "json"], default="text")

    # KB audit command
    kb_parser = subparsers.add_parser("kb-audit", help="Audit knowledge base freshness")
    kb_parser.add_argument("--output", choices=["text", "json"], default="text")

    # Expertise health command
    exp_parser = subparsers.add_parser("expertise-health", help="Check expertise store health")
    exp_parser.add_argument("--output", choices=["text", "json"], default="text")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Run command
    if args.command == "all":
        result = asyncio.run(cmd_all(args))
    elif args.command == "vendors":
        result = asyncio.run(cmd_vendors(args))
    elif args.command == "kb-audit":
        result = cmd_kb_audit(args)
    elif args.command == "expertise-health":
        result = cmd_expertise_health(args)
    else:
        parser.print_help()
        sys.exit(1)

    print_result(result, args.output)

    # Exit code based on health
    health = result.get("health") or result.get("overall_health") or result.get("status", "ok")
    if health in ("critical", "error"):
        sys.exit(2)
    elif health in ("warning", "needs_attention"):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
