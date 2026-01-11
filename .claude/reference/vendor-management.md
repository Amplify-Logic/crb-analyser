# Vendor Management Reference

> Load this when working on vendor database, research agents, or vendor recommendations.

---

## Vendor Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| slug | TEXT | Yes | Unique lowercase-hyphenated identifier |
| name | TEXT | Yes | Display name |
| category | TEXT | Yes | One of the categories below |
| website | TEXT | Yes | Full URL |
| description | TEXT | Yes | 1-2 sentences |
| pricing | JSONB | Yes | `{model, tiers[], starting_price, free_tier}` |
| status | TEXT | Yes | active, deprecated, pending |
| verified_at | TIMESTAMP | No | Last pricing verification |
| verified_by | TEXT | No | Who verified (claude-code, admin, etc.) |

## Categories

```
crm, customer_support, ai_sales_tools, automation, analytics,
ecommerce, finance, hr_payroll, marketing, project_management,
ai_assistants, ai_agents, ai_content_creation, dev_tools
```

## Industry Tiers

| Tier | Meaning | Refresh Frequency |
|------|---------|-------------------|
| T1 | Primary recommendations | Weekly |
| T2 | Secondary alternatives | Bi-weekly |
| T3 | Niche/specialized | Monthly |

## Supabase Access Patterns

```python
from src.config.supabase_client import get_async_supabase

supabase = await get_async_supabase()

# Insert vendor
await supabase.table("vendors").insert({
    "slug": "vendor-name",
    "name": "Vendor Name",
    "category": "crm",
    "website": "https://vendor.com",
    "description": "What the vendor does",
    "pricing": {"model": "subscription", "starting_price": 49, "free_tier": True},
    "status": "active",
}).execute()

# Update vendor
await supabase.table("vendors").update({
    "pricing": {...},
    "verified_at": datetime.utcnow().isoformat(),
    "verified_by": "claude-code",
}).eq("slug", "vendor-slug").execute()

# Log audit entry
await supabase.table("vendor_audit_log").insert({
    "vendor_slug": "vendor-slug",
    "action": "create",
    "changed_by": "claude-code",
    "changes": {"field": {"old": None, "new": "value"}},
}).execute()

# Set industry tier
await supabase.table("industry_vendor_tiers").upsert({
    "industry": "dental",
    "vendor_id": vendor_id,
    "tier": 1,
    "boost_score": 0,
}).execute()
```

## Adding a New Vendor

1. Fetch website and pricing page using WebFetch
2. Extract: name, pricing tiers, features, integrations, company sizes
3. Determine category from list above
4. Insert into `vendors` table
5. Log action in `vendor_audit_log`
6. Set industry tiers if relevant

## Refreshing Stale Vendors

```bash
# CLI helper
python -m backend.src.agents.research.cli refresh --stale-days 90
python -m backend.src.agents.research.cli refresh --vendor hubspot
```

## Research Agent

```
backend/src/agents/research/
├── cli.py              # Command-line interface
├── discover.py         # Find new vendors for industry
├── refresh.py          # Update existing vendor data
├── schemas.py          # Pydantic models
└── sources/
    ├── vendor_site.py  # Scrape vendor websites
    └── web_search.py   # Search for vendor info
```

## Data Quality Rules

- Pricing must be verified against vendor website (not AI-generated)
- `verified_at` must be < 90 days for recommendations
- Stale vendors get flagged in reports
- Every stat needs source + verified_date

## Admin UI

Access: `http://localhost:5174/admin/vendors`

Features:
- View/search/filter vendors
- Edit vendor details
- Manage industry tiers (T1/T2/T3)
- View audit log
- Mark vendors as verified
