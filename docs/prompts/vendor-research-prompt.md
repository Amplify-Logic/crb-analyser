# Vendor Research Prompt

Use this prompt with Claude (or web-enabled AI) to research vendors for a specific category. Copy and customize the variables at the top.

---

## The Prompt

```
You are a rigorous software analyst researching vendors for a business software database.

**CRITICAL RULES - READ CAREFULLY:**
1. NEVER fabricate or guess information. If you don't know something, say "UNVERIFIED" or "NOT FOUND"
2. ONLY include vendors you can verify exist via real websites
3. Every fact must be something you can attribute to a source (official website, G2, Capterra, etc.)
4. Pricing MUST come from official pricing pages - if not publicly available, mark as "Contact Sales"
5. Do NOT include vendors you're uncertain about - quality over quantity
6. If a vendor seems to exist but you can't verify details, list it in a separate "Needs Manual Verification" section

**RESEARCH TASK:**
- Category: [CATEGORY - e.g., "CRM", "Customer Support", "Marketing Automation"]
- Target audience: [AUDIENCE - e.g., "SMBs with 10-200 employees", "Dental practices", "Marketing agencies"]
- Must have: [REQUIREMENTS - e.g., "API available", "Under $100/month starting price", "Free trial"]

**FOR EACH VENDOR, PROVIDE:**

```json
{
  "name": "Vendor Name",
  "website": "https://...",
  "slug": "vendor-name",
  "category": "category_slug",
  "description": "One sentence - what it does",
  "pricing": {
    "model": "subscription|usage|freemium",
    "starting_price": 29,
    "currency": "USD",
    "free_tier": true|false,
    "free_trial_days": 14|null,
    "pricing_url": "https://..."
  },
  "ratings": {
    "g2_score": 4.5,
    "g2_reviews": 1200,
    "capterra_score": 4.3,
    "capterra_reviews": 800,
    "source_date": "2026-01"
  },
  "best_for": ["small teams", "specific use case"],
  "key_capabilities": ["capability 1", "capability 2", "capability 3"],
  "integrations": ["Salesforce", "HubSpot", "Zapier"],
  "why_recommended": "1-2 sentences on why this vendor stands out",
  "verification_status": "VERIFIED|PARTIALLY_VERIFIED|NEEDS_REVIEW",
  "confidence_notes": "Any caveats about this data"
}
```

**SELECTION CRITERIA (only include if meets 3+ of these):**
- [ ] G2/Capterra rating ≥ 4.0 with 100+ reviews
- [ ] Active product (updated in last 12 months)
- [ ] Clear pricing or free trial available
- [ ] Strong fit for target audience
- [ ] Notable differentiator or specialization
- [ ] Good integration ecosystem

**OUTPUT FORMAT:**

## Tier 1 - Highly Recommended (5-10 vendors)
[Best-in-class for the category/audience]

## Tier 2 - Worth Considering (5-10 vendors)
[Solid options with specific strengths]

## Tier 3 - Niche/Emerging (3-5 vendors)
[Specialized or newer options worth watching]

## Needs Manual Verification
[Vendors that seem relevant but couldn't fully verify]

## Excluded (with reasons)
[Notable vendors you considered but excluded, and why]

---

Now research: [CATEGORY] vendors for [AUDIENCE]
```

---

## Example Usage

### For CRM vendors targeting dental practices:

```
Category: CRM
Target audience: Dental practices with 1-10 locations
Must have: Patient management features, HIPAA compliant, under $200/month
```

### For AI automation tools targeting marketing agencies:

```
Category: AI Automation / AI Agents
Target audience: Marketing agencies with 5-50 employees
Must have: Content generation, social media automation, client reporting
```

---

## After Research

1. Review the output critically - spot-check 2-3 vendors manually
2. Visit pricing pages to verify current pricing
3. Check G2/Capterra for current ratings
4. Only import vendors marked "VERIFIED" directly
5. Manually verify "PARTIALLY_VERIFIED" before importing

## Import Format

Once verified, vendors can be added via:
- Admin UI: `/admin/vendors` → Add Vendor
- CLI: `python -m src.scripts.vendor_cli add`
- Direct API: `POST /api/admin/vendors`
