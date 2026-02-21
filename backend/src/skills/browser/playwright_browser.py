"""
Playwright Browser Skill

Provides browser automation capabilities for:
- JS-rendered page scraping (enhanced site analysis)
- Screenshot capture (UI testing, report validation)
- Navigation and interaction (vendor research, form filling)

Uses Playwright async API with headless Chromium by default.
Supports parallel named sessions for concurrent browser work.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.skills.base import BaseSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)

# Reuse tech fingerprints from CLI scraper for consistency
TECH_FINGERPRINTS = {
    "shopify": ["cdn.shopify.com", "Shopify.theme", "shopify-section", "myshopify.com"],
    "woocommerce": ["woocommerce", "wc-blocks", "wp-content"],
    "bigcommerce": ["bigcommerce.com", "stencil-utils"],
    "magento": ["magento", "mage-init"],
    "klaviyo": ["klaviyo.com", "klOnsite", "static.klaviyo.com"],
    "mailchimp": ["mailchimp.com", "mc-embedded"],
    "gorgias": ["gorgias.chat", "gorgias-chat"],
    "tidio": ["tidio.co", "tidioChatCode"],
    "zendesk": ["zendesk.com", "zdassets"],
    "klarna": ["klarna.com", "klarna-placement"],
    "afterpay": ["afterpay.com", "afterpay-placement"],
    "hotjar": ["hotjar.com", "hj-"],
    "google_analytics": ["google-analytics.com", "gtag", "googletagmanager"],
    "meta_pixel": ["facebook.net/tr", "fbevents.js"],
    "intercom": ["intercom.io", "intercomcdn.com"],
    "drift": ["drift.com", "driftt.com"],
    "hubspot": ["hubspot.com", "hs-scripts.com", "hs-analytics"],
    "segment": ["segment.com", "cdn.segment.com"],
    "stripe": ["stripe.com", "js.stripe.com"],
    "paypal": ["paypal.com", "paypalobjects.com"],
    "recharge": ["rechargepayments.com", "rechargecdn.com"],
    "yotpo": ["yotpo.com", "staticw2.yotpo.com"],
    "judge_me": ["judge.me"],
    "loox": ["loox.io"],
    "privy": ["privy.com"],
    "smile_io": ["smile.io"],
}


class PlaywrightBrowserSkill(BaseSkill[Dict[str, Any]]):
    """
    Browser automation skill using Playwright.

    Actions (passed via context.metadata["action"]):
    - "scrape": Navigate and extract page data with JS rendering
    - "navigate_and_screenshot": Navigate, screenshot, return page info
    - "extract_tech": Navigate and detect technologies
    - "multi_page_scrape": Scrape multiple pages from same domain

    Config (via context.metadata):
    - "url": Target URL (required)
    - "screenshot_path": Where to save screenshot (optional)
    - "session_name": Named session for parallel execution (optional)
    - "headless": Run headless (default: True)
    - "timeout_ms": Navigation timeout in ms (default: 30000)
    - "wait_for": CSS selector to wait for before extraction (optional)
    """

    name = "playwright-browser"
    description = "Browser automation with Playwright for JS-rendered scraping and screenshots"
    version = "1.0.0"
    requires_llm = False

    # Track active browser instances by session name
    _browsers: Dict[str, Any] = {}

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """Execute browser action based on context.metadata."""
        action = context.metadata.get("action", "scrape")
        url = context.metadata.get("url")

        if not url:
            raise SkillError(self.name, "Missing 'url' in metadata", recoverable=False)

        page = await self._get_page(context)

        try:
            if action == "scrape":
                return await self._action_scrape(page, context)
            elif action == "navigate_and_screenshot":
                return await self._action_navigate_screenshot(page, context)
            elif action == "extract_tech":
                return await self._action_extract_tech(page, context)
            elif action == "multi_page_scrape":
                return await self._action_multi_page(page, context)
            else:
                raise SkillError(self.name, f"Unknown action: {action}", recoverable=False)
        finally:
            # Close page but keep browser for session reuse
            if not context.metadata.get("keep_page", False):
                await page.close()

    async def _get_page(self, context: SkillContext) -> Any:
        """Get or create a browser page for this session."""
        from playwright.async_api import async_playwright

        session = context.metadata.get("session_name", "default")
        headless = context.metadata.get("headless", True)

        if session not in self._browsers:
            pw = await async_playwright().start()
            browser = await pw.chromium.launch(headless=headless)
            self._browsers[session] = {"pw": pw, "browser": browser}

        browser = self._browsers[session]["browser"]
        browser_context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        return await browser_context.new_page()

    def _session_name(self, name: str) -> str:
        """Return session name for parallel execution tracking."""
        return name

    async def _action_scrape(self, page: Any, context: SkillContext) -> Dict[str, Any]:
        """Navigate to URL and extract page data with JS rendering."""
        url = context.metadata["url"]
        timeout = context.metadata.get("timeout_ms", 30000)
        wait_for = context.metadata.get("wait_for")

        await page.goto(url, wait_until="networkidle", timeout=timeout)

        if wait_for:
            await page.wait_for_selector(wait_for, timeout=timeout)

        title = await page.title()
        html = await page.content()
        current_url = page.url

        # Extract structured data
        visible_tech = self._detect_tech(html)
        headings = await self._extract_headings(page)
        description = await self._extract_description(page)
        links = await self._extract_links(page)

        # Optional screenshot
        screenshot_path = context.metadata.get("screenshot_path")
        if screenshot_path:
            Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=screenshot_path, full_page=True)

        return {
            "url": current_url,
            "title": title,
            "description": description,
            "headings": headings,
            "visible_tech": visible_tech,
            "link_count": len(links),
            "screenshot_path": screenshot_path,
        }

    async def _action_navigate_screenshot(self, page: Any, context: SkillContext) -> Dict[str, Any]:
        """Navigate and take screenshot."""
        url = context.metadata["url"]
        screenshot_path = context.metadata.get("screenshot_path", "/tmp/crb_screenshot.png")
        timeout = context.metadata.get("timeout_ms", 30000)

        await page.goto(url, wait_until="networkidle", timeout=timeout)

        title = await page.title()

        Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=screenshot_path, full_page=True)

        return {
            "url": page.url,
            "title": title,
            "screenshot_path": screenshot_path,
        }

    async def _action_extract_tech(self, page: Any, context: SkillContext) -> Dict[str, Any]:
        """Navigate and detect all technologies."""
        url = context.metadata["url"]
        timeout = context.metadata.get("timeout_ms", 30000)

        await page.goto(url, wait_until="networkidle", timeout=timeout)

        html = await page.content()
        visible_tech = self._detect_tech(html)

        return {
            "url": page.url,
            "title": await page.title(),
            "visible_tech": visible_tech,
            "tech_count": len(visible_tech),
        }

    async def _action_multi_page(self, page: Any, context: SkillContext) -> Dict[str, Any]:
        """Scrape multiple pages from the same domain."""
        urls = context.metadata.get("urls", [context.metadata["url"]])
        timeout = context.metadata.get("timeout_ms", 30000)
        results = []

        for url in urls:
            try:
                await page.goto(url, wait_until="networkidle", timeout=timeout)
                title = await page.title()
                html = await page.content()
                results.append({
                    "url": page.url,
                    "title": title,
                    "visible_tech": self._detect_tech(html),
                    "success": True,
                })
            except Exception as e:
                results.append({
                    "url": url,
                    "error": str(e),
                    "success": False,
                })

        # Merge all detected tech
        all_tech: set[str] = set()
        for r in results:
            all_tech.update(r.get("visible_tech", []))

        return {
            "pages": results,
            "all_visible_tech": sorted(all_tech),
            "pages_scraped": sum(1 for r in results if r["success"]),
            "pages_failed": sum(1 for r in results if not r["success"]),
        }

    def _detect_tech(self, html: str) -> List[str]:
        """Detect technologies from rendered page source."""
        html_lower = html.lower()
        detected = []
        for tech, fingerprints in TECH_FINGERPRINTS.items():
            for fp in fingerprints:
                if fp.lower() in html_lower:
                    detected.append(tech)
                    break
        return detected

    async def _extract_headings(self, page: Any) -> List[str]:
        """Extract h1 and h2 headings from page."""
        headings = await page.eval_on_selector_all(
            "h1, h2",
            "els => els.slice(0, 10).map(el => el.textContent.trim()).filter(t => t.length > 0)"
        )
        return headings

    async def _extract_description(self, page: Any) -> str:
        """Extract meta description from page."""
        desc = await page.evaluate("""() => {
            const meta = document.querySelector('meta[name="description"]');
            if (meta) return meta.content;
            const og = document.querySelector('meta[property="og:description"]');
            if (og) return og.content;
            const p = document.querySelector('p');
            return p ? p.textContent.trim().substring(0, 300) : '';
        }""")
        return desc or ""

    async def _extract_links(self, page: Any) -> List[str]:
        """Extract all links from page."""
        return await page.eval_on_selector_all(
            "a[href]",
            "els => els.map(el => el.href).filter(h => h.startsWith('http'))"
        )

    async def cleanup(self) -> None:
        """Close all browser instances."""
        for session_name, session in self._browsers.items():
            try:
                await session["browser"].close()
                await session["pw"].stop()
            except Exception as e:
                logger.warning(f"Failed to close browser session {session_name}: {e}")
        self._browsers.clear()
