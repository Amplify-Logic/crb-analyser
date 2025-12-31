"""
Migrate vendors from JSON files to Supabase.

This script:
1. Loads all vendor JSON files from knowledge/vendors/
2. Loads industry-specific vendors from knowledge/{industry}/vendors.json
3. Transforms to Supabase schema
4. Inserts into vendors table
5. Creates industry_vendor_tiers for recommended_default vendors
6. Optionally generates embeddings
7. Logs all actions to vendor_audit_log

Usage:
    cd backend
    source venv/bin/activate
    python -m src.scripts.migrate_vendors_to_supabase

Options:
    --dry-run       Print what would be inserted without actually inserting
    --skip-embeddings   Skip embedding generation (faster, can add later)
    --clear-existing    Delete all existing vendors before migration
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge"
VENDOR_CATEGORIES_PATH = KNOWLEDGE_BASE_PATH / "vendors"

# Industry folders with vendor files
INDUSTRY_FOLDERS = [
    "dental",
    "home-services",
    "professional-services",
    "recruiting",
    "coaching",
    "veterinary",
]


def load_json_file(file_path: Path) -> Optional[Dict]:
    """Load a JSON file safely."""
    if not file_path.exists():
        logger.debug(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        return None


def normalize_complexity(complexity: Optional[str]) -> Optional[str]:
    """Normalize implementation complexity to allowed values."""
    if complexity is None:
        return None

    complexity = complexity.lower().strip()

    # Map invalid values to valid ones
    mapping = {
        "none": "low",
        "very_low": "low",
        "very_high": "high",
        "extreme": "high",
    }

    if complexity in ["low", "medium", "high"]:
        return complexity

    return mapping.get(complexity, "medium")


def transform_vendor_to_supabase(vendor: Dict, category: str) -> Dict:
    """Transform a vendor from JSON schema to Supabase schema."""

    # Extract ratings
    ratings = vendor.get("ratings", {})
    g2 = ratings.get("g2", {})
    capterra = ratings.get("capterra", {})

    # Extract implementation
    impl = vendor.get("implementation", {})
    impl_cost = impl.get("cost_range", {})

    # Build Supabase record
    return {
        "slug": vendor.get("slug"),
        "name": vendor.get("name"),
        "category": category,
        "subcategory": vendor.get("subcategory"),

        # Core info
        "website": vendor.get("website"),
        "pricing_url": vendor.get("pricing_url"),
        "description": vendor.get("description"),
        "tagline": vendor.get("tagline"),

        # Pricing as JSONB
        "pricing": vendor.get("pricing"),

        # Fit criteria
        "company_sizes": vendor.get("company_sizes", []),
        "industries": vendor.get("industries", []),
        "best_for": vendor.get("best_for", []),
        "avoid_if": vendor.get("avoid_if", []),

        # Recommendations
        "recommended_default": vendor.get("recommended_default", False),
        "recommended_for": vendor.get("recommended_for", []),

        # Ratings
        "our_rating": ratings.get("our_rating"),
        "our_notes": ratings.get("our_notes"),
        "g2_score": g2.get("score"),
        "g2_reviews": g2.get("reviews"),
        "capterra_score": capterra.get("score"),
        "capterra_reviews": capterra.get("reviews"),

        # Implementation
        "implementation_weeks": impl.get("avg_weeks"),
        "implementation_complexity": normalize_complexity(impl.get("complexity")),
        "implementation_cost": impl_cost if impl_cost else None,
        "requires_developer": impl.get("requires_developer", False),

        # Integrations & API
        "integrations": vendor.get("integrations", []),
        "api_available": vendor.get("api", {}).get("available", False),
        "api_type": vendor.get("api", {}).get("type"),
        "api_docs_url": vendor.get("api", {}).get("documentation"),

        # Competitors
        "competitors": vendor.get("competitors", []),

        # Key capabilities
        "key_capabilities": vendor.get("key_capabilities", []),

        # Metadata
        "verified_at": vendor.get("verified_at"),
        "verified_by": vendor.get("verified_by", "json_migration"),
        "source_url": vendor.get("source_url"),
        "notes": vendor.get("notes"),
        "status": "active",
    }


def load_all_vendors() -> List[Dict]:
    """Load all vendors from JSON files."""
    all_vendors = []
    seen_slugs = set()

    # Load from vendors/ category files
    if VENDOR_CATEGORIES_PATH.exists():
        for json_file in VENDOR_CATEGORIES_PATH.glob("*.json"):
            logger.info(f"Loading {json_file.name}...")
            data = load_json_file(json_file)
            if data and "vendors" in data:
                category = data.get("category", json_file.stem)
                for vendor in data["vendors"]:
                    slug = vendor.get("slug")
                    if slug and slug not in seen_slugs:
                        transformed = transform_vendor_to_supabase(vendor, category)
                        all_vendors.append(transformed)
                        seen_slugs.add(slug)
                        logger.debug(f"  Added: {vendor.get('name')} ({slug})")
                    elif slug:
                        logger.warning(f"  Duplicate slug skipped: {slug}")

    # Load from industry-specific vendor files
    for industry in INDUSTRY_FOLDERS:
        industry_path = KNOWLEDGE_BASE_PATH / industry / "vendors.json"
        if industry_path.exists():
            logger.info(f"Loading {industry}/vendors.json...")
            data = load_json_file(industry_path)
            if data:
                # Industry vendor files have different structures
                # Try to extract vendors from various formats
                vendors = []

                if "vendors" in data:
                    vendors = data["vendors"]
                elif "vendor_categories" in data:
                    for cat in data["vendor_categories"]:
                        vendors.extend(cat.get("vendors", []))
                elif "categories" in data:
                    for cat_name, cat_data in data["categories"].items():
                        if isinstance(cat_data, dict) and "vendors" in cat_data:
                            vendors.extend(cat_data["vendors"])

                for vendor in vendors:
                    slug = vendor.get("slug")
                    if slug and slug not in seen_slugs:
                        # Industry vendors often have simpler schema
                        category = vendor.get("category", "general")
                        transformed = transform_vendor_to_supabase(vendor, category)
                        # Add this industry to the industries list
                        if industry not in transformed.get("industries", []):
                            transformed["industries"] = transformed.get("industries", []) + [industry]
                        all_vendors.append(transformed)
                        seen_slugs.add(slug)
                        logger.debug(f"  Added: {vendor.get('name')} ({slug})")

    return all_vendors


def generate_embedding(text: str, settings) -> Optional[List[float]]:
    """Generate embedding for a vendor description."""
    try:
        from anthropic import Anthropic

        # Use Anthropic's embedding via Claude
        # Note: In production, you might want to use a dedicated embedding model
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        # For now, skip embeddings - can be added later with a dedicated service
        # This would use OpenAI, Cohere, or Voyage embeddings typically
        return None
    except Exception as e:
        logger.warning(f"Failed to generate embedding: {e}")
        return None


def migrate_vendors(
    dry_run: bool = False,
    skip_embeddings: bool = True,
    clear_existing: bool = False
):
    """Main migration function."""

    settings = get_settings()

    # Initialize Supabase client
    from supabase import create_client
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    # Load all vendors
    logger.info("Loading vendors from JSON files...")
    vendors = load_all_vendors()
    logger.info(f"Found {len(vendors)} vendors to migrate")

    if dry_run:
        logger.info("DRY RUN - No changes will be made")
        for v in vendors[:10]:
            logger.info(f"  Would insert: {v['name']} ({v['slug']}) - {v['category']}")
        if len(vendors) > 10:
            logger.info(f"  ... and {len(vendors) - 10} more")
        return

    # Clear existing if requested
    if clear_existing:
        logger.warning("Clearing existing vendors...")
        supabase.table("industry_vendor_tiers").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("vendor_audit_log").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("vendors").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        logger.info("Cleared existing data")

    # Insert vendors
    success_count = 0
    error_count = 0

    for vendor in vendors:
        try:
            # Generate embedding if enabled
            if not skip_embeddings and vendor.get("description"):
                embedding = generate_embedding(vendor["description"], settings)
                if embedding:
                    vendor["embedding"] = embedding

            # Insert vendor
            result = supabase.table("vendors").insert(vendor).execute()
            vendor_id = result.data[0]["id"] if result.data else None

            # Log the creation
            supabase.table("vendor_audit_log").insert({
                "vendor_id": vendor_id,
                "vendor_slug": vendor["slug"],
                "action": "create",
                "changed_by": "json_migration",
                "changes": {"source": "initial_migration"}
            }).execute()

            # Create industry tier if recommended_default
            if vendor.get("recommended_default") and vendor_id:
                # Add to tier 1 for industries in recommended_for
                for industry in vendor.get("industries", []):
                    try:
                        supabase.table("industry_vendor_tiers").insert({
                            "industry": industry,
                            "vendor_id": vendor_id,
                            "tier": 1,
                            "boost_score": 30,
                            "notes": "Auto-created from recommended_default"
                        }).execute()
                    except Exception as tier_error:
                        logger.debug(f"Could not create tier for {vendor['slug']}/{industry}: {tier_error}")

            success_count += 1
            logger.info(f"✓ Migrated: {vendor['name']} ({vendor['slug']})")

        except Exception as e:
            error_count += 1
            logger.error(f"✗ Failed to migrate {vendor.get('name', 'unknown')}: {e}")

    logger.info(f"\nMigration complete!")
    logger.info(f"  Successful: {success_count}")
    logger.info(f"  Errors: {error_count}")

    # Verify counts
    vendor_count = supabase.table("vendors").select("id", count="exact").execute()
    tier_count = supabase.table("industry_vendor_tiers").select("id", count="exact").execute()

    logger.info(f"\nDatabase state:")
    logger.info(f"  Vendors: {vendor_count.count}")
    logger.info(f"  Industry tiers: {tier_count.count}")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate vendors from JSON to Supabase"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be inserted without actually inserting"
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        default=True,
        help="Skip embedding generation (default: True)"
    )
    parser.add_argument(
        "--with-embeddings",
        action="store_true",
        help="Generate embeddings during migration"
    )
    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Delete all existing vendors before migration"
    )

    args = parser.parse_args()

    skip_embeddings = args.skip_embeddings and not args.with_embeddings

    migrate_vendors(
        dry_run=args.dry_run,
        skip_embeddings=skip_embeddings,
        clear_existing=args.clear_existing
    )


if __name__ == "__main__":
    main()
