"""
Enhanced Scraper Skill

Scrapes e-commerce sites using Playwright for full JS rendering.
Falls back to httpx if Playwright fails (graceful degradation).

This produces richer input data for CRB reports than the httpx-only scraper:
- Detects client-side-only technologies (Intercom widgets, Recharge, etc.)
- Captures dynamically loaded content
- Takes visual screenshots for report context
"""

import logging
from typing import Any, Dict

from src.skills.base import BaseSkill, SkillContext, SkillError
from src.cli.scraper import scrape_ecommerce_site  # httpx fallback

logger = logging.getLogger(__name__)


class EnhancedScraperSkill(BaseSkill[Dict[str, Any]]):
    """
    Enhanced site scraper with Playwright + httpx fallback.

    Input (via context.metadata):
    - "url": Target URL (required)
    - "screenshot_path": Save screenshot (optional)
    - "timeout_ms": Timeout in ms (default: 30000)

    Output:
    {
        "url": str,
        "title": str,
        "description": str,
        "headings": list[str],
        "visible_tech": list[str],
        "link_count": int,
        "scrape_method": "playwright" | "httpx_fallback",
        "screenshot_path": str | None,
    }
    """

    name = "enhanced-scraper"
    description = "Scrape e-commerce sites with JS rendering and httpx fallback"
    version = "1.0.0"
    requires_llm = False

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """Scrape with Playwright, falling back to httpx."""
        url = context.metadata.get("url")
        if not url:
            raise SkillError(self.name, "Missing 'url' in metadata", recoverable=False)

        # Try Playwright first
        try:
            result = await self._scrape_with_playwright(context)
            result["scrape_method"] = "playwright"
            return result
        except Exception as e:
            logger.warning(f"Playwright scrape failed for {url}, falling back to httpx: {e}")

        # Fallback to httpx
        httpx_result = await scrape_ecommerce_site(url)
        if httpx_result.get("success"):
            return {
                "url": httpx_result.get("url", url),
                "title": httpx_result.get("title", ""),
                "description": httpx_result.get("description", ""),
                "headings": httpx_result.get("headings", []),
                "visible_tech": httpx_result.get("visible_tech", []),
                "link_count": 0,
                "scrape_method": "httpx_fallback",
                "screenshot_path": None,
            }

        raise SkillError(
            self.name,
            f"Both Playwright and httpx failed for {url}: {httpx_result.get('error', 'unknown')}",
            recoverable=True,
        )

    async def _scrape_with_playwright(self, context: SkillContext) -> Dict[str, Any]:
        """Scrape using the PlaywrightBrowserSkill."""
        from src.skills.browser.playwright_browser import PlaywrightBrowserSkill

        browser_skill = PlaywrightBrowserSkill()
        scrape_context = SkillContext(
            industry=context.industry,
            metadata={
                "action": "scrape",
                "url": context.metadata["url"],
                "screenshot_path": context.metadata.get("screenshot_path"),
                "timeout_ms": context.metadata.get("timeout_ms", 30000),
            }
        )

        result = await browser_skill.run(scrape_context)
        if not result.success:
            raise Exception(f"PlaywrightBrowserSkill failed: {result.warnings}")

        return result.data
