# Vendor Database Redesign

**Date:** 2025-12-31
**Status:** Approved
**Authors:** Lars, Claude

## Overview

Migrate vendor knowledge base from JSON files to Supabase with an admin UI for non-technical team members. Add industry-specific tier lists and Claude Code integration for AI-powered vendor research.

## Goals

1. **Supabase storage** — Single source of truth, instant updates, queryable
2. **Admin UI** — Internal team can view, search, edit, and manage vendors
3. **Industry tiers** — Each industry has curated tier lists with boost scoring
4. **Claude Code integration** — AI-powered vendor research and enrichment
5. **Semantic search** — Find vendors by description using embeddings
6. **Audit trail** — Track all changes with who/what/when

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  ADMIN UI (Hosted on Railway)                                   │
│  - View/search/filter vendors                                   │
│  - Edit vendor details                                          │
│  - Manage industry tier lists                                   │
│  - View audit log                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↕ Supabase
┌─────────────────────────────────────────────────────────────────┐
│  SUPABASE                                                       │
│  - vendors table (main data)                                    │
│  - industry_vendor_tiers (boost system)                         │
│  - vendor_audit_log (history)                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────────┐
│  CLAUDE CODE (Local, on-demand)                                 │
│  - Research new vendors                                         │
│  - Enrich existing vendors                                      │
│  - Bulk refresh stale data                                      │
│  - Writes directly to Supabase                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema

### vendors table

```sql
CREATE TABLE vendors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  category TEXT NOT NULL,  -- 'crm', 'customer_support', etc.
  subcategory TEXT,

  -- Core info
  website TEXT,
  pricing_url TEXT,
  description TEXT,
  tagline TEXT,

  -- Pricing (JSONB for flexibility)
  pricing JSONB,  -- {model, tiers[], starting_price, free_tier, etc.}

  -- Fit criteria
  company_sizes TEXT[],  -- ['startup', 'smb', 'mid_market', 'enterprise']
  industries TEXT[],      -- ['dental', 'recruiting', 'saas', etc.]
  best_for TEXT[],
  avoid_if TEXT[],

  -- Recommendations
  recommended_default BOOLEAN DEFAULT false,
  recommended_for TEXT[],  -- ['website_chat', 'sales_enrichment']

  -- Ratings
  our_rating DECIMAL(2,1),
  our_notes TEXT,
  g2_score DECIMAL(2,1),
  g2_reviews INTEGER,
  capterra_score DECIMAL(2,1),
  capterra_reviews INTEGER,

  -- Implementation
  implementation_weeks INTEGER,
  implementation_complexity TEXT,  -- 'low', 'medium', 'high'
  implementation_cost JSONB,  -- {diy: {min, max}, with_help: {min, max}}
  requires_developer BOOLEAN DEFAULT false,

  -- Integrations
  integrations TEXT[],
  api_available BOOLEAN,
  api_type TEXT,  -- 'REST', 'GraphQL', etc.

  -- Competitors
  competitors TEXT[],

  -- Metadata
  verified_at TIMESTAMPTZ,
  verified_by TEXT,
  source_url TEXT,
  notes TEXT,
  status TEXT DEFAULT 'active',  -- 'active', 'deprecated', 'needs_review'

  -- Semantic search
  embedding VECTOR(1536),

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX idx_vendors_category ON vendors(category);
CREATE INDEX idx_vendors_status ON vendors(status);
CREATE INDEX idx_vendors_industries ON vendors USING GIN(industries);
CREATE INDEX idx_vendors_company_sizes ON vendors USING GIN(company_sizes);
```

### industry_vendor_tiers table

```sql
CREATE TABLE industry_vendor_tiers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  industry TEXT NOT NULL,  -- 'dental', 'recruiting', etc.
  vendor_id UUID REFERENCES vendors(id) ON DELETE CASCADE,
  tier INTEGER NOT NULL,   -- 1 = top pick, 2 = recommended, 3 = alternative
  boost_score INTEGER DEFAULT 0,  -- Extra points in matching
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),

  UNIQUE(industry, vendor_id)
);

CREATE INDEX idx_industry_tiers_industry ON industry_vendor_tiers(industry);
CREATE INDEX idx_industry_tiers_tier ON industry_vendor_tiers(tier);
```

### vendor_audit_log table

```sql
CREATE TABLE vendor_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vendor_id UUID REFERENCES vendors(id) ON DELETE SET NULL,
  vendor_slug TEXT,  -- Preserved even if vendor deleted
  action TEXT NOT NULL,  -- 'create', 'update', 'delete'
  changed_by TEXT,
  changes JSONB,  -- {field: {old: x, new: y}}
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_audit_vendor ON vendor_audit_log(vendor_id);
CREATE INDEX idx_audit_created ON vendor_audit_log(created_at DESC);
```

## Admin UI

### Routes

- `/admin/vendors` — Main vendor list (protected)
- `/admin/vendors/:slug` — Edit vendor
- `/admin/vendors/industries` — Industry tier management
- `/admin/vendors/audit` — Audit log

### Features

**All Vendors Tab:**
- Paginated list with search
- Filter by: category, industry, status, company size
- Actions: Edit, View JSON, Mark Stale, Delete

**By Industry Tab:**
- Select industry from dropdown
- View tier 1 / tier 2 / tier 3 vendors
- Drag to reorder tiers
- Add/remove vendors from tiers
- Set boost scores

**Stale/Needs Review Tab:**
- Vendors not verified in 90+ days
- Vendors marked as "needs_review"
- Quick actions: Refresh, Mark Verified, Deprecate

**Audit Tab:**
- Chronological list of all changes
- Filter by vendor, action type, user
- View diff of changes

### Access Control

- Protected by Supabase Auth
- Whitelist of allowed emails (you + teammate)
- RLS policies on all tables

## Industry Tier System

### How it works

1. **Global vendors** have base scores from `recommended_default` and ratings
2. **Industry tiers** add boost scores:
   - Tier 1: +30 points
   - Tier 2: +20 points
   - Tier 3: +10 points
3. **Filter by industry** — Only show vendors where `industries` array contains the client's industry
4. **Final score** = base score + industry boost

### Example

```
Client industry: dental

Vendor: Forethought
- Base score: 65 (ratings + recommended_default)
- Tier 1 for dental: +30
- Final score: 95 ← Top recommendation

Vendor: Zendesk
- Base score: 60 (ratings)
- Not in dental tiers: +0
- Final score: 60 ← Lower ranking

Vendor: Shopify
- Not in dental industries array
- Filtered out entirely
```

## Claude Code Integration

### CLAUDE.md Addition

```markdown
## Vendor Database Management

The vendor knowledge base is stored in Supabase. Use these patterns:

### Adding a New Vendor

1. Fetch the vendor's website and pricing page using WebFetch
2. Extract: name, pricing tiers, features, integrations, company sizes
3. Determine category from: crm, customer_support, ai_sales_tools, automation,
   analytics, ecommerce, finance, hr_payroll, marketing, project_management,
   ai_assistants, ai_agents, ai_content_creation, dev_tools
4. Insert into Supabase `vendors` table
5. Generate embedding using embedding_service
6. Log action in `vendor_audit_log`

### Vendor Schema (Required Fields)

- slug: lowercase-hyphenated unique identifier
- name: Display name
- category: One of the categories above
- website: Full URL
- description: 1-2 sentences
- pricing: JSONB with {model, tiers[], starting_price, free_tier}

### Quick Commands

- "Add vendor: [url]" — Research and add new vendor
- "Refresh vendor: [slug]" — Re-fetch pricing and update
- "Set [slug] as tier 1 for [industry]" — Add to industry tier list
- "Mark [slug] as deprecated, replaced by [new-slug]" — Soft delete
- "List stale vendors" — Show vendors not verified in 90+ days
```

### Supabase Access from Claude Code

Claude Code can write directly to Supabase using the existing client:

```python
from src.config.settings import get_settings
from supabase import create_client

settings = get_settings()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

# Insert vendor
supabase.table("vendors").insert({...}).execute()

# Update vendor
supabase.table("vendors").update({...}).eq("slug", "vendor-slug").execute()

# Log audit
supabase.table("vendor_audit_log").insert({
    "vendor_slug": "vendor-slug",
    "action": "create",
    "changed_by": "claude-code",
    "changes": {...}
}).execute()
```

## Migration Plan

### Phase 1: Database Setup (2-3 hours)

1. Create Supabase migration file with all tables
2. Enable pgvector extension for embeddings
3. Set up RLS policies for admin access
4. Run migration

### Phase 2: Data Migration (1-2 hours)

1. Create migration script: `backend/src/scripts/migrate_vendors_to_supabase.py`
2. Load all 14 vendor JSON files
3. Load industry-specific vendor files
4. Transform to flat schema
5. Insert into Supabase
6. Generate embeddings for all vendors
7. Create industry_vendor_tiers entries for existing `recommended_default` vendors

### Phase 3: Update Backend (1-2 hours)

1. Update `knowledge/__init__.py` to read from Supabase
2. Keep JSON fallback for local dev: `USE_SUPABASE_VENDORS=true/false`
3. Update `VendorMatchingSkill` to query Supabase
4. Add industry tier boost to scoring logic

### Phase 4: Admin UI - Core (4-5 hours)

1. Create admin routes in backend
2. Create React admin pages
3. Implement: list, search, filter, pagination
4. Implement: edit modal with validation
5. Implement: mark stale, delete actions
6. Add auth protection

### Phase 5: Admin UI - Industry Tiers (2-3 hours)

1. Create industry selector
2. Create tier management UI
3. Implement drag-and-drop reordering
4. Implement add/remove from tiers

### Phase 6: Claude Code Tools (1-2 hours)

1. Add vendor management section to CLAUDE.md
2. Create helper functions for Supabase writes
3. Test add/update/refresh workflows

### Phase 7: Semantic Search (2-3 hours)

1. Add embedding generation on vendor create/update
2. Add semantic search endpoint
3. Add search-by-description to admin UI

## Rollback Plan

- JSON files preserved as backup
- Environment variable to switch: `USE_SUPABASE_VENDORS=false`
- Can regenerate JSON from Supabase if needed

## Success Criteria

- [ ] All 80 vendors migrated to Supabase
- [ ] Admin UI accessible to internal team
- [ ] Can add new vendor via Claude Code in < 2 minutes
- [ ] Industry tier lists working for all 6 industries
- [ ] Semantic search returning relevant results
- [ ] Audit log tracking all changes

## Future Enhancements (Not in Scope)

- Vendor comparison tool for clients
- Public vendor directory
- Automated pricing refresh via scraping
- Vendor review aggregation
- Integration with external APIs (G2, Capterra)
