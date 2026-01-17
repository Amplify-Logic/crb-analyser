# Vendor System Analysis Report
*Generated: 2026-01-14*

## Executive Summary

The vendor database has **213 active vendors** but has significant issues with **recommendation accuracy** and **industry coverage**. The vendor matching skill returns the same vendors regardless of category, which is a critical problem for report quality.

---

## 1. Database Health Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total vendors | 213 | Good |
| Active status | 213 (100%) | Good |
| Missing pricing | 15 (7%) | Needs fix |
| Missing ratings | 26 (12%) | Needs fix |
| Missing industries | 8 (4%) | Needs fix |
| Missing company_sizes | 4 (2%) | Minor |
| API openness scored | 212 (99%) | Good |

### API Openness Distribution

- Score 5 (excellent): 61 vendors
- Score 4 (good): 87 vendors
- Score 3 (basic): 51 vendors
- Score 2 (limited): 13 vendors
- Score 1 (closed): 1 vendor

### Vendors Missing Pricing

```
activecampaign, acuity-scheduling, attio-crm, cal-com, calendly,
google-meet, hubspot, microsoft-teams, monday-com, n8n-ai,
notion, pipedrive, salesforce, slack, zoom
```

### Vendors Missing Ratings

```
activecampaign, acuity-scheduling, attio-crm, cal-com, calendly,
descript, fireflies-ai, freshdesk-test, gamma-presentations,
google-meet, hubspot, loom, microsoft-teams, monday-com, n8n-ai,
notion, opus-clip, outbond-agents, pipedrive, salesforce, slack,
suno-ai, synthesia, zoom, [+2 more]
```

---

## 2. Industry Tier Coverage

| Industry | T1 | T2 | T3 | Total | Status |
|----------|----|----|----|----|--------|
| dental | 6 | 9 | 2 | 17 | Good |
| home-services | 3 | 6 | 4 | 13 | Good |
| professional-services | 7 | 11 | 4 | 22 | Good |
| veterinary | 3 | 5 | 3 | 11 | Good |
| coaching | 3 | 5 | 3 | 11 | Good |
| physical-therapy | 4 | 4 | 4 | 12 | Good |
| medspa | 4 | 3 | 4 | 11 | Good |
| **recruiting** | 0 | 0 | 0 | 0 | **CRITICAL** |
| **chiropractic** | 0 | 0 | 0 | 0 | **CRITICAL** |
| **legal** | 0 | 0 | 0 | 0 | **CRITICAL** |
| **accounting** | 0 | 0 | 0 | 0 | **CRITICAL** |
| **construction** | 0 | 0 | 0 | 0 | **CRITICAL** |

**5 industries have ZERO tier assignments** - recommendations for these industries will fail or return poor results.

### T1 Dental Vendors

- NexHealth (patient_communication)
- RevenueWell (dental_marketing)
- Open Dental (dental_practice_management)
- CareStack (dental_practice_management)
- Curve Dental (dental_practice_management)
- Weave (patient_communication)

---

## 3. Vendor Matching Quality

### Critical Issue: Same Vendors Returned Regardless of Category

Test Results (Dental industry, SMB, moderate budget):

| Finding | Category Detected | Off-the-shelf | Best-in-class | Correct? |
|---------|-------------------|---------------|---------------|----------|
| Manual appointment scheduling | scheduling | Open Dental | tab32 | **NO** |
| No CRM system | crm | Open Dental | tab32 | **NO** |
| Manual invoice creation | finance | Open Dental | tab32 | **NO** |
| Website has no chat | crm | Open Dental | tab32 | **NO** |

**Expected Results:**
- Scheduling → Calendly, Acuity Scheduling
- CRM → HubSpot, Salesforce, Pipedrive
- Finance → QuickBooks, FreshBooks
- Chat/Support → Intercom, Crisp, Zendesk

### Root Cause Analysis

**Issue 1: Category Mismatch**

The vendor database uses industry-specific categories, but findings use generic categories:

```
Generic categories (in findings):    Database categories:
- scheduling                         - dental_practice_management
- crm                               - pt_practice_management
- finance                           - veterinary_practice_management
- customer_support                  - medspa_management
```

**Issue 2: Tier Boost Dominance**

When category matching fails (returns 0 vendors), the system falls back to tier-boosted vendors regardless of actual fit. Since dental T1 vendors are dental practice management tools, they win every time.

**Issue 3: Cross-Industry Tools Not Included**

Generic tools like Calendly have `industries: ['*']` (wildcard) but the Supabase query for `industry='dental'` doesn't include these.

---

## 4. Category Distribution

### Top 10 Categories

| Category | Count |
|----------|-------|
| field_service_management | 15 |
| crm | 13 |
| recruitment_ats | 13 |
| medspa_management | 11 |
| pt_practice_management | 11 |
| veterinary_practice_management | 10 |
| coaching_platform | 10 |
| customer_support | 8 |
| dental_practice_management | 8 |
| project_management | 8 |

### Generic Tools Available (But Not Industry-Tagged)

| Category | Count | Examples |
|----------|-------|----------|
| scheduling | 4 | Calendly, Acuity, Cal.com |
| crm | 13 | HubSpot, Salesforce, Pipedrive |
| finance | 7 | QuickBooks, FreshBooks |
| customer_support | 8 | Intercom, Zendesk, Freshdesk |
| automation | 6 | Make, n8n, Zapier |

---

## 5. Technical Issues

### Broken: Stale Vendor Detection

```python
# Error when calling get_vendors_needing_refresh()
postgrest.exceptions.APIError: {'code': '42703', 'message': 'column vendors.pricing_verified_at does not exist'}
```

The method references `pricing_verified_at` which doesn't exist. Should use `verified_at` instead.

**File:** `backend/src/services/vendor_service.py:263`

---

## Recommendations

### Critical (Blocks Core Functionality)

#### 1. Fix Category Mapping in Vendor Matching

**Option A:** Add category aliases to vendor_matching.py

```python
CATEGORY_ALIASES = {
    'scheduling': ['scheduling', 'dental_practice_management', 'pt_practice_management', 'appointment'],
    'crm': ['crm', 'patient_communication', 'legal_crm', 'customer'],
    'finance': ['finance', 'accounting_practice_management', 'billing'],
    'customer_support': ['customer_support', 'patient_communication', 'helpdesk'],
}
```

**Option B:** Add secondary category tags to vendors

Add a `secondary_categories` array field to vendors so dental practice management can also be tagged as `scheduling` + `crm` + `billing`.

#### 2. Add Tier Assignments for 5 Industries

```sql
-- Recruiting
INSERT INTO industry_vendor_tiers (industry, vendor_id, tier)
SELECT 'recruiting', id, 1 FROM vendors
WHERE category = 'recruitment_ats'
AND slug IN ('greenhouse', 'lever', 'workable');

-- Legal
INSERT INTO industry_vendor_tiers (industry, vendor_id, tier)
SELECT 'legal', id, 1 FROM vendors
WHERE category = 'legal_practice_management';

-- Accounting
INSERT INTO industry_vendor_tiers (industry, vendor_id, tier)
SELECT 'accounting', id, 1 FROM vendors
WHERE category = 'accounting_practice_management';

-- Chiropractic
INSERT INTO industry_vendor_tiers (industry, vendor_id, tier)
SELECT 'chiropractic', id, 1 FROM vendors
WHERE category = 'chiropractic_practice_management';

-- Construction
INSERT INTO industry_vendor_tiers (industry, vendor_id, tier)
SELECT 'construction', id, 1 FROM vendors
WHERE category IN ('construction_project_management', 'construction_estimating');
```

#### 3. Include Cross-Industry Tools in Queries

Update `list_vendors()` to also return vendors with `industries: ['*']`:

```python
# In vendor_service.py list_vendors()
if industry:
    # Include both industry-specific AND universal vendors
    query = query.or_(
        f"industries.cs.{{{industry}}},industries.cs.{{\"*\"}}"
    )
```

### High Priority

#### 4. Add Missing Pricing Data

```bash
# Refresh pricing for key missing vendors
cd backend
python -m src.agents.research.cli refresh --vendor calendly
python -m src.agents.research.cli refresh --vendor hubspot
python -m src.agents.research.cli refresh --vendor salesforce
python -m src.agents.research.cli refresh --vendor monday-com
```

#### 5. Fix Stale Vendor Detection

```python
# In vendor_service.py, line ~263, change:
# FROM: .lt("pricing_verified_at", cutoff)
# TO:   .lt("verified_at", cutoff)
```

#### 6. Add Ratings for Missing Vendors

Either:
- Scrape G2/Capterra scores via research agent
- Add manual `our_rating` (1-5 scale)

### Medium Priority

#### 7. Tag Generic Tools for Primary Industries

Add dental, recruiting, etc. to industries array for cross-industry tools:

```python
# Example: Update Calendly to include dental
UPDATE vendors
SET industries = industries || '["dental", "recruiting", "coaching"]'::jsonb
WHERE slug = 'calendly';
```

---

## Action Plan

### Week 1: Critical Fixes

1. [ ] Fix vendor matching category aliases
2. [ ] Add tier assignments for recruiting (highest volume missing industry)
3. [ ] Fix stale vendor detection method

### Week 2: Data Quality

4. [ ] Add tier assignments for legal, accounting, chiropractic, construction
5. [ ] Refresh pricing for 15 vendors missing data
6. [ ] Include cross-industry tools in industry queries

### Week 3: Enhancement

7. [ ] Add ratings for top 10 missing vendors
8. [ ] Tag generic tools for primary industries
9. [ ] Add secondary_categories field to vendor schema

---

## Verification Commands

```bash
# Re-run health check after fixes
cd backend && python -c "
import asyncio
from src.services.vendor_service import VendorService

async def check():
    vs = VendorService()
    result = await vs.list_vendors(page_size=300)
    vendors = result['vendors']

    missing_pricing = sum(1 for v in vendors if not v.get('pricing'))
    missing_ratings = sum(1 for v in vendors if not v.get('our_rating') and not v.get('g2_score'))

    print(f'Missing pricing: {missing_pricing}')
    print(f'Missing ratings: {missing_ratings}')

asyncio.run(check())
"

# Test vendor matching after fix
cd backend && python -c "
# Run matching test for scheduling finding
# Should return Calendly, not Open Dental
"
```
