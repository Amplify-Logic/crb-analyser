# Multi-Region Vendor System for Home Services

**Date:** 2026-01-24
**Status:** Approved

## Overview

Comprehensive vendor coverage for home services across English-speaking markets. Enables country-specific vendor recommendations with tiered detail levels.

## Target Markets

| Code | Country | Priority |
|------|---------|----------|
| US | United States | Primary |
| CA | Canada | Primary |
| UK | United Kingdom | Primary |
| NZ | New Zealand | Primary |
| AU | Australia | Primary |
| IE | Ireland | Secondary |
| NL | Netherlands | Secondary |
| DE | Germany | Secondary |
| SE | Sweden | Secondary |
| DK | Denmark | Secondary |
| NO | Norway | Secondary |

## Schema Changes

```sql
-- Migration: 019_vendor_regions.sql
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS
  countries TEXT[] DEFAULT '{}';

ALTER TABLE vendors ADD COLUMN IF NOT EXISTS
  tier INTEGER DEFAULT 2 CHECK (tier BETWEEN 1 AND 3);

ALTER TABLE vendors ADD COLUMN IF NOT EXISTS
  home_services_subcategory TEXT;

-- Index for country filtering
CREATE INDEX IF NOT EXISTS idx_vendors_countries ON vendors USING GIN(countries);
```

## Vendor Tiers

| Tier | Detail Level | Purpose | Fields |
|------|--------------|---------|--------|
| 1 | Full | Primary recommendations | All fields including integrations, AI capabilities, G2 scores |
| 2 | Essentials | Alternatives | Name, pricing, countries, best_for, pros/cons |
| 3 | Minimal | Completeness | Name, website, countries, one_liner |

## Categories

| Category Slug | Name | Tier 1 | Tier 2 | Tier 3 |
|---------------|------|--------|--------|--------|
| field-service-management | Field Service Management | 10 | 15 | 15 |
| quoting-estimating | Quoting & Estimating | 6 | 8 | 6 |
| accounting-finance | Accounting & Finance | 6 | 8 | 6 |
| communication-reputation | Communication & Reputation | 6 | 10 | 8 |
| call-handling | Call Handling & Answering | 4 | 6 | 6 |
| payments-financing | Payments & Financing | 4 | 6 | 6 |
| fleet-gps | Fleet & GPS Tracking | 4 | 6 | 6 |
| marketing-lead-gen | Marketing & Lead Gen | 6 | 10 | 8 |

**Total: ~176 vendors** (46 Tier 1, 69 Tier 2, 61 Tier 3)

## Data Structure

### Tier 1 (Full Detail)

```json
{
  "slug": "fergus",
  "name": "Fergus",
  "website": "fergus.com",
  "tier": 1,
  "category": "field-service-management",
  "countries": ["NZ", "AU", "UK"],
  "pricing": {
    "currency": "NZD",
    "plans": [
      {"name": "Basic", "price": 49, "period": "month/user", "features": ["Quoting", "Invoicing", "Scheduling"]},
      {"name": "Pro", "price": 79, "period": "month/user", "features": ["+ Site docs", "Purchase orders", "Timesheets"]},
      {"name": "Premium", "price": 99, "period": "month/user", "features": ["+ Reporting", "Integrations", "API"]}
    ],
    "free_trial_days": 14
  },
  "company_sizes": ["startup", "smb"],
  "best_for": ["Plumbers", "Electricians", "Builders", "HVAC"],
  "pros": ["Built for ANZ trades", "Xero integration", "Simple mobile app", "NZ-based support"],
  "cons": ["Less powerful than ServiceTitan", "Limited marketing features", "No AI call handling"],
  "integrations": ["Xero", "MYOB", "Stripe", "Google Calendar", "Outlook"],
  "implementation_weeks": 1,
  "ai_capabilities": ["Automated reminders", "Online booking"],
  "g2_score": 4.5,
  "verified_date": "2026-01"
}
```

### Tier 2 (Essentials)

```json
{
  "slug": "servicem8",
  "name": "ServiceM8",
  "website": "servicem8.com",
  "tier": 2,
  "category": "field-service-management",
  "countries": ["AU", "NZ", "UK", "US"],
  "pricing": {"currency": "AUD", "starting_price": 29, "period": "month"},
  "company_sizes": ["startup", "smb"],
  "best_for": ["Solo operators", "Small teams"],
  "pros": ["Very affordable", "Easy to use", "Good mobile app"],
  "cons": ["Limited scalability", "Basic reporting"]
}
```

### Tier 3 (Minimal)

```json
{
  "slug": "workiz",
  "name": "Workiz",
  "website": "workiz.com",
  "tier": 3,
  "category": "field-service-management",
  "countries": ["US", "CA"],
  "best_for": ["Locksmiths", "Junk removal", "Appliance repair"],
  "one_liner": "US-focused FSM for service niches, strong call tracking"
}
```

## Regional Vendor Coverage

### Field Service Management (Tier 1)

| Vendor | NZ | AU | UK | US | CA | EU |
|--------|----|----|----|----|----|----|
| Fergus | ✓ | ✓ | ✓ | | | |
| Tradify | ✓ | ✓ | ✓ | | | |
| simPRO | ✓ | ✓ | ✓ | ✓ | | |
| ServiceTitan | | | | ✓ | ✓ | |
| Housecall Pro | | | | ✓ | ✓ | |
| Jobber | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| FieldEdge | | | | ✓ | ✓ | |
| ServiceM8 | ✓ | ✓ | ✓ | | | |
| Commusoft | | | ✓ | | | |
| BigChange | | | ✓ | | | |

### Accounting (Tier 1)

| Vendor | NZ | AU | UK | US | CA | EU |
|--------|----|----|----|----|----|----|
| Xero | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| QuickBooks | | ✓ | ✓ | ✓ | ✓ | |
| MYOB | ✓ | ✓ | | | | |
| FreshBooks | | | ✓ | ✓ | ✓ | |
| Exact | | | | | | NL |
| Fortnox | | | | | | SE |

## Recommendation Prompt

See `backend/src/prompts/vendor_recommendation.md` for the full system prompt.

Key principles:
- Country-specific filtering
- Size-appropriate recommendations
- Trade-type matching
- Pain point → solution mapping
- Honest limitations
- Local currency pricing

## Implementation Steps

1. Create migration `019_vendor_regions.sql`
2. Update `home-services/vendors.json` with new structure
3. Add comprehensive vendor data per category
4. Create `vendor_recommendation.md` prompt
5. Update vendor matching skill to use countries filter
6. Test with sample businesses from each region

## File Changes

| File | Change |
|------|--------|
| `backend/supabase/migrations/019_vendor_regions.sql` | New migration |
| `backend/src/knowledge/home-services/vendors.json` | Replace with multi-region data |
| `backend/src/prompts/vendor_recommendation.md` | New prompt file |
| `backend/src/skills/analysis/vendor_matching.py` | Add country filtering |
