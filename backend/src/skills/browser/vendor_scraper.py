"""
Vendor Site Scraper Skill

Scrapes vendor pricing pages using Playwright for full JS rendering,
then uses Claude (Haiku) to extract structured pricing data.

This complements the existing crawl4ai-based vendor scraper by handling
JS-heavy pricing pages that crawl4ai may miss (e.g., React/Vue SPAs,
interactive pricing calculators, toggle-based annual/monthly pricing).
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)

# Common pricing page URL patterns
PRICING_URL_PATTERNS = [
    "/pricing",
    "/pricing/",
    "/plans",
    "/plans/",
    "/plans-pricing",
    "/prices",
]


class VendorSiteScraperSkill(LLMSkill[Dict[str, Any]]):
    """
    Playwright-based vendor site scraper with LLM pricing extraction.

    Input (via context.metadata):
    - "vendor_url": Vendor homepage URL (required)
    - "vendor_name": Vendor name for context (required)
    - "category": Vendor category e.g. "crm", "customer_service" (optional)
    - "timeout_ms": Navigation timeout (default: 30000)

    Output:
    {
        "vendor_name": str,
        "pricing_url": str,
        "tiers": [{"name": str, "price_monthly": float|None, "currency": str, ...}],
        "has_free_tier": bool,
        "pricing_model": str,  # "per_seat", "flat", "usage_based", "custom"
    }
    """

    name = "vendor-site-scraper"
    description = "Scrape vendor pricing pages with Playwright and extract structured pricing via LLM"
    version = "1.0.0"
    requires_llm = True
    default_task = "extract_pricing"
    default_tier = "quick"

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """Scrape vendor site and extract pricing."""
        vendor_url = context.metadata.get("vendor_url")
        vendor_name = context.metadata.get("vendor_name")

        if not vendor_url:
            raise SkillError(self.name, "Missing 'vendor_url' in metadata", recoverable=False)
        if not vendor_name:
            raise SkillError(self.name, "Missing 'vendor_name' in metadata", recoverable=False)

        # Navigate to pricing page and get HTML
        html_content = await self._navigate_to_pricing(context)

        if not html_content:
            # Raise generic Exception so base class catches it and returns success=False
            raise Exception(f"Could not find pricing page for {vendor_name}")

        # Use LLM to extract structured pricing
        category = context.metadata.get("category", "unknown")
        pricing_data = await self._extract_pricing_with_llm(
            html_content, vendor_name, category
        )

        pricing_data["vendor_name"] = vendor_name
        return pricing_data

    async def _navigate_to_pricing(self, context: SkillContext) -> Optional[str]:
        """Navigate to vendor's pricing page and return HTML content."""
        from src.skills.browser.playwright_browser import PlaywrightBrowserSkill

        vendor_url = context.metadata["vendor_url"]
        timeout_ms = context.metadata.get("timeout_ms", 30000)
        pricing_urls = self._guess_pricing_urls(vendor_url)

        browser_skill = PlaywrightBrowserSkill()

        for url in pricing_urls:
            try:
                scrape_context = SkillContext(
                    industry=context.industry,
                    metadata={
                        "action": "scrape",
                        "url": url,
                        "timeout_ms": timeout_ms,
                    }
                )
                result = await browser_skill.run(scrape_context)

                if result.success:
                    # Check if the page looks like a pricing page
                    title = (result.data.get("title") or "").lower()
                    headings = [h.lower() for h in result.data.get("headings", [])]
                    all_text = title + " " + " ".join(headings)

                    if any(kw in all_text for kw in ["pricing", "plans", "price", "cost", "free", "starter", "pro", "enterprise"]):
                        logger.info(f"Found pricing page for {context.metadata['vendor_name']}: {url}")
                        # Return the full HTML by re-fetching content
                        # (result.data contains extracted data, not raw HTML)
                        return await self._get_page_html(url, timeout_ms)

            except Exception as e:
                logger.debug(f"Failed to load {url}: {e}")
                continue

        return None

    async def _get_page_html(self, url: str, timeout_ms: int) -> Optional[str]:
        """Get raw HTML content of a page."""
        from playwright.async_api import async_playwright

        try:
            async with await async_playwright().start() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                html = await page.content()
                await browser.close()
                return html
        except Exception as e:
            logger.warning(f"Failed to get HTML for {url}: {e}")
            return None

    def _guess_pricing_urls(self, base_url: str) -> List[str]:
        """Generate list of potential pricing URLs from a base URL."""
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        urls = []
        for pattern in PRICING_URL_PATTERNS:
            urls.append(f"{base}{pattern}")

        # Add the base URL as fallback (some vendors show pricing on homepage)
        urls.append(base_url)
        return urls

    async def _extract_pricing_with_llm(
        self,
        html_content: str,
        vendor_name: str,
        category: str,
    ) -> Dict[str, Any]:
        """Use Claude to extract structured pricing from HTML."""
        # Truncate HTML to avoid token limits
        max_chars = 15000
        if len(html_content) > max_chars:
            html_content = html_content[:max_chars]

        prompt = f"""Extract pricing information from this {vendor_name} ({category}) pricing page HTML.

Return JSON with this structure:
{{
    "tiers": [
        {{
            "name": "tier name",
            "price_monthly": number or null if custom/contact-sales,
            "price_annual_monthly": number or null (monthly price when billed annually),
            "currency": "USD",
            "custom": true/false (true if "contact sales" / "custom pricing"),
            "features": ["key feature 1", "key feature 2"]
        }}
    ],
    "has_free_tier": true/false,
    "pricing_model": "per_seat" | "flat" | "usage_based" | "tiered" | "custom",
    "pricing_url": "the URL of the pricing page if visible"
}}

Rules:
- Extract ALL visible tiers
- Use monthly prices (convert annual to monthly if needed)
- Set price_monthly to null for custom/enterprise tiers
- Include top 3-5 features per tier
- If no pricing found, return empty tiers array

HTML content:
{html_content}"""

        return await self.call_llm_json(prompt)
