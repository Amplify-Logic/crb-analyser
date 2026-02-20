"""Tests for quiz answer fabrication from seed profiles."""
import pytest
from src.cli.fabricator import fabricate_quiz_session


class TestFabricateQuizSession:
    """Test quiz session fabrication from seed + optional scraped data."""

    def test_minimal_seed_produces_valid_session(self):
        """A seed with just required fields produces a complete quiz_session."""
        seed = {
            "name": "Test Store",
            "website": "https://test-store.com",
            "country": "NL",
            "profile": {
                "tier": "small",
                "staff_size": "1-10",
                "monthly_orders": 300,
                "platform": "shopify",
                "product_category": "fashion",
                "has_erp": False,
                "current_tools": ["shopify", "mailchimp"],
                "pain_points": ["manual order processing"]
            }
        }
        tier_defaults = {
            "budget": 500,
            "hourly_cost": 40,
            "pain_points": ["manual order processing", "customer service volume"]
        }

        session = fabricate_quiz_session(seed, tier_defaults)

        assert session["company_name"] == "Test Store"
        assert session["company_website"] == "https://test-store.com"
        assert session["answers"]["industry"] == "ecommerce"
        assert session["answers"]["company_size"] == "1-10"
        assert session["status"] == "paid"
        assert session["tier"] == "quick"
        assert "id" in session
        assert "email" in session

    def test_seed_pain_points_override_tier_defaults(self):
        """Seed-specific pain points are used over tier defaults."""
        seed = {
            "name": "Store",
            "website": "https://store.com",
            "country": "NL",
            "profile": {
                "tier": "small",
                "staff_size": "1-10",
                "monthly_orders": 200,
                "platform": "shopify",
                "product_category": "health",
                "has_erp": False,
                "current_tools": ["shopify"],
                "pain_points": ["returns volume"]
            }
        }
        tier_defaults = {
            "budget": 500,
            "hourly_cost": 40,
            "pain_points": ["generic pain"]
        }

        session = fabricate_quiz_session(seed, tier_defaults)

        assert "returns volume" in session["answers"]["pain_points"]

    def test_scraped_data_enriches_session(self):
        """Scraped company profile data is included in the session."""
        seed = {
            "name": "Store",
            "website": "https://store.com",
            "country": "NL",
            "profile": {
                "tier": "mid",
                "staff_size": "11-50",
                "monthly_orders": 1000,
                "platform": "shopify",
                "product_category": "electronics",
                "has_erp": False,
                "current_tools": ["shopify", "klaviyo"],
                "pain_points": ["inventory sync"]
            }
        }
        tier_defaults = {"budget": 2000, "hourly_cost": 50, "pain_points": []}
        scraped = {
            "description": "Premium electronics retailer",
            "products": ["headphones", "speakers"],
            "visible_tech": ["shopify", "klarna", "klaviyo"]
        }

        session = fabricate_quiz_session(seed, tier_defaults, scraped_data=scraped)

        assert session["company_profile"] is not None
        assert "description" in session["company_profile"]

    def test_country_determines_currency(self):
        """Currency is set based on country code."""
        seed_nl = {"name": "NL Store", "website": "https://nl.com", "country": "NL",
                   "profile": {"tier": "small", "staff_size": "1-10", "monthly_orders": 100,
                               "platform": "shopify", "product_category": "fashion",
                               "has_erp": False, "current_tools": ["shopify"], "pain_points": []}}
        seed_us = {**seed_nl, "name": "US Store", "website": "https://us.com", "country": "US"}
        defaults = {"budget": 500, "hourly_cost": 40, "pain_points": []}

        session_nl = fabricate_quiz_session(seed_nl, defaults)
        session_us = fabricate_quiz_session(seed_us, defaults)

        assert session_nl["answers"].get("currency", "EUR") == "EUR"
        assert session_us["answers"].get("currency", "EUR") == "USD"

    def test_revenue_estimated_from_orders_and_category(self):
        """Monthly revenue is estimated from order count and product category AOV."""
        seed = {
            "name": "Store", "website": "https://store.com", "country": "NL",
            "profile": {"tier": "mid", "staff_size": "11-50", "monthly_orders": 2000,
                        "platform": "shopify", "product_category": "electronics",
                        "has_erp": False, "current_tools": ["shopify"], "pain_points": []}
        }
        defaults = {"budget": 2000, "hourly_cost": 50, "pain_points": []}

        session = fabricate_quiz_session(seed, defaults)

        # Electronics AOV ~150, so 2000 * 150 = 300,000/month
        revenue = session["answers"].get("monthly_revenue", 0)
        assert revenue > 0
        assert revenue > 100000  # Should be meaningful for 2000 orders of electronics
