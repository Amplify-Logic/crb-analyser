"""
CRB Report Generator CLI

Generate full CRB reports for testing across industries.

Usage:
    # Single report by industry (random seed)
    python -m src.cli.generate_report --industry dental
    python -m src.cli.generate_report --industry ecommerce --tier mid
    python -m src.cli.generate_report --industry professional-services

    # Default: ecommerce (backward compatible)
    python -m src.cli.generate_report --tier small

    # Single report from URL (ecommerce only)
    python -m src.cli.generate_report --url https://store.com --country NL --staff 1-10

    # Batch: one per industry
    python -m src.cli.generate_report --batch --all-industries

    # Batch: multiple from one industry
    python -m src.cli.generate_report --batch --industry dental --count 3
"""

import argparse
import asyncio
import json
import logging
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
load_dotenv()  # Must be before src.* imports

from src.cli.fabricator import fabricate_quiz_session
from src.cli.scraper import scrape_ecommerce_site
from src.config.supabase_client import get_async_supabase
from src.services.report_service import generate_report_streaming

logger = logging.getLogger(__name__)

SEEDS_DIR = Path(__file__).parent / "seeds"

SUPPORTED_INDUSTRIES = ["ecommerce", "dental", "professional-services", "b2b-platforms"]


def load_seeds(industry: str = "ecommerce") -> Dict[str, Any]:
    """Load seed list for a given industry."""
    seeds_file = SEEDS_DIR / f"{industry}.json"
    if not seeds_file.exists():
        print(f"No seed file found for industry '{industry}' at {seeds_file}")
        print(f"Available: {', '.join(list_available_industries())}")
        sys.exit(1)
    with open(seeds_file) as f:
        return json.load(f)


def list_available_industries() -> List[str]:
    """List industries that have seed files."""
    return [p.stem for p in sorted(SEEDS_DIR.glob("*.json"))]


def pick_seed(seeds_data: Dict[str, Any], tier: Optional[str] = None) -> Dict[str, Any]:
    """Pick a random seed, optionally filtered by tier."""
    all_seeds = seeds_data["seeds"]
    if tier:
        filtered = [s for s in all_seeds if s["profile"]["tier"] == tier]
        if not filtered:
            tiers = sorted(set(s["profile"]["tier"] for s in all_seeds))
            print(f"No seeds found for tier '{tier}'. Available tiers: {', '.join(tiers)}")
            sys.exit(1)
        return random.choice(filtered)
    return random.choice(all_seeds)


def print_header(name: str, url: str, tier: str, country: str, staff: str, industry: str) -> None:
    """Print report generation header."""
    print(f"\n{'=' * 60}")
    print(f"  CRB Report Generator")
    print(f"{'=' * 60}")
    print(f"  Target:    {name}")
    print(f"  Industry:  {industry}")
    print(f"  URL:       {url}")
    print(f"  Profile:   {tier} | {country} | {staff} staff")
    print(f"{'=' * 60}\n")


def print_progress(data: Dict[str, Any]) -> None:
    """Print a progress update line."""
    progress = data.get("progress", 0)
    step = data.get("step", "")

    bar_width = 20
    filled = int(bar_width * progress / 100)
    bar = "\u2588" * filled + "\u2591" * (bar_width - filled)

    print(f"  [{bar}] {progress:3d}%  {step}", end="\r", flush=True)

    if data.get("phase_complete"):
        print()


async def generate_single_report(
    seed: Dict[str, Any],
    seeds_data: Dict[str, Any],
    report_tier: str = "quick",
    scrape: bool = True,
    skip_review: bool = False,
    use_playwright: bool = False,
    dev_mode: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Generate a single report from a seed.

    Returns dict with report_id, findings_count, ai_readiness, etc.
    """
    profile = seed["profile"]
    tier = profile["tier"]
    industry = profile.get("industry", seeds_data.get("industry", "ecommerce"))
    tier_defaults = seeds_data["tiers"][tier]["defaults"]

    print_header(
        name=seed["name"],
        url=seed.get("website", "N/A"),
        tier=tier,
        country=seed.get("country", "?"),
        staff=profile.get("staff_size", "?"),
        industry=industry,
    )

    # Step 1: Scrape website (only for ecommerce with websites)
    scraped_data = None
    if scrape and seed.get("website") and industry == "ecommerce":
        print("  Scraping website...", end="", flush=True)
        if use_playwright:
            from src.skills.browser.enhanced_scraper import EnhancedScraperSkill
            from src.skills.base import SkillContext
            scraper = EnhancedScraperSkill()
            scrape_context = SkillContext(
                industry="ecommerce",
                metadata={"url": seed["website"]}
            )
            result = await scraper.run(scrape_context)
            if result.success:
                scraped_data = result.data
                tech = scraped_data.get("visible_tech", [])
                method = scraped_data.get("scrape_method", "unknown")
                print(f" done via {method} ({len(tech)} technologies detected)")
            else:
                print(f" failed, using seed data only")
                scraped_data = None
        else:
            scraped_data = await scrape_ecommerce_site(seed["website"])
            if scraped_data.get("success"):
                tech = scraped_data.get("visible_tech", [])
                print(f" done ({len(tech)} technologies detected)")
            else:
                print(f" failed ({scraped_data.get('error', 'unknown')}), using seed data only")
                scraped_data = None

    # Workshop transcript info
    transcript = seed.get("workshop_transcript", [])
    if transcript:
        print(f"  Workshop transcript: {len(transcript)} messages loaded")
    else:
        print(f"  Workshop transcript: none (report will have less context)")

    # Step 2: Fabricate quiz session
    session_data = fabricate_quiz_session(seed, tier_defaults, scraped_data, report_tier)
    session_id = session_data["id"]

    # Step 3: Insert into Supabase
    print("  Creating quiz session...", end="", flush=True)
    supabase = await get_async_supabase()
    await supabase.table("quiz_sessions").insert(session_data).execute()
    print(f" done (id: {session_id[:8]}...)")

    # Step 4: Generate report
    print("\n  Generating report:\n")
    start_time = time.time()
    report_id = None
    last_phase = None
    error = None

    async for event in generate_report_streaming(session_id, report_tier, skip_review=skip_review, dev_mode=dev_mode):
        if not event.startswith("data: "):
            continue

        try:
            data = json.loads(event[6:].strip())
        except json.JSONDecodeError:
            continue

        phase = data.get("phase", "")
        if phase != last_phase and last_phase is not None:
            print()
        last_phase = phase

        if data.get("report_id"):
            report_id = data["report_id"]

        if data.get("phase") == "error" or data.get("error"):
            error = data.get("error", "Unknown error")
            break

        print_progress(data)

    elapsed = time.time() - start_time
    print("\n")

    if error:
        print(f"  ERROR: {error}")
        return None

    print(f"{'=' * 60}")
    print(f"  Complete")
    print(f"{'=' * 60}")
    print(f"  Report ID:    {report_id}")
    print(f"  Session ID:   {session_id}")
    print(f"  Industry:     {industry}")
    print(f"  Transcript:   {len(transcript)} messages")
    print(f"  Total Time:   {elapsed:.1f}s")
    print(f"{'=' * 60}\n")

    return {
        "report_id": report_id,
        "session_id": session_id,
        "company": seed["name"],
        "industry": industry,
        "tier": tier,
        "elapsed": elapsed,
    }


async def generate_from_url(
    url: str,
    country: str = "NL",
    staff_size: str = "11-50",
    report_tier: str = "quick",
    skip_review: bool = False,
    use_playwright: bool = False,
    dev_mode: bool = False,
) -> Optional[Dict[str, Any]]:
    """Generate a report from a custom URL (ecommerce only)."""
    seed = {
        "name": url.replace("https://", "").replace("http://", "").split("/")[0],
        "website": url,
        "country": country,
        "profile": {
            "tier": "mid",
            "industry": "ecommerce",
            "staff_size": staff_size,
            "monthly_orders": 500,
            "platform": "unknown",
            "product_category": "general",
            "has_erp": False,
            "current_tools": [],
            "pain_points": [],
        }
    }

    seeds_data = {
        "industry": "ecommerce",
        "tiers": {
            "mid": {"defaults": {"budget": 2000, "hourly_cost": 50,
                                 "pain_points": ["scaling operations", "customer service volume",
                                                 "manual processes"]}}
        }
    }

    return await generate_single_report(seed, seeds_data, report_tier, scrape=True, skip_review=skip_review, use_playwright=use_playwright, dev_mode=dev_mode)


async def cmd_single(args: argparse.Namespace) -> None:
    """Generate a single report."""
    dev_mode = getattr(args, 'dev_mode', False)
    if args.url:
        result = await generate_from_url(
            url=args.url,
            country=args.country,
            staff_size=args.staff,
            report_tier=args.report_tier,
            skip_review=args.no_review,
            use_playwright=args.playwright,
            dev_mode=dev_mode,
        )
    else:
        seeds_data = load_seeds(args.industry)
        seed = pick_seed(seeds_data, args.tier)
        result = await generate_single_report(
            seed, seeds_data, args.report_tier,
            skip_review=args.no_review, use_playwright=args.playwright,
            dev_mode=dev_mode,
        )

    if not result:
        sys.exit(1)


async def cmd_batch(args: argparse.Namespace) -> None:
    """Generate multiple reports."""
    dev_mode = getattr(args, 'dev_mode', False)
    if args.all_industries:
        industries = list_available_industries()
    else:
        industries = [args.industry]

    results = []
    total_count = 0

    for industry in industries:
        seeds_data = load_seeds(industry)
        count = 1 if args.all_industries else args.count

        for i in range(count):
            total_count += 1
            print(f"\n{'\u2500' * 60}")
            print(f"  Report {total_count} \u2014 {industry}")
            print(f"{'\u2500' * 60}")

            seed = pick_seed(seeds_data, args.tier)
            result = await generate_single_report(
                seed, seeds_data, args.report_tier,
                skip_review=args.no_review, use_playwright=args.playwright,
                dev_mode=dev_mode,
            )

            if result:
                results.append(result)
            else:
                print(f"  Skipping failed report, continuing batch...")

    # Print batch summary
    print(f"\n{'=' * 70}")
    print(f"  Batch Complete: {len(results)}/{total_count} reports generated")
    print(f"{'=' * 70}")
    print(f"  {'Company':30s}  {'Industry':22s}  {'Tier':8s}  {'Time':>6s}  {'Report ID'}")
    print(f"  {'-'*30}  {'-'*22}  {'-'*8}  {'-'*6}  {'-'*10}")
    for r in results:
        rid = r['report_id'][:8] if r['report_id'] else 'N/A'
        print(f"  {r['company']:30s}  {r['industry']:22s}  {r['tier']:8s}  {r['elapsed']:5.1f}s  {rid}...")
    total_time = sum(r["elapsed"] for r in results)
    print(f"\n  Total time: {total_time:.1f}s ({total_time / 60:.1f} min)")
    print(f"{'=' * 70}\n")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CRB Report Generator \u2014 generate full reports across industries"
    )

    # Mode selection
    parser.add_argument("--batch", action="store_true", help="Generate multiple reports")
    parser.add_argument("--count", type=int, default=5, help="Number of reports in batch mode (default: 5)")

    # Industry & seed selection
    parser.add_argument("--industry", default="ecommerce",
                        help=f"Industry to generate for (available: {', '.join(SUPPORTED_INDUSTRIES)})")
    parser.add_argument("--all-industries", action="store_true",
                        help="Generate one report per available industry (batch mode)")
    parser.add_argument("--tier", choices=["small", "mid", "scaling"], help="Business tier filter")

    # Custom URL mode (ecommerce only)
    parser.add_argument("--url", help="Custom website URL (ecommerce only, overrides seed list)")
    parser.add_argument("--country", default="NL", help="Country code for URL mode (default: NL)")
    parser.add_argument("--staff", default="11-50", help="Staff size for URL mode (default: 11-50)")

    # Report options
    parser.add_argument("--report-tier", choices=["quick", "full"], default="quick",
                        help="Report tier (default: quick)")
    parser.add_argument("--no-scrape", action="store_true", help="Skip website scraping")
    parser.add_argument("--no-review", action="store_true",
                        help="Skip review/validation phase for faster iteration")
    parser.add_argument("--playwright", action="store_true",
                        help="Use Playwright for JS-rendered scraping (ecommerce only)")
    parser.add_argument("--dev-mode", action="store_true", dest="dev_mode",
                        help="Route LLM calls through Claude Code CLI (uses Max subscription instead of API credits)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")

    # Route to command
    if args.batch or args.all_industries:
        asyncio.run(cmd_batch(args))
    else:
        asyncio.run(cmd_single(args))


if __name__ == "__main__":
    main()
