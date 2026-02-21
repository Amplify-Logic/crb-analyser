"""Tests for vendor site scraper skill."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.skills.browser.vendor_scraper import VendorSiteScraperSkill
from src.skills.base import SkillContext


class TestVendorSiteScraperSkill:
    """Test Playwright-based vendor site scraping."""

    def _make_skill(self):
        """Create skill with mock client to satisfy requires_llm."""
        return VendorSiteScraperSkill(client=MagicMock())

    def test_skill_metadata(self):
        skill = VendorSiteScraperSkill()
        assert skill.name == "vendor-site-scraper"
        assert skill.requires_llm is True  # Uses Claude to extract pricing

    @pytest.mark.asyncio
    async def test_extracts_pricing_from_js_page(self):
        """Extracts pricing tiers from JS-rendered pricing page."""
        skill = self._make_skill()
        context = SkillContext(
            industry="ecommerce",
            metadata={
                "vendor_url": "https://vendor.example.com",
                "vendor_name": "TestVendor",
                "category": "customer_service",
            }
        )

        mock_page_content = """
        <html><body>
            <h1>Pricing</h1>
            <div class="plan">
                <h3>Starter</h3><span class="price">$29/mo</span>
            </div>
            <div class="plan">
                <h3>Pro</h3><span class="price">$79/mo</span>
            </div>
            <div class="plan">
                <h3>Enterprise</h3><span class="price">Custom</span>
            </div>
        </body></html>
        """

        with patch.object(skill, '_navigate_to_pricing', return_value=mock_page_content):
            with patch.object(skill, 'call_llm_json', return_value={
                "tiers": [
                    {"name": "Starter", "price_monthly": 29, "currency": "USD"},
                    {"name": "Pro", "price_monthly": 79, "currency": "USD"},
                    {"name": "Enterprise", "price_monthly": None, "currency": "USD", "custom": True},
                ],
                "has_free_tier": False,
                "pricing_model": "per_seat",
            }):
                result = await skill.run(context)

        assert result.success is True
        assert len(result.data["tiers"]) == 3
        assert result.data["tiers"][0]["price_monthly"] == 29

    @pytest.mark.asyncio
    async def test_finds_pricing_page_from_homepage(self):
        """Navigates from homepage to pricing page."""
        skill = VendorSiteScraperSkill()
        # Verify the pricing URL patterns
        urls = skill._guess_pricing_urls("https://vendor.com")
        assert "https://vendor.com/pricing" in urls
        assert "https://vendor.com/plans" in urls

    @pytest.mark.asyncio
    async def test_returns_failure_when_no_pricing_found(self):
        """Returns failure when pricing page cannot be found."""
        skill = self._make_skill()
        context = SkillContext(
            industry="ecommerce",
            metadata={
                "vendor_url": "https://no-pricing.example.com",
                "vendor_name": "NoPricing",
                "category": "crm",
            }
        )

        with patch.object(skill, '_navigate_to_pricing', return_value=None):
            result = await skill.run(context)

        assert result.success is False
