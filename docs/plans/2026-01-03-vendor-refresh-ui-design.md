# Vendor Refresh & Discovery UI Design

## Overview

Add UI buttons and CLI commands to the VendorAdmin page for refreshing stale vendors, discovering new vendors, and scouting emerging tools from Product Hunt.

**Key decisions:**
- Interface: Both UI buttons + CLI
- Interaction: Preview first, then approve
- Scope: Filtered (respects current category/industry view)
- Discovery sources: G2 + Capterra + web search
- Product Hunt: Separate "Scout Emerging" button with filters
- Preview format: Diff view with warnings
- Reminders: Stale badge in header

---

## UI Layout

Three new action buttons in the VendorAdmin header:

```
┌─────────────────────────────────────────────────────────────────┐
│  Vendors (80)                                                    │
│                                                                  │
│  [Refresh Stale (12)] [Discover New] [Scout Emerging]           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Search...                        [+ Add Vendor]          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Button States

| Button | Badge | Behavior |
|--------|-------|----------|
| **Refresh Stale (N)** | Count of stale vendors matching current filters | Disabled when 0 |
| **Discover New** | None | Always enabled |
| **Scout Emerging** | None | Opens filter modal first |

### Stale Badge Colors

- Amber: stale count > 0
- Red: > 20% of filtered vendors are stale

---

## Preview Modal Flow

All actions follow the same two-phase pattern:

### Phase 1: Scanning

```
┌─────────────────────────────────────────────────────────────┐
│  Refreshing Stale Vendors                             [×]   │
│                                                             │
│  Scanning 12 vendors in CRM × Dental...                     │
│  ████████████░░░░░░░░ 8/12                                  │
│                                                             │
│  ✓ HubSpot - pricing updated                                │
│  ✓ Salesforce - no changes                                  │
│  ⟳ Pipedrive - checking G2...                               │
└─────────────────────────────────────────────────────────────┘
```

### Phase 2: Review & Approve

```
┌─────────────────────────────────────────────────────────────┐
│  Review Changes                                       [×]   │
│                                                             │
│  Found 8 updates, 4 unchanged                               │
│                                                             │
│  ☑ HubSpot                                    [View Diff]   │
│    pricing: $45/mo → $50/mo                                 │
│    g2_score: 4.4 → 4.5                                      │
│                                                             │
│  ☑ Freshsales                                 [View Diff]   │
│    ⚠️ pricing: $15/mo → $69/mo (+360%)                      │
│    free_tier: true → false                                  │
│                                                             │
│  ☐ Zoho CRM                                   [View Diff]   │
│    description: minor wording change                        │
│                                                             │
│  [Select All] [Deselect All]     [Cancel] [Apply Selected]  │
└─────────────────────────────────────────────────────────────┘
```

### Key Behaviors

- Large price changes (>50%) show warning icon
- Checkboxes pre-selected by default
- "View Diff" expands to show full before/after
- Apply writes to Supabase + audit log

---

## Discover New Flow

Searches for vendors not yet in database:

### Phase 1: Searching

```
┌─────────────────────────────────────────────────────────────┐
│  Discovering New Vendors                              [×]   │
│                                                             │
│  Searching CRM tools for Dental industry...                 │
│                                                             │
│  ✓ G2.com - found 24 vendors                                │
│  ✓ Capterra - found 18 vendors                              │
│  ⟳ Web search - "best dental CRM 2026"...                   │
│                                                             │
│  Cross-referencing with existing 12 vendors...              │
└─────────────────────────────────────────────────────────────┘
```

### Phase 2: Review Candidates

```
┌─────────────────────────────────────────────────────────────┐
│  New Vendor Candidates                                [×]   │
│                                                             │
│  Found 6 new vendors not in database                        │
│                                                             │
│  ☑ Dentrix Ascend                              ⭐ 4.2 G2    │
│    "Practice management with built-in CRM"                  │
│    Sources: G2, Capterra, dentaleconomics.com               │
│    [Preview Data]                                           │
│                                                             │
│  ☑ CareStack                                   ⭐ 4.5 G2    │
│    "All-in-one dental software with patient CRM"            │
│    Sources: G2, web search                                  │
│    [Preview Data]                                           │
│                                                             │
│  ☐ DentiMax                                    ⭐ 3.8 G2    │
│    "Dental imaging with basic patient tracking"             │
│    Sources: Capterra                                        │
│    ⚠️ Low relevance - primarily imaging, not CRM            │
│                                                             │
│  [Cancel]                              [Add 2 Selected]     │
└─────────────────────────────────────────────────────────────┘
```

### Key Behaviors

- Agent pre-filters obvious mismatches (shown unchecked with warning)
- "Preview Data" shows full vendor record to be created
- Multiple sources = higher confidence
- Added vendors get `status: needs_review`

---

## Scout Emerging (Product Hunt)

Separate button with filter modal:

### Filter Modal

```
┌─────────────────────────────────────────────────────────────┐
│  Scout Emerging Tools                                 [×]   │
│                                                             │
│  Search Product Hunt for new tools matching your filters.   │
│                                                             │
│  Category:    [CRM ▼]  (from current filter, or "All")      │
│  Industry:    [Dental ▼]                                    │
│                                                             │
│  Filters:                                                   │
│  ☑ B2B tools only                                           │
│  ☑ Minimum upvotes: [100]                                   │
│  ☐ Launched in last: [30 days ▼]                            │
│                                                             │
│  [Cancel]                                    [Start Scout]  │
└─────────────────────────────────────────────────────────────┘
```

### Results

```
┌─────────────────────────────────────────────────────────────┐
│  Product Hunt Results                                 [×]   │
│                                                             │
│  Found 3 relevant launches (filtered from 47)               │
│                                                             │
│  ☑ DentalAI Pro                        🔺 342 upvotes      │
│    "AI receptionist for dental practices"                   │
│    Launched: Dec 15, 2025                                   │
│    ⚠️ Early stage - no G2/Capterra ratings yet              │
│    [Preview Data]                                           │
│                                                             │
│  ☐ PatientFlow                         🔺 128 upvotes      │
│    "Patient scheduling automation"                          │
│    Launched: Nov 28, 2025                                   │
│    ⚠️ May overlap with existing: Dentrix                    │
│                                                             │
│  [Cancel]                               [Add 1 Selected]    │
└─────────────────────────────────────────────────────────────┘
```

### Key Behaviors

- Product Hunt tools flagged as "early stage" if no G2/Capterra presence
- Overlap detection warns if similar to existing vendors
- Added with `status: needs_review` + `source: product_hunt`

---

## CLI Interface

```bash
# Refresh stale vendors (respects filters)
python -m src.agents.research refresh --stale
python -m src.agents.research refresh --stale --category crm --industry dental

# Refresh specific vendors
python -m src.agents.research refresh --vendor hubspot --vendor salesforce

# Discover new vendors
python -m src.agents.research discover --category crm --industry dental

# Scout Product Hunt
python -m src.agents.research scout --category crm --min-upvotes 100 --b2b-only

# Dry run (preview only, no database writes)
python -m src.agents.research refresh --stale --dry-run

# JSON output for scripting
python -m src.agents.research refresh --stale --output json

# Auto-approve (skip preview, for scheduled runs)
python -m src.agents.research refresh --stale --auto-approve
```

### Interactive Output

```
Scanning 12 stale vendors in CRM × Dental...

Found 8 updates:
  HubSpot:     pricing $45 → $50, g2_score 4.4 → 4.5
  Freshsales:  ⚠️ pricing $15 → $69 (+360%), free_tier removed

Apply changes? [Y/n/select]:
```

### Auto-Approve Behavior

For scheduled/cron jobs. Applies all changes except those with warnings (>50% price change). Warnings are logged and skipped.

---

## Backend API

All endpoints require admin auth.

### Endpoints

```python
# Trigger refresh
POST /api/admin/research/refresh
{
    "scope": "stale",           # "stale" | "all" | "specific"
    "vendor_slugs": [],         # if scope=specific
    "category": "crm",          # optional filter
    "industry": "dental",       # optional filter
    "dry_run": false
}

# Trigger discovery
POST /api/admin/research/discover
{
    "category": "crm",
    "industry": "dental"
}

# Trigger Product Hunt scout
POST /api/admin/research/scout
{
    "category": "crm",
    "industry": "dental",
    "min_upvotes": 100,
    "b2b_only": true,
    "days_back": 30
}

# Apply approved changes from preview
POST /api/admin/research/apply
{
    "task_id": "uuid",
    "approved_items": ["hubspot", "freshsales"]
}

# Get task status/results (SSE for live progress)
GET /api/admin/research/status/{task_id}
```

### File Structure

```
backend/src/agents/research/
├── __init__.py
├── agent.py           # Orchestrator
├── refresh.py         # Refresh stale logic
├── discover.py        # New vendor discovery
├── scout.py           # Product Hunt scout
├── sources/
│   ├── g2.py          # G2 scraper (Crawl4AI)
│   ├── capterra.py    # Capterra scraper
│   ├── vendor_site.py # Direct pricing scrape
│   ├── web_search.py  # Brave/Tavily
│   └── product_hunt.py
└── cli.py             # CLI entry point
```

---

## Implementation Phases

### Phase 1 - MVP (Core refresh + discover)

- Refresh Stale button + preview modal
- Discover New button + preview modal
- G2 + Capterra + vendor website scraping via Crawl4AI
- CLI with `refresh` and `discover` commands
- Audit logging to `vendor_audit_log`

### Phase 2 - Enhanced discovery

- Web search integration (Brave/Tavily)
- Scout Emerging (Product Hunt)
- Duplicate/overlap detection
- Stale badge in header

### Phase 3 - Polish

- `--auto-approve` for scheduled runs
- Email digest option (if needed later)
- Bulk actions in list view (select multiple → refresh)

---

## Related Documents

- [Vendor Research Agent Spec](./2026-01-03-vendor-research-agent-spec.md) - Technical agent specification
- [CLAUDE.md](../../CLAUDE.md) - Vendor database management section

---

*Design created: 2026-01-03*
