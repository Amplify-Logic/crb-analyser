---
name: vendor-refresh
description: Research and update vendor entries in the knowledge base and Supabase. Use when vendor pricing is stale (>90 days), when adding new vendors, or for periodic vendor data maintenance. Keywords - vendor, refresh, pricing, stale, update, research.
---

# Vendor Data Refresh

## When to Use

- Vendor pricing is stale (verified_at > 90 days ago)
- Adding a new vendor to the catalog
- Periodic maintenance of vendor data quality
- After a user reports incorrect vendor pricing in a report

## Phase 1: Assess Staleness

### Check Supabase Vendors

```bash
cd backend && python -c "
import asyncio
from src.config.supabase_client import get_async_supabase
from datetime import datetime, timedelta

async def check():
    sb = await get_async_supabase()
    cutoff = (datetime.utcnow() - timedelta(days=90)).isoformat()
    result = await sb.table('vendors').select('slug,name,category,verified_at').or_('verified_at.is.null,verified_at.lt.' + cutoff).eq('status', 'active').execute()
    for v in result.data:
        print(f'  STALE: {v[\"slug\"]} ({v[\"category\"]}) — last verified: {v.get(\"verified_at\", \"never\")}')
    print(f'\n{len(result.data)} stale vendors found')

asyncio.run(check())
"
```

### Check Knowledge Base Vendors

```bash
cd backend && grep -r '"verified_date"' src/knowledge/vendors/ | grep -v "2026-0[1-3]" | head -20
```

Look for entries with `verified_date` older than 3 months or missing entirely.

## Phase 2: Prioritize

Rank stale vendors by impact:
1. **T1 vendors** (primary recommendations) — refresh first
2. **Frequently recommended** — vendors that appear in recent reports
3. **T2/T3 vendors** — refresh if time allows

Present the priority list to the user and ask which vendors to refresh.

## Phase 3: Research a Vendor

For each vendor to refresh:

### 3.1 Fetch Current Pricing

Use WebFetch to visit the vendor's pricing page:

```
WebFetch: https://[vendor].com/pricing
```

Extract:
- Pricing tiers (name, price, billing cycle)
- Free tier availability
- Enterprise pricing (if listed)
- Key features per tier
- API access tier

### 3.2 Check for Changes

Compare fetched data against stored data:
- Pricing changed? Update with new values
- New tiers added? Add them
- Features changed? Update feature list
- Vendor renamed/acquired? Update name and notes

### 3.3 Update Knowledge Base JSON

Edit the relevant file in `backend/src/knowledge/vendors/[category].json`:

- Update `pricing` object
- Update `verified_date` to current month (YYYY-MM format)
- Update `source` to the URL you fetched from
- Add `"status": "VERIFIED"` if confirmed

### 3.4 Update Supabase (if vendor exists there)

```python
# Pattern for updating
await supabase.table("vendors").update({
    "pricing": {updated pricing object},
    "verified_at": datetime.utcnow().isoformat(),
    "verified_by": "claude-code",
}).eq("slug", "vendor-slug").execute()

# Log the change
await supabase.table("vendor_audit_log").insert({
    "vendor_slug": "vendor-slug",
    "action": "refresh",
    "changed_by": "claude-code",
    "changes": {"pricing": {"old": ..., "new": ...}},
}).execute()
```

## Phase 4: Add a New Vendor

If adding a vendor that doesn't exist yet:

1. **Research**: Fetch website, pricing page, features
2. **Categorize**: Pick from the category list:
   ```
   crm, customer_support, ai_sales_tools, automation, analytics,
   ecommerce, finance, hr_payroll, marketing, project_management,
   ai_assistants, ai_agents, ai_content_creation, dev_tools
   ```
3. **Create slug**: lowercase-hyphenated (e.g., `hubspot-crm`)
4. **Add to knowledge base**: Edit `backend/src/knowledge/vendors/[category].json`
5. **Add to Supabase**: Insert into `vendors` table
6. **Set industry tiers**: Upsert into `industry_vendor_tiers` for relevant industries
7. **Log**: Insert into `vendor_audit_log`

## Phase 5: Validation

After updates, verify data quality:

- [ ] All updated vendors have `verified_date` set to current month
- [ ] Pricing is numeric where expected (not placeholder text)
- [ ] `source` URLs are valid
- [ ] No duplicate slugs
- [ ] Industry tiers make sense for ecommerce (e.g., Shopify ecosystem tools should be T1)

Run the vendor validator hook mentally:
- [ ] Slug is lowercase-hyphenated
- [ ] Category is from the allowed list
- [ ] Pricing has `model`, `starting_price`, `free_tier`
- [ ] Status is `active`, `deprecated`, or `pending`

## Phase 6: Summary

Present results:

```
Vendor Refresh Summary
======================
Vendors checked: X
Updated: X
Added: X
Skipped: X (reason)

Updated vendors:
- vendor-name: pricing updated (was €X, now €Y)
- vendor-name: new tier added (Enterprise)

Still stale (couldn't verify):
- vendor-name: website down / pricing not public
```

## Rules

- **Never invent pricing** — if you can't verify from the vendor website, mark as `"status": "UNVERIFIED"`
- **Always log changes** — every update goes in `vendor_audit_log`
- **Preserve existing data** — update fields, don't delete and recreate
- **Load `.claude/reference/vendor-management.md`** for full schema details
- **Use WebFetch for research** — don't guess from training data
- **Respect rate limits** — don't hammer vendor websites
- **Focus on ecommerce vendors** — Shopify, Klaviyo, Gorgias, etc. are our primary vertical. Check `backend/src/knowledge/ecommerce/vendors.json` and `backend/src/knowledge/vendors/ecommerce.json` first
