"""
Software Research Service

Researches unknown software to determine API/integration capabilities.
Used in the Connect vs Replace feature to evaluate user's existing stack.

When a user enters software not in our vendor database, this service:
1. Searches the web for API documentation, Zapier listings, webhook mentions
2. Uses Claude to analyze findings and estimate API openness score (1-5)
3. Returns structured capabilities data

Results can be cached in:
- Session only (for immediate use)
- Vendors table as status="unverified" (for reuse across sessions)
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from src.config.llm_client import get_llm_client
from src.config.model_routing import CLAUDE_MODELS
from src.config.supabase_client import get_async_supabase
from src.tools.research_scraper_tools import search_web
from src.models.software_research import (
    SoftwareCapabilities,
    SoftwareResearchResult,
    ExistingStackItemResearched,
)

logger = logging.getLogger(__name__)

# Cache duration for research results
RESEARCH_CACHE_HOURS = 24 * 30  # 30 days

# Search queries to run for each software
SEARCH_QUERIES = [
    "{name} API documentation",
    "{name} Zapier integration",
    "{name} webhooks developer",
    "{name} Make integration",
]


class SoftwareResearchService:
    """
    Service for researching unknown software API capabilities.

    Searches for API docs, integration listings, and webhook support,
    then uses Claude to estimate an API openness score.
    """

    async def research_unknown_software(
        self,
        name: str,
        context: Optional[str] = None,
        check_cache: bool = True,
    ) -> SoftwareResearchResult:
        """
        Research an unknown software to determine API capabilities.

        Args:
            name: Software name to research
            context: Optional context (e.g., industry, software type)
            check_cache: Whether to check vendor DB cache first

        Returns:
            SoftwareResearchResult with capabilities or error
        """
        name = name.strip()
        if not name:
            return SoftwareResearchResult(
                name=name,
                found=False,
                error="Software name cannot be empty",
            )

        logger.info(f"Researching software: {name}")

        # Check cache first
        if check_cache:
            cached = await self._check_vendor_cache(name)
            if cached:
                logger.info(f"Found cached research for {name}")
                return SoftwareResearchResult(
                    name=name,
                    capabilities=cached,
                    found=True,
                    cached=True,
                )

        # Run web searches in parallel
        try:
            search_results = await self._run_searches(name)
        except Exception as e:
            logger.error(f"Search failed for {name}: {e}")
            return SoftwareResearchResult(
                name=name,
                found=False,
                error=f"Search failed: {str(e)}",
            )

        # Check if we found anything useful
        total_results = sum(len(r.get("results", [])) for r in search_results.values())
        if total_results == 0:
            logger.warning(f"No search results found for {name}")
            return SoftwareResearchResult(
                name=name,
                found=False,
                error="No information found for this software",
            )

        # Use Claude to analyze results
        try:
            capabilities = await self._analyze_with_claude(name, search_results, context)
        except Exception as e:
            logger.error(f"Claude analysis failed for {name}: {e}")
            return SoftwareResearchResult(
                name=name,
                found=False,
                error=f"Analysis failed: {str(e)}",
            )

        logger.info(
            f"Research complete for {name}: score={capabilities.estimated_api_score}"
        )

        return SoftwareResearchResult(
            name=name,
            capabilities=capabilities,
            found=True,
            cached=False,
        )

    async def _run_searches(self, name: str) -> Dict[str, Any]:
        """Run all search queries in parallel."""
        results = {}

        # Create search tasks
        tasks = []
        for query_template in SEARCH_QUERIES:
            query = query_template.format(name=name)
            tasks.append(search_web(query, num_results=5))

        # Run in parallel with timeout
        try:
            search_responses = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Search timeout for {name}")
            return {}

        # Map results to query types
        query_types = ["api_docs", "zapier", "webhooks", "make"]
        for i, response in enumerate(search_responses):
            if isinstance(response, Exception):
                logger.warning(f"Search query {i} failed: {response}")
                continue
            results[query_types[i]] = response

        return results

    async def _analyze_with_claude(
        self,
        name: str,
        search_results: Dict[str, Any],
        context: Optional[str] = None,
    ) -> SoftwareCapabilities:
        """Use Claude to analyze search results and determine API capabilities."""

        # Format search results for the prompt
        formatted_results = self._format_search_results(search_results)

        # Collect source URLs
        source_urls = []
        for query_type, result in search_results.items():
            for item in result.get("results", []):
                url = item.get("url")
                if url and url not in source_urls:
                    source_urls.append(url)

        # Build the analysis prompt
        system_prompt = """You are an expert at evaluating software API and integration capabilities.

Your task is to analyze search results about a software product and determine its API/integration capabilities.

Rate the software's API openness on a 1-5 scale:
5 = Full REST API with webhooks, OAuth, comprehensive documentation (e.g., Stripe, Twilio, HubSpot)
4 = Good API with some limitations, decent documentation (e.g., Salesforce, Zendesk)
3 = Basic API with limited endpoints, or well-documented Zapier/Make integration only
2 = Zapier/Make integration only with no direct API access
1 = Closed system with no documented integrations

Respond with JSON only, no other text:
{
    "estimated_api_score": <1-5>,
    "has_api": <true/false>,
    "has_webhooks": <true/false>,
    "has_zapier": <true/false>,
    "has_make": <true/false>,
    "has_oauth": <true/false>,
    "reasoning": "<2-3 sentences explaining the score>",
    "confidence": <0.0-1.0 confidence in assessment>
}"""

        user_prompt = f"""Analyze the API/integration capabilities of: {name}

{f"Context: {context}" if context else ""}

Search Results:
{formatted_results}

Based on these search results, what are the API and integration capabilities of {name}?
If the search results don't contain clear information, make reasonable assumptions based on:
- Whether API documentation pages were found
- Whether Zapier/Make integrations exist
- Whether webhooks are mentioned

Respond with JSON only."""

        # Call Claude using Haiku (fast task)
        client = get_llm_client("anthropic")
        response = client.generate(
            model=CLAUDE_MODELS["haiku"],
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=500,
            temperature=0.3,  # Lower temperature for more consistent analysis
        )

        # Parse the response
        content = response.get("content", "")

        # Extract JSON from response (handle potential markdown code blocks)
        json_match = re.search(r"\{[^{}]*\}", content, re.DOTALL)
        if not json_match:
            logger.warning(f"Could not parse JSON from Claude response: {content[:200]}")
            # Return default low-confidence result
            return SoftwareCapabilities(
                name=name,
                estimated_api_score=2,
                has_api=False,
                has_webhooks=False,
                has_zapier=False,
                has_make=False,
                has_oauth=False,
                reasoning="Could not determine API capabilities from available information",
                source_urls=source_urls[:5],
                confidence=0.2,
            )

        import json
        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {e}")
            return SoftwareCapabilities(
                name=name,
                estimated_api_score=2,
                has_api=False,
                has_webhooks=False,
                has_zapier=False,
                has_make=False,
                has_oauth=False,
                reasoning="Could not parse analysis results",
                source_urls=source_urls[:5],
                confidence=0.2,
            )

        return SoftwareCapabilities(
            name=name,
            estimated_api_score=min(5, max(1, data.get("estimated_api_score", 2))),
            has_api=data.get("has_api", False),
            has_webhooks=data.get("has_webhooks", False),
            has_zapier=data.get("has_zapier", False),
            has_make=data.get("has_make", False),
            has_oauth=data.get("has_oauth", False),
            reasoning=data.get("reasoning", ""),
            source_urls=source_urls[:5],
            confidence=data.get("confidence", 0.5),
        )

    def _format_search_results(self, search_results: Dict[str, Any]) -> str:
        """Format search results into a readable string for the prompt."""
        sections = []

        for query_type, result in search_results.items():
            if not result.get("results"):
                continue

            section_name = {
                "api_docs": "API Documentation Search",
                "zapier": "Zapier Integration Search",
                "webhooks": "Webhooks Search",
                "make": "Make Integration Search",
            }.get(query_type, query_type)

            items = []
            for item in result.get("results", [])[:3]:  # Limit to top 3 per query
                title = item.get("title", "")
                desc = item.get("description", "")
                url = item.get("url", "")
                items.append(f"- {title}\n  {desc[:200]}...\n  URL: {url}")

            if items:
                sections.append(f"## {section_name}\n" + "\n".join(items))

        return "\n\n".join(sections) if sections else "No relevant results found."

    async def _check_vendor_cache(self, name: str) -> Optional[SoftwareCapabilities]:
        """Check if this software was already researched and cached in vendors table."""
        try:
            supabase = await get_async_supabase()

            # Search by name (case-insensitive) in vendors with unverified status
            result = await supabase.table("vendors").select(
                "name, api_openness_score, api_available, has_webhooks, "
                "zapier_integration, make_integration, has_oauth, "
                "description, updated_at"
            ).ilike("name", f"%{name}%").eq("status", "unverified").limit(1).execute()

            if not result.data:
                return None

            vendor = result.data[0]

            # Check if cache is still fresh
            updated_at = vendor.get("updated_at")
            if updated_at:
                updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                if datetime.now(updated.tzinfo) - updated > timedelta(hours=RESEARCH_CACHE_HOURS):
                    return None  # Cache expired

            if vendor.get("api_openness_score") is None:
                return None

            return SoftwareCapabilities(
                name=vendor.get("name", name),
                estimated_api_score=vendor.get("api_openness_score", 2),
                has_api=vendor.get("api_available", False),
                has_webhooks=vendor.get("has_webhooks", False),
                has_zapier=vendor.get("zapier_integration", False),
                has_make=vendor.get("make_integration", False),
                has_oauth=vendor.get("has_oauth", False),
                reasoning=vendor.get("description", ""),
                source_urls=[],
                confidence=0.7,  # Higher confidence for cached results
            )

        except Exception as e:
            logger.warning(f"Cache check failed for {name}: {e}")
            return None

    async def cache_research_result(
        self,
        capabilities: SoftwareCapabilities,
    ) -> bool:
        """
        Cache research result in vendors table as unverified.

        This allows reuse across sessions and eventual human verification.
        """
        try:
            supabase = await get_async_supabase()

            # Generate a slug from the name
            slug = re.sub(r"[^a-z0-9]+", "-", capabilities.name.lower()).strip("-")
            slug = f"unverified-{slug}"

            # Check if already exists
            existing = await supabase.table("vendors").select("id").eq(
                "slug", slug
            ).limit(1).execute()

            vendor_data = {
                "name": capabilities.name,
                "slug": slug,
                "category": "unknown",  # Will be categorized if verified later
                "status": "unverified",
                "api_openness_score": capabilities.estimated_api_score,
                "api_available": capabilities.has_api,
                "has_webhooks": capabilities.has_webhooks,
                "zapier_integration": capabilities.has_zapier,
                "make_integration": capabilities.has_make,
                "has_oauth": capabilities.has_oauth,
                "description": capabilities.reasoning,
                "updated_at": datetime.utcnow().isoformat(),
            }

            if existing.data:
                # Update existing
                await supabase.table("vendors").update(vendor_data).eq(
                    "slug", slug
                ).execute()
            else:
                # Insert new
                vendor_data["created_at"] = datetime.utcnow().isoformat()
                await supabase.table("vendors").insert(vendor_data).execute()

            logger.info(f"Cached research result for {capabilities.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to cache research result: {e}")
            return False


# ============================================================================
# SESSION INTEGRATION HELPERS
# ============================================================================


async def research_session_stack(
    existing_stack: List[Dict[str, Any]],
    cache_results: bool = True,
) -> List[ExistingStackItemResearched]:
    """
    Research all free_text entries in a session's existing_stack.

    Args:
        existing_stack: List of existing stack items from session
        cache_results: Whether to cache results in vendors table

    Returns:
        List of researched items with API scores
    """
    service = SoftwareResearchService()
    researched_items = []

    for item in existing_stack:
        source = item.get("source", "selected")
        slug = item.get("slug", "")
        name = item.get("name", slug)

        if source == "free_text" and name:
            # Research this unknown software
            result = await service.research_unknown_software(name)

            if result.found and result.capabilities:
                # Cache for future use
                if cache_results:
                    await service.cache_research_result(result.capabilities)

                researched_items.append(ExistingStackItemResearched(
                    slug=slug,
                    source=source,
                    name=name,
                    researched=True,
                    api_score=result.capabilities.estimated_api_score,
                    reasoning=result.capabilities.reasoning,
                    has_api=result.capabilities.has_api,
                    has_webhooks=result.capabilities.has_webhooks,
                    has_zapier=result.capabilities.has_zapier,
                ))
            else:
                # Research failed, keep item without score
                researched_items.append(ExistingStackItemResearched(
                    slug=slug,
                    source=source,
                    name=name,
                    researched=True,
                    api_score=None,
                    reasoning=result.error or "Research inconclusive",
                ))
        else:
            # Selected from our list - look up API score from vendor DB
            api_score = await _get_vendor_api_score(slug)
            researched_items.append(ExistingStackItemResearched(
                slug=slug,
                source=source,
                name=name,
                researched=False,
                api_score=api_score,
            ))

    return researched_items


async def _get_vendor_api_score(slug: str) -> Optional[int]:
    """Get API openness score for a known vendor."""
    try:
        supabase = await get_async_supabase()
        result = await supabase.table("vendors").select(
            "api_openness_score"
        ).eq("slug", slug).limit(1).execute()

        if result.data:
            return result.data[0].get("api_openness_score")
        return None

    except Exception as e:
        logger.warning(f"Failed to get API score for {slug}: {e}")
        return None


# Singleton instance
software_research_service = SoftwareResearchService()
