"""
Vendor Refresh Service

Automatically refreshes vendor pricing using web scraping and AI extraction.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

import httpx
from anthropic import Anthropic

from src.config.settings import settings
from src.services.vendor_service import vendor_service

logger = logging.getLogger(__name__)


class VendorRefreshService:
    """
    Automatically refresh vendor pricing from their websites.
    Uses web scraping + AI extraction.
    """

    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

    async def refresh_vendor(self, vendor_slug: str) -> Dict[str, Any]:
        """
        Refresh pricing for a single vendor.

        1. Fetch pricing page
        2. Extract pricing with Claude
        3. Compare with current
        4. Update if changed
        5. Log history
        """
        vendor = await vendor_service.get_vendor(vendor_slug)
        if not vendor:
            return {"vendor": vendor_slug, "success": False, "error": "Vendor not found"}

        pricing_url = vendor.get("website")
        if not pricing_url:
            return {"vendor": vendor_slug, "success": False, "error": "No website URL"}

        # Construct pricing page URL if not explicitly set
        pricing_source = vendor.get("pricing_source")
        if not pricing_source:
            # Common pricing page patterns
            pricing_source = f"{pricing_url.rstrip('/')}/pricing"

        try:
            # Fetch pricing page
            html = await self._fetch_page(pricing_source)

            if not html:
                return {
                    "vendor": vendor_slug,
                    "success": False,
                    "error": "Could not fetch pricing page"
                }

            # Extract with AI
            extracted = await self._extract_pricing_with_ai(html, vendor["name"])

            if not extracted:
                return {
                    "vendor": vendor_slug,
                    "success": False,
                    "error": "Could not extract pricing"
                }

            # Compare and update
            old_pricing = vendor.get("pricing", {})
            changed = self._pricing_changed(old_pricing, extracted)

            if changed:
                await vendor_service.update_vendor_pricing(
                    vendor["id"],
                    extracted,
                    pricing_source,
                )

            return {
                "vendor": vendor_slug,
                "success": True,
                "changed": changed,
                "old_pricing": old_pricing if changed else None,
                "new_pricing": extracted if changed else None,
            }

        except Exception as e:
            logger.error(f"Refresh error for {vendor_slug}: {e}")
            await vendor_service.mark_refresh_error(vendor["id"], str(e))
            return {"vendor": vendor_slug, "success": False, "error": str(e)}

    async def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a web page and return HTML content."""
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    async def _extract_pricing_with_ai(
        self, html: str, vendor_name: str
    ) -> Optional[Dict[str, Any]]:
        """Use Claude to extract structured pricing from HTML."""
        # Truncate HTML to avoid token limits
        html_truncated = html[:15000]

        prompt = f"""Extract pricing information from this {vendor_name} pricing page.

Return ONLY valid JSON with this exact structure:
{{
    "model": "per_seat|flat|usage|custom",
    "currency": "USD|EUR|GBP",
    "tiers": [
        {{
            "name": "tier name",
            "price": 0,
            "per": "month|year|user/month",
            "features": ["feature1", "feature2"],
            "limits": "optional limit description"
        }}
    ],
    "free_trial_days": null or number,
    "custom_pricing": true|false
}}

Rules:
- Extract ALL pricing tiers visible
- Convert all prices to numbers (no currency symbols)
- If price is "Contact us" or similar, use null for price and set custom_pricing: true
- If there's a free tier, include it with price: 0
- per should be the billing period
- Only return JSON, no explanation

HTML content:
{html_truncated}"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",  # Fast + cheap for extraction
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text.strip()

            # Clean and parse JSON
            if "```" in content:
                import re
                match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
                if match:
                    content = match.group(1)

            return json.loads(content.strip())

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error for {vendor_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"AI extraction error for {vendor_name}: {e}")
            return None

    def _pricing_changed(
        self, old_pricing: Dict[str, Any], new_pricing: Dict[str, Any]
    ) -> bool:
        """Compare two pricing structures to detect changes."""
        if not old_pricing:
            return True

        # Compare key fields
        if old_pricing.get("model") != new_pricing.get("model"):
            return True

        if old_pricing.get("currency") != new_pricing.get("currency"):
            return True

        old_tiers = old_pricing.get("tiers", [])
        new_tiers = new_pricing.get("tiers", [])

        if len(old_tiers) != len(new_tiers):
            return True

        # Compare tier prices
        for old_tier, new_tier in zip(old_tiers, new_tiers):
            if old_tier.get("price") != new_tier.get("price"):
                return True
            if old_tier.get("name") != new_tier.get("name"):
                return True

        return False

    async def refresh_all_vendors(
        self, older_than_days: int = 7, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Background job to refresh all vendors needing updates.

        Returns list of refresh results.
        """
        vendors = await vendor_service.get_vendors_needing_refresh(
            older_than_days=older_than_days,
            limit=limit,
        )

        results = []
        for vendor in vendors:
            result = await self.refresh_vendor(vendor["slug"])
            results.append(result)

            # Small delay between requests to be polite
            import asyncio
            await asyncio.sleep(1)

        logger.info(f"Refreshed {len(results)} vendors")
        return results

    async def close(self):
        """Clean up HTTP client."""
        await self.http_client.aclose()


# Singleton instance
vendor_refresh_service = VendorRefreshService()
