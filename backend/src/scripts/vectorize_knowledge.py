"""
Vectorize Knowledge Base

Generates embeddings for all knowledge base content and stores in pgvector.
Run this script after:
1. Running migration 008_vector_embeddings.sql in Supabase
2. Adding/updating knowledge base content

Usage:
    cd backend
    python -m src.scripts.vectorize_knowledge

Options:
    --force     Re-embed all content (ignore hashes)
    --type      Only embed specific type (vendor, opportunity, etc.)
    --industry  Only embed specific industry
    --stats     Show current embedding statistics
"""

import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.embedding_service import (
    EmbeddingService,
    EmbeddingContent,
    get_embedding_service
)
from src.knowledge import (
    KNOWLEDGE_BASE_PATH,
    VENDOR_CATEGORIES,
    load_industry_data,
    list_supported_industries
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONTENT LOADERS
# =============================================================================

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file safely."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        return {}


def load_vendor_content() -> List[EmbeddingContent]:
    """Load all vendors from category files."""
    items = []
    vendors_path = KNOWLEDGE_BASE_PATH / "vendors"

    for category in VENDOR_CATEGORIES:
        file_path = vendors_path / f"{category}.json"
        if not file_path.exists():
            continue

        data = load_json_file(file_path)
        vendors = data.get("vendors", [])

        for vendor in vendors:
            # Build searchable content
            content_parts = [
                vendor.get("description", ""),
                f"Best for: {vendor.get('best_for', '')}",
            ]

            if vendor.get("avoid_if"):
                content_parts.append(f"Avoid if: {vendor['avoid_if']}")

            if vendor.get("key_features"):
                content_parts.append(f"Features: {', '.join(vendor['key_features'])}")

            if vendor.get("integrations"):
                content_parts.append(f"Integrations: {', '.join(vendor['integrations'][:10])}")

            # Pricing info
            pricing = vendor.get("pricing", {})
            if pricing:
                if pricing.get("starting_price"):
                    content_parts.append(f"Pricing: {pricing['starting_price']}")
                if pricing.get("model"):
                    content_parts.append(f"Pricing model: {pricing['model']}")

            content = "\n".join(content_parts)

            items.append(EmbeddingContent(
                content_type="vendor",
                content_id=vendor.get("slug", vendor.get("name", "").lower().replace(" ", "-")),
                industry=None,  # Vendors are cross-industry
                title=vendor.get("name", "Unknown Vendor"),
                content=content,
                metadata={
                    "category": category,
                    "subcategory": vendor.get("subcategory"),
                    "pricing": pricing,
                    "website": vendor.get("website"),
                    "industries": vendor.get("industries", []),
                    "company_sizes": vendor.get("company_sizes", [])
                },
                source_file=str(file_path.relative_to(KNOWLEDGE_BASE_PATH))
            ))

    logger.info(f"Loaded {len(items)} vendors from {len(VENDOR_CATEGORIES)} categories")
    return items


def load_industry_opportunities(industry: str) -> List[EmbeddingContent]:
    """Load opportunities for a specific industry."""
    items = []
    file_path = KNOWLEDGE_BASE_PATH / industry / "opportunities.json"

    if not file_path.exists():
        return items

    data = load_json_file(file_path)
    opportunities = data.get("ai_opportunities", [])

    for opp in opportunities:
        # Build searchable content
        content_parts = [
            opp.get("description", ""),
        ]

        # Impact
        impact = opp.get("impact", {})
        if impact.get("value_saved"):
            saved = impact["value_saved"]
            if saved.get("time_hours_per_week"):
                content_parts.append(f"Time saved: {saved['time_hours_per_week']} hours/week")
            if saved.get("description"):
                content_parts.append(f"Savings: {saved['description']}")

        if impact.get("value_created"):
            created = impact["value_created"]
            if created.get("description"):
                content_parts.append(f"Value created: {created['description']}")
            if created.get("potential_revenue_impact"):
                content_parts.append(f"Revenue impact: {created['potential_revenue_impact']}")

        # ROI example
        roi = opp.get("roi_example", {})
        if roi:
            if roi.get("scenario"):
                content_parts.append(f"Example: {roi['scenario']}")
            if roi.get("roi_percentage"):
                content_parts.append(f"ROI: {roi['roi_percentage']}%")

        # Options summary
        options = opp.get("options", {})
        if options.get("off_the_shelf", {}).get("tools"):
            tools = options["off_the_shelf"]["tools"]
            content_parts.append(f"Off-the-shelf options: {', '.join(tools[:5])}")

        # Jevons Effect
        jevons = opp.get("jevons_effect", {})
        if jevons.get("applies"):
            content_parts.append(f"Jevons Effect: {jevons.get('mechanism', 'Efficiency gains lead to demand expansion')}")

        content = "\n".join(content_parts)

        items.append(EmbeddingContent(
            content_type="opportunity",
            content_id=opp.get("id", opp.get("name", "").lower().replace(" ", "-")),
            industry=industry,
            title=opp.get("name", "Unknown Opportunity"),
            content=content,
            metadata={
                "category": opp.get("category"),
                "customer_value_score": opp.get("customer_value_score"),
                "business_health_score": opp.get("business_health_score"),
                "implementation_complexity": opp.get("implementation", {}).get("complexity"),
                "timeline_weeks": opp.get("implementation", {}).get("timeline_weeks"),
                "options": options,
                "jevons_effect": jevons
            },
            source_file=f"{industry}/opportunities.json"
        ))

    logger.info(f"Loaded {len(items)} opportunities for {industry}")
    return items


def load_industry_benchmarks(industry: str) -> List[EmbeddingContent]:
    """Load benchmarks for a specific industry."""
    items = []
    file_path = KNOWLEDGE_BASE_PATH / industry / "benchmarks.json"

    if not file_path.exists():
        return items

    data = load_json_file(file_path)

    # Industry overview
    if data.get("industry_overview"):
        overview = data["industry_overview"]
        content = json.dumps(overview, indent=2)
        items.append(EmbeddingContent(
            content_type="benchmark",
            content_id=f"{industry}-overview",
            industry=industry,
            title=f"{industry.replace('-', ' ').title()} Industry Overview",
            content=content,
            metadata=overview,
            source_file=f"{industry}/benchmarks.json"
        ))

    # Key metrics
    for metric in data.get("key_metrics", []):
        content = f"{metric.get('description', '')}\nValue: {metric.get('value')}\nSource: {metric.get('source', 'Unknown')}"
        items.append(EmbeddingContent(
            content_type="benchmark",
            content_id=f"{industry}-metric-{metric.get('name', 'unknown').lower().replace(' ', '-')}",
            industry=industry,
            title=f"{industry}: {metric.get('name', 'Unknown Metric')}",
            content=content,
            metadata=metric,
            source_file=f"{industry}/benchmarks.json"
        ))

    logger.info(f"Loaded {len(items)} benchmarks for {industry}")
    return items


def load_patterns() -> List[EmbeddingContent]:
    """Load patterns from playbook and other pattern files."""
    items = []
    patterns_path = KNOWLEDGE_BASE_PATH / "patterns"

    # AI Implementation Playbook
    playbook_path = patterns_path / "ai_implementation_playbook.json"
    if playbook_path.exists():
        playbook = load_json_file(playbook_path)

        # Platform evolution
        if playbook.get("platform_evolution"):
            pe = playbook["platform_evolution"]
            content = json.dumps(pe, indent=2)
            items.append(EmbeddingContent(
                content_type="pattern",
                content_id="platform-evolution",
                title="Platform Evolution Path (Function → Integrated → Operating System)",
                content=content,
                metadata=pe,
                source_file="patterns/ai_implementation_playbook.json"
            ))

        # Jevons Effect
        if playbook.get("jevons_effect"):
            je = playbook["jevons_effect"]
            content = json.dumps(je, indent=2)
            items.append(EmbeddingContent(
                content_type="pattern",
                content_id="jevons-effect",
                title="Jevons Effect: Efficiency → Demand Expansion",
                content=content,
                metadata=je,
                source_file="patterns/ai_implementation_playbook.json"
            ))

        # ROI Framework
        if playbook.get("roi_framework"):
            rf = playbook["roi_framework"]
            content = json.dumps(rf, indent=2)
            items.append(EmbeddingContent(
                content_type="pattern",
                content_id="roi-framework",
                title="ROI Framework: 8 Categories with Impact Rates",
                content=content,
                metadata=rf,
                source_file="patterns/ai_implementation_playbook.json"
            ))

        # Custom solution guidance
        if playbook.get("custom_solution_guidance"):
            csg = playbook["custom_solution_guidance"]
            for key, value in csg.items():
                content = json.dumps(value, indent=2) if isinstance(value, dict) else str(value)
                items.append(EmbeddingContent(
                    content_type="pattern",
                    content_id=f"custom-solution-{key}",
                    title=f"Custom Solution: {key.replace('_', ' ').title()}",
                    content=content,
                    metadata={"category": "custom_solution_guidance", "key": key},
                    source_file="patterns/ai_implementation_playbook.json"
                ))

    # Vertical AI SaaS Examples
    examples_path = patterns_path / "vertical_ai_saas_examples.json"
    if examples_path.exists():
        examples = load_json_file(examples_path)

        # YC-backed examples
        for example in examples.get("yc_backed_examples", []):
            content_parts = [
                example.get("description", ""),
                f"Industry: {example.get('industry', 'Unknown')}",
                f"Funding: {example.get('funding', 'Unknown')}",
            ]
            if example.get("key_insight"):
                content_parts.append(f"Key insight: {example['key_insight']}")
            if example.get("pricing"):
                content_parts.append(f"Pricing: {example['pricing']}")

            items.append(EmbeddingContent(
                content_type="case_study",
                content_id=f"yc-{example.get('company', 'unknown').lower().replace(' ', '-')}",
                industry=example.get("industry_slug"),
                title=f"YC Example: {example.get('company', 'Unknown')} - {example.get('niche', '')}",
                content="\n".join(content_parts),
                metadata=example,
                source_file="patterns/vertical_ai_saas_examples.json"
            ))

        # Non-YC examples
        for example in examples.get("non_yc_examples", []):
            items.append(EmbeddingContent(
                content_type="case_study",
                content_id=f"example-{example.get('company', 'unknown').lower().replace(' ', '-')}",
                industry=example.get("industry_slug"),
                title=f"Case Study: {example.get('company', 'Unknown')}",
                content=example.get("description", ""),
                metadata=example,
                source_file="patterns/vertical_ai_saas_examples.json"
            ))

    logger.info(f"Loaded {len(items)} patterns and case studies")
    return items


def load_roi_examples() -> List[EmbeddingContent]:
    """Load ROI examples from roi_calculator.py as case studies."""
    items = []

    # Import the Jevons Effect examples
    try:
        from src.models.roi_calculator import JEVONS_EFFECT_EXAMPLES, INDUSTRY_DEMAND_EXPANSION_DEFAULTS

        for example in JEVONS_EFFECT_EXAMPLES:
            content = f"""
Industry: {example['industry']}
Scenario: {example['scenario']}
Efficiency Gain: {example['efficiency_gain']}
Result: {example['demand_expansion_result']}
Source: {example.get('source', 'CRB Analysis')}
            """.strip()

            items.append(EmbeddingContent(
                content_type="case_study",
                content_id=f"jevons-{example['industry'].lower().replace(' ', '-').replace('/', '-')}",
                title=f"Jevons Effect: {example['industry']} - {example['scenario']}",
                content=content,
                metadata=example,
                source_file="models/roi_calculator.py"
            ))

        # Industry expansion defaults as insights
        for industry, defaults in INDUSTRY_DEMAND_EXPANSION_DEFAULTS.items():
            content = f"""
Industry: {industry}
Typical Expansion Rate: {defaults['typical_expansion_rate'] * 100}%
Trigger: {defaults['trigger']}
Example: {defaults['example']}
Revenue Multiplier: {defaults['revenue_multiplier']}x
            """.strip()

            items.append(EmbeddingContent(
                content_type="insight",
                content_id=f"demand-expansion-{industry}",
                industry=industry,
                title=f"Demand Expansion Default: {industry.replace('-', ' ').title()}",
                content=content,
                metadata=defaults,
                source_file="models/roi_calculator.py"
            ))

        logger.info(f"Loaded {len(items)} ROI examples and insights")

    except Exception as e:
        logger.error(f"Failed to load ROI examples: {e}")

    return items


# =============================================================================
# MAIN VECTORIZATION LOGIC
# =============================================================================

async def vectorize_all(
    force: bool = False,
    content_type: str = None,
    industry: str = None
) -> Dict[str, Any]:
    """
    Vectorize all knowledge base content.

    Args:
        force: Re-embed even if content unchanged
        content_type: Only process specific type
        industry: Only process specific industry

    Returns:
        Statistics about the operation
    """
    all_content: List[EmbeddingContent] = []

    # Load vendors
    if not content_type or content_type == "vendor":
        all_content.extend(load_vendor_content())

    # Load industry-specific content
    industries = [industry] if industry else list_supported_industries()

    for ind in industries:
        if not content_type or content_type == "opportunity":
            all_content.extend(load_industry_opportunities(ind))
        if not content_type or content_type == "benchmark":
            all_content.extend(load_industry_benchmarks(ind))

    # Load patterns and case studies
    if not content_type or content_type in ("pattern", "case_study"):
        all_content.extend(load_patterns())

    # Load ROI examples
    if not content_type or content_type in ("case_study", "insight"):
        all_content.extend(load_roi_examples())

    logger.info(f"Total content to vectorize: {len(all_content)} items")

    if not all_content:
        return {"total": 0, "success": 0, "skipped": 0, "failed": 0}

    # Get embedding service and process
    service = await get_embedding_service()
    results = await service.embed_and_store(all_content, skip_unchanged=not force)

    # Calculate stats
    stats = {
        "total": len(results),
        "success": sum(1 for r in results if r.success and r.error != "Skipped (unchanged)"),
        "skipped": sum(1 for r in results if r.error == "Skipped (unchanged)"),
        "failed": sum(1 for r in results if not r.success),
        "by_type": {}
    }

    # Group by content type
    for item, result in zip(all_content, results):
        ct = item.content_type
        if ct not in stats["by_type"]:
            stats["by_type"][ct] = {"success": 0, "skipped": 0, "failed": 0}

        if result.success and result.error != "Skipped (unchanged)":
            stats["by_type"][ct]["success"] += 1
        elif result.error == "Skipped (unchanged)":
            stats["by_type"][ct]["skipped"] += 1
        else:
            stats["by_type"][ct]["failed"] += 1

    return stats


async def show_stats():
    """Display current embedding statistics."""
    service = await get_embedding_service()
    stats = await service.get_embedding_stats()

    print("\n" + "=" * 60)
    print("EMBEDDING STATISTICS")
    print("=" * 60)

    if stats.get("error"):
        print(f"Error: {stats['error']}")
        return

    print(f"Total embeddings: {stats['total']}")
    print("\nBy content type:")

    for row in stats.get("stats", []):
        industries = row.get("industries", [])
        industries_str = ", ".join(industries[:5]) if industries else "cross-industry"
        print(f"  {row['content_type']:20} {row['count']:5} items  ({industries_str})")

    print("=" * 60 + "\n")


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(description="Vectorize CRB knowledge base")
    parser.add_argument("--force", action="store_true", help="Re-embed all content")
    parser.add_argument("--type", type=str, help="Only embed specific type")
    parser.add_argument("--industry", type=str, help="Only embed specific industry")
    parser.add_argument("--stats", action="store_true", help="Show embedding statistics")

    args = parser.parse_args()

    if args.stats:
        await show_stats()
        return

    print("\n" + "=" * 60)
    print("VECTORIZING KNOWLEDGE BASE")
    print("=" * 60)

    if args.force:
        print("Mode: FORCE (re-embedding all content)")
    else:
        print("Mode: INCREMENTAL (skipping unchanged content)")

    if args.type:
        print(f"Filter: content_type = {args.type}")
    if args.industry:
        print(f"Filter: industry = {args.industry}")

    print("-" * 60)

    stats = await vectorize_all(
        force=args.force,
        content_type=args.type,
        industry=args.industry
    )

    print("\n" + "-" * 60)
    print("RESULTS")
    print("-" * 60)
    print(f"Total processed: {stats['total']}")
    print(f"  ✓ Embedded:    {stats['success']}")
    print(f"  ○ Skipped:     {stats['skipped']} (unchanged)")
    print(f"  ✗ Failed:      {stats['failed']}")

    print("\nBy content type:")
    for ct, ct_stats in stats.get("by_type", {}).items():
        print(f"  {ct:20} ✓{ct_stats['success']:3} ○{ct_stats['skipped']:3} ✗{ct_stats['failed']:3}")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
