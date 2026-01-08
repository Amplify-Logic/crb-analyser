# Vendor Research Agent Specification

## Goal

Build an automated research agent that continuously discovers, validates, and updates vendor/tool information in our Supabase knowledge base. The agent should provide verified, up-to-date data for our industry-specific recommendations.

---

## Context

### Current State
- **80 vendors** in `vendors` table
- **94 benchmarks** in `knowledge_embeddings`
- **8 supported industries**: dental, home-services, professional-services, recruiting, coaching, veterinary, physical-therapy, medspa
- **14 vendor categories**: CRM, customer_support, ai_sales_tools, automation, analytics, etc.

### Problem
- Vendor pricing changes frequently (monthly)
- New AI tools launch constantly
- Industry benchmarks become stale
- Manual updates are time-consuming and error-prone

### Solution
An autonomous agent that:
1. Discovers new relevant vendors
2. Validates and refreshes existing vendor data
3. Updates industry benchmarks from authoritative sources
4. Maintains audit trail of all changes

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Research Agent                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Discovery   │  │  Validation  │  │   Update     │      │
│  │    Phase     │──▶│    Phase     │──▶│   Phase      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                  │              │
│         ▼                 ▼                  ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Crawl4AI    │  │  LLM Extract │  │  Supabase    │      │
│  │  Web Search  │  │  Verify Src  │  │  Audit Log   │      │
│  │  G2/Capterra │  │  Cross-check │  │  Embeddings  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Sources

### Primary Sources (Crawl4AI)
| Source | Data Type | Refresh Frequency |
|--------|-----------|-------------------|
| Vendor websites | Pricing, features, integrations | Weekly |
| G2.com | Reviews, ratings, comparisons | Monthly |
| Capterra | Reviews, pricing, alternatives | Monthly |
| Product Hunt | New tool launches | Daily |
| Industry blogs | Benchmarks, trends | Monthly |

### Secondary Sources (API/Search)
| Source | Data Type | Method |
|--------|-----------|--------|
| Brave Search API | General research | API |
| Tavily API | Structured search | API |
| LinkedIn | Company info | Scrape |
| Crunchbase | Funding, company data | API |

### Authoritative Benchmark Sources
| Industry | Sources |
|----------|---------|
| Dental | ADA, Dental Economics, DentistryIQ |
| Home Services | ServiceTitan reports, Home Service Expert |
| Recruiting | SHRM, Bullhorn reports, ERE Media |
| Coaching | ICF Global Study, coaching industry reports |
| Veterinary | AVMA, Veterinary Practice News |
| Professional Services | Industry associations, McKinsey |

---

## Database Schema (Target)

### `vendors` table
```sql
-- Key fields to populate/update
slug TEXT UNIQUE NOT NULL,
name TEXT NOT NULL,
category TEXT NOT NULL,
website TEXT,
pricing_url TEXT,
description TEXT,
tagline TEXT,

-- Pricing (JSONB)
pricing JSONB,  -- {model, currency, tiers[], starting_price, free_tier, free_trial_days}

-- Fit criteria
company_sizes TEXT[],  -- ['startup', 'smb', 'mid_market', 'enterprise']
industries TEXT[],
best_for TEXT[],
avoid_if TEXT[],

-- Ratings
our_rating DECIMAL(2,1),
g2_score DECIMAL(2,1),
g2_reviews INTEGER,
capterra_score DECIMAL(2,1),
capterra_reviews INTEGER,

-- Implementation
implementation_weeks INTEGER,
implementation_complexity TEXT,  -- 'low', 'medium', 'high'
requires_developer BOOLEAN,

-- Integrations
integrations TEXT[],
api_available BOOLEAN,
key_capabilities TEXT[],

-- Verification
verified_at TIMESTAMPTZ,
verified_by TEXT,  -- 'research-agent-v1'
source_url TEXT,
status TEXT  -- 'active', 'deprecated', 'needs_review'
```

### `industry_vendor_tiers` table
```sql
industry TEXT NOT NULL,
vendor_id UUID REFERENCES vendors(id),
tier INTEGER,  -- 1 = top pick, 2 = recommended, 3 = alternative
boost_score INTEGER,
notes TEXT
```

### `knowledge_embeddings` table
```sql
content_type TEXT,  -- 'benchmark', 'opportunity', 'vendor', etc.
content_id TEXT,
industry TEXT,
title TEXT,
content TEXT,
metadata JSONB,  -- Must include source.name, source.verified_date
embedding VECTOR(1536)
```

### `vendor_audit_log` table
```sql
vendor_id UUID,
vendor_slug TEXT,
action TEXT,  -- 'create', 'update', 'delete', 'deprecate'
changed_by TEXT,  -- 'research-agent-v1'
changes JSONB  -- {field: {old: value, new: value}}
```

---

## Agent Tasks

### Task 1: Vendor Discovery
```
INPUT: Industry or category to research
OUTPUT: List of potential new vendors

STEPS:
1. Search G2/Capterra for category + industry
2. Search "best [category] for [industry] 2025/2026"
3. Check Product Hunt for recent launches
4. Cross-reference with existing vendors table
5. Return new candidates with initial data
```

### Task 2: Vendor Data Refresh
```
INPUT: Vendor slug or list of stale vendors
OUTPUT: Updated vendor data

STEPS:
1. Crawl vendor website for current pricing page
2. Extract pricing tiers using LLM
3. Fetch G2/Capterra scores
4. Validate against multiple sources
5. Update database with changes
6. Log changes to audit table
```

### Task 3: Industry Benchmark Update
```
INPUT: Industry slug
OUTPUT: Updated benchmarks in knowledge_embeddings

STEPS:
1. Search for "[industry] benchmarks 2025"
2. Crawl authoritative sources (ADA, SHRM, etc.)
3. Extract key metrics with LLM
4. Validate source credibility
5. Store with source attribution in metadata
6. Generate embeddings
```

### Task 4: Industry Tier Assignment
```
INPUT: Industry + category
OUTPUT: Tier assignments (T1/T2/T3)

STEPS:
1. Get all vendors in category
2. Filter by industry fit
3. Score by: ratings, pricing fit, industry features
4. Assign tiers based on scoring
5. Update industry_vendor_tiers table
```

---

## Implementation

### Tech Stack
```python
# Core
crawl4ai          # Web scraping with LLM extraction
anthropic         # Claude for extraction/validation
supabase          # Database client

# Search
brave-search      # Web search API
tavily-python     # Structured search

# Utilities
pydantic          # Data validation
structlog         # Logging
tenacity          # Retry logic
```

### File Structure
```
backend/src/agents/research/
├── __init__.py
├── agent.py              # Main orchestrator
├── discovery.py          # New vendor discovery
├── scraper.py            # Crawl4AI integration
├── validator.py          # Data validation
├── updater.py            # Database updates
├── sources/
│   ├── g2.py             # G2 scraping
│   ├── capterra.py       # Capterra scraping
│   ├── vendor_site.py    # Direct vendor scraping
│   └── benchmarks.py     # Industry benchmark sources
└── prompts/
    ├── extract_pricing.py
    ├── extract_features.py
    └── validate_data.py
```

### Crawl4AI Usage
```python
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

async def scrape_vendor_pricing(url: str) -> dict:
    """Scrape and extract pricing from vendor website."""

    extraction_strategy = LLMExtractionStrategy(
        provider="anthropic/claude-haiku-4-5-20251001",
        schema=PricingSchema.model_json_schema(),
        instruction="""
        Extract pricing information from this page:
        - Pricing model (subscription, usage, one-time)
        - Available tiers with names and prices
        - What's included in each tier
        - Free tier or trial availability
        - Enterprise/custom pricing indicator
        """
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            extraction_strategy=extraction_strategy,
            bypass_cache=True
        )

    return result.extracted_content
```

### Validation Requirements
```python
class VendorValidation:
    """Validation rules for vendor data."""

    # Pricing must be verified from vendor website
    PRICING_SOURCE_REQUIRED = True

    # Ratings must come from G2 or Capterra
    RATING_SOURCES = ["g2.com", "capterra.com"]

    # Data older than 90 days needs refresh
    STALE_THRESHOLD_DAYS = 90

    # Required fields for a valid vendor
    REQUIRED_FIELDS = [
        "name", "slug", "category", "website",
        "description", "pricing"
    ]

    # Benchmark sources must be authoritative
    BENCHMARK_SOURCES = {
        "dental": ["ada.org", "dentaleconomics.com"],
        "recruiting": ["shrm.org", "ere.net"],
        # ... etc
    }
```

---

## CLI Interface

```bash
# Discover new vendors for a category
python -m src.agents.research discover --category crm --industry dental

# Refresh specific vendor
python -m src.agents.research refresh --vendor hubspot

# Refresh all stale vendors (>90 days)
python -m src.agents.research refresh --stale

# Update industry benchmarks
python -m src.agents.research benchmarks --industry dental

# Assign industry tiers
python -m src.agents.research tiers --industry dental --category crm

# Full industry refresh
python -m src.agents.research full-refresh --industry dental

# Dry run (no database updates)
python -m src.agents.research refresh --stale --dry-run
```

---

## API Endpoints

```python
# Trigger research tasks via API
POST /api/admin/research/discover
{
    "category": "crm",
    "industry": "dental"
}

POST /api/admin/research/refresh
{
    "vendor_slugs": ["hubspot", "salesforce"],  # or
    "stale_only": true
}

POST /api/admin/research/benchmarks
{
    "industry": "dental"
}

GET /api/admin/research/status/{task_id}
```

---

## Scheduling

```python
# Suggested schedule (can use cron or Celery)

# Daily: Check for new tools on Product Hunt
"0 6 * * *"  research discover --source producthunt

# Weekly: Refresh pricing for top-tier vendors
"0 3 * * 1"  research refresh --tier 1

# Monthly: Full stale vendor refresh
"0 2 1 * *"  research refresh --stale

# Monthly: Update all industry benchmarks
"0 4 1 * *"  research benchmarks --all

# Quarterly: Re-evaluate tier assignments
"0 5 1 */3 *"  research tiers --all
```

---

## Audit & Monitoring

### Logging
```python
# All changes logged with context
logger.info(
    "vendor_updated",
    vendor_slug=slug,
    fields_changed=["pricing", "g2_score"],
    source="g2.com",
    verified_at=datetime.utcnow()
)
```

### Audit Trail
Every database change creates an entry in `vendor_audit_log`:
```json
{
    "vendor_slug": "hubspot",
    "action": "update",
    "changed_by": "research-agent-v1",
    "changes": {
        "pricing.starting_price": {"old": 45, "new": 50},
        "g2_score": {"old": 4.4, "new": 4.5}
    },
    "created_at": "2026-01-03T15:00:00Z"
}
```

### Alerts
- Vendor website unreachable for 7+ days
- Pricing increased >50%
- G2 score dropped >0.5
- New vendor in top 10 we don't have

---

## Success Criteria

1. **Coverage**: 95%+ of top vendors per category have current data
2. **Freshness**: No vendor data older than 90 days
3. **Accuracy**: Pricing matches vendor website within 48 hours
4. **Sources**: All benchmarks have authoritative source attribution
5. **Audit**: 100% of changes logged with source

---

## Phase 1 Implementation (MVP)

Focus on:
1. **Crawl4AI integration** for vendor pricing pages
2. **G2 scraper** for ratings
3. **Basic CLI** for manual triggers
4. **Supabase updater** with audit logging
5. **One industry**: Dental (as pilot)

Defer to Phase 2:
- Automated scheduling
- API endpoints
- All industries
- Product Hunt monitoring
- Tier auto-assignment

---

## Example Prompt for Agent

When you build this agent, use this context:

```
You are building a vendor research agent for the CRB Analyser platform.

GOAL: Keep our vendor database fresh and accurate with verified data.

DATABASE: Supabase (use src.config.supabase_client.get_async_supabase)

TABLES TO UPDATE:
- vendors (80 rows, pricing/ratings/features)
- industry_vendor_tiers (tier assignments per industry)
- knowledge_embeddings (benchmarks with source attribution)
- vendor_audit_log (all changes must be logged)

TOOLS AVAILABLE:
- Crawl4AI for web scraping with LLM extraction
- Brave Search API (settings.BRAVE_API_KEY)
- Anthropic Claude for data extraction/validation

VALIDATION RULES:
- Pricing must come from vendor's official website
- Ratings must come from G2 or Capterra
- Benchmarks must cite authoritative sources with dates
- All changes logged to vendor_audit_log

INDUSTRIES: dental, home-services, professional-services, recruiting,
            coaching, veterinary, physical-therapy, medspa

CATEGORIES: crm, customer_support, ai_sales_tools, automation, analytics,
            ecommerce, finance, hr_payroll, marketing, project_management,
            ai_assistants, ai_agents, ai_content_creation, dev_tools

START WITH: Dental industry, CRM category as pilot
```
