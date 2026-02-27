"""
Enrich vendors with AIOS readiness fields.

Run with: python -m scripts.enrich_vendors_aios

Maps existing vendor data to new AIOS fields:
1. Cross-references mcp_ecosystem.json with vendor slugs → mcp_server_slug
2. Calculates aios_readiness_score from existing fields
3. Sets claude_code_compatible based on API availability
4. Populates data_portability based on api_openness_score
5. Sets agent_buildable and agent_patterns

Run once, then maintain via vendor research agent.
"""

import asyncio
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to MCP ecosystem knowledge base
MCP_ECOSYSTEM_PATH = Path(__file__).parent.parent / "src" / "knowledge" / "platforms" / "mcp_ecosystem.json"


def load_mcp_slug_map() -> dict[str, dict]:
    """Build a map of vendor slug → MCP server data from mcp_ecosystem.json."""
    with open(MCP_ECOSYSTEM_PATH) as f:
        ecosystem = json.load(f)

    slug_map: dict[str, dict] = {}
    for _cat_name, cat_data in ecosystem.get("categories", {}).items():
        for server in cat_data.get("servers", []):
            slug = server["slug"]
            slug_map[slug] = {
                "mcp_server_slug": slug,
                "maturity": server.get("maturity", "community"),
            }

    return slug_map


def derive_data_portability(api_openness_score: int | None) -> str | None:
    """Map api_openness_score (1-5) to data_portability level."""
    if api_openness_score is None:
        return None
    if api_openness_score >= 4:
        return "full_export"
    if api_openness_score == 3:
        return "api_access"
    if api_openness_score == 2:
        return "limited_export"
    return "trapped"


def derive_agent_patterns(
    has_webhooks: bool,
    api_openness_score: int | None,
    category: str | None,
) -> list[str]:
    """Derive agent patterns based on vendor capabilities."""
    patterns = []

    # All API-accessible vendors support data extraction
    if api_openness_score and api_openness_score >= 3:
        patterns.append("data_extraction")

    # Webhook-capable vendors support monitoring/event-driven patterns
    if has_webhooks:
        patterns.append("monitoring")

    # Full API = workflow automation possible
    if api_openness_score and api_openness_score >= 4:
        patterns.append("workflow_automation")

    # Content-related categories support content generation
    content_categories = {
        "marketing", "ai_content_creation", "ai_video",
        "ai_image", "ai_productivity", "documents",
    }
    if category and category in content_categories:
        patterns.append("content_generation")

    return patterns


def calculate_aios_readiness_score(
    api_openness_score: int | None,
    has_webhooks: bool,
    mcp_server_slug: str | None,
    mcp_server_maturity: str | None,
    has_oauth: bool,
    zapier_integration: bool,
    make_integration: bool,
    n8n_integration: bool,
    data_portability: str | None,
    agent_buildable: bool,
) -> int:
    """Calculate AIOS readiness score (1-10) from vendor fields.

    Scoring:
    +2 if API available and type is REST/GraphQL (api_openness >= 3)
    +2 if has_webhooks
    +2 if MCP server exists and maturity is production or beta
    +1 if has_oauth
    +1 if any integration platform (zapier/make/n8n)
    +1 if data_portability is full_export or api_access
    +1 if agent_buildable
    """
    score = 0

    # +2 for API availability
    if api_openness_score and api_openness_score >= 3:
        score += 2

    # +2 for webhooks
    if has_webhooks:
        score += 2

    # +2 for MCP server (production or beta)
    if mcp_server_slug and mcp_server_maturity in ("production", "beta"):
        score += 2

    # +1 for OAuth
    if has_oauth:
        score += 1

    # +1 for any integration platform
    if zapier_integration or make_integration or n8n_integration:
        score += 1

    # +1 for data portability
    if data_portability in ("full_export", "api_access"):
        score += 1

    # +1 for agent buildable
    if agent_buildable:
        score += 1

    return max(1, min(10, score))


async def enrich_vendors() -> None:
    """Enrich all vendors with AIOS readiness fields."""
    from src.config.supabase_client import get_async_supabase

    supabase = await get_async_supabase()
    mcp_map = load_mcp_slug_map()

    logger.info("Loaded %d MCP server slugs", len(mcp_map))

    # Fetch all vendors
    result = await supabase.table("vendors").select(
        "id, slug, category, api_openness_score, has_webhooks, has_oauth, "
        "zapier_integration, make_integration, n8n_integration"
    ).execute()

    vendors = result.data
    logger.info("Found %d vendors to enrich", len(vendors))

    updated = 0
    skipped = 0

    for vendor in vendors:
        slug = vendor["slug"]
        api_openness = vendor.get("api_openness_score")
        has_webhooks = vendor.get("has_webhooks", False)
        has_oauth = vendor.get("has_oauth", False)
        zapier = vendor.get("zapier_integration", False)
        make = vendor.get("make_integration", False)
        n8n = vendor.get("n8n_integration", False)
        category = vendor.get("category")

        # 1. Cross-reference MCP ecosystem
        mcp_data = mcp_map.get(slug)
        mcp_server_slug = mcp_data["mcp_server_slug"] if mcp_data else None
        mcp_server_maturity = mcp_data["maturity"] if mcp_data else None

        # 2. Derive data portability
        data_portability = derive_data_portability(api_openness)

        # 3. Claude Code compatible if has REST API (openness >= 3)
        claude_code_compatible = bool(api_openness and api_openness >= 3)

        # 4. Agent buildable if good API + webhooks or MCP
        agent_buildable = bool(
            api_openness and api_openness >= 4 and (has_webhooks or mcp_server_slug)
        )

        # 5. Agent patterns
        agent_patterns = derive_agent_patterns(has_webhooks, api_openness, category)

        # 6. Calculate AIOS readiness score
        aios_readiness_score = calculate_aios_readiness_score(
            api_openness_score=api_openness,
            has_webhooks=has_webhooks,
            mcp_server_slug=mcp_server_slug,
            mcp_server_maturity=mcp_server_maturity,
            has_oauth=has_oauth,
            zapier_integration=zapier,
            make_integration=make,
            n8n_integration=n8n,
            data_portability=data_portability,
            agent_buildable=agent_buildable,
        )

        # Build update payload
        update_data: dict = {
            "claude_code_compatible": claude_code_compatible,
            "agent_buildable": agent_buildable,
            "agent_patterns": agent_patterns,
            "aios_readiness_score": aios_readiness_score,
        }

        # Only set MCP fields if we have data
        if mcp_server_slug:
            update_data["mcp_server_slug"] = mcp_server_slug
            update_data["mcp_server_maturity"] = mcp_server_maturity

        # Only set data_portability if derivable
        if data_portability:
            update_data["data_portability"] = data_portability

        try:
            await supabase.table("vendors").update(update_data).eq("id", vendor["id"]).execute()
            updated += 1
            mcp_label = f" [MCP: {mcp_server_slug}]" if mcp_server_slug else ""
            logger.info(
                "  %s: score=%d, cc=%s, agent=%s%s",
                slug, aios_readiness_score, claude_code_compatible, agent_buildable, mcp_label,
            )
        except Exception:
            logger.exception("  Failed to update %s", slug)
            skipped += 1

    logger.info("Done: %d updated, %d skipped", updated, skipped)


async def main() -> None:
    """Run the enrichment."""
    logger.info("Starting AIOS vendor enrichment...")
    logger.info("MCP ecosystem file: %s", MCP_ECOSYSTEM_PATH)
    await enrich_vendors()


if __name__ == "__main__":
    asyncio.run(main())
