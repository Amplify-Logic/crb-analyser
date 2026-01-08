"""
Web search for vendor discovery using Brave Search or Tavily.
"""

import json
from typing import Optional

import httpx
import structlog

from src.config.settings import settings

logger = structlog.get_logger()


async def search_vendors(
    category: str,
    industry: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """
    Search for vendors in a category/industry.

    Returns list of search results with:
    - title: str
    - url: str
    - description: str
    - source: str (brave or tavily)
    """
    # Build search queries
    queries = _build_search_queries(category, industry)

    all_results = []

    for query in queries:
        # Try Brave first, then Tavily
        if settings.BRAVE_SEARCH_API_KEY:
            results = await _search_brave(query, limit=limit // len(queries))
            all_results.extend(results)
        elif settings.TAVILY_API_KEY:
            results = await _search_tavily(query, limit=limit // len(queries))
            all_results.extend(results)
        else:
            logger.warning("no_search_api_configured")
            break

    # Deduplicate by URL
    seen_urls = set()
    unique_results = []
    for r in all_results:
        url = r.get("url", "").rstrip("/").lower()
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(r)

    return unique_results[:limit]


def _build_search_queries(category: str, industry: Optional[str] = None) -> list[str]:
    """Build search queries for vendor discovery."""
    queries = []

    # Map category to search-friendly terms
    category_terms = {
        "crm": "CRM software",
        "customer_support": "customer support software helpdesk",
        "ai_sales_tools": "AI sales tools software",
        "automation": "automation software workflow",
        "analytics": "analytics software business intelligence",
        "marketing": "marketing automation software",
        "project_management": "project management software",
        "ai_assistants": "AI assistant software business",
        "ai_agents": "AI agents automation software",
    }

    category_term = category_terms.get(category, f"{category} software")

    # Industry-specific queries
    if industry:
        queries.append(f"best {category_term} for {industry} 2026")
        queries.append(f"{industry} {category_term} tools")
    else:
        queries.append(f"best {category_term} 2026")
        queries.append(f"top {category_term} small business")

    return queries


async def _search_brave(query: str, limit: int = 10) -> list[dict]:
    """Search using Brave Search API."""
    if not settings.BRAVE_SEARCH_API_KEY:
        return []

    logger.info("brave_search", query=query)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={
                    "X-Subscription-Token": settings.BRAVE_SEARCH_API_KEY,
                    "Accept": "application/json",
                },
                params={
                    "q": query,
                    "count": limit,
                    "text_decorations": False,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("web", {}).get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", ""),
                    "source": "brave",
                })

            logger.info("brave_search_results", query=query, count=len(results))
            return results

    except Exception as e:
        logger.exception("brave_search_failed", query=query, error=str(e))
        return []


async def _search_tavily(query: str, limit: int = 10) -> list[dict]:
    """Search using Tavily API."""
    if not settings.TAVILY_API_KEY:
        return []

    logger.info("tavily_search", query=query)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.TAVILY_API_KEY,
                    "query": query,
                    "max_results": limit,
                    "include_domains": [],
                    "exclude_domains": [],
                },
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("content", "")[:300],
                    "source": "tavily",
                })

            logger.info("tavily_search_results", query=query, count=len(results))
            return results

    except Exception as e:
        logger.exception("tavily_search_failed", query=query, error=str(e))
        return []


def extract_vendor_from_url(url: str) -> Optional[str]:
    """Extract vendor name/slug from a URL."""
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]

        # Remove common TLDs
        for tld in [".com", ".io", ".co", ".ai", ".app", ".dev", ".org", ".net"]:
            if domain.endswith(tld):
                domain = domain[:-len(tld)]
                break

        # Clean up and return
        slug = domain.replace(".", "-").replace("_", "-")
        return slug if slug else None

    except Exception:
        return None
