# Knowledge Base Management UI - Design Document

**Date**: 2025-12-26
**Status**: Approved, ready for implementation

## Overview

Internal admin UI for managing the CRB Analyser knowledge base. Enables browsing, searching, adding, editing, and deleting knowledge entries, plus full control over vector embeddings.

## Requirements

- **User**: Internal team only (developers/admins)
- **Workflows**: Browse, add, edit, monitor embeddings
- **Layout**: Sidebar navigation with global search
- **Editing**: Hybrid (forms + JSON for advanced fields)
- **Embeddings**: Full control with per-item visibility and similarity testing

## Architecture

### Route
`/admin/knowledge` (protected, admin-only)

### Layout Structure
```
┌─────────────────────────────────────────────────────────────┐
│  Header: "Knowledge Base" + Global Search Bar + Stats Badge │
├────────────┬────────────────────────────────────────────────┤
│            │                                                │
│  Sidebar   │              Main Content Area                 │
│            │                                                │
│  - Vendors │   [List View / Detail View / Editor]          │
│  - Opps    │                                                │
│  - Bench   │                                                │
│  - Cases   │                                                │
│  - Pattern │                                                │
│  - Insights│                                                │
│  ────────  │                                                │
│  - Stats   │                                                │
│  - Settings│                                                │
│            │                                                │
└────────────┴────────────────────────────────────────────────┘
```

### Sidebar Categories
- Vendors (by category: CRM, Automation, AI Assistants, etc.)
- Opportunities (by industry: dental, home-services, etc.)
- Benchmarks (by industry)
- Case Studies (YC examples, Jevons Effect examples)
- Patterns (playbook sections)
- Insights (video/podcast learnings)
- ─────
- Embedding Stats (dashboard)
- Settings (re-vectorize all, API keys status)

## List View & Search

### Global Search (top bar)
- Searches across ALL content types
- Shows results grouped by type with match highlighting
- Keyboard shortcut: `Cmd+K` to focus
- Results show: title, type badge, industry, embedding status dot

### List View
```
┌─────────────────────────────────────────────────────────────┐
│ Vendors > CRM                          [+ Add New] [⟳ Sync] │
├─────────────────────────────────────────────────────────────┤
│ 🔍 Filter: [________] Industry: [All ▼] Embedded: [All ▼]  │
├─────────────────────────────────────────────────────────────┤
│ ● HubSpot CRM                    dental, home-services      │
│   Free tier available · $50-1200/mo        Embedded: 2h ago │
├─────────────────────────────────────────────────────────────┤
│ ● Salesforce                     professional-services      │
│   Enterprise · $25-300/user/mo             Embedded: 2h ago │
├─────────────────────────────────────────────────────────────┤
│ ○ Pipedrive                      recruiting, coaching       │
│   SMB-friendly · $15-99/user/mo          ⚠️ Not embedded    │
└─────────────────────────────────────────────────────────────┘

● = embedded    ○ = not embedded    ⚠️ = outdated/changed
```

### Row Actions
- Edit
- Duplicate
- Re-embed
- Delete
- View in JSON

## Editor Interface (Hybrid)

### Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Edit Vendor: HubSpot CRM                    [Save] [Cancel] │
├─────────────────────────────────────────────────────────────┤
│  Name:        [HubSpot CRM_____________]                    │
│  Slug:        [hubspot-crm] (auto-generated)                │
│  Category:    [CRM ▼]                                       │
│  Website:     [https://hubspot.com_____]                    │
│  Description: [___________________________________]         │
│  Best For:    [___________________________________]         │
│  Avoid If:    [___________________________________]         │
│  Industries:  [☑ dental] [☑ home-services] [☐ recruiting]  │
│  Pricing:                                                   │
│    Model:     [Freemium ▼]                                  │
│    Starting:  [€0/mo_____]                                  │
│                                                             │
│  [▼ Advanced: JSON Metadata]                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ { "integrations": [...], "key_features": [...] }    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Embedding Status: ● Embedded 2 hours ago                   │
│  [Re-embed Now]                                             │
└─────────────────────────────────────────────────────────────┘
```

### Features
- Form fields for common properties (validated)
- Collapsible JSON editor for metadata arrays/objects
- Embedding status shown at bottom with manual re-embed button
- Auto-save draft to localStorage
- Validation before save (required fields, JSON syntax)

## Embedding Stats & Testing Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│ Embedding Statistics                      [Refresh All ⟳]  │
├─────────────────────────────────────────────────────────────┤
│  Total Embeddings: 347          Last Full Sync: 2h ago      │
│  OpenAI API Cost (est): $0.02   Vector Index: Healthy ✓     │
├─────────────────────────────────────────────────────────────┤
│  By Content Type                                            │
│  ┌──────────────────┬───────┬──────────┬─────────────────┐ │
│  │ Type             │ Count │ Embedded │ Needs Update    │ │
│  ├──────────────────┼───────┼──────────┼─────────────────┤ │
│  │ Vendors          │  198  │  195 ✓   │  3 ⚠️           │ │
│  │ Opportunities    │  287  │  287 ✓   │  0              │ │
│  │ ...              │  ...  │  ...     │  ...            │ │
│  └──────────────────┴───────┴──────────┴─────────────────┘ │
│                                                             │
│  [View items needing update →]                              │
├─────────────────────────────────────────────────────────────┤
│  Similarity Testing                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Test query: [________________________]   [🔍 Search] │   │
│  │ Industry:   [All ▼]                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│  Results:                                                   │
│  ├─ 0.89  AI Voice Receptionist (opportunity, dental)      │
│  ├─ 0.84  Acuity Scheduling (vendor)                        │
│  └─ 0.81  Auto Ace - Voice AI (case_study)                  │
└─────────────────────────────────────────────────────────────┘
```

### Features
- Overview stats with health indicators
- Table showing embedded vs needs-update per type
- Quick link to filter list by "needs update"
- Similarity tester: enter query, see what vectors match with scores
- Bulk actions: "Re-embed All", "Re-embed Type", "Re-embed Outdated"

## API Endpoints

### List & Search
```
GET  /api/admin/knowledge/                    # List all (paginated, filterable)
GET  /api/admin/knowledge/search?q=...        # Semantic search across all types
GET  /api/admin/knowledge/{type}              # List by type
GET  /api/admin/knowledge/{type}/{id}         # Get single item
```

### CRUD
```
POST   /api/admin/knowledge/{type}            # Create new item
PUT    /api/admin/knowledge/{type}/{id}       # Update item
DELETE /api/admin/knowledge/{type}/{id}       # Delete item (and embedding)
```

### Embeddings
```
GET  /api/admin/knowledge/stats               # Embedding statistics
POST /api/admin/knowledge/embed/{type}/{id}   # Re-embed single item
POST /api/admin/knowledge/embed/all           # Re-embed all (async job)
POST /api/admin/knowledge/embed/outdated      # Re-embed only changed items
GET  /api/admin/knowledge/test-search         # Test similarity search
```

### Sync
```
POST /api/admin/knowledge/sync                # Sync JSON files to DB
GET  /api/admin/knowledge/sync/status         # Check sync status
```

## Data Flow

```
JSON Files (source of truth)
       ↓ sync
   Supabase DB (structured storage)
       ↓ embed
   pgvector (embeddings for search)
       ↓ query
   Agent retrieval (semantic matches)
```

## Authentication

Admin-only routes, protected by role check on JWT.

## Implementation Order

1. Backend API endpoints
2. Frontend page structure and routing
3. List view component
4. Editor component
5. Stats dashboard
6. Search functionality
7. Embedding management features

## Tech Stack

- **Backend**: FastAPI routes, Pydantic models
- **Frontend**: React + TypeScript + Tailwind
- **State**: React Query for server state
- **Editor**: Monaco editor for JSON (or simple textarea)
