# Vendor Database Redesign - Handoff Document

**Date:** 2025-12-31
**Status:** Phase 1-2 Complete, Phase 3-6 Pending
**Design Doc:** `docs/plans/2025-12-31-vendor-database-redesign.md`

## Overview

Migrating vendor knowledge base from JSON files to Supabase with:
- Industry-specific tier lists with boost scoring
- Admin UI for non-technical team management
- Claude Code integration for AI-powered vendor research
- Semantic search using embeddings

## Completed Work

### Phase 1: Database Setup ✅

**Files Created:**
- `backend/supabase/migrations/012_vendor_database.sql` - Full schema
- `backend/src/scripts/migrate_vendors_to_supabase.py` - Migration script

**Database Tables:**
```
vendors                  - 80 vendors migrated from JSON
industry_vendor_tiers    - 12 tier assignments created
vendor_audit_log         - Tracks all changes
vendor_categories        - 14 categories (reference)
supported_industries     - 8 industries (reference)
```

**Key Schema Points:**
- `vendors.industries` is a TEXT[] array for multi-industry support
- `vendors.recommended_for` is a TEXT[] for tag-based matching
- `industry_vendor_tiers` links vendors to industry-specific tiers (1-3)
- Tier boost scores: Tier 1 = +30, Tier 2 = +20, Tier 3 = +10
- pgvector enabled for future semantic search (1536-dim embeddings)

**Migration Run:**
```bash
cd backend
source venv/bin/activate
python -m src.scripts.migrate_vendors_to_supabase --clear-existing
```

### Phase 2: Backend Integration ✅

**Files Modified:**
- `backend/src/config/settings.py` - Added `USE_SUPABASE_VENDORS=True`
- `backend/src/services/vendor_service.py` - Added tier boost methods
- `backend/src/skills/analysis/vendor_matching.py` - Supabase integration

**New VendorService Methods:**
```python
# Get vendors with industry tier boosts
await vendor_service.get_vendors_with_tier_boost(
    industry="dental",
    category="customer_support",
    finding_tags=["website_chat"]
)

# Get vendors in a specific tier
await vendor_service.get_tier_vendors(industry="dental", tier=1)

# Manage tier assignments
await vendor_service.set_vendor_tier("dental", vendor_id, tier=1, boost_score=30)
await vendor_service.remove_vendor_tier("dental", vendor_id)
```

**VendorMatchingSkill Changes:**
- Extracts finding tags via `_extract_finding_tags()`
- Calls `_get_candidate_vendors_supabase()` when `USE_SUPABASE_VENDORS=True`
- Scoring includes tier boost: `score += tier_boost` (30/20/10 points)
- Automatic JSON fallback on Supabase errors

**Environment Variable:**
```bash
USE_SUPABASE_VENDORS=true  # Default, uses Supabase
USE_SUPABASE_VENDORS=false # Fallback to JSON files
```

## Remaining Phases

### Phase 3: Admin UI - Core (Estimated: 4-5 hours)

**Goal:** Internal team can view, search, and edit vendors

**Backend Routes to Create:**
```
GET    /api/admin/vendors          - List with pagination, search, filters
GET    /api/admin/vendors/:slug    - Get single vendor
PUT    /api/admin/vendors/:slug    - Update vendor
POST   /api/admin/vendors          - Create vendor
DELETE /api/admin/vendors/:slug    - Soft delete (set status=deprecated)
GET    /api/admin/vendors/categories - List categories with counts
GET    /api/admin/vendors/audit    - Audit log with filters
```

**Frontend Pages to Create:**
```
/admin/vendors           - Main vendor list (protected)
/admin/vendors/:slug     - Edit vendor form
/admin/vendors/audit     - Audit log viewer
```

**UI Features:**
- Paginated list with search (name, description)
- Filter by: category, industry, status, company_size
- Edit modal with all vendor fields
- Actions: Edit, View JSON, Mark Stale, Deprecate

**Auth Protection:**
- Use existing Supabase Auth
- Whitelist emails in RLS or check in middleware

### Phase 4: Admin UI - Industry Tiers (Estimated: 2-3 hours)

**Goal:** Manage industry-specific vendor rankings

**Backend Routes:**
```
GET    /api/admin/vendors/industries/:industry/tiers - Get tier list
POST   /api/admin/vendors/industries/:industry/tiers - Set vendor tier
DELETE /api/admin/vendors/industries/:industry/tiers/:vendor_id - Remove
PUT    /api/admin/vendors/industries/:industry/tiers/reorder - Reorder
```

**Frontend:**
- Industry selector dropdown
- Three-column tier view (Tier 1 / Tier 2 / Tier 3)
- Drag-and-drop between tiers
- Add vendor to tier from search
- Edit boost_score per vendor

### Phase 5: Claude Code Integration (Estimated: 1-2 hours)

**Goal:** AI-powered vendor research and enrichment

**Add to CLAUDE.md:**
```markdown
## Vendor Database Management

The vendor knowledge base is stored in Supabase. Use these patterns:

### Adding a New Vendor
1. Fetch the vendor's website and pricing page using WebFetch
2. Extract: name, pricing tiers, features, integrations, company sizes
3. Determine category from: crm, customer_support, ai_sales_tools, etc.
4. Insert into Supabase `vendors` table
5. Log action in `vendor_audit_log`

### Quick Commands
- "Add vendor: [url]" — Research and add new vendor
- "Refresh vendor: [slug]" — Re-fetch pricing and update
- "Set [slug] as tier 1 for [industry]" — Add to industry tier list
- "List stale vendors" — Show vendors not verified in 90+ days
```

**Helper Script to Create:**
`backend/src/scripts/vendor_cli.py` - CLI for vendor operations

### Phase 6: Semantic Search (Estimated: 2-3 hours)

**Goal:** Find vendors by natural language description

**Steps:**
1. Add embedding generation on vendor create/update
2. Use OpenAI or Voyage embeddings (1536 dimensions)
3. Create endpoint: `POST /api/vendors/search/semantic`
4. Add to admin UI search

**Supabase Function Already Exists:**
```sql
search_vendors_semantic(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10,
    filter_category TEXT DEFAULT NULL,
    filter_industry TEXT DEFAULT NULL
)
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/supabase/migrations/012_vendor_database.sql` | Full Supabase schema |
| `backend/src/scripts/migrate_vendors_to_supabase.py` | JSON → Supabase migration |
| `backend/src/services/vendor_service.py` | Vendor CRUD + tier methods |
| `backend/src/skills/analysis/vendor_matching.py` | Agent vendor matching |
| `backend/src/config/settings.py` | `USE_SUPABASE_VENDORS` setting |
| `backend/src/knowledge/__init__.py` | JSON fallback functions |
| `docs/plans/2025-12-31-vendor-database-redesign.md` | Full design document |

## Testing the Current Implementation

**Verify Supabase Data:**
```sql
-- Check vendor count
SELECT COUNT(*) FROM vendors;  -- Should be 80

-- Check tier assignments
SELECT industry, COUNT(*) FROM industry_vendor_tiers GROUP BY industry;

-- Check a specific vendor
SELECT name, category, recommended_default, industries
FROM vendors WHERE slug = 'forethought';
```

**Test Vendor Matching:**
```python
# In Python REPL
import asyncio
from src.services.vendor_service import vendor_service

async def test():
    vendors = await vendor_service.get_vendors_with_tier_boost(
        industry="dental",
        finding_tags=["website_chat"]
    )
    for v in vendors[:5]:
        print(f"{v['name']}: tier={v.get('_tier')}, boost={v.get('_tier_boost')}, score={v.get('_recommendation_score')}")

asyncio.run(test())
```

## Important Decisions Made

1. **Tier Model:** Filter + Boost (vendors must be in industry's industries[] array, then get tier boost)

2. **Scoring System:**
   - Base score: 50
   - Tier 1: +30, Tier 2: +20, Tier 3: +10
   - recommended_default: +25 (if no tier)
   - recommended_for tag match: +10
   - Size match: +20
   - High rating: +15
   - Easy implementation: +10

3. **Admin Access:** Internal team only (2 users), hosted on Railway

4. **Claude Code Integration:** Uses local Claude Code account (not API) for vendor research

5. **JSON Fallback:** Always available via `USE_SUPABASE_VENDORS=false`

## Git Commits

```
486184d feat(vendors): add Supabase vendor database with migration
db14049 feat(vendors): add Supabase vendor queries with industry tier boosts
```

## Next Session Starting Point

Start with **Phase 3: Admin UI - Core**:
1. Create backend routes in `backend/src/routes/admin_vendors.py`
2. Register in `main.py`
3. Create React pages in `frontend/src/pages/admin/`
4. Add route protection for admin access
