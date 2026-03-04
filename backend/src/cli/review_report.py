"""
CRB Report Reviewer CLI

Review the latest generated report for an industry, or a specific report file.

Usage:
    # Review latest report for an industry
    python -m src.cli.review_report --industry professional-services
    python -m src.cli.review_report --industry dental
    python -m src.cli.review_report --industry ecommerce

    # Review a specific report file
    python -m src.cli.review_report --file reports/dental/20260227_120000_smile_dental.json

    # List available reports for an industry
    python -m src.cli.review_report --industry dental --list
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPORTS_DIR = Path(__file__).parents[2] / "reports"


def list_reports(industry: str) -> List[Path]:
    """List report files for an industry, newest first."""
    industry_dir = REPORTS_DIR / industry
    if not industry_dir.exists():
        return []
    # Only main reports (not _quality files)
    return sorted(
        [p for p in industry_dir.glob("*.json") if "_quality" not in p.name],
        reverse=True,
    )


def load_report(path: Path) -> Dict[str, Any]:
    """Load a report JSON file."""
    with open(path) as f:
        return json.load(f)


def analyze_recommendations(report_data: Dict[str, Any]) -> Dict[str, Any]:
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

    rec_counts = {"connect_and_automate": 0, "enhance_with_ai": 0, "targeted_upgrade": 0}
    rec_details = []

    for rec in recommendations:
        our_rec = rec.get("our_recommendation", "unknown")
        if our_rec in rec_counts:
            rec_counts[our_rec] += 1

        rationale = rec.get("recommendation_rationale", "")
        options = rec.get("options", {})

        is_boilerplate = any(phrase in rationale.lower() for phrase in [
            "your existing tools likely support",
            "ships in days, not weeks",
            "costs a fraction of a saas",
        ])

        tu = options.get("targeted_upgrade", {})
        tu_when = tu.get("when_needed", "")
        tu_is_boilerplate = "no api or are fundamentally broken" in tu_when.lower()

        ca = options.get("connect_and_automate", {})
        ca_cost = ca.get("monthly_cost", "")
        has_dev_labor = any(w in ca_cost.lower() for w in ["hour", "build", "dev", "labor"])

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


def print_quality_report(analysis: Dict[str, Any], source: str) -> None:
    """Print a formatted quality report."""
    print(f"\n{'=' * 70}")
    print(f"  QUALITY REVIEW")
    print(f"  Source: {source}")
    print(f"{'=' * 70}")

    dist = analysis["recommendation_distribution"]
    total = analysis["total_recommendations"]

    print(f"\n  Findings: {analysis['total_findings']}")
    print(f"  Recommendations: {total}")
    print(f"  AI Readiness Score: {analysis['ai_readiness_score']}")

    print(f"\n  RECOMMENDATION DISTRIBUTION:")
    for opt, count in dist.items():
        pct = (count / total * 100) if total > 0 else 0
        bar = "\u2588" * int(pct / 5) + "\u2591" * (20 - int(pct / 5))
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

    print(f"    Boilerplate rationales:     {bp}/{total}  {'\u2713 CLEAN' if bp == 0 else '\u2717 FIX NEEDED'}")
    print(f"    Boilerplate when_needed:    {bw}/{total}  {'\u2713 CLEAN' if bw == 0 else '\u2717 FIX NEEDED'}")
    print(f"    Connect missing dev labor:  {dl}/{total}  {'\u2713 INCLUDED' if dl == 0 else '\u26a0 CHECK'}")
    print(f"    Avg NET score spread:       {spread}      {'\u2713 NEUTRAL' if isinstance(spread, (int, float)) and spread < 10 else '\u26a0 BIASED' if isinstance(spread, (int, float)) else '?'}")

    print(f"\n  PER-RECOMMENDATION BREAKDOWN:")
    print(f"  {'#':>3}  {'Title':<40}  {'Rec':<22}  {'Boilerplate':>10}  {'NET Spread':>10}")
    print(f"  {'\u2500' * 3}  {'\u2500' * 40}  {'\u2500' * 22}  {'\u2500' * 10}  {'\u2500' * 10}")

    for i, rd in enumerate(analysis["details"], 1):
        title = rd["title"][:40].ljust(40)
        rec_label = {
            "connect_and_automate": "Connect",
            "enhance_with_ai": "Enhance",
            "targeted_upgrade": "Upgrade",
        }.get(rd["recommendation"], rd["recommendation"])
        bp_flag = "YES \u2717" if rd["is_boilerplate_rationale"] else "no"
        scores = rd["net_scores"]
        if scores:
            vals = [v for v in scores.values() if isinstance(v, (int, float))]
            spread_str = f"{max(vals) - min(vals):.1f}" if len(vals) >= 2 else "\u2014"
        else:
            spread_str = "\u2014"

        print(f"  {i:3d}  {title}  {rec_label:<22}  {bp_flag:>10}  {spread_str:>10}")

    print(f"\n{'=' * 70}\n")


def print_report_list(reports: List[Path], industry: str) -> None:
    """Print available reports for an industry."""
    print(f"\n  Reports for {industry}:")
    print(f"  {'#':>3}  {'File':<60}  {'Size':>10}")
    print(f"  {'\u2500' * 3}  {'\u2500' * 60}  {'\u2500' * 10}")

    for i, path in enumerate(reports, 1):
        size_kb = path.stat().st_size / 1024
        print(f"  {i:3d}  {path.name:<60}  {size_kb:>7.0f} KB")

    if not reports:
        print(f"  (none — run 'make gen-{industry}' first)")
    print()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CRB Report Reviewer \u2014 review quality of generated reports"
    )

    parser.add_argument("--industry",
                        choices=["ecommerce", "dental", "professional-services", "b2b-platforms"],
                        help="Industry to review latest report for")
    parser.add_argument("--file", type=Path, help="Path to a specific report JSON file")
    parser.add_argument("--list", action="store_true", help="List available reports")
    parser.add_argument("--nth", type=int, default=1,
                        help="Review the Nth most recent report (default: 1 = latest)")

    args = parser.parse_args()

    if not args.industry and not args.file:
        parser.error("Provide --industry or --file")

    # List mode
    if args.list:
        if not args.industry:
            parser.error("--list requires --industry")
        reports = list_reports(args.industry)
        print_report_list(reports, args.industry)
        return

    # Resolve report file
    if args.file:
        report_path = args.file
        if not report_path.exists():
            print(f"  File not found: {report_path}")
            sys.exit(1)
    else:
        reports = list_reports(args.industry)
        if not reports:
            print(f"\n  No reports found for '{args.industry}'.")
            print(f"  Generate one first: make gen-{args.industry}\n")
            sys.exit(1)
        if args.nth > len(reports):
            print(f"\n  Only {len(reports)} reports available, requested #{args.nth}")
            sys.exit(1)
        report_path = reports[args.nth - 1]

    # Load and analyze
    print(f"\n  Loading: {report_path.name}")
    report_data = load_report(report_path)
    analysis = analyze_recommendations(report_data)

    # Save quality analysis alongside report
    quality_path = report_path.with_name(
        report_path.stem + "_quality.json"
    )
    with open(quality_path, "w") as f:
        json.dump(analysis, f, indent=2, default=str)

    # Print
    print_quality_report(analysis, report_path.name)
    print(f"  Quality file: {quality_path}\n")


if __name__ == "__main__":
    main()
