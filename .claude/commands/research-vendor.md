# Research Vendor Command

Discover and scrape vendor pricing using Playwright-enhanced research.

## Usage

```
/research-vendor customer_service        # Research vendors in a category
/research-vendor crm ecommerce           # Category + industry filter
```

## Arguments

- First argument: vendor category (required)
  - Examples: `customer_service`, `crm`, `email_marketing`, `analytics`, `payments`, `shipping`, `inventory`, `erp`
- Second argument: industry filter (optional, defaults to "ecommerce")

## Workflow

### 1. Load Existing Vendors

Read the vendor database to understand what's already known:

```python
# Check existing vendors in this category
from src.services.vendor_service import VendorService
vendors = await vendor_service.get_vendors_by_category(category)
```

### 2. Discover New Vendors

Use the research agent to discover vendors:

```bash
cd backend && python -m src.agents.research.cli discover --category {category}
```

### 3. Scrape Pricing with Playwright

For each discovered vendor, use the VendorSiteScraperSkill for JS-rendered pricing extraction:

```python
from src.skills.browser.vendor_scraper import VendorSiteScraperSkill
from src.skills.base import SkillContext

skill = VendorSiteScraperSkill(client=anthropic_client)
context = SkillContext(
    industry=industry,
    metadata={
        "vendor_url": vendor_url,
        "vendor_name": vendor_name,
        "category": category,
    }
)
result = await skill.run(context)
```

### 4. Report Results

```
Vendor Research: {category}
═══════════════════════════

  Found 12 vendors, scraped pricing for 9:

  Vendor              Starting At    Tiers    Method
  ──────────────────────────────────────────────────
  Gorgias             $10/mo         3        playwright
  Zendesk             $19/mo         4        crawl4ai
  Intercom            $39/mo         3        playwright
  Freshdesk           Free           5        crawl4ai
  ...

  Failed (3):
  - HelpScout: Pricing page requires login
  - Kustomer: Enterprise-only, no public pricing
  - Gladly: Custom pricing only
```

### 5. Save Results

Save structured results to:
```
docs/research/{category}-{date}.json
```

## Notes

- Playwright fallback activates automatically when crawl4ai fails
- Rate limiting is built into the scraper (2s between requests)
- Results include confidence scores — review low-confidence extractions
