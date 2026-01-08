"""
Vendor discovery service.

Handles:
- Searching for new vendors via web search
- Extracting vendor info from search results
- Filtering out existing vendors
- Validating and scoring candidates
"""

import json
import re
import uuid
from typing import AsyncGenerator, Optional
from urllib.parse import urlparse

import structlog
from anthropic import Anthropic

from src.config.supabase_client import get_async_supabase

from .schemas import DiscoveredVendor, DiscoverRequest
from .sources.web_search import search_vendors, extract_vendor_from_url
from .sources.vendor_site import scrape_vendor_pricing

logger = structlog.get_logger()


async def get_existing_vendor_slugs() -> set[str]:
    """Get set of all existing vendor slugs."""
    supabase = await get_async_supabase()
    result = await supabase.table("vendors").select("slug").execute()
    return {v["slug"] for v in (result.data or [])}


async def get_existing_vendor_domains() -> set[str]:
    """Get set of all existing vendor website domains."""
    supabase = await get_async_supabase()
    result = await supabase.table("vendors").select("website").execute()

    domains = set()
    for v in result.data or []:
        website = v.get("website", "")
        if website:
            try:
                parsed = urlparse(website)
                domain = parsed.netloc.lower().replace("www.", "")
                if domain:
                    domains.add(domain)
            except Exception:
                pass

    return domains


async def discover_vendors(
    request: DiscoverRequest,
) -> AsyncGenerator[dict, None]:
    """
    Discover new vendors based on category/industry.

    Yields progress updates:
    - {"type": "started", "task_id": str}
    - {"type": "searching", "query": str}
    - {"type": "found", "count": int, "raw_results": int}
    - {"type": "validating", "current": int, "total": int, "vendor": str}
    - {"type": "candidate", "vendor": DiscoveredVendor}
    - {"type": "completed", "task_id": str, "candidates": int}
    """
    task_id = str(uuid.uuid4())
    logger.info(
        "discovery_started",
        task_id=task_id,
        category=request.category,
        industry=request.industry,
    )

    yield {"type": "started", "task_id": task_id}

    # Get existing vendors to filter out
    existing_slugs = await get_existing_vendor_slugs()
    existing_domains = await get_existing_vendor_domains()

    yield {"type": "searching", "category": request.category, "industry": request.industry}

    # Search for vendors
    search_results = await search_vendors(
        category=request.category,
        industry=request.industry,
        limit=request.limit * 3,  # Get extra to account for filtering
    )

    yield {"type": "found", "raw_results": len(search_results)}

    # Filter out non-vendor results and existing vendors
    candidates = []
    for result in search_results:
        url = result.get("url", "")
        domain = _extract_domain(url)

        # Skip if already have this vendor
        if domain and domain in existing_domains:
            continue

        slug = extract_vendor_from_url(url)
        if slug and slug in existing_slugs:
            continue

        # Skip obvious non-vendors (review sites, blogs, etc.)
        if _is_non_vendor_url(url):
            continue

        candidates.append({
            "url": url,
            "title": result.get("title", ""),
            "description": result.get("description", ""),
            "source": result.get("source", "web"),
            "domain": domain,
        })

    logger.info("candidates_filtered", total=len(search_results), remaining=len(candidates))

    yield {
        "type": "filtering_complete",
        "raw_results": len(search_results),
        "candidates": len(candidates),
    }

    # Validate and enrich candidates
    validated = []
    for i, candidate in enumerate(candidates[:request.limit]):
        url = candidate["url"]
        title = candidate["title"]

        yield {
            "type": "validating",
            "current": i + 1,
            "total": min(len(candidates), request.limit),
            "vendor": title,
        }

        # Try to extract vendor info
        vendor_info = await _extract_vendor_info(candidate, request.category)

        if vendor_info:
            validated.append(vendor_info)
            yield {
                "type": "candidate",
                "vendor": vendor_info.model_dump(),
            }

    yield {
        "type": "completed",
        "task_id": task_id,
        "candidates": len(validated),
    }

    logger.info(
        "discovery_completed",
        task_id=task_id,
        candidates=len(validated),
    )


async def _extract_vendor_info(candidate: dict, category: str) -> Optional[DiscoveredVendor]:
    """Extract and validate vendor info from a search result."""
    url = candidate["url"]
    title = candidate["title"]
    description = candidate["description"]
    domain = candidate["domain"]

    # Generate slug from domain
    slug = extract_vendor_from_url(url)
    if not slug:
        return None

    # Use Claude to extract vendor name and assess relevance
    client = Anthropic()

    prompt = f"""Analyze this search result and determine if it's a software vendor:

Title: {title}
URL: {url}
Description: {description}
Target category: {category}

Return JSON:
{{
    "is_vendor": true/false,
    "vendor_name": "extracted vendor/product name",
    "description": "one sentence description of what the software does",
    "relevance_score": 0.0-1.0 (how relevant to {category}),
    "warning": "any concerns, or null"
}}

Only JSON, no other text."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        data = json.loads(content)

        if not data.get("is_vendor", False):
            return None

        # Build discovered vendor
        vendor = DiscoveredVendor(
            name=data.get("vendor_name", title),
            slug=slug,
            website=_normalize_website(url),
            description=data.get("description", description[:200]),
            category=category,
            sources=[candidate.get("source", "web")],
            relevance_score=float(data.get("relevance_score", 0.5)),
            warning=data.get("warning"),
        )

        return vendor

    except Exception as e:
        logger.warning("vendor_extraction_failed", url=url, error=str(e))
        return None


async def add_discovered_vendor(vendor: DiscoveredVendor) -> dict:
    """Add a discovered vendor to the database."""
    supabase = await get_async_supabase()

    try:
        # Insert vendor
        result = await (
            supabase.table("vendors")
            .insert({
                "slug": vendor.slug,
                "name": vendor.name,
                "category": vendor.category,
                "website": vendor.website,
                "description": vendor.description,
                "status": "needs_review",  # New vendors need manual review
                "verified_by": "research-agent-v1",
            })
            .execute()
        )

        # Log to audit
        await (
            supabase.table("vendor_audit_log")
            .insert({
                "vendor_slug": vendor.slug,
                "action": "create",
                "changed_by": "research-agent-v1",
                "changes": {"source": "discovery", "sources": vendor.sources},
            })
            .execute()
        )

        logger.info("vendor_added", slug=vendor.slug, name=vendor.name)

        return {"success": True, "slug": vendor.slug}

    except Exception as e:
        logger.exception("add_vendor_failed", slug=vendor.slug, error=str(e))
        return {"success": False, "error": str(e)}


async def add_multiple_vendors(vendors: list[DiscoveredVendor]) -> dict:
    """Add multiple discovered vendors to the database."""
    results = {"added": [], "errors": []}

    for vendor in vendors:
        result = await add_discovered_vendor(vendor)
        if result.get("success"):
            results["added"].append(vendor.slug)
        else:
            results["errors"].append(f"{vendor.slug}: {result.get('error')}")

    return results


def _extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
        return domain if domain else None
    except Exception:
        return None


def _normalize_website(url: str) -> str:
    """Normalize URL to just the base website."""
    try:
        parsed = urlparse(url)
        return f"https://{parsed.netloc}"
    except Exception:
        return url


def _is_non_vendor_url(url: str) -> bool:
    """Check if URL is likely not a vendor website."""
    non_vendor_patterns = [
        r"g2\.com",
        r"capterra\.com",
        r"trustradius\.com",
        r"softwareadvice\.com",
        r"getapp\.com",
        r"producthunt\.com",
        r"wikipedia\.org",
        r"youtube\.com",
        r"linkedin\.com",
        r"twitter\.com",
        r"facebook\.com",
        r"reddit\.com",
        r"medium\.com",
        r"forbes\.com",
        r"techcrunch\.com",
        r"blog\.",
        r"/blog/",
        r"/reviews?/",
        r"/compare/",
        r"/vs/",
        r"/alternatives/",
        r"best-.*-software",
    ]

    url_lower = url.lower()
    for pattern in non_vendor_patterns:
        if re.search(pattern, url_lower):
            return True

    return False
