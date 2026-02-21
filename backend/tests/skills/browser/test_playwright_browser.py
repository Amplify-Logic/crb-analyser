"""Tests for Playwright browser skill."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.skills.browser.playwright_browser import PlaywrightBrowserSkill
from src.skills.base import SkillContext


class TestPlaywrightBrowserSkill:
    """Test the Playwright browser skill."""

    def test_skill_metadata(self):
        """Skill has correct metadata."""
        skill = PlaywrightBrowserSkill()
        assert skill.name == "playwright-browser"
        assert skill.requires_llm is False

    @pytest.mark.asyncio
    async def test_navigate_and_screenshot(self):
        """Navigate to URL and take screenshot."""
        skill = PlaywrightBrowserSkill()
        context = SkillContext(
            industry="ecommerce",
            metadata={
                "action": "navigate_and_screenshot",
                "url": "https://example.com",
                "screenshot_path": "/tmp/test_screenshot.png",
            }
        )

        # Mock playwright
        mock_page = AsyncMock()
        mock_page.title = AsyncMock(return_value="Example Domain")
        mock_page.url = "https://example.com"
        mock_page.content = AsyncMock(return_value="<html><body>Hello</body></html>")

        with patch.object(skill, '_get_page', return_value=mock_page):
            result = await skill.run(context)

        assert result.success is True
        assert result.data["title"] == "Example Domain"
        mock_page.goto.assert_called_once_with("https://example.com", wait_until="networkidle", timeout=30000)
        mock_page.screenshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_scrape_with_js_rendering(self):
        """Scrape page with full JS rendering."""
        skill = PlaywrightBrowserSkill()
        context = SkillContext(
            industry="ecommerce",
            metadata={
                "action": "scrape",
                "url": "https://example.com",
            }
        )

        mock_page = AsyncMock()
        mock_page.title = AsyncMock(return_value="JS Store")
        mock_page.url = "https://example.com"
        mock_page.content = AsyncMock(return_value="""
            <html><head><title>JS Store</title></head>
            <body>
                <h1>Welcome</h1>
                <script src="https://cdn.shopify.com/theme.js"></script>
                <script src="https://static.klaviyo.com/onsite/js/klaviyo.js"></script>
            </body></html>
        """)
        mock_page.eval_on_selector_all = AsyncMock(return_value=["Welcome"])
        mock_page.evaluate = AsyncMock(return_value="")
        mock_page.close = AsyncMock()

        with patch.object(skill, '_get_page', return_value=mock_page):
            result = await skill.run(context)

        assert result.success is True
        assert "shopify" in result.data.get("visible_tech", [])
        assert "klaviyo" in result.data.get("visible_tech", [])

    @pytest.mark.asyncio
    async def test_handles_timeout_gracefully(self):
        """Timeout returns failure, not exception."""
        skill = PlaywrightBrowserSkill()
        context = SkillContext(
            industry="ecommerce",
            metadata={
                "action": "navigate_and_screenshot",
                "url": "https://slow-site.example.com",
                "screenshot_path": "/tmp/test.png",
            }
        )

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(side_effect=TimeoutError("Navigation timeout"))

        with patch.object(skill, '_get_page', return_value=mock_page):
            result = await skill.run(context)

        assert result.success is False

    @pytest.mark.asyncio
    async def test_parallel_sessions(self):
        """Multiple sessions can run with different names."""
        skill = PlaywrightBrowserSkill()
        # Verify session naming works
        assert skill._session_name("user-flow-1") == "user-flow-1"
        assert skill._session_name("vendor-research") == "vendor-research"
