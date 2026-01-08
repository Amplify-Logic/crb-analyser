# Vendor Data Quality Audit - 2026-01-04

## Mission

Scrutinize the entire vendor database (117 vendors across 8 industries) to ensure:
1. All data is REAL and VERIFIED (not hallucinated)
2. Pricing is accurate and current
3. Tier assignments are appropriate
4. The recommendation engine is selecting the right vendors for opportunities

## Context

We've imported vendors across these industries:
- dental (17), recruitment (21), professional-services (22)
- home-services (13), coaching (11), veterinary (10)
- physical-therapy (12), medspa (11)

**Concern:** Some data may have been inferred or outdated. We need to validate.

---

## Phase 1: Database Audit

### 1.1 Verify Vendor Existence
For each vendor, confirm:
- [ ] Website is live and accessible
- [ ] Company still exists and is active
- [ ] Name/branding hasn't changed

### 1.2 Validate Pricing
For each vendor with public pricing, verify against official source:
```sql
SELECT slug, name, pricing->>'starting_price' as price,
       pricing->>'model' as model, website, pricing_url
FROM vendors
WHERE pricing->>'starting_price' IS NOT NULL
ORDER BY industries, slug;
```

**Red flags to check:**
- Prices that seem too low or too high
- "Custom pricing" where public pricing exists
- Outdated pricing from 2024 or earlier

### 1.3 Validate Ratings
Cross-reference G2 and Capterra scores:
```sql
SELECT slug, name, g2_score, capterra_score,
       industries, verified_at
FROM vendors
WHERE g2_score IS NOT NULL OR capterra_score IS NOT NULL
ORDER BY industries, slug;
```

### 1.4 Check for Duplicates
```sql
SELECT name, COUNT(*)
FROM vendors
GROUP BY LOWER(name)
HAVING COUNT(*) > 1;
```

---

## Phase 2: Recommendation Engine Analysis

### 2.1 Understand the Matching Logic

Key files to review:
- `backend/src/skills/analysis/vendor_matching.py` - Core matching logic
- `backend/src/knowledge/__init__.py` - Industry definitions
- `backend/src/routes/vendors.py` or `admin_vendors.py` - API endpoints

Questions to answer:
1. How does the agent decide which vendors to recommend?
2. What role do tiers play (1/2/3)?
3. What role does `boost_score` play?
4. How are industry-specific vendors prioritized?
5. Is there semantic matching or just keyword matching?

### 2.2 Test Recommendation Scenarios

For each industry, simulate an opportunity and verify recommendations:

**Scenario 1: Dental Practice Automation**
- Input: "We need to automate patient reminders and reduce no-shows"
- Expected: Weave, NexHealth, RevenueWell (Tier 1 patient communication)
- Check: Does the engine return these?

**Scenario 2: HVAC Field Service**
- Input: "We're an HVAC company with 15 techs needing scheduling and invoicing"
- Expected: ServiceTitan or Housecall Pro (Tier 1)
- Check: Does budget influence the recommendation?

**Scenario 3: Solo Coach CRM**
- Input: "I'm a solo executive coach needing client management"
- Expected: Paperbell or Practice.do (affordable, solo-friendly)
- Check: Does it avoid enterprise solutions like CoachHub?

**Scenario 4: Multi-location MedSpa**
- Input: "We have 5 medspa locations needing unified management"
- Expected: Zenoti or Boulevard (multi-location capable)
- Check: Does it filter out solo-only solutions?

### 2.3 Identify Gaps

For each industry, check:
- Are there major vendors missing?
- Are there outdated/deprecated vendors included?
- Are tier assignments correct based on market position?

---

## Phase 3: Data Remediation

### 3.1 Create Validation Queries

```sql
-- Vendors without pricing
SELECT slug, name, industries FROM vendors
WHERE pricing->>'starting_price' IS NULL
  AND pricing->>'custom_pricing' IS NOT TRUE;

-- Vendors without ratings
SELECT slug, name, industries FROM vendors
WHERE g2_score IS NULL AND capterra_score IS NULL;

-- Vendors not verified recently
SELECT slug, name, verified_at FROM vendors
WHERE verified_at < NOW() - INTERVAL '90 days';
```

### 3.2 Update Stale Data

For each flagged vendor:
1. Web search for current pricing
2. Check G2/Capterra for current ratings
3. Update database with verified data
4. Log changes in `vendor_audit_log`

### 3.3 Fix Tier Assignments

Review `industry_vendor_tiers` for accuracy:
```sql
SELECT v.name, ivt.industry, ivt.tier, ivt.boost_score, ivt.notes
FROM industry_vendor_tiers ivt
JOIN vendors v ON v.id = ivt.vendor_id
ORDER BY ivt.industry, ivt.tier, ivt.boost_score DESC;
```

Tier criteria:
- **Tier 1**: Market leaders, highest ratings, most features, recommended for most use cases
- **Tier 2**: Strong alternatives, good value, specific strengths
- **Tier 3**: Niche, budget, or emerging options

---

## Phase 4: Recommendation Engine Improvements

### 4.1 Matching Criteria Review

Current matching may use:
- Industry match
- Company size fit
- Budget alignment
- Feature requirements
- Tier preference

Improvements to consider:
- Integration requirements (e.g., "must integrate with QuickBooks")
- Geographic availability (e.g., HoneyBook is USA/Canada only)
- Specific use case matching (e.g., "voice documentation" → Clinicient)

### 4.2 Test and Validate

Create test cases for the recommendation engine:
```python
test_cases = [
    {
        "industry": "dental",
        "input": "patient communication and reminders",
        "expected_tier_1": ["weave", "nexhealth"],
        "should_not_include": ["dentrix"]  # Not communication focused
    },
    {
        "industry": "home-services",
        "input": "small plumbing company, 3 techs, budget under $100/mo",
        "expected": ["kickserv", "servicem8"],
        "should_not_include": ["servicetitan"]  # Too expensive
    },
    # ... more cases
]
```

---

## Files Reference

### Import Scripts
```
backend/src/scripts/import_dental_vendors.py
backend/src/scripts/import_recruitment_vendors.py
backend/src/scripts/import_professional_services_vendors.py
backend/src/scripts/import_home_services_vendors.py
backend/src/scripts/import_coaching_vendors.py
backend/src/scripts/import_veterinary_vendors.py
backend/src/scripts/import_physical_therapy_vendors.py
backend/src/scripts/import_medspa_vendors.py
```

### Core Logic
```
backend/src/skills/analysis/vendor_matching.py
backend/src/knowledge/__init__.py
backend/src/services/report_service.py (may use vendor data)
```

### Database
```
Tables: vendors, industry_vendor_tiers, vendor_audit_log
```

---

## Prompt for New Session

```
I need to audit and validate the CRB Analyser vendor database for quality and accuracy.

Read the audit plan: docs/handoffs/2026-01-04-vendor-quality-audit.md

## Tasks

### Phase 1: Database Audit
1. Query the database to get all 117 vendors across 8 industries
2. For a sample of 20 vendors (spread across industries), verify:
   - Website is live (use WebFetch)
   - Pricing matches what's in our database
   - G2/Capterra ratings are accurate
3. Flag any discrepancies

### Phase 2: Recommendation Engine
1. Find and read the vendor matching logic in the codebase
2. Understand how tiers and boost_scores influence recommendations
3. Trace how vendor recommendations flow into reports

### Phase 3: Test Recommendations
Run these test scenarios and verify the engine recommends appropriately:
1. "Dental practice needs patient communication" → expect Weave, NexHealth
2. "Solo coach needs client management" → expect Paperbell, Practice.do
3. "5-location medspa chain" → expect Zenoti, Boulevard
4. "Small HVAC company, tight budget" → expect Kickserv, ServiceM8

### Phase 4: Fix Issues
- Update any incorrect pricing/ratings
- Adjust tier assignments if needed
- Document changes in vendor_audit_log

Report findings with specific data points - don't summarize, show evidence.
```

---

## Success Criteria

- [ ] 100% of Tier 1 vendors verified as active with correct pricing
- [ ] No hallucinated vendors (all have real, accessible websites)
- [ ] Recommendation engine returns appropriate vendors for test scenarios
- [ ] All pricing data verified within last 90 days
- [ ] Tier assignments align with market position and user reviews
