"""Tests for enhanced scraper skill (Playwright-powered)."""
import pytest
from unittest.mock import AsyncMock, patch

from src.skills.browser.enhanced_scraper import EnhancedScraperSkill
from src.skills.base import SkillContext


class TestEnhancedScraperSkill:
    """Test the enhanced Playwright-based scraper."""

    def test_skill_metadata(self):
        """Skill has correct metadata."""
        skill = EnhancedScraperSkill()
        assert skill.name == "enhanced-scraper"

    @pytest.mark.asyncio
    async def test_scrapes_js_rendered_content(self):
        """Detects tech from JS-rendered pages that httpx would miss."""
        skill = EnhancedScraperSkill()
        context = SkillContext(
            industry="ecommerce",
            metadata={"url": "https://js-store.example.com"}
        )

        with patch.object(skill, '_scrape_with_playwright', return_value={
            "url": "https://js-store.example.com",
            "title": "JS Fashion Store",
            "description": "Premium fashion",
            "headings": ["Welcome to JS Fashion Store"],
            "visible_tech": ["shopify", "klaviyo", "intercom", "recharge"],
            "link_count": 42,
        }):
            result = await skill.run(context)

        assert result.success is True
        assert "shopify" in result.data["visible_tech"]
        assert "klaviyo" in result.data["visible_tech"]
        assert len(result.data["visible_tech"]) >= 2

    @pytest.mark.asyncio
    async def test_falls_back_to_httpx_on_playwright_failure(self):
        """Falls back to httpx scraper if Playwright fails."""
        skill = EnhancedScraperSkill()
        context = SkillContext(
            industry="ecommerce",
            metadata={"url": "https://simple-site.example.com"}
        )

        with patch.object(skill, '_scrape_with_playwright', side_effect=Exception("Playwright failed")):
            with patch('src.skills.browser.enhanced_scraper.scrape_ecommerce_site', new_callable=AsyncMock, return_value={
                "success": True,
                "title": "Simple Site",
                "description": "A simple store",
                "headings": ["Welcome"],
                "visible_tech": ["shopify"],
                "url": "https://simple-site.example.com",
            }) as mock_httpx:
                result = await skill.run(context)

        assert result.success is True
        assert result.data["scrape_method"] == "httpx_fallback"
        mock_httpx.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_scrape_method_in_result(self):
        """Result includes which method was used (playwright vs httpx)."""
        skill = EnhancedScraperSkill()
        context = SkillContext(
            industry="ecommerce",
            metadata={"url": "https://store.example.com"}
        )

        with patch.object(skill, '_scrape_with_playwright', return_value={
            "url": "https://store.example.com",
            "title": "Store",
            "description": "",
            "headings": [],
            "visible_tech": ["shopify"],
            "link_count": 10,
        }):
            result = await skill.run(context)

        assert result.success is True
        assert result.data["scrape_method"] == "playwright"
