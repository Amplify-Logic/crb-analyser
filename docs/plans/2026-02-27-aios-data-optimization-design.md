# AIOS Data & Architecture Optimization — Design

> Output of brainstorming session, 2026-02-27
> Goal: Align database, knowledge base, and report generation to recommend complete AI Operating Systems — not just tools.

---

## The Shift

**Before**: "Here are 3 software tools that could help with client onboarding"
**After**: "Here's your complete AI Operating System architecture — tools connected via MCP, orchestrated by Claude Code, with custom skills for your workflows, a context layer that makes AI act as YOUR business, and a dashboard to manage it all"

---

## The 7-Layer AIOS Framework

Every CRB report should now assess and recommend across all 7 layers:

```
┌─────────────────────────────────────────────────────────────┐
│  7. DASHBOARD        Single pane of glass                   │
│     Command center for your AIOS                            │
├─────────────────────────────────────────────────────────────┤
│  6. CONTEXT OS       Business identity + memory             │
│     CLAUDE.md, goals, preferences, style, processes         │
│     → AI acts AS you, not just FOR you                      │
├─────────────────────────────────────────────────────────────┤
│  5. SKILLS           Custom Claude Code skills              │
│     Reusable business process automations                   │
│     /generate-invoice, /onboard-client, /prep-meeting       │
├─────────────────────────────────────────────────────────────┤
│  4. DATA OS          Centralized business data              │
│     All tool data accessible, structured, queryable         │
├─────────────────────────────────────────────────────────────┤
│  3. INTELLIGENCE     Claude Code + Cowork                   │
│     Build & connect (Code) + Operate & act (Cowork)         │
├─────────────────────────────────────────────────────────────┤
│  2. CONNECTIONS      MCP servers + APIs + webhooks          │
│     The wiring between your tools                           │
├─────────────────────────────────────────────────────────────┤
│  1. STACK            Your existing tools                    │
│     CRM, billing, PM, email, calendar, ERP                  │
└─────────────────────────────────────────────────────────────┘
```

### Layer Descriptions

**Layer 1: Stack** — The tools they already use. We assess API readiness, data portability, MCP availability. Connect-first philosophy: keep what works.

**Layer 2: Connections** — MCP servers, native APIs, webhooks, automation platforms (Make/n8n) that wire tools together. The "nervous system" of the AIOS.

**Layer 3: Intelligence** — Claude Code is the "builder" — creates integrations, writes MCP connections, deploys agents, builds skills. Claude Cowork is the "operator" — handles web tasks, browser automation, computer use, real-time agentic work. Together they form the intelligence hub. Make/n8n/Zapier sit alongside for scheduled orchestration.

**Layer 4: Data OS** — Centralized business data pulled from all tools via MCP/API. A single source of truth the AI layer can query: client records, financial data, project status, communications. Could be Supabase, Notion, Airtable, or custom DB.

**Layer 5: Skills** — Custom Claude Code skills (slash commands) for business processes. Each skill encodes a workflow: `/onboard-client`, `/generate-invoice`, `/prep-meeting`, `/analyze-competitor`. These are the business's institutional knowledge made executable. Teaching clients to create and refine their own skills is a key recommendation.

**Layer 6: Context OS** — The business's identity layer that makes AI personal and reliable:
- `CLAUDE.md` equivalent — Business rules, brand voice, decision frameworks
- Memory files — Client preferences, project history, relationship context
- Goal tracking — Quarterly objectives, KPIs, strategic priorities
- Process documentation — How the business does things (style, standards, approvals)
- Team profiles — Who does what, expertise areas, communication preferences

This is what makes AI act AS the business rather than just being a generic assistant. Without context, AI gives generic answers. With a rich Context OS, AI produces work that's indistinguishable from the business's own output.

**Layer 7: Dashboard** — A centralized command center to manage the AIOS. Could be a Notion workspace, custom web app, or Claude Code project structure. Shows: active automations, data flows, recent AI actions, pending reviews, skill library, context health.

---

## Database Changes

### 1. Vendor Table Enrichment

Add columns to the existing `vendors` table:

```sql
-- Migration 021: Add AIOS readiness fields to vendors
ALTER TABLE vendors ADD COLUMN mcp_server_slug TEXT;
ALTER TABLE vendors ADD COLUMN mcp_server_maturity TEXT
  CHECK (mcp_server_maturity IN ('production', 'beta', 'community', 'none'));
ALTER TABLE vendors ADD COLUMN claude_code_compatible BOOLEAN DEFAULT false;
ALTER TABLE vendors ADD COLUMN agent_buildable BOOLEAN DEFAULT false;
ALTER TABLE vendors ADD COLUMN agent_patterns TEXT[];
ALTER TABLE vendors ADD COLUMN data_portability TEXT
  CHECK (data_portability IN ('full_export', 'api_access', 'limited_export', 'trapped'));
ALTER TABLE vendors ADD COLUMN aios_readiness_score INT CHECK (aios_readiness_score BETWEEN 1 AND 10);

-- Index for AIOS-ready vendor queries
CREATE INDEX idx_vendors_mcp ON vendors(mcp_server_slug) WHERE mcp_server_slug IS NOT NULL;
CREATE INDEX idx_vendors_aios_ready ON vendors(aios_readiness_score) WHERE aios_readiness_score IS NOT NULL;
CREATE INDEX idx_vendors_agent_patterns ON vendors USING GIN(agent_patterns);
```

**`aios_readiness_score` calculation** (computed on write):
```
score = 0
+2 if api_available AND api_type IN ('REST', 'GraphQL')
+2 if has_webhooks
+2 if mcp_server_slug IS NOT NULL AND mcp_server_maturity IN ('production', 'beta')
+1 if has_oauth
+1 if zapier_integration OR make_integration OR n8n_integration
+1 if data_portability IN ('full_export', 'api_access')
+1 if agent_buildable
= max 10
```

### 2. Vendor Integrations Table (Connection Graph)

```sql
-- Migration 022: Create vendor integration graph
CREATE TABLE vendor_integrations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  from_vendor_id UUID NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
  to_vendor_id UUID NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
  connection_type TEXT NOT NULL CHECK (connection_type IN (
    'mcp', 'native', 'api', 'webhook', 'zapier', 'make', 'n8n', 'custom'
  )),
  connection_quality TEXT NOT NULL CHECK (connection_quality IN (
    'production', 'reliable', 'basic', 'workaround'
  )),
  setup_complexity TEXT CHECK (setup_complexity IN ('easy', 'moderate', 'complex')),
  bidirectional BOOLEAN DEFAULT false,
  data_flows TEXT[],
  setup_time_hours INT,
  requires_claude_code BOOLEAN DEFAULT false,
  mcp_server_slug TEXT,
  verified_at TIMESTAMPTZ,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(from_vendor_id, to_vendor_id, connection_type)
);

CREATE INDEX idx_vi_from ON vendor_integrations(from_vendor_id);
CREATE INDEX idx_vi_to ON vendor_integrations(to_vendor_id);
CREATE INDEX idx_vi_type ON vendor_integrations(connection_type);
CREATE INDEX idx_vi_mcp ON vendor_integrations(mcp_server_slug) WHERE mcp_server_slug IS NOT NULL;

-- Enable public read access (same as vendors)
ALTER TABLE vendor_integrations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read vendor_integrations" ON vendor_integrations
  FOR SELECT USING (true);
CREATE POLICY "Service write vendor_integrations" ON vendor_integrations
  FOR ALL USING (auth.role() = 'service_role');
```

### 3. Workflow Templates Table (Index for KB JSON)

```sql
-- Migration 023: Create workflow templates index
CREATE TABLE workflow_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  industry TEXT NOT NULL,
  category TEXT NOT NULL,

  -- Matching criteria
  required_tools TEXT[],
  optional_tools TEXT[],
  required_capabilities TEXT[],
  pain_points_addressed TEXT[],

  -- AIOS layer mapping
  aios_layers_involved TEXT[] CHECK (aios_layers_involved <@ ARRAY[
    'stack', 'connections', 'intelligence', 'data_os', 'skills', 'context_os', 'dashboard'
  ]),

  -- Complexity & effort
  complexity TEXT CHECK (complexity IN ('low', 'medium', 'high')),
  build_time_hours INT,
  mcp_servers_used TEXT[],
  claude_code_involved BOOLEAN DEFAULT false,
  cowork_involved BOOLEAN DEFAULT false,

  -- Flow diagram data
  flow_diagram JSONB,

  -- Value
  estimated_monthly_value INT,
  estimated_time_saved_hours INT,

  -- Source tracking
  source_file TEXT,
  content_hash TEXT,
  synced_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_wt_industry ON workflow_templates(industry);
CREATE INDEX idx_wt_category ON workflow_templates(category);
CREATE INDEX idx_wt_required_tools ON workflow_templates USING GIN(required_tools);
CREATE INDEX idx_wt_pain_points ON workflow_templates USING GIN(pain_points_addressed);
CREATE INDEX idx_wt_mcp_servers ON workflow_templates USING GIN(mcp_servers_used);
CREATE INDEX idx_wt_aios_layers ON workflow_templates USING GIN(aios_layers_involved);

ALTER TABLE workflow_templates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read workflow_templates" ON workflow_templates
  FOR SELECT USING (true);
CREATE POLICY "Service write workflow_templates" ON workflow_templates
  FOR ALL USING (auth.role() = 'service_role');
```

### 4. Reports Table — AIOS Assessment Fields

```sql
-- Migration 024: Add AIOS assessment fields to reports
ALTER TABLE reports ADD COLUMN aios_maturity JSONB;
-- Structure: {
--   current_level: 'disconnected' | 'partially_connected' | 'automated' | 'ai_native',
--   layer_scores: { stack: 1-10, connections: 1-10, intelligence: 1-10,
--                   data_os: 1-10, skills: 1-10, context_os: 1-10, dashboard: 1-10 },
--   gaps: ['No MCP connections', 'No custom skills', 'No Context OS'],
--   target_level: 'automated',
--   path_to_target: ['Connect CRM via MCP', 'Build 3 core skills', 'Create CLAUDE.md']
-- }

ALTER TABLE reports ADD COLUMN readiness_profile JSONB;
-- Structure: {
--   infrastructure: 'digitized' | 'partial' | 'paper-based',
--   build_willingness: 'eager' | 'open' | 'prefers-turnkey',
--   ai_experience: 'none' | 'dabbled' | 'active-user',
--   stack_api_readiness: 'most-apis' | 'mixed' | 'mostly-closed',
--   urgency: 'this_week' | 'this_month' | 'this_quarter' | 'no_rush'
-- }
```

---

## Knowledge Base Enrichment

### 1. AIOS Layer Templates (New KB Section)

Create `backend/src/knowledge/aios/` with:

```
backend/src/knowledge/aios/
├── layers.json              # 7-layer framework definition + assessment criteria
├── context_os_templates.json # Templates for building Context OS per industry
├── skills_catalog.json       # Pre-built skill templates per industry
├── dashboard_patterns.json   # Dashboard architecture patterns
├── maturity_model.json       # AIOS maturity assessment rubric
└── education/
    ├── claude_code_guide.json    # How to use Claude Code for business
    ├── cowork_guide.json         # How to use Cowork for web tasks
    ├── skills_creation.json      # How to create custom skills
    ├── context_os_setup.json     # How to build your Context OS
    └── mcp_setup_guides.json     # Per-vendor MCP setup instructions
```

### 2. Context OS Templates per Industry

```json
{
  "professional-services": {
    "claude_md_template": {
      "sections": [
        {
          "title": "Business Identity",
          "description": "Who you are, what you do, your specialization",
          "example": "We are a mid-market accounting firm specializing in SME audit and tax advisory...",
          "prompts": ["What does your firm specialize in?", "What's your brand voice?"]
        },
        {
          "title": "Client Interaction Rules",
          "description": "How you communicate, tone, standards",
          "example": "Always use formal Dutch in client communications. Reference specific regulations by number...",
          "prompts": ["What tone do you use with clients?", "Any compliance rules for communications?"]
        },
        {
          "title": "Decision Framework",
          "description": "How decisions are made, approval chains",
          "example": "Engagements over EUR 10K require partner approval. New service offerings need...",
          "prompts": ["What are your approval thresholds?", "Who signs off on what?"]
        },
        {
          "title": "Process Standards",
          "description": "SOPs, quality standards, checklists",
          "example": "Every audit follows our 47-step checklist. Client deliverables are reviewed by...",
          "prompts": ["What are your key processes?", "What quality checks exist?"]
        }
      ],
      "memory_structure": {
        "clients/": "Per-client context (preferences, history, contacts)",
        "projects/": "Active project state and decisions",
        "knowledge/": "Industry-specific knowledge accumulated",
        "team/": "Team member profiles and expertise"
      }
    }
  }
}
```

### 3. Skills Catalog per Industry

```json
{
  "professional-services": {
    "skills": [
      {
        "slug": "onboard-client",
        "name": "/onboard-client",
        "description": "Automated client onboarding workflow",
        "what_it_does": "Creates client folder structure, generates engagement letter from template, sets up recurring meetings, sends welcome packet, creates tasks in PM tool",
        "tools_needed": ["CRM (via MCP)", "Document storage", "Calendar (via MCP)", "PM tool"],
        "build_time_hours": 4,
        "complexity": "moderate",
        "aios_layers": ["skills", "connections", "context_os"],
        "prerequisite_layers": ["stack", "connections"],
        "example_usage": "/onboard-client --name 'Acme BV' --type audit --partner jan",
        "estimated_time_saved_monthly_hours": 8
      },
      {
        "slug": "prep-meeting",
        "name": "/prep-meeting",
        "description": "Pre-meeting intelligence briefing",
        "what_it_does": "Pulls client context from memory, recent communications, open items, financial data. Generates a 1-page briefing with talking points and action items to review",
        "tools_needed": ["CRM (via MCP)", "Email (via MCP)", "Calendar", "Context OS"],
        "build_time_hours": 3,
        "complexity": "moderate",
        "aios_layers": ["skills", "context_os", "data_os"],
        "prerequisite_layers": ["context_os"],
        "example_usage": "/prep-meeting --client 'Acme BV' --date tomorrow",
        "estimated_time_saved_monthly_hours": 6
      }
    ]
  }
}
```

### 4. Education Content for Reports

Each report should include an "AIOS Education" section tailored to the client's maturity. For a client at "partially_connected" level:

```json
{
  "education_modules": [
    {
      "title": "Getting Started with Claude Code",
      "for_maturity": ["disconnected", "partially_connected"],
      "content": "Step-by-step guide to installing Claude Code, connecting your first MCP server, and running your first automation",
      "estimated_time": "30 minutes",
      "outcome": "First working automation between two of your tools"
    },
    {
      "title": "Building Your Context OS",
      "for_maturity": ["partially_connected", "automated"],
      "content": "How to create your business CLAUDE.md, set up memory files for client context, and teach AI your processes",
      "estimated_time": "2 hours",
      "outcome": "AI that knows your business identity, rules, and preferences"
    },
    {
      "title": "Creating Custom Skills",
      "for_maturity": ["automated", "ai_native"],
      "content": "How to turn your most repetitive workflows into reusable Claude Code skills your whole team can use",
      "estimated_time": "1 hour per skill",
      "outcome": "Team-wide productivity skills like /onboard-client, /prep-meeting"
    }
  ]
}
```

---

## Report Generation Changes

### New Skill: `system_architecture.py`

Runs AFTER findings + recommendations, generates the full AIOS blueprint:

**Input**: Client stack, all recommendations, matched workflow templates, readiness profile
**Output**: `SystemArchitecture` object with 7-layer assessment

```python
class SystemArchitecture(BaseModel):
    """Complete AIOS blueprint for the client"""

    # The visual diagram data
    layers: ArchitectureLayers
    connections: list[ArchitectureConnection]

    # AIOS maturity assessment (per layer)
    maturity: AIOSMaturity

    # Build sequence (phased implementation)
    build_phases: list[BuildPhase]

    # Education path (what to learn)
    education_path: list[EducationModule]

    # Recommended skills to build
    recommended_skills: list[SkillRecommendation]

    # Context OS starter template
    context_os_template: ContextOSTemplate

class ArchitectureLayers(BaseModel):
    stack: list[ArchNode]           # Layer 1: Existing tools
    connections: list[ArchNode]     # Layer 2: MCP/API/webhook connections
    intelligence: list[ArchNode]    # Layer 3: Claude Code + Cowork + automations
    data_os: list[ArchNode]         # Layer 4: Data centralization
    skills: list[ArchNode]          # Layer 5: Custom skills
    context_os: list[ArchNode]      # Layer 6: Business identity/memory
    dashboard: list[ArchNode]       # Layer 7: Management interface

class ArchNode(BaseModel):
    id: str
    name: str
    type: str  # existing_tool, mcp_server, claude_code, claude_cowork,
               # automation_platform, ai_agent, data_store, trigger,
               # skill, context_file, dashboard_view, output
    category: str
    status: str  # active, recommended, future
    linked_recommendation_id: str | None

class AIOSMaturity(BaseModel):
    current_level: str  # disconnected, partially_connected, automated, ai_native
    target_level: str
    layer_scores: dict[str, int]  # layer_name -> 1-10
    overall_score: int  # 1-100
    gaps: list[str]
    quick_wins: list[str]  # fastest path to next maturity level

class BuildPhase(BaseModel):
    phase: int
    title: str
    weeks: str
    focus_layers: list[str]  # which AIOS layers this phase addresses
    actions: list[str]
    nodes_added: list[str]
    connections_added: list[str]
    estimated_value_unlocked: int  # EUR/month

class SkillRecommendation(BaseModel):
    slug: str
    name: str
    description: str
    build_time_hours: int
    tools_needed: list[str]
    prerequisite_layers: list[str]
    estimated_time_saved_monthly: int  # hours

class ContextOSTemplate(BaseModel):
    claude_md_sections: list[dict]  # Starter CLAUDE.md template
    memory_structure: dict           # Recommended memory file organization
    initial_context_prompts: list[str]  # Questions to populate initial context
```

### Updated Report Generation Flow

```
1. Extract industry + existing stack
2. Build readiness profile (quiz/workshop data → readiness vocabulary)
3. Query vendor_integrations for client's stack connection paths
4. Query workflow_templates matching client's pain points + tools
5. Generate findings (with AIOS layer tagging)
6. Generate recommendations (3 AIOS options, using workflow templates)
7. Generate system architecture (7-layer blueprint)      ← NEW
8. Generate AIOS maturity assessment                     ← NEW
9. Generate education path based on maturity             ← NEW
10. Recommend custom skills based on findings             ← NEW
11. Generate Context OS starter template                  ← NEW
12. Generate roadmap (now aligned to AIOS build phases)
13. Generate value summary + verdict
14. Generate playbooks (now include skill-building tasks)
```

### Enriched Recommendation Options

The `connect_and_automate` option now includes:

```python
class AIOSConnectOption(BaseModel):
    approach: str
    build_time: str
    tools_used: list[str]
    mcp_servers: list[str]
    monthly_cost: str
    prerequisite: str | None
    diy_complexity: str
    automation_flow: AutomationFlow | None

    # NEW: AIOS layer enrichment
    aios_layers_touched: list[str]     # Which layers this builds
    skills_created: list[str] | None   # Skills that result from this
    context_needed: list[str] | None   # Context OS data needed
    education_prereq: str | None       # What to learn first
    cowork_tasks: list[str] | None     # What Cowork handles ongoing
```

---

## Vendor Data Enrichment Script

To populate the new vendor fields, create a one-time enrichment script that:

1. Cross-references `knowledge/platforms/mcp_ecosystem.json` with vendor slugs
2. Sets `mcp_server_slug` for vendors that have matching MCP servers
3. Calculates `aios_readiness_score` from existing fields
4. Sets `claude_code_compatible = true` for vendors with REST APIs
5. Populates `data_portability` based on `api_openness_score`

```python
# backend/scripts/enrich_vendors_aios.py
# Maps existing vendor data to new AIOS fields
# Run once, then maintain via vendor research agent
```

---

## Implementation Batches

### Batch 1: Database Migrations (no code changes)
- Migration 021: Vendor AIOS fields
- Migration 022: vendor_integrations table
- Migration 023: workflow_templates table
- Migration 024: Reports AIOS assessment fields
- Run migrations on Supabase

### Batch 2: Vendor Data Enrichment
- Create `enrich_vendors_aios.py` script
- Cross-reference MCP ecosystem JSON with vendor slugs
- Calculate aios_readiness_score for all vendors
- Populate vendor_integrations for known integration paths
- Run the enrichment

### Batch 3: Knowledge Base — AIOS Layer Content
- Create `backend/src/knowledge/aios/` directory
- Write `layers.json` (7-layer framework definition)
- Write `maturity_model.json` (assessment rubric)
- Write `context_os_templates.json` per industry
- Write `skills_catalog.json` per industry
- Write education content JSON files

### Batch 4: Workflow Template Sync
- Add `sync_workflow_templates()` to `knowledge/__init__.py`
- Enrich existing workflow JSON files with `aios_layers_involved`
- Create sync function that upserts JSON → DB
- Wire into app startup

### Batch 5: Report Generation — System Architecture Skill
- Create `system_architecture.py` skill
- Create Pydantic models for SystemArchitecture
- Wire into report_service.py generation flow
- Populate `report.system_architecture` and `report.aios_maturity`

### Batch 6: Report Generation — Education + Skills + Context
- Add education path generation to report flow
- Add skill recommendation generation
- Add Context OS template generation
- Update playbook generator to include skill-building tasks

### Batch 7: Readiness Profile + Adaptive Recommendations
- Build `_build_readiness_profile()` in report_service.py
- Update three_options.py prompt with readiness context
- Store readiness_profile on report
- Test with different client profiles

### Batch 8: Frontend — AIOS Blueprint Visualization
- (Handled by visual workflow builder terminal prompt)
- System architecture diagram
- AIOS maturity radar chart
- Education path display
- Skill recommendations display

---

## Success Criteria

A generated report should now:

1. Show a complete 7-layer AIOS architecture blueprint (visual)
2. Assess AIOS maturity per layer (1-10 scores)
3. Recommend specific Claude Code skills to build
4. Provide a Context OS starter template (CLAUDE.md + memory structure)
5. Include education modules appropriate to the client's maturity
6. Show integration paths between their specific tools (from vendor_integrations)
7. Recommend workflow templates that match their pain points + stack
8. Present build phases that progressively activate AIOS layers

---

## What This Changes About CRB's Positioning

**Before**: "We analyze your software stack and recommend tools"
**After**: "We architect your AI Operating System — the complete intelligence layer on top of your business"

The report becomes a **buildable specification**, not just advice. A client with Claude Code can take our report and literally start building their AIOS from the skills catalog, Context OS template, and MCP connection instructions we provide.

This is the moat. Generic AI tools give generic advice. We give architecture blueprints with executable specifications.
