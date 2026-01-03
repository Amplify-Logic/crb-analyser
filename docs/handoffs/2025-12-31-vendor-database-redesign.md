# Vendor Database Redesign - Handoff Document

**Date:** 2025-12-31
**Status:** Phase 1-4 Complete, Phase 5-6 Pending
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

### Phase 3: Admin UI - Core ✅

**Files Created:**
- `backend/src/routes/admin_vendors.py` - Admin API routes
- `frontend/src/pages/admin/VendorAdmin.tsx` - Admin UI page

**Backend Routes Implemented:**
```
GET    /api/admin/vendors              - List with pagination, search, filters
GET    /api/admin/vendors/:slug        - Get single vendor with tier assignments
PUT    /api/admin/vendors/:slug        - Update vendor
POST   /api/admin/vendors              - Create vendor
DELETE /api/admin/vendors/:slug        - Soft delete (set status=deprecated)
POST   /api/admin/vendors/:slug/verify - Mark vendor as verified
GET    /api/admin/vendors/categories   - List categories with counts
GET    /api/admin/vendors/industries   - List supported industries
GET    /api/admin/vendors/stats        - Vendor database statistics
GET    /api/admin/vendors/stale        - List vendors not verified in X days
GET    /api/admin/vendors/audit        - Audit log with filters
GET    /api/admin/vendors/industries/:industry/tiers - Get tier list for industry
POST   /api/admin/vendors/industries/:industry/tiers/:vendor_id - Set vendor tier
DELETE /api/admin/vendors/industries/:industry/tiers/:vendor_id - Remove from tier
```

**Frontend Features:**
- Paginated vendor list with search (name, description, tagline)
- Filter by: category, industry, status
- Vendor editor with full field editing (2-column layout)
- Statistics view with:
  - Total vendors, active, stale, deprecated counts
  - Vendors by category breakdown
  - Industry tier assignment counts
- Mark vendor as verified action
- Create new vendor form
- Soft delete (deprecate) functionality
- All changes logged to audit trail

**Frontend Route:**
```
/admin/vendors - Protected route, requires auth
```

**Registration:**
- Routes registered in `backend/src/routes/__init__.py`
- Router included in `backend/src/main.py` with prefix `/api/admin`
- React route added to `frontend/src/App.tsx`

### Phase 4: Admin UI - Industry Tiers ✅

**Goal:** Visual tier management UI

**Features Implemented:**
- Industry Tiers tab in sidebar navigation
- Industry selector dropdown
- Three-column tier view (Tier 1 / Tier 2 / Tier 3)
- Color-coded columns (green/blue/gray) with boost labels
- Search vendors to add to tiers
- Move vendors between tiers with quick buttons (→ T1, → T2, → T3)
- Edit modal for tier assignment with:
  - Tier selection
  - Extra boost score (0-50)
  - Notes field
- Remove vendor from tier
- Auto-refresh after changes

**Component:** `IndustryTierManager` in `VendorAdmin.tsx`

## Remaining Phases

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
| `backend/src/routes/admin_vendors.py` | Admin API routes |
| `frontend/src/pages/admin/VendorAdmin.tsx` | Admin UI page |
| `backend/src/skills/analysis/vendor_matching.py` | Agent vendor matching |
| `backend/src/config/settings.py` | `USE_SUPABASE_VENDORS` setting |
| `backend/src/knowledge/__init__.py` | JSON fallback functions |
| `docs/plans/2025-12-31-vendor-database-redesign.md` | Full design document |

## Testing the Admin UI

**Access URL:**
```
http://localhost:5174/admin/vendors
```
(Requires being logged in)

**Test Checklist:**
- [ ] Load vendor list
- [ ] Search vendors
- [ ] Filter by category
- [ ] Filter by industry
- [ ] View vendor details
- [ ] Edit vendor
- [ ] Create new vendor
- [ ] Mark vendor as verified
- [ ] View statistics
- [ ] Check audit log

**Backend Test:**
```bash
cd backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8383

# Test endpoints
curl http://localhost:8383/api/admin/vendors | jq
curl http://localhost:8383/api/admin/vendors/stats | jq
curl http://localhost:8383/api/admin/vendors/categories | jq
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
[pending] feat(vendors): add admin UI for vendor database management
```

## Next Session Starting Point

Start with **Phase 5: Claude Code Integration**:
1. Add vendor management section to CLAUDE.md
2. Create `backend/src/scripts/vendor_cli.py` for CLI operations
3. Test add/update/refresh workflows

Or proceed with **Phase 6: Semantic Search** if embeddings are higher priority.
