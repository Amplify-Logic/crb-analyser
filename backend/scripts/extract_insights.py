#!/usr/bin/env python3
"""
CLI tool for extracting and managing curated insights.

Usage:
    # Extract from a file
    python -m backend.scripts.extract_insights --file path/to/transcript.txt

    # Extract from clipboard/paste
    python -m backend.scripts.extract_insights --paste

    # List existing insights
    python -m backend.scripts.extract_insights --list

    # List by type
    python -m backend.scripts.extract_insights --list --type trend

    # Show stats
    python -m backend.scripts.extract_insights --stats

    # Mark insight as reviewed
    python -m backend.scripts.extract_insights --review insight-id

Examples:
    # Extract Jeff Su AI trends video
    python -m backend.scripts.extract_insights \\
        --file backend/src/knowledge/insights/raw/2026-01-jeff-su-ai-trends.txt \\
        --title "Top 6 AI Trends That Will Define 2026" \\
        --author "Jeff Su" \\
        --date "2026-01-06" \\
        --type youtube
"""

import argparse
import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add backend to path for proper imports
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from anthropic import Anthropic

from src.models.insight import InsightType, UseIn
from src.services.insight_service import get_insight_service
from src.skills.extraction.insight_extraction import (
    InsightExtractionSkill,
    extract_insights_from_content,
)
from src.skills.base import SkillContext


def get_client() -> Anthropic:
    """Get Anthropic client from environment."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
    return Anthropic(api_key=api_key)


def read_from_file(file_path: str) -> str:
    """Read content from a file."""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    with open(path, "r") as f:
        return f.read()


def read_from_paste() -> str:
    """Read content from user paste (opens editor or stdin)."""
    # Try to open in editor
    editor = os.environ.get("EDITOR", "nano")

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False) as f:
        f.write("# Paste your content below this line and save.\n")
        f.write("# Lines starting with # will be ignored.\n\n")
        temp_path = f.name

    try:
        os.system(f"{editor} {temp_path}")

        with open(temp_path, "r") as f:
            lines = f.readlines()

        # Remove comment lines
        content = "\n".join(
            line for line in lines if not line.strip().startswith("#")
        )

        if not content.strip():
            print("Error: No content provided")
            sys.exit(1)

        return content

    finally:
        os.unlink(temp_path)


async def do_extraction(
    content: str,
    title: str,
    author: str = None,
    url: str = None,
    date: str = None,
    source_type: str = "article",
    auto_save: bool = False,
) -> None:
    """Run the extraction workflow."""
    client = get_client()
    service = get_insight_service()

    print(f"\n{'='*60}")
    print(f"EXTRACTING INSIGHTS")
    print(f"{'='*60}")
    print(f"Source: {title}")
    print(f"Content length: {len(content):,} characters")
    print(f"{'='*60}\n")

    print("Analyzing content with AI... (this may take 30-60 seconds)\n")

    try:
        extracted = await extract_insights_from_content(
            client=client,
            raw_content=content,
            source_title=title,
            source_author=author,
            source_url=url,
            source_date=date,
            source_type=source_type,
        )
    except Exception as e:
        print(f"Error during extraction: {e}")
        sys.exit(1)

    print(f"Found {len(extracted.insights)} insights:\n")

    for i, insight in enumerate(extracted.insights, 1):
        print(f"{i}. [{insight.type.upper()}] {insight.title}")
        print(f"   ID: {insight.id}")
        if insight.supporting_data:
            for sd in insight.supporting_data:
                print(f"   - {sd.source}: {sd.claim[:60]}...")
        print()

    if extracted.extraction_notes:
        print(f"Notes: {extracted.extraction_notes}\n")

    # Auto-save or prompt
    if auto_save:
        result = service.save_extracted_insights(extracted)
        print(f"\nSaved: {result['added']} insights ({result['skipped']} skipped)")
    else:
        response = input("\nSave these insights? [y/N/edit]: ").strip().lower()

        if response == "y":
            result = service.save_extracted_insights(extracted)
            print(f"Saved: {result['added']} insights ({result['skipped']} skipped)")
            print("\nNote: Insights are marked as 'unreviewed'. Use --review <id> to mark as reviewed.")

        elif response == "edit":
            # Save to temp file for editing
            temp_path = Path(tempfile.gettempdir()) / f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(temp_path, "w") as f:
                json.dump(
                    {"insights": [i.model_dump() for i in extracted.insights]},
                    f,
                    indent=2,
                    default=str,
                )
            print(f"\nSaved to: {temp_path}")
            print("Edit the file and run: python -m backend.scripts.extract_insights --import <file>")

        else:
            print("Discarded.")


def list_insights(insight_type: str = None, reviewed_only: bool = False) -> None:
    """List existing insights."""
    service = get_insight_service()

    if insight_type:
        try:
            t = InsightType(insight_type)
            insights = service.get_insights_by_type(t, reviewed_only=reviewed_only)
        except ValueError:
            print(f"Error: Invalid type '{insight_type}'")
            print(f"Valid types: {', '.join(t.value for t in InsightType)}")
            sys.exit(1)
    else:
        insights = service.get_all_insights(reviewed_only=reviewed_only)

    if not insights:
        print("No insights found.")
        return

    print(f"\n{'='*60}")
    print(f"INSIGHTS ({len(insights)} total)")
    print(f"{'='*60}\n")

    # Group by type
    by_type = {}
    for insight in insights:
        t = insight.type.value if isinstance(insight.type, InsightType) else insight.type
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(insight)

    for t, type_insights in sorted(by_type.items()):
        print(f"\n## {t.upper()} ({len(type_insights)})\n")
        for insight in type_insights:
            status = "[R]" if insight.reviewed else "[ ]"
            print(f"  {status} {insight.id}")
            print(f"      {insight.title}")


def show_stats() -> None:
    """Show insight statistics."""
    service = get_insight_service()
    stats = service.get_stats()

    print(f"\n{'='*60}")
    print(f"INSIGHT STATISTICS")
    print(f"{'='*60}\n")

    print(f"Total insights: {stats['total']}")
    print(f"  Reviewed: {stats['reviewed']}")
    print(f"  Unreviewed: {stats['unreviewed']}")

    print(f"\nBy type:")
    for t, counts in stats["by_type"].items():
        print(f"  {t}: {counts['total']} ({counts['reviewed']} reviewed)")

    print(f"\nBy surface:")
    for surface, count in stats["by_use_in"].items():
        print(f"  {surface}: {count}")


def review_insight(insight_id: str) -> None:
    """Mark an insight as reviewed."""
    service = get_insight_service()

    insight = service.get_insight_by_id(insight_id)
    if not insight:
        print(f"Error: Insight not found: {insight_id}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"REVIEWING INSIGHT")
    print(f"{'='*60}\n")

    print(f"ID: {insight.id}")
    print(f"Type: {insight.type}")
    print(f"Title: {insight.title}")
    print(f"\nContent:\n{insight.content}")

    if insight.supporting_data:
        print(f"\nSupporting data:")
        for sd in insight.supporting_data:
            print(f"  - [{sd.credibility}] {sd.source}: {sd.claim}")

    if insight.actionable_insight:
        print(f"\nActionable: {insight.actionable_insight}")

    print(f"\nTags: {insight.tags.model_dump()}")

    response = input("\nMark as reviewed? [Y/n]: ").strip().lower()

    if response != "n":
        if service.mark_reviewed(insight_id, True):
            print("Marked as reviewed.")
        else:
            print("Error: Failed to update insight.")


def import_insights(file_path: str) -> None:
    """Import insights from a JSON file."""
    service = get_insight_service()

    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    with open(path, "r") as f:
        data = json.load(f)

    from src.models.insight import Insight

    insights = [Insight(**i) for i in data.get("insights", [])]

    if not insights:
        print("No insights found in file.")
        return

    result = service.add_insights_batch(insights)
    print(f"Imported: {result['added']} insights ({result['skipped']} skipped)")


def main():
    parser = argparse.ArgumentParser(
        description="Extract and manage curated insights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Extraction options
    parser.add_argument("--file", "-f", help="Path to file containing content to extract")
    parser.add_argument("--paste", "-p", action="store_true", help="Open editor to paste content")
    parser.add_argument("--url", "-u", help="URL of the source (for metadata)")
    parser.add_argument("--title", "-t", help="Title of the source")
    parser.add_argument("--author", "-a", help="Author of the source")
    parser.add_argument("--date", "-d", help="Date of the source (YYYY-MM-DD)")
    parser.add_argument("--source-type", default="article", help="Type: youtube, article, report, etc.")
    parser.add_argument("--auto-save", action="store_true", help="Automatically save without prompting")

    # Management options
    parser.add_argument("--list", "-l", action="store_true", help="List existing insights")
    parser.add_argument("--type", help="Filter by type (trend, framework, case_study, statistic, quote, prediction)")
    parser.add_argument("--reviewed", action="store_true", help="Show only reviewed insights")
    parser.add_argument("--stats", "-s", action="store_true", help="Show statistics")
    parser.add_argument("--review", help="Mark an insight as reviewed by ID")
    parser.add_argument("--import", dest="import_file", help="Import insights from JSON file")

    args = parser.parse_args()

    # Handle different modes
    if args.list:
        list_insights(args.type, args.reviewed)

    elif args.stats:
        show_stats()

    elif args.review:
        review_insight(args.review)

    elif args.import_file:
        import_insights(args.import_file)

    elif args.file or args.paste:
        # Extraction mode
        if args.file:
            content = read_from_file(args.file)
            # Try to parse metadata from file if it has our format
            if content.startswith("Source:"):
                lines = content.split("\n")
                metadata = {}
                content_start = 0
                for i, line in enumerate(lines):
                    if line.startswith("---"):
                        content_start = i + 1
                        break
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip().lower()] = value.strip()

                content = "\n".join(lines[content_start:])

                # Use metadata if not overridden
                args.title = args.title or metadata.get("title", "Unknown")
                args.author = args.author or metadata.get("author")
                args.date = args.date or metadata.get("date")
                args.source_type = args.source_type or metadata.get("type", "article")
                args.url = args.url or metadata.get("url")
        else:
            content = read_from_paste()

        if not args.title:
            args.title = input("Source title: ").strip() or "Unknown"

        asyncio.run(do_extraction(
            content=content,
            title=args.title,
            author=args.author,
            url=args.url,
            date=args.date,
            source_type=args.source_type,
            auto_save=args.auto_save,
        ))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
