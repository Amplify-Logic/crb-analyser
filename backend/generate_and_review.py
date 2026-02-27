"""
Generate a CRB report and review recommendation quality.

Usage:
    # Professional Services (start here)
    python generate_and_review.py --industry professional-services

    # Dental
    python generate_and_review.py --industry dental

    # E-commerce
    python generate_and_review.py --industry ecommerce

    # B2B Platforms
    python generate_and_review.py --industry b2b-platforms

    # Specific company tier
    python generate_and_review.py --industry dental --tier small
    python generate_and_review.py --industry dental --tier mid

    # Quick tier (Sonnet, faster/cheaper for iteration)
    python generate_and_review.py --industry professional-services --quick

All reports use Opus 4.6 by default (--report-tier full).
Reports are saved to reports/<industry>/<timestamp>_<company>.json
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from src.cli.generate_report import load_seeds, pick_seed, generate_single_report
from src.config.supabase_client import get_async_supabase


REPORTS_DIR = Path(__file__).parent / "reports"


def ensure_dir(industry: str) -> Path:
    """Create reports directory for industry."""
    d = REPORTS_DIR / industry
    d.mkdir(parents=True, exist_ok=True)
    return d


async def fetch_report(report_id: str) -> dict:
    """Fetch full report JSON from Supabase."""
    supabase = await get_async_supabase()
    result = await supabase.table("reports").select("*").eq("id", report_id).execute()
    if result.data:
        return result.data[0]
    return {}


def analyze_recommendations(report_data: dict) -> dict:
    """Analyze recommendation quality from a generated report."""
    recommendations = report_data.get("recommendations", [])
    if isinstance(recommendations, str):
        recommendations = json.loads(recommendations)
    findings = report_data.get("findings", [])
    if isinstance(findings, str):
        findings = json.loads(findings)
    exec_summary = report_data.get("executive_summary", {})
    if isinstance(exec_summary, str):
        exec_summary = json.loads(exec_summary)

    # --- Recommendation distribution ---
    rec_counts = {"connect_and_automate": 0, "enhance_with_ai": 0, "targeted_upgrade": 0}
    rec_details = []

    for rec in recommendations:
        our_rec = rec.get("our_recommendation", "unknown")
        if our_rec in rec_counts:
            rec_counts[our_rec] += 1

        rationale = rec.get("recommendation_rationale", "")
        options = rec.get("options", {})

        # Check for boilerplate
        is_boilerplate = any(phrase in rationale.lower() for phrase in [
            "your existing tools likely support",
            "ships in days, not weeks",
            "costs a fraction of a saas",
        ])

        # Check targeted_upgrade when_needed quality
        tu = options.get("targeted_upgrade", {})
        tu_when = tu.get("when_needed", "")
        tu_is_boilerplate = "no api or are fundamentally broken" in tu_when.lower()

        # Check connect cost includes dev labor
        ca = options.get("connect_and_automate", {})
        ca_cost = ca.get("monthly_cost", "")
        has_dev_labor = any(w in ca_cost.lower() for w in ["hour", "build", "dev", "labor"])

        # NET scores
        net_scores = rec.get("net_scores", {})

        rec_details.append({
            "title": rec.get("title", "?")[:60],
            "recommendation": our_rec,
            "rationale_preview": rationale[:80] + "..." if len(rationale) > 80 else rationale,
            "is_boilerplate_rationale": is_boilerplate,
            "tu_when_needed_boilerplate": tu_is_boilerplate,
            "connect_has_dev_labor": has_dev_labor,
            "net_scores": {
                k: round(v, 1) if isinstance(v, (int, float)) else v
                for k, v in net_scores.items()
                if k in ("connect_and_automate", "enhance_with_ai", "targeted_upgrade")
            },
        })

    # --- NET score spread ---
    all_spreads = []
    for rd in rec_details:
        scores = rd["net_scores"]
        if len(scores) >= 2:
            vals = [v for v in scores.values() if isinstance(v, (int, float))]
            if vals:
                all_spreads.append(max(vals) - min(vals))

    return {
        "total_findings": len(findings),
        "total_recommendations": len(recommendations),
        "ai_readiness_score": exec_summary.get("ai_readiness_score", "?"),
        "recommendation_distribution": rec_counts,
        "boilerplate_rationales": sum(1 for r in rec_details if r["is_boilerplate_rationale"]),
        "boilerplate_when_needed": sum(1 for r in rec_details if r["tu_when_needed_boilerplate"]),
        "connect_missing_dev_labor": sum(1 for r in rec_details if not r["connect_has_dev_labor"]),
        "avg_net_score_spread": round(sum(all_spreads) / len(all_spreads), 1) if all_spreads else "N/A",
        "details": rec_details,
    }


def print_quality_report(analysis: dict, company: str, industry: str) -> None:
    """Print a formatted quality report."""
    print(f"\n{'=' * 70}")
    print(f"  QUALITY REVIEW: {company} ({industry})")
    print(f"{'=' * 70}")

    dist = analysis["recommendation_distribution"]
    total = analysis["total_recommendations"]

    print(f"\n  Findings: {analysis['total_findings']}")
    print(f"  Recommendations: {total}")
    print(f"  AI Readiness Score: {analysis['ai_readiness_score']}")

    print(f"\n  RECOMMENDATION DISTRIBUTION:")
    for opt, count in dist.items():
        pct = (count / total * 100) if total > 0 else 0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        label = {
            "connect_and_automate": "Connect & Automate",
            "enhance_with_ai": "Enhance with AI  ",
            "targeted_upgrade": "Targeted Upgrade ",
        }.get(opt, opt)
        print(f"    {label}  [{bar}] {count}/{total} ({pct:.0f}%)")

    print(f"\n  QUALITY FLAGS:")
    bp = analysis["boilerplate_rationales"]
    bw = analysis["boilerplate_when_needed"]
    dl = analysis["connect_missing_dev_labor"]
    spread = analysis["avg_net_score_spread"]

    print(f"    Boilerplate rationales:     {bp}/{total}  {'✓ CLEAN' if bp == 0 else '✗ FIX NEEDED'}")
    print(f"    Boilerplate when_needed:    {bw}/{total}  {'✓ CLEAN' if bw == 0 else '✗ FIX NEEDED'}")
    print(f"    Connect missing dev labor:  {dl}/{total}  {'✓ INCLUDED' if dl == 0 else '⚠ CHECK'}")
    print(f"    Avg NET score spread:       {spread}      {'✓ NEUTRAL' if isinstance(spread, (int, float)) and spread < 10 else '⚠ BIASED' if isinstance(spread, (int, float)) else '?'}")

    print(f"\n  PER-RECOMMENDATION BREAKDOWN:")
    print(f"  {'#':>3}  {'Title':<40}  {'Rec':<22}  {'Boilerplate':>10}  {'NET Spread':>10}")
    print(f"  {'─'*3}  {'─'*40}  {'─'*22}  {'─'*10}  {'─'*10}")

    for i, rd in enumerate(analysis["details"], 1):
        title = rd["title"][:40].ljust(40)
        rec_label = {
            "connect_and_automate": "Connect",
            "enhance_with_ai": "Enhance",
            "targeted_upgrade": "Upgrade",
        }.get(rd["recommendation"], rd["recommendation"])
        bp_flag = "YES ✗" if rd["is_boilerplate_rationale"] else "no"
        scores = rd["net_scores"]
        if scores:
            vals = [v for v in scores.values() if isinstance(v, (int, float))]
            spread_str = f"{max(vals) - min(vals):.1f}" if len(vals) >= 2 else "—"
        else:
            spread_str = "—"

        print(f"  {i:3d}  {title}  {rec_label:<22}  {bp_flag:>10}  {spread_str:>10}")

    print(f"\n{'=' * 70}\n")


async def main():
    parser = argparse.ArgumentParser(description="Generate and review CRB report quality")
    parser.add_argument("--industry", required=True,
                        choices=["professional-services", "dental", "ecommerce", "b2b-platforms"])
    parser.add_argument("--tier", choices=["small", "mid", "scaling"],
                        help="Filter seed by business tier")
    parser.add_argument("--quick", action="store_true",
                        help="Use quick tier (Sonnet) instead of full (Opus)")
    parser.add_argument("--seed-name", help="Use a specific seed company by name")
    parser.add_argument("--dev-mode", action="store_true", dest="dev_mode",
                        help="Route LLM calls through Claude Code CLI (uses Max subscription instead of API credits)")
    args = parser.parse_args()

    report_tier = "quick" if args.quick else "full"
    dev_mode = getattr(args, 'dev_mode', False)
    industry = args.industry

    # Load seeds
    seeds_data = load_seeds(industry)

    # Pick seed
    if args.seed_name:
        seed = None
        for s in seeds_data["seeds"]:
            if s["name"].lower() == args.seed_name.lower():
                seed = s
                break
        if not seed:
            names = [s["name"] for s in seeds_data["seeds"]]
            print(f"Seed '{args.seed_name}' not found. Available: {', '.join(names)}")
            sys.exit(1)
    else:
        seed = pick_seed(seeds_data, args.tier)

    company = seed["name"]
    print(f"\n  Generating {report_tier.upper()} report for: {company} ({industry})")
    print(f"  Model: {'Opus 4.6 (full)' if report_tier == 'full' else 'Sonnet 4.6 (quick)'}")
    if dev_mode:
        print(f"  DEV MODE: Using Claude CLI (Max subscription) instead of Anthropic API")

    # Generate
    start = time.time()
    result = await generate_single_report(
        seed=seed,
        seeds_data=seeds_data,
        report_tier=report_tier,
        scrape=False,
        skip_review=False,
        dev_mode=dev_mode,
    )

    if not result:
        print("  FAILED to generate report")
        sys.exit(1)

    # Fetch full report
    print("  Fetching report from Supabase...", end="", flush=True)
    report_data = await fetch_report(result["report_id"])
    print(" done")

    # Save to file
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = company.lower().replace(" ", "_").replace("&", "and")
    out_dir = ensure_dir(industry)
    out_file = out_dir / f"{ts}_{safe_name}.json"

    with open(out_file, "w") as f:
        json.dump(report_data, f, indent=2, default=str)
    print(f"  Saved to: {out_file}")

    # Analyze quality
    analysis = analyze_recommendations(report_data)

    # Save analysis
    analysis_file = out_dir / f"{ts}_{safe_name}_quality.json"
    with open(analysis_file, "w") as f:
        json.dump(analysis, f, indent=2, default=str)

    # Print quality report
    print_quality_report(analysis, company, industry)

    elapsed = time.time() - start
    print(f"  Total time: {elapsed:.0f}s | Cost: ~${'2-5' if report_tier == 'full' else '0.50-1.50'}")
    print(f"  Report: {out_file}")
    print(f"  Quality: {analysis_file}\n")


if __name__ == "__main__":
    asyncio.run(main())
