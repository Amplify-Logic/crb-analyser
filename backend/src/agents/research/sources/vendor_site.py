"""
Vendor website scraper using Crawl4AI + Claude extraction.

Based on spike testing that showed:
- Crawl4AI successfully renders JS-heavy pages
- Claude Haiku extracts pricing data accurately
- 2-3 second delay needed for JS rendering
"""

import json
import structlog
from typing import Optional

from anthropic import Anthropic

from ..schemas import ExtractedPricing, PricingTier

logger = structlog.get_logger()


async def scrape_vendor_pricing(url: str, vendor_name: str) -> dict:
    """
    Scrape pricing page using Crawl4AI, extract with Claude.

    Returns:
        dict with keys:
        - success: bool
        - data: ExtractedPricing (if success)
        - error: str (if failed)
        - markdown_length: int
    """
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError:
        logger.error("crawl4ai_not_installed")
        return {"success": False, "error": "crawl4ai not installed"}

    logger.info("scraping_vendor_pricing", vendor=vendor_name, url=url)

    try:
        async with AsyncWebCrawler(
            headless=True,
            verbose=False,
        ) as crawler:
            result = await crawler.arun(
                url=url,
                cache_mode="bypass",
                delay_before_return_html=2.5,
            )

            if not result.success:
                logger.warning("crawl_failed", vendor=vendor_name, error=result.error_message)
                return {"success": False, "error": f"Crawl failed: {result.error_message}"}

            markdown = result.markdown or ""
            logger.info(
                "page_crawled",
                vendor=vendor_name,
                html_length=len(result.html),
                markdown_length=len(markdown),
            )

            if len(markdown) < 200:
                logger.warning("insufficient_content", vendor=vendor_name, length=len(markdown))
                return {
                    "success": False,
                    "error": "Insufficient content - page may be JS-heavy or blocked",
                    "markdown_length": len(markdown),
                }

            # Extract pricing with Claude
            pricing_data = _extract_pricing_with_claude(markdown, vendor_name)

            if "error" in pricing_data:
                return {"success": False, "error": pricing_data["error"]}

            return {
                "success": True,
                "data": pricing_data,
                "markdown_length": len(markdown),
            }

    except Exception as e:
        logger.exception("scrape_exception", vendor=vendor_name, error=str(e))
        return {"success": False, "error": str(e)}


def _extract_pricing_with_claude(markdown: str, vendor_name: str) -> dict:
    """Extract pricing data from markdown using Claude Haiku."""
    client = Anthropic()

    # Truncate if too long (pricing usually in first 15k chars)
    if len(markdown) > 15000:
        markdown = markdown[:15000] + "\n\n[... truncated ...]"

    prompt = f"""Extract pricing information for {vendor_name} from this page content.

<page_content>
{markdown}
</page_content>

Return a JSON object with this exact structure:
{{
    "vendor_name": "string - name of the product",
    "pricing_model": "subscription|usage|one-time|freemium",
    "currency": "USD|EUR|GBP",
    "free_tier": true/false/null,
    "free_trial_days": number or null,
    "starting_price": lowest_monthly_price_as_number_or_null,
    "tiers": [
        {{
            "name": "tier name",
            "price": monthly_price_as_number_or_null,
            "price_annual": annual_monthly_equivalent_or_null,
            "billing": "monthly|annual|one-time",
            "features": ["feature1", "feature2"]
        }}
    ],
    "enterprise_available": true/false/null,
    "notes": "any important notes about pricing"
}}

Rules:
- If prices are shown as annual, calculate the monthly equivalent
- If pricing requires contacting sales, set price to null
- starting_price should be the lowest non-zero price
- Include at most 5 features per tier (most important ones)
- Return ONLY valid JSON, no other text"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text.strip()

        # Handle markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        data = json.loads(content)

        # Validate and convert to schema
        return _validate_pricing_data(data, vendor_name)

    except json.JSONDecodeError as e:
        logger.warning("json_parse_failed", vendor=vendor_name, error=str(e))
        return {"error": f"JSON parse failed: {e}"}
    except Exception as e:
        logger.exception("claude_extraction_failed", vendor=vendor_name, error=str(e))
        return {"error": f"Extraction failed: {e}"}


def _validate_pricing_data(data: dict, vendor_name: str) -> dict:
    """Validate and normalize extracted pricing data."""
    try:
        # Build tiers list
        tiers = []
        for tier_data in data.get("tiers", []):
            tier = PricingTier(
                name=tier_data.get("name", "Unknown"),
                price=tier_data.get("price"),
                price_annual=tier_data.get("price_annual"),
                billing=tier_data.get("billing"),
                features=tier_data.get("features", [])[:5],  # Limit features
            )
            tiers.append(tier)

        # Calculate starting_price if not provided
        starting_price = data.get("starting_price")
        if starting_price is None and tiers:
            prices = [t.price for t in tiers if t.price and t.price > 0]
            if prices:
                starting_price = min(prices)

        pricing = ExtractedPricing(
            vendor_name=data.get("vendor_name", vendor_name),
            pricing_model=data.get("pricing_model"),
            currency=data.get("currency", "USD"),
            free_tier=data.get("free_tier"),
            free_trial_days=data.get("free_trial_days"),
            tiers=tiers,
            enterprise_available=data.get("enterprise_available"),
            starting_price=starting_price,
            notes=data.get("notes"),
        )

        return pricing.model_dump()

    except Exception as e:
        logger.warning("validation_failed", vendor=vendor_name, error=str(e))
        return {"error": f"Validation failed: {e}"}


async def scrape_multiple_vendors(vendors: list[dict]) -> list[dict]:
    """
    Scrape pricing for multiple vendors.

    Args:
        vendors: List of dicts with 'slug', 'name', 'pricing_url' keys

    Returns:
        List of results with vendor_slug and scrape result
    """
    results = []

    for vendor in vendors:
        slug = vendor.get("slug", "unknown")
        name = vendor.get("name", slug)
        url = vendor.get("pricing_url") or vendor.get("website")

        if not url:
            results.append({
                "vendor_slug": slug,
                "success": False,
                "error": "No URL provided",
            })
            continue

        # Add /pricing if URL is just the main site
        if url and not any(p in url.lower() for p in ["pricing", "plans", "price"]):
            # Try common pricing URL patterns
            pricing_url = url.rstrip("/") + "/pricing"
        else:
            pricing_url = url

        result = await scrape_vendor_pricing(pricing_url, name)
        result["vendor_slug"] = slug
        results.append(result)

    return results
