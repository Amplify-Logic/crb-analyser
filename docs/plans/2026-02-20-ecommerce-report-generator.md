# E-Commerce Report Generator — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** CLI tool that generates full CRB reports for real e-commerce businesses through the complete Supabase pipeline, with a curated seed list and e-commerce expertise baseline.

**Architecture:** A CLI module (`backend/src/cli/`) that fabricates realistic quiz_session data from a seed list of ~30 real businesses (or a custom URL), inserts it into Supabase, and runs the existing `generate_report_streaming()` pipeline unchanged. An e-commerce expertise baseline ensures quality from report #1.

**Tech Stack:** Python 3.12, argparse, asyncio, httpx, BeautifulSoup4, Supabase SDK, existing report_service.py

**Design doc:** `docs/plans/2026-02-20-ecommerce-report-generator-design.md`

**CRB Context — load these references during implementation:**
- `.claude/reference/api-development.md` — error handling patterns
- `.claude/reference/skills.md` — skill/agent patterns

---

## Task 1: Create E-Commerce Expertise Baseline

**Files:**
- Create: `backend/src/expertise/data/industries/ecommerce.json`

**Step 1: Check existing expertise file for reference**

Read `backend/src/expertise/data/industries/marketing-agencies.json` to match the exact JSON structure.

**Step 2: Read the expertise schema**

Read `backend/src/expertise/schemas.py` to confirm field names:
- `IndustryExpertise`: industry, last_updated, total_analyses, confidence, pain_points, processes, effective_patterns, anti_patterns, size_specific, avg_ai_readiness, avg_potential_savings, common_tech_stacks
- `PainPointPattern`: name, frequency (int), avg_impact, typical_causes, effective_solutions, last_seen
- `ProcessInsight`: process_name, automation_potential_observed (List[int]), common_tools_used, common_blockers, quick_win_potential
- `RecommendationPattern`: pattern, recommendation, frequency, context

**Step 3: Create the expertise file**

Create `backend/src/expertise/data/industries/ecommerce.json` matching the schema exactly. Content:

```json
{
  "industry": "ecommerce",
  "last_updated": "2026-02-20T00:00:00",
  "total_analyses": 0,
  "confidence": "low",
  "pain_points": {
    "manual_order_processing": {
      "name": "Manual order processing and fulfillment",
      "frequency": 1,
      "avg_impact": "high",
      "typical_causes": ["No automation rules in Shopify", "Manual copy-paste to shipping provider", "No order routing logic"],
      "effective_solutions": ["Shopify Flow automation", "Mesa/Alloy integration platform", "ShipStation/Sendcloud for shipping"],
      "last_seen": "2026-02-20T00:00:00"
    },
    "customer_service_volume": {
      "name": "High volume of repetitive customer service inquiries",
      "frequency": 1,
      "avg_impact": "high",
      "typical_causes": ["No self-service order tracking", "Manual response to where-is-my-order", "No chatbot for FAQs", "Returns handled via email"],
      "effective_solutions": ["Gorgias AI agent", "Tidio chatbot", "Self-service order tracking page", "Automated return portal (Returnly/Loop)"],
      "last_seen": "2026-02-20T00:00:00"
    },
    "abandoned_cart_loss": {
      "name": "Revenue lost to abandoned carts",
      "frequency": 1,
      "avg_impact": "high",
      "typical_causes": ["No recovery email flow", "Generic messaging", "No SMS follow-up", "Checkout friction"],
      "effective_solutions": ["Klaviyo abandoned cart flow", "Omnisend multi-channel recovery", "Exit-intent popups", "Checkout optimization"],
      "last_seen": "2026-02-20T00:00:00"
    },
    "inventory_sync_errors": {
      "name": "Inventory discrepancies across channels",
      "frequency": 1,
      "avg_impact": "high",
      "typical_causes": ["Manual stock updates", "Multi-channel without sync", "No safety stock rules", "Spreadsheet-based tracking"],
      "effective_solutions": ["Stocky/Shopify inventory", "Skubana/Extensiv for multi-channel", "Real-time sync via API", "Automated reorder points"],
      "last_seen": "2026-02-20T00:00:00"
    },
    "manual_product_content": {
      "name": "Time-consuming product listing and content creation",
      "frequency": 1,
      "avg_impact": "medium",
      "typical_causes": ["Manual product descriptions", "No SEO optimization", "Photo editing bottleneck", "Inconsistent brand voice"],
      "effective_solutions": ["AI product descriptions (Shopify Magic/Jasper)", "Bulk SEO optimization", "AI image editing", "Content templates"],
      "last_seen": "2026-02-20T00:00:00"
    },
    "returns_processing": {
      "name": "Manual and costly returns processing",
      "frequency": 1,
      "avg_impact": "medium",
      "typical_causes": ["Email-based return requests", "No self-service portal", "Manual refund processing", "No return analytics"],
      "effective_solutions": ["Loop Returns / Returnly portal", "Automated refund rules", "Return reason analytics", "Exchange-first policies"],
      "last_seen": "2026-02-20T00:00:00"
    }
  },
  "processes": {
    "order_management": {
      "process_name": "Order Management",
      "automation_potential_observed": [85],
      "common_tools_used": ["shopify_flow", "mesa", "alloy"],
      "common_blockers": ["Custom fulfillment logic", "Multi-warehouse routing"],
      "quick_win_potential": true
    },
    "customer_service": {
      "process_name": "Customer Service",
      "automation_potential_observed": [75],
      "common_tools_used": ["gorgias", "tidio", "zendesk"],
      "common_blockers": ["Complex product questions", "Warranty claims"],
      "quick_win_potential": true
    },
    "email_marketing": {
      "process_name": "Email Marketing & Retention",
      "automation_potential_observed": [85],
      "common_tools_used": ["klaviyo", "omnisend", "mailchimp"],
      "common_blockers": ["Data quality", "Segmentation setup time"],
      "quick_win_potential": true
    },
    "inventory_management": {
      "process_name": "Inventory Management",
      "automation_potential_observed": [80],
      "common_tools_used": ["stocky", "skubana", "cin7"],
      "common_blockers": ["Multi-channel sync", "Supplier lead times"],
      "quick_win_potential": false
    },
    "fulfillment_shipping": {
      "process_name": "Fulfillment & Shipping",
      "automation_potential_observed": [75],
      "common_tools_used": ["shipstation", "sendcloud", "shipbob"],
      "common_blockers": ["International shipping rules", "Custom packaging"],
      "quick_win_potential": true
    },
    "returns_processing": {
      "process_name": "Returns Processing",
      "automation_potential_observed": [70],
      "common_tools_used": ["loop_returns", "returnly", "aftership"],
      "common_blockers": ["Inspection requirements", "Partial refund logic"],
      "quick_win_potential": false
    }
  },
  "effective_patterns": [
    {
      "pattern": "AI chatbot handles order status, shipping, and return inquiries automatically",
      "recommendation": "Deploy Gorgias or Tidio AI agent for tier-1 support",
      "frequency": 1,
      "context": {"min_orders_per_month": 200, "company_size": "any"}
    },
    {
      "pattern": "Multi-step abandoned cart recovery with email + SMS",
      "recommendation": "Implement Klaviyo 3-email + 1-SMS abandoned cart flow",
      "frequency": 1,
      "context": {"min_orders_per_month": 100, "company_size": "any"}
    },
    {
      "pattern": "AI-generated product descriptions at catalog scale",
      "recommendation": "Use Shopify Magic or Jasper for stores with 100+ SKUs",
      "frequency": 1,
      "context": {"min_skus": 100, "company_size": "any"}
    },
    {
      "pattern": "Automated order routing based on location and stock",
      "recommendation": "Shopify Flow for single-warehouse, Mesa/Alloy for multi-warehouse",
      "frequency": 1,
      "context": {"min_orders_per_month": 500, "company_size": "11-50+"}
    },
    {
      "pattern": "Self-service returns portal reduces support tickets by 40-60%",
      "recommendation": "Deploy Loop Returns for stores with >5% return rate",
      "frequency": 1,
      "context": {"min_return_rate": 0.05, "company_size": "any"}
    }
  ],
  "anti_patterns": [
    "Full ERP replacement for stores under 1000 orders/month — ROI doesn't justify complexity",
    "Custom-built chatbot when Gorgias/Tidio exist with native Shopify integration",
    "AI pricing optimization without at least 6 months of historical sales data",
    "Multi-channel expansion before core single-channel operations are automated",
    "Building custom inventory sync when Stocky/Extensiv handle standard use cases",
    "Recommending headless commerce rebuild for stores under EUR 2M annual revenue"
  ],
  "size_specific": {
    "1-10": {
      "avg_ai_readiness": 35,
      "avg_potential_savings": 15000,
      "typical_priorities": ["customer_service", "abandoned_cart", "email_marketing"],
      "common_stack": ["shopify", "mailchimp"]
    },
    "11-50": {
      "avg_ai_readiness": 50,
      "avg_potential_savings": 45000,
      "typical_priorities": ["inventory", "order_routing", "customer_service", "returns"],
      "common_stack": ["shopify", "klaviyo", "gorgias", "shipstation"]
    },
    "51-200": {
      "avg_ai_readiness": 65,
      "avg_potential_savings": 120000,
      "typical_priorities": ["multi_channel_sync", "warehouse_automation", "data_analytics"],
      "common_stack": ["shopify_plus", "klaviyo", "gorgias", "erp", "warehouse_mgmt"]
    }
  },
  "avg_ai_readiness": 50.0,
  "avg_potential_savings": 60000.0,
  "common_tech_stacks": ["shopify", "klaviyo", "gorgias", "mailchimp", "shipstation", "sendcloud"]
}
```

**Step 4: Validate the file loads correctly**

```bash
cd backend && python -c "
from src.expertise.schemas import IndustryExpertise
import json
with open('src/expertise/data/industries/ecommerce.json') as f:
    data = json.load(f)
exp = IndustryExpertise(**data)
print(f'Loaded: {exp.industry}, {len(exp.pain_points)} pain points, {len(exp.processes)} processes')
print(f'Confidence: {exp.confidence}, Patterns: {len(exp.effective_patterns)}, Anti-patterns: {len(exp.anti_patterns)}')
"
```

Expected: `Loaded: ecommerce, 6 pain points, 6 processes` + `Confidence: low, Patterns: 5, Anti-patterns: 6`

**Step 5: Commit**

```bash
git add backend/src/expertise/data/industries/ecommerce.json
git commit -m "feat: add curated e-commerce expertise baseline"
```

---

## Task 2: Create Seed List

**Files:**
- Create: `backend/src/cli/__init__.py`
- Create: `backend/src/cli/seeds/ecommerce.json`

**Step 1: Research real e-commerce businesses**

Use web search to find ~30 real e-commerce businesses across 3 tiers (small/mid/scaling), primarily NL, UK, and US. For each, get:
- Company name and website URL
- Country
- Approximate staff size and order volume
- Platform (Shopify/WooCommerce/other)
- Product category
- Known tools (visible on site or from BuiltWith)

**Step 2: Create the CLI module**

Create `backend/src/cli/__init__.py` (empty).

**Step 3: Create the seed list**

Create `backend/src/cli/seeds/ecommerce.json` with this structure:

```json
{
  "industry": "ecommerce",
  "description": "Real e-commerce businesses for CRB report generation",
  "tiers": {
    "small": {
      "description": "1-10 staff, 100-500 orders/month, basic stack",
      "defaults": {
        "budget": 500,
        "hourly_cost": 40,
        "pain_points": ["manual order processing", "customer service volume", "no email automation"]
      }
    },
    "mid": {
      "description": "11-50 staff, 500-5000 orders/month, integrated stack",
      "defaults": {
        "budget": 2000,
        "hourly_cost": 50,
        "pain_points": ["scaling bottlenecks", "inventory sync issues", "tool sprawl", "returns volume"]
      }
    },
    "scaling": {
      "description": "51-200 staff, 5000-50000 orders/month, multi-channel + ERP",
      "defaults": {
        "budget": 5000,
        "hourly_cost": 60,
        "pain_points": ["multi-channel complexity", "data silos", "warehouse automation", "international expansion"]
      }
    }
  },
  "seeds": [
    {
      "name": "Company Name",
      "website": "https://example.com",
      "country": "NL",
      "profile": {
        "tier": "small",
        "staff_size": "1-10",
        "monthly_orders": 300,
        "platform": "shopify",
        "product_category": "fashion",
        "has_erp": false,
        "current_tools": ["shopify", "mailchimp"],
        "pain_points": ["manual order processing", "customer service volume"]
      }
    }
  ]
}
```

Include ~10 businesses per tier. Mix of NL, UK, US. Real businesses with real URLs.

**Step 4: Validate seed JSON structure**

```bash
cd backend && python -c "
import json
with open('src/cli/seeds/ecommerce.json') as f:
    data = json.load(f)
seeds = data['seeds']
tiers = {}
for s in seeds:
    t = s['profile']['tier']
    tiers[t] = tiers.get(t, 0) + 1
print(f'Total seeds: {len(seeds)}')
for t, c in sorted(tiers.items()):
    print(f'  {t}: {c}')
assert len(seeds) >= 25, f'Need at least 25 seeds, got {len(seeds)}'
for s in seeds:
    assert s.get('name'), 'Missing name'
    assert s.get('website'), 'Missing website'
    assert s.get('country'), 'Missing country'
    assert s['profile'].get('tier') in ('small', 'mid', 'scaling'), f'Invalid tier: {s[\"profile\"].get(\"tier\")}'
print('All validations passed')
"
```

**Step 5: Commit**

```bash
git add backend/src/cli/
git commit -m "feat: add e-commerce seed list with ~30 real businesses"
```

---

## Task 3: Create Quiz Answer Fabricator

**Files:**
- Create: `backend/src/cli/fabricator.py`
- Create: `backend/tests/cli/test_fabricator.py`

**Step 1: Write the failing test**

Create `backend/tests/cli/__init__.py` (empty) and `backend/tests/cli/test_fabricator.py`:

```python
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

        # Electronics AOV ~€150, so 2000 * 150 = €300,000/month
        revenue = session["answers"].get("monthly_revenue", 0)
        assert revenue > 0
        assert revenue > 100000  # Should be meaningful for 2000 orders of electronics
```

**Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/cli/test_fabricator.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.cli.fabricator'`

**Step 3: Implement the fabricator**

Create `backend/src/cli/fabricator.py`:

```python
"""
Quiz Answer Fabricator

Converts seed business profiles + optional scraped website data
into realistic quiz_session data for the report pipeline.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.skills.base import COUNTRY_CURRENCY_MAP


# Average Order Value by product category (EUR)
CATEGORY_AOV = {
    "fashion": 85,
    "electronics": 150,
    "health": 65,
    "beauty": 55,
    "home": 120,
    "food": 45,
    "sports": 95,
    "pets": 60,
    "jewelry": 200,
    "kids": 70,
    "general": 80,
}

# Hourly cost defaults by country (local currency)
COUNTRY_HOURLY_COST = {
    "NL": 45, "DE": 45, "FR": 40, "BE": 42,
    "UK": 40, "GB": 40,
    "US": 55, "CA": 50,
    "AU": 50, "NZ": 45,
}


def fabricate_quiz_session(
    seed: Dict[str, Any],
    tier_defaults: Dict[str, Any],
    scraped_data: Optional[Dict[str, Any]] = None,
    report_tier: str = "quick",
) -> Dict[str, Any]:
    """
    Build a complete quiz_session dict from seed + scraped data.

    Args:
        seed: Business seed from ecommerce.json
        tier_defaults: Default values for this business tier (small/mid/scaling)
        scraped_data: Optional scraped website data
        report_tier: "quick" or "full"

    Returns:
        Dict ready to INSERT into quiz_sessions table
    """
    profile = seed["profile"]
    country = seed.get("country", "NL")
    currency = COUNTRY_CURRENCY_MAP.get(country, "EUR")

    # Estimate monthly revenue from orders * category AOV
    category = profile.get("product_category", "general")
    aov = CATEGORY_AOV.get(category, CATEGORY_AOV["general"])
    monthly_orders = profile.get("monthly_orders", 300)
    monthly_revenue = monthly_orders * aov

    # Use seed pain points, falling back to tier defaults
    pain_points = profile.get("pain_points") or tier_defaults.get("pain_points", [])

    # Hourly cost: country-specific or tier default
    hourly_cost = COUNTRY_HOURLY_COST.get(country, tier_defaults.get("hourly_cost", 40))

    # Build answers dict (mirrors what quiz UI would produce)
    answers = {
        "industry": "ecommerce",
        "company_size": profile.get("staff_size", "1-10"),
        "current_tools": profile.get("current_tools", []),
        "pain_points": pain_points,
        "biggest_challenge": pain_points[0] if pain_points else "scaling operations",
        "monthly_revenue": monthly_revenue,
        "hourly_rate": hourly_cost,
        "budget": tier_defaults.get("budget", 1000),
        "currency": currency,
        "platform": profile.get("platform", "shopify"),
        "has_erp": profile.get("has_erp", False),
        "product_category": category,
        "monthly_orders": monthly_orders,
    }

    # Build company profile from scraped data or seed
    company_profile = None
    if scraped_data:
        company_profile = {
            "description": scraped_data.get("description", ""),
            "products": scraped_data.get("products", []),
            "visible_tech": scraped_data.get("visible_tech", []),
            "source": "cli_scraper",
            **{k: v for k, v in scraped_data.items() if k not in ("description", "products", "visible_tech")},
        }
    else:
        company_profile = {
            "description": f"{seed['name']} - {category} e-commerce store",
            "products": [],
            "visible_tech": profile.get("current_tools", []),
            "source": "seed_only",
        }

    now = datetime.now(timezone.utc).isoformat()

    return {
        "id": str(uuid.uuid4()),
        "email": f"cli-{uuid.uuid4().hex[:8]}@crb-analyser.local",
        "tier": report_tier,
        "status": "paid",
        "current_section": 0,
        "current_question": 0,
        "answers": answers,
        "results": {},
        "company_name": seed["name"],
        "company_website": seed.get("website", ""),
        "company_profile": company_profile,
        "existing_stack": _build_existing_stack(profile),
        "interview_data": {"messages": [], "confidence": {}},
        "created_at": now,
        "updated_at": now,
    }


def _build_existing_stack(profile: Dict[str, Any]) -> list:
    """Build existing_stack list from seed tools."""
    tools = profile.get("current_tools", [])
    return [
        {"name": tool, "slug": tool.lower().replace(" ", "-"), "api_score": 3}
        for tool in tools
    ]
```

**Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/cli/test_fabricator.py -v
```

Expected: All 5 tests PASS.

**Step 5: Commit**

```bash
git add backend/src/cli/fabricator.py backend/tests/cli/
git commit -m "feat: add quiz answer fabricator with tests"
```

---

## Task 4: Create Website Scraper

**Files:**
- Create: `backend/src/cli/scraper.py`
- Create: `backend/tests/cli/test_scraper.py`

**Step 1: Read the existing scraper pattern**

Read `backend/src/tools/research_scraper_tools.py` to understand the `scrape_website` function pattern. We'll create a simplified version for the CLI that doesn't need the full agent loop.

**Step 2: Write the failing test**

Create `backend/tests/cli/test_scraper.py`:

```python
"""Tests for CLI website scraper."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.cli.scraper import scrape_ecommerce_site


class TestScrapeEcommerceSite:
    """Test lightweight e-commerce site scraper."""

    @pytest.mark.asyncio
    async def test_successful_scrape_returns_structured_data(self):
        """Successful scrape returns description, products, visible_tech."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <head>
            <title>Cool Fashion Store</title>
            <meta name="description" content="Premium fashion for modern people">
        </head>
        <body>
            <h1>Cool Fashion Store</h1>
            <p>We sell the best fashion items online since 2020.</p>
        </body>
        </html>
        """

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await scrape_ecommerce_site("https://cool-fashion.com")

        assert result["success"] is True
        assert "description" in result
        assert result["title"] == "Cool Fashion Store"

    @pytest.mark.asyncio
    async def test_failed_scrape_returns_empty_with_error(self):
        """Failed scrape returns success=False with error message."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
            mock_client_cls.return_value = mock_client

            result = await scrape_ecommerce_site("https://dead-site.com")

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_detects_shopify(self):
        """Detects Shopify platform from page source."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html><head><title>Store</title>
        <meta name="description" content="A store">
        <link rel="stylesheet" href="//cdn.shopify.com/s/files/theme.css">
        </head><body></body></html>
        """

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await scrape_ecommerce_site("https://shopify-store.com")

        assert "shopify" in result.get("visible_tech", [])
```

**Step 3: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/cli/test_scraper.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 4: Implement the scraper**

Create `backend/src/cli/scraper.py`:

```python
"""
Lightweight E-Commerce Site Scraper

Scrapes a single URL to extract company profile data for report generation.
Simplified version of the full pre-research agent scraper.
"""

import logging
from typing import Any, Dict, List

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Known tech fingerprints in page source
TECH_FINGERPRINTS = {
    "shopify": ["cdn.shopify.com", "Shopify.theme", "shopify-section"],
    "woocommerce": ["woocommerce", "wc-blocks", "wp-content"],
    "bigcommerce": ["bigcommerce.com", "stencil-utils"],
    "magento": ["magento", "mage-init"],
    "klaviyo": ["klaviyo.com", "klOnsite"],
    "mailchimp": ["mailchimp.com", "mc-embedded"],
    "gorgias": ["gorgias.chat", "gorgias-chat"],
    "tidio": ["tidio.co", "tidioChatCode"],
    "zendesk": ["zendesk.com", "zdassets"],
    "klarna": ["klarna.com", "klarna-placement"],
    "afterpay": ["afterpay.com", "afterpay-placement"],
    "hotjar": ["hotjar.com", "hj-"],
    "google_analytics": ["google-analytics.com", "gtag", "googletagmanager"],
    "meta_pixel": ["facebook.net/tr", "fbevents.js"],
}


async def scrape_ecommerce_site(url: str, timeout: int = 15) -> Dict[str, Any]:
    """
    Scrape an e-commerce site for company profile data.

    Args:
        url: The website URL to scrape
        timeout: Request timeout in seconds

    Returns:
        Dict with: success, title, description, visible_tech, headings, error
    """
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; CRB-Analyser/1.0)"}
        ) as client:
            response = await client.get(url)

        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Extract metadata
        title = _get_title(soup)
        description = _get_description(soup)
        headings = _get_headings(soup)
        visible_tech = _detect_tech(html)

        return {
            "success": True,
            "title": title,
            "description": description,
            "headings": headings,
            "visible_tech": visible_tech,
            "url": url,
        }

    except Exception as e:
        logger.warning(f"Failed to scrape {url}: {e}")
        return {"success": False, "error": str(e)}


def _get_title(soup: BeautifulSoup) -> str:
    """Extract page title."""
    tag = soup.find("title")
    return tag.get_text(strip=True) if tag else ""


def _get_description(soup: BeautifulSoup) -> str:
    """Extract meta description or OG description."""
    # Try meta description
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"].strip()

    # Try Open Graph
    og = soup.find("meta", attrs={"property": "og:description"})
    if og and og.get("content"):
        return og["content"].strip()

    # Fallback: first substantial paragraph
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if len(text) > 50:
            return text[:300]

    return ""


def _get_headings(soup: BeautifulSoup) -> List[str]:
    """Extract h1 and h2 headings."""
    headings = []
    for tag in soup.find_all(["h1", "h2"], limit=10):
        text = tag.get_text(strip=True)
        if text:
            headings.append(text)
    return headings


def _detect_tech(html: str) -> List[str]:
    """Detect technologies from page source."""
    html_lower = html.lower()
    detected = []
    for tech, fingerprints in TECH_FINGERPRINTS.items():
        for fp in fingerprints:
            if fp.lower() in html_lower:
                detected.append(tech)
                break
    return detected
```

**Step 5: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/cli/test_scraper.py -v
```

Expected: All 3 tests PASS.

**Step 6: Commit**

```bash
git add backend/src/cli/scraper.py backend/tests/cli/test_scraper.py
git commit -m "feat: add lightweight e-commerce site scraper with tests"
```

---

## Task 5: Create CLI Entry Point

**Files:**
- Create: `backend/src/cli/generate_report.py`
- Create: `backend/src/cli/__main__.py`

This is the main orchestration file. It ties together seeds, fabricator, scraper, and the report pipeline.

**Step 1: Create the CLI entry point**

Create `backend/src/cli/generate_report.py`:

```python
"""
CRB Report Generator CLI

Generate full CRB reports for real e-commerce businesses.

Usage:
    # Single report from seed (random pick from tier)
    python -m src.cli.generate_report --tier small

    # Single report from URL
    python -m src.cli.generate_report --url https://store.com --country NL --staff 1-10

    # Batch mode
    python -m src.cli.generate_report --batch --count 10
    python -m src.cli.generate_report --batch --tier mid --count 5
"""

import argparse
import asyncio
import json
import logging
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
load_dotenv()  # Must be before src.* imports

from src.cli.fabricator import fabricate_quiz_session
from src.cli.scraper import scrape_ecommerce_site
from src.config.supabase_client import get_async_supabase
from src.services.report_service import generate_report_streaming

logger = logging.getLogger(__name__)

SEEDS_DIR = Path(__file__).parent / "seeds"


def load_seeds() -> Dict[str, Any]:
    """Load e-commerce seed list."""
    seeds_file = SEEDS_DIR / "ecommerce.json"
    with open(seeds_file) as f:
        return json.load(f)


def pick_seed(seeds_data: Dict[str, Any], tier: Optional[str] = None) -> Dict[str, Any]:
    """Pick a random seed, optionally filtered by tier."""
    all_seeds = seeds_data["seeds"]
    if tier:
        filtered = [s for s in all_seeds if s["profile"]["tier"] == tier]
        if not filtered:
            print(f"No seeds found for tier '{tier}'. Available tiers: small, mid, scaling")
            sys.exit(1)
        return random.choice(filtered)
    return random.choice(all_seeds)


def print_header(name: str, url: str, tier: str, country: str, staff: str) -> None:
    """Print report generation header."""
    print(f"\n{'=' * 50}")
    print(f"  CRB Report Generator")
    print(f"{'=' * 50}")
    print(f"  Target:  {name}")
    print(f"  URL:     {url}")
    print(f"  Profile: {tier} | {country} | {staff} staff")
    print(f"{'=' * 50}\n")


def print_progress(data: Dict[str, Any]) -> None:
    """Print a progress update line."""
    progress = data.get("progress", 0)
    step = data.get("step", "")
    phase = data.get("phase", "")

    bar_width = 20
    filled = int(bar_width * progress / 100)
    bar = "█" * filled + "░" * (bar_width - filled)

    print(f"  [{bar}] {progress:3d}%  {step}", end="\r", flush=True)

    # Print newline when phase changes
    if data.get("phase_complete"):
        print()


async def generate_single_report(
    seed: Dict[str, Any],
    seeds_data: Dict[str, Any],
    report_tier: str = "quick",
    scrape: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Generate a single report from a seed.

    Returns dict with report_id, findings_count, ai_readiness, etc.
    """
    profile = seed["profile"]
    tier = profile["tier"]
    tier_defaults = seeds_data["tiers"][tier]["defaults"]

    print_header(
        name=seed["name"],
        url=seed.get("website", "N/A"),
        tier=tier,
        country=seed.get("country", "?"),
        staff=profile.get("staff_size", "?"),
    )

    # Step 1: Scrape website (optional)
    scraped_data = None
    if scrape and seed.get("website"):
        print("  Scraping website...", end="", flush=True)
        scraped_data = await scrape_ecommerce_site(seed["website"])
        if scraped_data.get("success"):
            tech = scraped_data.get("visible_tech", [])
            print(f" done ({len(tech)} technologies detected)")
        else:
            print(f" failed ({scraped_data.get('error', 'unknown')}), using seed data only")
            scraped_data = None

    # Step 2: Fabricate quiz session
    session_data = fabricate_quiz_session(seed, tier_defaults, scraped_data, report_tier)
    session_id = session_data["id"]

    # Step 3: Insert into Supabase
    print("  Creating quiz session...", end="", flush=True)
    supabase = await get_async_supabase()
    await supabase.table("quiz_sessions").insert(session_data).execute()
    print(f" done (id: {session_id[:8]}...)")

    # Step 4: Generate report
    print("\n  Generating report:\n")
    start_time = time.time()
    report_id = None
    last_phase = None
    error = None

    async for event in generate_report_streaming(session_id, report_tier):
        if not event.startswith("data: "):
            continue

        try:
            data = json.loads(event[6:].strip())
        except json.JSONDecodeError:
            continue

        # Track phase transitions
        phase = data.get("phase", "")
        if phase != last_phase and last_phase is not None:
            print()  # Newline on phase change
        last_phase = phase

        # Handle completion
        if data.get("report_id"):
            report_id = data["report_id"]

        # Handle errors
        if data.get("phase") == "error" or data.get("error"):
            error = data.get("error", "Unknown error")
            break

        print_progress(data)

    elapsed = time.time() - start_time
    print("\n")

    if error:
        print(f"  ERROR: {error}")
        return None

    # Step 5: Print summary
    print(f"{'=' * 50}")
    print(f"  Complete")
    print(f"{'=' * 50}")
    print(f"  Report ID:    {report_id}")
    print(f"  Session ID:   {session_id}")
    print(f"  Total Time:   {elapsed:.1f}s")
    print(f"{'=' * 50}\n")

    return {
        "report_id": report_id,
        "session_id": session_id,
        "company": seed["name"],
        "tier": tier,
        "elapsed": elapsed,
    }


async def generate_from_url(
    url: str,
    country: str = "NL",
    staff_size: str = "11-50",
    report_tier: str = "quick",
) -> Optional[Dict[str, Any]]:
    """Generate a report from a custom URL."""
    # Create a synthetic seed from URL
    seed = {
        "name": url.replace("https://", "").replace("http://", "").split("/")[0],
        "website": url,
        "country": country,
        "profile": {
            "tier": "mid",
            "staff_size": staff_size,
            "monthly_orders": 500,
            "platform": "unknown",
            "product_category": "general",
            "has_erp": False,
            "current_tools": [],
            "pain_points": [],
        }
    }

    # Use mid-tier defaults for URL-based generation
    seeds_data = {"tiers": {
        "mid": {"defaults": {"budget": 2000, "hourly_cost": 50,
                             "pain_points": ["scaling operations", "customer service volume",
                                             "manual processes"]}}
    }}

    return await generate_single_report(seed, seeds_data, report_tier, scrape=True)


async def cmd_single(args: argparse.Namespace) -> None:
    """Generate a single report."""
    if args.url:
        result = await generate_from_url(
            url=args.url,
            country=args.country,
            staff_size=args.staff,
            report_tier=args.report_tier,
        )
    else:
        seeds_data = load_seeds()
        seed = pick_seed(seeds_data, args.tier)
        result = await generate_single_report(seed, seeds_data, args.report_tier)

    if not result:
        sys.exit(1)


async def cmd_batch(args: argparse.Namespace) -> None:
    """Generate multiple reports."""
    seeds_data = load_seeds()
    count = args.count
    results = []

    print(f"\n  Batch mode: generating {count} reports\n")

    for i in range(count):
        print(f"\n{'─' * 50}")
        print(f"  Report {i + 1} of {count}")
        print(f"{'─' * 50}")

        seed = pick_seed(seeds_data, args.tier)
        result = await generate_single_report(seed, seeds_data, args.report_tier)

        if result:
            results.append(result)
        else:
            print(f"  Skipping failed report, continuing batch...")

    # Print batch summary
    print(f"\n{'=' * 60}")
    print(f"  Batch Complete: {len(results)}/{count} reports generated")
    print(f"{'=' * 60}")
    for r in results:
        print(f"  {r['company']:30s}  {r['tier']:8s}  {r['elapsed']:6.1f}s  {r['report_id'][:8]}...")
    total_time = sum(r["elapsed"] for r in results)
    print(f"\n  Total time: {total_time:.1f}s ({total_time / 60:.1f} min)")
    print(f"{'=' * 60}\n")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CRB Report Generator — generate full reports for real e-commerce businesses"
    )

    # Mode selection
    parser.add_argument("--batch", action="store_true", help="Generate multiple reports")
    parser.add_argument("--count", type=int, default=5, help="Number of reports in batch mode (default: 5)")

    # Seed selection
    parser.add_argument("--tier", choices=["small", "mid", "scaling"], help="Business tier filter")

    # Custom URL mode
    parser.add_argument("--url", help="Custom website URL (overrides seed list)")
    parser.add_argument("--country", default="NL", help="Country code for URL mode (default: NL)")
    parser.add_argument("--staff", default="11-50", help="Staff size for URL mode (default: 11-50)")

    # Report options
    parser.add_argument("--report-tier", choices=["quick", "full"], default="quick",
                        help="Report tier (default: quick)")
    parser.add_argument("--no-scrape", action="store_true", help="Skip website scraping")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")

    # Route to command
    if args.batch:
        asyncio.run(cmd_batch(args))
    else:
        asyncio.run(cmd_single(args))


if __name__ == "__main__":
    main()
```

**Step 2: Create `__main__.py` for module invocation**

Create `backend/src/cli/__main__.py`:

```python
"""Allow running as: python -m src.cli.generate_report"""
from src.cli.generate_report import main

if __name__ == "__main__":
    main()
```

**Step 3: Verify the CLI shows help**

```bash
cd backend && python -m src.cli.generate_report --help
```

Expected: Argparse help output with all options listed.

**Step 4: Commit**

```bash
git add backend/src/cli/generate_report.py backend/src/cli/__main__.py
git commit -m "feat: add CLI report generator with single and batch modes"
```

---

## Task 6: Add Makefile Target

**Files:**
- Modify: `Makefile`

**Step 1: Add generate-report target**

Add to the root `Makefile`:

```makefile
generate-report:
	cd backend && python -m src.cli.generate_report $(ARGS)
```

**Step 2: Verify**

```bash
make generate-report ARGS="--help"
```

Expected: Same argparse help output.

**Step 3: Commit**

```bash
git add Makefile
git commit -m "feat: add generate-report target to Makefile"
```

---

## Task 7: End-to-End Smoke Test

**This is NOT an automated test** — it's a manual verification that the full pipeline works.

**Step 1: Ensure services are running**

```bash
brew services start redis
```

Verify `.env` has SUPABASE_URL, SUPABASE_SERVICE_KEY, ANTHROPIC_API_KEY.

**Step 2: Run a single report from seed**

```bash
cd backend && python -m src.cli.generate_report --tier small --report-tier quick
```

**Expected output:**
- Website scrape completes (or gracefully fails)
- Quiz session created in Supabase
- Report generation progresses through all 10 phases
- Report ID printed at completion
- No errors

**Step 3: Verify report in Supabase**

Check the `reports` table for the new report. Verify it has:
- Status: "completed"
- Findings: 10+ findings
- Recommendations with CRB options
- Executive summary with AI readiness score

**Step 4: Run a batch of 3**

```bash
cd backend && python -m src.cli.generate_report --batch --count 3
```

Verify all 3 complete and batch summary table prints.

**Step 5: Run from custom URL**

```bash
cd backend && python -m src.cli.generate_report --url https://www.coolblue.nl --country NL --staff 51-200
```

Verify scraping works and report generates.

**Step 6: Commit any fixes from smoke test**

Fix any issues discovered during smoke testing, then:

```bash
git add -A
git commit -m "fix: smoke test fixes for CLI report generator"
```

---

## Summary

| Task | Description | New Files | Tests |
|------|-------------|-----------|-------|
| 1 | E-commerce expertise baseline | 1 JSON | Schema validation |
| 2 | Seed list (~30 businesses) | 2 files (init + JSON) | Structure validation |
| 3 | Quiz answer fabricator | 1 py + 1 test | 5 unit tests |
| 4 | Website scraper | 1 py + 1 test | 3 unit tests |
| 5 | CLI entry point | 2 py | --help verification |
| 6 | Makefile target | Modify 1 | --help verification |
| 7 | End-to-end smoke test | — | Manual verification |

**Total:** ~400 lines new code, 8 unit tests, 3 new Python files, 2 JSON files, zero changes to existing code.
