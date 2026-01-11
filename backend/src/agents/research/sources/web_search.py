"""
Web search for vendor discovery using Brave Search or Tavily.

Improvements:
- Better error handling with specific error types
- Retry logic for transient failures
- Clearer logging and diagnostics
"""

import asyncio
from typing import Optional

import httpx
import structlog

from src.config.settings import settings

logger = structlog.get_logger()


# =============================================================================
# Configuration
# =============================================================================

class SearchConfig:
    """Search configuration constants."""
    REQUEST_TIMEOUT = 15.0
    MAX_RETRIES = 2
    RETRY_DELAY = 1.0


# =============================================================================
# Error Types
# =============================================================================

class SearchError(Exception):
    """Base class for search errors."""
    pass


class NoSearchAPIError(SearchError):
    """No search API configured."""
    pass


class SearchAPIError(SearchError):
    """Search API returned an error."""
    def __init__(self, message: str, provider: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code


# =============================================================================
# Main Search Function
# =============================================================================

async def search_vendors(
    category: str,
    industry: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """
    Search for vendors in a category/industry.

    Uses Brave Search (primary) or Tavily (fallback).

    Returns list of search results with:
    - title: str
    - url: str
    - description: str
    - source: str (brave or tavily)

    Raises:
        NoSearchAPIError: If no search API is configured
    """
    # Check if any search API is available
    if not settings.BRAVE_SEARCH_API_KEY and not settings.TAVILY_API_KEY:
        logger.error("no_search_api_configured")
        raise NoSearchAPIError(
            "No search API configured. Set BRAVE_SEARCH_API_KEY or TAVILY_API_KEY."
        )

    # Build search queries
    queries = _build_search_queries(category, industry)

    all_results = []
    errors = []

    for query in queries:
        results = None

        # Try Brave first
        if settings.BRAVE_SEARCH_API_KEY:
            try:
                results = await _search_brave_with_retry(query, limit=limit // len(queries))
            except SearchAPIError as e:
                errors.append(f"Brave: {e}")
                logger.warning("brave_search_error", query=query, error=str(e))

        # Try Tavily as fallback
        if results is None and settings.TAVILY_API_KEY:
            try:
                results = await _search_tavily_with_retry(query, limit=limit // len(queries))
            except SearchAPIError as e:
                errors.append(f"Tavily: {e}")
                logger.warning("tavily_search_error", query=query, error=str(e))

        if results:
            all_results.extend(results)

    # Log if we had errors but still got some results
    if errors and all_results:
        logger.info("search_completed_with_errors", result_count=len(all_results), errors=errors)

    # If no results and we had errors, log them
    if not all_results and errors:
        logger.error("all_searches_failed", errors=errors)

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


# =============================================================================
# Brave Search
# =============================================================================

async def _search_brave_with_retry(query: str, limit: int = 10) -> list[dict]:
    """Search using Brave Search API with retry."""
    last_error = None

    for attempt in range(SearchConfig.MAX_RETRIES):
        try:
            return await _search_brave(query, limit)
        except SearchAPIError as e:
            last_error = e
            if e.status_code and e.status_code < 500:
                # Client error, don't retry
                raise
            if attempt < SearchConfig.MAX_RETRIES - 1:
                await asyncio.sleep(SearchConfig.RETRY_DELAY * (attempt + 1))

    raise last_error or SearchAPIError("Unknown error", "brave")


async def _search_brave(query: str, limit: int = 10) -> list[dict]:
    """Search using Brave Search API."""
    if not settings.BRAVE_SEARCH_API_KEY:
        raise SearchAPIError("Brave API key not configured", "brave")

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
                timeout=SearchConfig.REQUEST_TIMEOUT,
            )

            if response.status_code == 429:
                raise SearchAPIError("Rate limited", "brave", 429)

            if response.status_code != 200:
                raise SearchAPIError(
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    "brave",
                    response.status_code,
                )

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

    except httpx.TimeoutException:
        raise SearchAPIError("Request timed out", "brave")
    except httpx.RequestError as e:
        raise SearchAPIError(f"Request failed: {e}", "brave")


# =============================================================================
# Tavily Search
# =============================================================================

async def _search_tavily_with_retry(query: str, limit: int = 10) -> list[dict]:
    """Search using Tavily API with retry."""
    last_error = None

    for attempt in range(SearchConfig.MAX_RETRIES):
        try:
            return await _search_tavily(query, limit)
        except SearchAPIError as e:
            last_error = e
            if e.status_code and e.status_code < 500:
                # Client error, don't retry
                raise
            if attempt < SearchConfig.MAX_RETRIES - 1:
                await asyncio.sleep(SearchConfig.RETRY_DELAY * (attempt + 1))

    raise last_error or SearchAPIError("Unknown error", "tavily")


async def _search_tavily(query: str, limit: int = 10) -> list[dict]:
    """Search using Tavily API."""
    if not settings.TAVILY_API_KEY:
        raise SearchAPIError("Tavily API key not configured", "tavily")

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
                timeout=SearchConfig.REQUEST_TIMEOUT,
            )

            if response.status_code == 429:
                raise SearchAPIError("Rate limited", "tavily", 429)

            if response.status_code != 200:
                raise SearchAPIError(
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    "tavily",
                    response.status_code,
                )

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

    except httpx.TimeoutException:
        raise SearchAPIError("Request timed out", "tavily")
    except httpx.RequestError as e:
        raise SearchAPIError(f"Request failed: {e}", "tavily")


# =============================================================================
# Utilities
# =============================================================================

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
