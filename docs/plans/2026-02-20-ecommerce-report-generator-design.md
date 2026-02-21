# E-Commerce Report Generator — Design

> **Date**: 2026-02-20
> **Status**: Approved
> **Purpose**: CLI tool to generate full CRB reports for real e-commerce businesses, building out e-commerce expertise through volume

---

## Problem

1. No way to generate reports from the terminal — only via HTTP API
2. No e-commerce expertise file — reports start from zero knowledge
3. No repeatable way to test full report pipeline quality
4. Building expertise requires running many reports, which requires realistic input data

## Solution

A CLI tool (`python -m src.cli.generate_report`) that generates full CRB reports for real e-commerce businesses through the complete Supabase pipeline. Includes a curated seed list of ~30 real businesses and supports custom URLs.

---

## Architecture

### Three Components

```
1. E-Commerce Expertise File (baseline)
   backend/src/expertise/data/industries/ecommerce.json
   └── Hand-crafted, high-quality starting point

2. Seed List (test data)
   backend/src/cli/seeds/ecommerce.json
   └── ~30 real businesses with metadata

3. CLI Tool (orchestration)
   backend/src/cli/generate_report.py
   └── Creates quiz_session → runs full pipeline → outputs results
```

### Flow

```
CLI invocation
  → Scrape website (or use cached company_profile)
  → Infer quiz answers from scraped data + niche defaults
  → Create quiz_session row in Supabase
  → Call generate_report_streaming() (the real pipeline)
  → Stream progress to terminal
  → Report saved to Supabase + summary to stdout
  → Self-improve loop fires (expertise builds)
```

**Key insight:** The CLI's job is to fabricate realistic quiz_session input from a real website, then hand off to the existing pipeline unchanged. We don't modify the report generation code at all.

---

## CLI Interface

```bash
# Single report from seed list (random pick from tier)
python -m src.cli.generate_report --tier small

# Single report from specific URL
python -m src.cli.generate_report --url https://some-store.com --country NL --staff 1-10

# Batch mode — generate N reports across all tiers
python -m src.cli.generate_report --batch --count 10

# Batch mode — specific tier only
python -m src.cli.generate_report --batch --tier mid --count 5
```

### Terminal Output

```
═══ CRB Report Generator ═══
Target: Bloom & Wild (https://bloomandwild.com)
Tier: small | Country: UK | Staff: 11-50

[1/10] Loading.............. ✓  (2.1s)
[2/10] Research............. ✓  (8.3s)
[3/10] Analysis............. ✓  (5.1s)
[4/10] Findings............. ✓  (12.4s)
[5/10] Recommendations...... ✓  (9.7s)
[6/10] Roadmap.............. ✓  (4.2s)
[7/10] Verdict.............. ✓  (3.1s)
[8/10] Playbooks............ ✓  (6.8s)
[9/10] Architecture......... ✓  (2.9s)
[10/10] Finalization........ ✓  (1.3s)

═══ Complete ═══
Report ID:   rpt_abc123
AI Readiness: 62/100
Findings:    14 generated
Top Finding: "Customer service automation could save 120 hrs/month"
Tokens Used: 48,230 (€0.82)
Total Time:  55.9s
Expertise:   ecommerce confidence now "low" (3/5 needed for "medium")
```

### Makefile Integration

```makefile
generate-report:
	cd backend && python -m src.cli.generate_report $(ARGS)
```

---

## Seed List Structure

File: `backend/src/cli/seeds/ecommerce.json`

Each entry is a real business with enough metadata to generate realistic quiz answers:

```json
{
  "seeds": [
    {
      "name": "Example Store",
      "website": "https://example-store.com",
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

### Three Tiers (~10 each)

| Tier | Staff | Orders/mo | Typical Stack | Key Pain |
|------|-------|-----------|---------------|----------|
| Small | 1-10 | 100-500 | Shopify + basic email | Everything manual, owner does support |
| Mid | 11-50 | 500-5,000 | Shopify/WooCommerce + CRM + shipping tool | Scaling bottlenecks, tool sprawl |
| Scaling | 51-200 | 5,000-50,000 | Multi-channel + ERP + warehouse mgmt | Integration complexity, data silos |

Organized by **business profile** (size/maturity), not product niche. Product categories tagged but not used as primary dimension. This matches the strategy of treating e-commerce as one vertical until 50 reports are delivered.

---

## Quiz Answer Fabrication

```python
def fabricate_quiz_answers(seed: dict, scraped_data: dict | None) -> dict:
    """Turn seed profile + scraped site into quiz_session fields."""
```

### Mapping

| Quiz Field | Source | Fallback |
|-----------|--------|----------|
| `industry` | Always `"ecommerce"` | — |
| `company_name` | Scraped `<title>` or Open Graph | seed `name` |
| `company_website` | seed `website` | — |
| `company_size` | seed `staff_size` | `"1-10"` |
| `current_tools` | seed `current_tools` | Inferred from platform |
| `pain_points` | seed `pain_points` | Tier-based defaults |
| `biggest_challenge` | First pain point | `"scaling operations"` |
| `monthly_revenue` | Estimated from `monthly_orders` x niche AOV | Tier-based default |
| `hourly_cost` | Country-based default (NL: EUR 45, US: $55, UK: GBP 40) | EUR 40 |
| `budget` | Tier-based (small: EUR 500/mo, mid: EUR 2000/mo, scaling: EUR 5000/mo) | EUR 1000/mo |

### Website Scraping

Uses existing `pre_research_agent` patterns to populate `company_profile`:
- What the company sells
- Visible tech stack (Shopify badge, Klarna widget, etc.)
- Company description from meta tags
- Any visible team/about info

If scrape fails, falls back to seed metadata alone.

---

## E-Commerce Expertise Baseline

File: `backend/src/expertise/data/industries/ecommerce.json`

Curated baseline seeded before running any reports. Ensures quality from report #1.

### Content

- `total_analyses: 0` — honest, no real analyses yet
- `confidence: "low"` — upgrades to "medium" at 5 analyses
- **Pain points** pre-seeded from processes.json: manual_order_processing, customer_service_volume, inventory_sync_errors, abandoned_cart_loss, manual_product_content, returns_processing
- **Processes** with automation scores and common tools
- **Effective patterns**: AI chatbot for order status, Klaviyo abandoned cart flows, AI product descriptions for catalog scale
- **Anti-patterns**: Full ERP replacement under 1000 orders/month, custom chatbot when Gorgias exists, AI pricing without 6+ months data
- **Size-specific** readiness and savings estimates per tier

### Self-Improvement

After each report, `SelfImproveService.learn_from_analysis()` automatically:
- Updates pain point frequencies
- Adds new pain points discovered
- Adjusts readiness scores
- Records which recommendations scored highest
- Grows confidence from low → medium → high

---

## File Structure

```
backend/
├── src/
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── generate_report.py      # CLI entry point + orchestration
│   │   ├── fabricator.py            # Quiz answer fabrication from seed + scrape
│   │   ├── scraper.py               # Website scraping (reuses pre_research patterns)
│   │   └── seeds/
│   │       └── ecommerce.json       # ~30 real businesses, 3 tiers
│   ├── expertise/
│   │   └── data/industries/
│   │       └── ecommerce.json       # NEW — curated baseline expertise
```

### What We Do NOT Change

- `report_service.py` — untouched
- `quiz_engine.py` — untouched
- Skills, agents, knowledge base — all consumed as-is
- No new API endpoints

### Dependencies on Existing Code

- `pre_research_agent.py` patterns for website scraping
- `supabase_client.py` for creating quiz_session rows
- `report_service.py` for `generate_report_streaming()`
- `expertise/` schemas for the baseline file

---

## Estimated Scope

~400 lines of new code across 3 Python files + 2 JSON files. Zero changes to existing code.

## CRB Context

Reference docs to load during implementation:
- `.claude/reference/skills.md` — for understanding skill/agent patterns
- `.claude/reference/api-development.md` — for error handling patterns
