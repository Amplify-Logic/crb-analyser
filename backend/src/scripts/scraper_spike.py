"""
Scraper Spike: Test Crawl4AI on vendor pricing pages.

Usage:
    cd backend
    source venv/bin/activate
    pip install crawl4ai
    crawl4ai-setup  # Install browser dependencies
    python -m src.scripts.scraper_spike

Approach:
    1. Crawl4AI fetches page and converts to markdown (good at JS rendering)
    2. Our Claude API extracts structured pricing data (we control the model)
"""

import asyncio
import json
import os
from pydantic import BaseModel, Field
from typing import Optional
from anthropic import Anthropic


# ============================================================================
# Pydantic schemas for extraction
# ============================================================================

class PricingTier(BaseModel):
    """A single pricing tier."""
    name: str = Field(description="Tier name (e.g., 'Starter', 'Professional')")
    price: Optional[float] = Field(description="Monthly price in USD, null if custom/enterprise")
    price_annual: Optional[float] = Field(description="Annual price per month if different")
    billing: Optional[str] = Field(description="Billing period: 'monthly', 'annual', 'one-time'")
    features: list[str] = Field(default_factory=list, description="Key features included")


class VendorPricing(BaseModel):
    """Extracted pricing data from a vendor website."""
    vendor_name: str = Field(description="Name of the vendor/product")
    pricing_model: str = Field(description="Model: 'subscription', 'usage', 'one-time', 'freemium'")
    currency: str = Field(default="USD", description="Currency code")
    free_tier: bool = Field(description="Whether a free tier exists")
    free_trial_days: Optional[int] = Field(description="Free trial duration if offered")
    tiers: list[PricingTier] = Field(default_factory=list, description="Available pricing tiers")
    enterprise_available: bool = Field(description="Whether custom enterprise pricing exists")
    notes: Optional[str] = Field(description="Any important notes about pricing")


# Load env
from dotenv import load_dotenv
load_dotenv()


# ============================================================================
# Test URLs
# ============================================================================

TEST_VENDORS = [
    {
        "name": "HubSpot CRM",
        "url": "https://www.hubspot.com/pricing/crm",
        "category": "crm",
    },
    {
        "name": "Freshdesk",
        "url": "https://www.freshworks.com/freshdesk/pricing/",
        "category": "customer_support",
    },
    {
        "name": "Calendly",
        "url": "https://calendly.com/pricing",
        "category": "automation",
    },
]

# G2 URLs for rating/review data
TEST_G2_VENDORS = [
    {
        "name": "HubSpot CRM",
        "url": "https://www.g2.com/products/hubspot-crm/reviews",
        "slug": "hubspot-crm",
    },
    {
        "name": "Freshdesk",
        "url": "https://www.g2.com/products/freshdesk/reviews",
        "slug": "freshdesk",
    },
    {
        "name": "Calendly",
        "url": "https://www.g2.com/products/calendly/reviews",
        "slug": "calendly",
    },
]


# ============================================================================
# Scraper implementation
# ============================================================================

def extract_pricing_with_claude(markdown: str, vendor_name: str) -> dict:
    """Extract pricing data from markdown using Claude API directly."""
    client = Anthropic()

    # Truncate markdown if too long (keep first 15k chars which usually has pricing)
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
    "free_tier": true/false,
    "free_trial_days": number or null,
    "tiers": [
        {{
            "name": "tier name",
            "price": monthly_price_as_number_or_null,
            "price_annual": annual_monthly_equivalent_or_null,
            "billing": "monthly|annual|one-time",
            "features": ["feature1", "feature2"]
        }}
    ],
    "enterprise_available": true/false,
    "notes": "any important notes about pricing"
}}

If prices are shown as annual, calculate the monthly equivalent.
If pricing requires contacting sales, set price to null and note it.
Return ONLY the JSON, no other text."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text.strip()

        # Try to parse JSON (handle markdown code blocks)
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        return json.loads(content)

    except json.JSONDecodeError as e:
        return {"error": f"JSON parse failed: {e}", "raw": content[:500]}
    except Exception as e:
        return {"error": f"Claude API error: {e}"}


async def scrape_pricing_page(url: str, vendor_name: str) -> dict:
    """Scrape pricing page using Crawl4AI, then extract with Claude."""
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError:
        print("ERROR: crawl4ai not installed. Run: pip install crawl4ai && crawl4ai-setup")
        return {"error": "crawl4ai not installed"}

    print(f"\n{'='*60}")
    print(f"Scraping: {vendor_name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    try:
        # Step 1: Crawl the page
        async with AsyncWebCrawler(
            headless=True,
            verbose=False,
        ) as crawler:
            result = await crawler.arun(
                url=url,
                cache_mode="bypass",
                delay_before_return_html=2.0,  # Wait for JS to load
            )

            if not result.success:
                print(f"\n✗ Crawl failed: {result.error_message}")
                return {"error": result.error_message}

            markdown = result.markdown or ""
            print(f"\n✓ Page crawled: {len(result.html)} chars HTML, {len(markdown)} chars markdown")

            if len(markdown) < 100:
                print("  ⚠ Very little markdown content - page may be JS-heavy")
                return {"error": "Insufficient content extracted"}

            # Step 2: Extract pricing with Claude
            print("  Extracting pricing with Claude...")
            pricing_data = extract_pricing_with_claude(markdown, vendor_name)

            if "error" in pricing_data:
                print(f"  ✗ Extraction failed: {pricing_data['error']}")
                return pricing_data

            print(f"\n📦 Extracted pricing:")
            print(json.dumps(pricing_data, indent=2))

            return {"success": True, "data": pricing_data}

    except Exception as e:
        print(f"\n✗ Exception: {type(e).__name__}: {e}")
        return {"error": str(e)}


class G2VendorData(BaseModel):
    """Extracted G2 data for a vendor."""
    vendor_name: str
    g2_score: Optional[float] = Field(description="Overall G2 rating out of 5")
    review_count: Optional[int] = Field(description="Total number of reviews")
    category: Optional[str] = Field(description="Primary G2 category")
    description: Optional[str] = Field(description="Short product description")
    best_for: list[str] = Field(default_factory=list, description="Who the product is best for")
    pros: list[str] = Field(default_factory=list, description="Common pros mentioned")
    cons: list[str] = Field(default_factory=list, description="Common cons mentioned")


def extract_g2_data_with_claude(markdown: str, vendor_name: str) -> dict:
    """Extract G2 vendor data from markdown using Claude."""
    client = Anthropic()

    if len(markdown) > 20000:
        markdown = markdown[:20000] + "\n\n[... truncated ...]"

    prompt = f"""Extract G2 review data for {vendor_name} from this G2.com page content.

<page_content>
{markdown}
</page_content>

Return a JSON object with this structure:
{{
    "vendor_name": "{vendor_name}",
    "g2_score": rating_out_of_5_as_float,
    "review_count": total_reviews_as_integer,
    "category": "primary category",
    "description": "short product description",
    "best_for": ["audience1", "audience2"],
    "pros": ["common pro 1", "common pro 2", "common pro 3"],
    "cons": ["common con 1", "common con 2"]
}}

Extract the overall star rating, review count, and summarize common pros/cons from reviews.
Return ONLY the JSON, no other text."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        return json.loads(content)

    except json.JSONDecodeError as e:
        return {"error": f"JSON parse failed: {e}", "raw": content[:500]}
    except Exception as e:
        return {"error": f"Claude API error: {e}"}


async def scrape_g2_page(url: str, vendor_name: str) -> dict:
    """Scrape G2 vendor page for ratings and reviews."""
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError:
        return {"error": "crawl4ai not installed"}

    print(f"\n{'='*60}")
    print(f"Scraping G2: {vendor_name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    try:
        async with AsyncWebCrawler(
            headless=True,
            verbose=False,
        ) as crawler:
            result = await crawler.arun(
                url=url,
                cache_mode="bypass",
                delay_before_return_html=3.0,  # G2 needs more time
            )

            if not result.success:
                print(f"\n✗ Crawl failed: {result.error_message}")
                return {"error": result.error_message}

            markdown = result.markdown or ""
            print(f"\n✓ Page crawled: {len(result.html)} chars HTML, {len(markdown)} chars markdown")

            if len(markdown) < 100:
                print("  ⚠ Very little content - may be blocked")
                return {"error": "Insufficient content - possibly blocked"}

            print("  Extracting G2 data with Claude...")
            g2_data = extract_g2_data_with_claude(markdown, vendor_name)

            if "error" in g2_data:
                print(f"  ✗ Extraction failed: {g2_data['error']}")
                return g2_data

            print(f"\n📦 Extracted G2 data:")
            print(json.dumps(g2_data, indent=2))

            return {"success": True, "data": g2_data}

    except Exception as e:
        print(f"\n✗ Exception: {type(e).__name__}: {e}")
        return {"error": str(e)}


async def scrape_with_basic_crawl(url: str, vendor_name: str) -> dict:
    """Fallback: Basic crawl without LLM extraction (for debugging)."""
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError:
        return {"error": "crawl4ai not installed"}

    print(f"\n{'='*60}")
    print(f"Basic crawl (no LLM): {vendor_name}")
    print(f"{'='*60}")

    try:
        async with AsyncWebCrawler(headless=True, verbose=False) as crawler:
            result = await crawler.arun(
                url=url,
                cache_mode="bypass",
                delay_before_return_html=2.0,
            )

            if result.success:
                print(f"✓ Page loaded: {len(result.html)} chars")
                print(f"  Markdown: {len(result.markdown or '')} chars")

                # Look for pricing-related content
                markdown = result.markdown or ""
                if "$" in markdown or "€" in markdown or "price" in markdown.lower():
                    print("  ✓ Found pricing-related content")
                    # Print a sample
                    lines = [l for l in markdown.split('\n') if '$' in l or 'price' in l.lower()][:10]
                    for line in lines:
                        print(f"    {line[:100]}")
                else:
                    print("  ⚠ No obvious pricing content found")

                return {"success": True, "markdown_length": len(markdown)}
            else:
                print(f"✗ Failed: {result.error_message}")
                return {"error": result.error_message}

    except Exception as e:
        print(f"✗ Exception: {e}")
        return {"error": str(e)}


# ============================================================================
# Main
# ============================================================================

async def test_pricing_pages():
    """Test vendor pricing page scraping."""
    print("\n" + "="*60)
    print("TEST 1: Vendor Pricing Pages")
    print("="*60)

    results = {}
    for vendor in TEST_VENDORS:
        result = await scrape_pricing_page(vendor["url"], vendor["name"])
        results[vendor["name"]] = result

    print("\n--- Pricing Summary ---")
    for name, result in results.items():
        status = "✓" if result.get("success") else "✗"
        if result.get("success"):
            data = result.get("data", {})
            tiers = data.get("tiers", [])
            prices = [f"${t.get('price')}" for t in tiers if t.get("price")]
            print(f"{status} {name}: {len(tiers)} tiers, prices: {', '.join(prices) or 'contact sales'}")
        else:
            print(f"{status} {name}: {result.get('error', 'Unknown error')[:50]}")

    return results


async def test_g2_pages():
    """Test G2 review page scraping."""
    print("\n" + "="*60)
    print("TEST 2: G2 Review Pages")
    print("="*60)

    results = {}
    for vendor in TEST_G2_VENDORS:
        result = await scrape_g2_page(vendor["url"], vendor["name"])
        results[vendor["name"]] = result

    print("\n--- G2 Summary ---")
    for name, result in results.items():
        status = "✓" if result.get("success") else "✗"
        if result.get("success"):
            data = result.get("data", {})
            score = data.get("g2_score", "?")
            reviews = data.get("review_count", "?")
            print(f"{status} {name}: {score}/5 ({reviews} reviews)")
        else:
            print(f"{status} {name}: {result.get('error', 'Unknown error')[:50]}")

    return results


async def main():
    """Run all scraper spike tests."""
    print("\n" + "="*60)
    print("SCRAPER SPIKE: Testing Crawl4AI + Claude extraction")
    print("="*60)

    # Test pricing pages
    pricing_results = await test_pricing_pages()

    # Test G2 pages
    g2_results = await test_g2_pages()

    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)

    pricing_success = sum(1 for r in pricing_results.values() if r.get("success"))
    g2_success = sum(1 for r in g2_results.values() if r.get("success"))

    print(f"Pricing pages: {pricing_success}/{len(pricing_results)} successful")
    print(f"G2 pages: {g2_success}/{len(g2_results)} successful")


if __name__ == "__main__":
    asyncio.run(main())
