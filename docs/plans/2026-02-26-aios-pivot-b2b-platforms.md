# AIOS Pivot + B2B Platforms Vertical Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Pivot CRB Analyser from a software recommendation engine to an AI Operating System (AIOS) architecture platform. Every report should lead with "connect what you have + build AI workflows" instead of "buy these tools." Also add `b2b-platforms` as the 4th primary industry vertical, seeded with Aquablu-like company data.

**Architecture:** The existing `four_options.py` (BUY/CONNECT/BUILD/HIRE) already has the right bones. We evolve it into the primary recommendation system with a Connect→Enhance→Replace hierarchy. The three_options.py (off_the_shelf/best_in_class/custom) becomes legacy/fallback. All opportunity JSON files, report generation, frontend components, and documentation shift to this AIOS framing.

**Tech Stack:** Python (FastAPI), React/TypeScript, JSON knowledge base files, Pydantic models

## CRB Context
- Affected user journey stage: ALL (Landing → Quiz → Report → Dashboard)
- Industries impacted: ALL (dental, ecommerce, professional-services, b2b-platforms, general)
- Reference docs to load during execution: `report-quality.md`, `vendor-management.md`, `frontend-development.md`, `FRAMEWORK.md`, `PRODUCT.md`, `STRATEGY.md`

## Rollback Plan
If this fails, revert by: `git revert` the merge commit. All changes are additive or in-place edits to existing files. No database migrations required.

---

## Batch 1: Documentation & Framework Pivot (Foundation)

Everything else depends on these files being updated first — they define the vocabulary, methodology, and quality criteria for all downstream work.

### Task 1.1: Update PRODUCT.md — Core Value Prop & Methodology

**Files:**
- Modify: `PRODUCT.md`

**Step 1: Update Product Overview section**

Replace the opening sections (lines 1-18) to reflect the AIOS vision:

```markdown
## Product Overview

**CRB Analyser** delivers AI-powered architecture blueprints that show businesses how to build their AI Operating System (AIOS) on top of their existing tools. We help companies get clarity on what to connect, what to automate, and what to build — without ripping out what already works.

### Core Promise

> "Connect what you have. Automate what slows you down. Build what doesn't exist."

We don't just list software recommendations. Our CRB framework analyzes your existing stack, identifies the gaps between systems, and architects an AI layer that connects everything — with specific workflows, agents, and integrations you can build this week.
```

**Step 2: Replace Three Options Model with AIOS Options**

Replace the "Three Options Model (3O)" section (around line 69-75) with:

```markdown
## AIOS Options Model

Every recommendation presents options prioritized by implementation speed and disruption:

| Priority | Option | When We Recommend |
|----------|--------|-------------------|
| 1st | **Connect & Automate** | Your tools work. Wire them together with AI workflows (MCP, APIs, Claude). |
| 2nd | **Enhance with AI** | Add an intelligence layer — agents, predictive workflows, command stations. |
| 3rd | **Targeted Upgrade** | One specific tool is a dead end. Replace ONLY that link in the chain. |

**Connect-first philosophy:** We never recommend replacing software unless the existing tool genuinely cannot be integrated (no API, fundamentally broken, blocking growth). Most businesses can get 80% of the value by connecting what they have.

> **Full AIOS methodology** → [FRAMEWORK.md](./FRAMEWORK.md#aios-options-model)
```

**Step 3: Update Connect vs Replace section (around line 92-111)**

Replace with:

```markdown
## Connect → Enhance → Replace Strategy

For every automation opportunity, we evaluate in this order:

| Strategy | Priority | When We Recommend | Example |
|----------|----------|-------------------|---------|
| **Connect** | 1st (default) | Tool works, just needs wiring | "Keep HubSpot + Exact, build Claude workflow to sync deals → invoices" |
| **Enhance** | 2nd | Need intelligence on top of existing data | "Build an AI agent that monitors IoT usage data and flags churn risk" |
| **Replace** | 3rd (last resort) | Tool is a dead end — no API, fundamentally broken | "Migrate from spreadsheets to Odoo for inventory tracking" |

### Decision Factors

| Factor | Favors Connect/Enhance | Favors Replace |
|--------|------------------------|----------------|
| Tool has API | Yes — wire it up | - |
| Tool fundamentally broken | - | Yes — it's blocking you |
| Team already trained | Yes — don't retrain | - |
| Data is trapped | - | Yes — if no export path |
| Budget constrained | Yes — build, don't buy | - |
| Technical capability | Yes — build workflows | Low — may need turnkey |
```

**Step 4: Update Positioning section (around line 389-403)**

```markdown
## Positioning

> "We help businesses build their AI Operating System — connecting what they have, automating what slows them down."

### The Promise
- You get an architecture blueprint specific to YOUR stack
- No generic "buy this tool" advice — we show what to build and connect
- Clear verdicts: Connect, Enhance, or Replace
- Enterprise-quality analysis at €147, not €15,000

### What We're NOT
- Not a software comparison site (we're an architecture firm)
- Not an AI vendor (we recommend, don't sell)
- Not generic (we know your industry and your stack)
```

**Step 5: Verify the file reads correctly**

Run: `head -20 PRODUCT.md`
Expected: Updated product overview with AIOS language

**Step 6: Commit**

```bash
git add PRODUCT.md
git commit -m "docs: pivot PRODUCT.md to AIOS architecture vision"
```

---

### Task 1.2: Update STRATEGY.md — Strategic Framing

**Files:**
- Modify: `STRATEGY.md`

**Step 1: Update Vision & Mission (lines 9-14)**

```markdown
## Vision & Mission

**Vision:** Become the go-to platform for businesses building their AI Operating System — connecting existing tools, automating workflows, and deploying AI agents.

**Mission:** Deliver architecture blueprints that show businesses exactly how to build AI workflows on their existing stack, at SMB pricing, in days not months.
```

**Step 2: Update Core Thesis (lines 18-25)**

```markdown
## Core Thesis

> "Most businesses don't need new software. They need an AI layer that connects what they already have."

We solve this by:
1. **Analyzing your existing stack** — what tools you have, where the gaps are, what's connected and what isn't
2. **Architecting your AIOS** — AI workflows, agents, and automations that bridge the gaps between your tools
3. **Providing a build plan** — specific, actionable steps you can execute this week with Claude Code, MCP servers, and API integrations
```

**Step 3: Update the Three Verticals table (line 49-55) to Four Verticals**

```markdown
### Four Verticals

| Vertical | Why It Could Win | Risk |
|----------|------------------|------|
| **Professional Services** | Compliance-focused, referral-driven, budget available | Slower sales cycles |
| **Dental** | Clear processes, tech-forward, high-ticket services | Niche community |
| **E-commerce** | Volume market, automation-hungry, measurable ROI | Crowded space |
| **B2B Platforms** | Hardware-to-platform companies scaling lean, complex integrations | Niche but high-value |
```

**Step 4: Add B2B Platforms vertical section after E-commerce (after line 230)**

```markdown
### Vertical 4: B2B Platforms

**Slug:** `b2b-platforms`

**Customer Profile:**
- Hardware-to-platform companies (IoT devices, connected products, subscription hardware)
- 20-200 employees, scaling rapidly with lean teams
- Complex stacks: custom IoT + ERP + CRM + field service
- Already AI-forward, looking for architecture help at scale

**Key Pain Points:**
| Pain Point | Impact |
|------------|--------|
| System Integration Gaps | Manual data sync between CRM, ERP, IoT, billing |
| Scaling Operations | Processes that worked at 20 people break at 100 |
| Partner Channel Management | Onboarding and managing distributors across countries |
| Field Service Coordination | Scheduling, parts, technician routing at scale |

**Software Ecosystem:**
| Category | Key Vendors |
|----------|-------------|
| IoT Platform | Azure IoT Hub, AWS IoT Core, custom |
| ERP | Exact Online, NetSuite, Odoo |
| CRM | HubSpot, Salesforce |
| Field Service | Salesforce FSL, ServiceMax, Zuper |
| Subscription Billing | Chargebee, Zuora, Stripe Billing |
| Partner Management | Impartner, PartnerStack |
```

**Step 5: Commit**

```bash
git add STRATEGY.md
git commit -m "docs: pivot STRATEGY.md to AIOS vision, add b2b-platforms vertical"
```

---

### Task 1.3: Update CLAUDE.md — Development Guide

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update CRB Analysis Framework section (around line 171-180)**

Replace:
```markdown
## CRB Analysis Framework

> **Full framework details** → [PRODUCT.md](./PRODUCT.md) and [FRAMEWORK.md](./FRAMEWORK.md)

Core principle: **"Connect what you have. Automate what slows you down. Build what doesn't exist."**

- **6 Costs**: Financial, Time, Opportunity, Complexity, Risk, Brand/Trust
- **4 Benefits**: Financial, Time, Strategic, Quality
- **NET SCORE** = Benefit - Cost - (Risk ÷ 10)
- **AIOS Options**: Connect & Automate → Enhance with AI → Targeted Upgrade (replace only as last resort)
- **Connect-First**: Never recommend replacing software unless the existing tool is genuinely a dead end (no API, fundamentally broken)

When working on report generation, load `.claude/reference/report-quality.md`.
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md CRB framework to AIOS options model"
```

---

### Task 1.4: Update report-quality.md — Quality Criteria

**Files:**
- Modify: `.claude/reference/report-quality.md`

**Step 1: Update Three Options Format section (lines 84-101)**

Replace with:

```markdown
## AIOS Options Format

Every recommendation presents options in connect-first priority:

```
Option A: [Connect & Automate]   NET: +5.2  ◀ RECOMMENDED
Option B: [Enhance with AI]      NET: +3.8
Option C: [Targeted Upgrade]     NET: +1.5

WHY OPTION A WINS:
✓ Uses your existing HubSpot + Exact stack
✓ Claude workflow ships in 8 hours
✓ Zero disruption, zero migration

TRADE-OFFS:
△ Requires API access to both tools
△ Custom workflow needs maintenance
```

### Connect-First Rules
1. **Always lead with Connect** — show how to wire existing tools with AI
2. **Enhance second** — add AI agents/workflows on top of existing data
3. **Replace ONLY when** — tool has no API, is fundamentally broken, or data is trapped
4. **Never recommend Replace** just because a "better" tool exists
5. **Include build time** — "Ship in 8 hours with Claude Code" not "6-month migration"
```

**Step 2: Add AIOS-specific anti-slop rules**

Add to the anti-slop table:

```markdown
| "Consider migrating to X" | "Connect HubSpot to Exact with a Claude workflow that syncs deals → invoices" |
| "We recommend Tool X" | "Build an AI agent that monitors your IoT data and flags churn risk" |
| "Best-in-class solution" | "Wire your existing CRM + ERP + IoT data into a unified context layer" |
```

**Step 3: Update Quality Checklist**

Add to checklist:
```markdown
- [ ] First recommendation is CONNECT, not REPLACE
- [ ] Every finding explains what can be built on existing stack
- [ ] Custom build estimates include Claude Code hours and MCP servers needed
- [ ] "Replace" option only appears when Connect is genuinely impossible (document why)
```

**Step 4: Commit**

```bash
git add .claude/reference/report-quality.md
git commit -m "docs: update report quality criteria for AIOS connect-first model"
```

---

## Batch 2: Knowledge Base Schema Evolution (All Verticals)

### Task 2.1: Restructure Ecommerce opportunities.json

**Files:**
- Modify: `backend/src/knowledge/ecommerce/opportunities.json`

**Step 1: Update the options structure for each opportunity**

For each opportunity in the `ai_opportunities` array, restructure the `options` field from:

```json
{
  "options": {
    "off_the_shelf": { "tools": [...], "cost_range": "...", "pros": [...], "cons": [...] },
    "best_in_class": { "tools": [...], "cost_range": "...", "pros": [...], "cons": [...] },
    "custom_solution": { "approach": "...", "cost_range": "...", "pros": [...], "cons": [...] },
    "claude_code_path": { "feasible": true, "estimated_hours": 12, "mcp_servers": [...], "approach": "...", "complexity": "medium" }
  }
}
```

To:

```json
{
  "options": {
    "connect_and_automate": {
      "approach": "Build a Claude workflow that connects Shopify order data to your existing support tool, auto-responding to WISMO and return status queries via API",
      "build_time": "8-12 hours",
      "tools_used": ["Claude Code", "Shopify MCP", "existing support tool API"],
      "mcp_servers": ["shopify-mcp"],
      "monthly_cost": "€50-100 (API usage)",
      "pros": ["Uses your existing stack", "Ships this week", "Fully customized to your workflow"],
      "cons": ["Requires API access", "Needs maintenance"]
    },
    "enhance_with_ai": {
      "approach": "Deploy AI agent that learns from ticket history, handles tier-1 autonomously, drafts responses for tier-2, provides CS team with customer health dashboard",
      "build_time": "2-3 weeks",
      "tools_used": ["Claude API", "Your support tool", "Analytics dashboard"],
      "monthly_cost": "€200-400",
      "pros": ["Autonomous handling of routine queries", "Learns and improves", "Team productivity boost"],
      "cons": ["Needs training data", "Gradual rollout required"]
    },
    "targeted_upgrade": {
      "when_needed": "Only if your current support tool has no API or is fundamentally broken",
      "tools": ["Gorgias Automate", "Intercom Fin"],
      "cost_range": "€200-500/month",
      "migration_time": "4-6 weeks",
      "pros": ["Pre-built AI support", "Quick setup"],
      "cons": ["Monthly SaaS cost", "Locked into vendor", "Less customization"]
    }
  },
  "our_recommendation": "connect_and_automate",
  "recommendation_rationale": "Your Shopify store already has full API access. A Claude workflow connecting order data to your support tool ships in days, not weeks, and costs a fraction of a SaaS subscription."
}
```

**Important:** Do this for ALL opportunities in the file. Keep `agent_opportunity`, `roi_example`, and `jevons_effect` fields unchanged. The `claude_code_path` is now absorbed into `connect_and_automate`.

**Step 2: Verify JSON is valid**

Run: `python -c "import json; json.load(open('backend/src/knowledge/ecommerce/opportunities.json'))"`
Expected: No error

**Step 3: Commit**

```bash
git add backend/src/knowledge/ecommerce/opportunities.json
git commit -m "feat: restructure ecommerce opportunities to AIOS connect-first model"
```

---

### Task 2.2: Restructure Dental opportunities.json

**Files:**
- Modify: `backend/src/knowledge/dental/opportunities.json`

Same restructuring pattern as Task 2.1. For dental, examples:

- **Patient no-show reminders:** Connect → "Build Claude workflow that pulls appointment data from your practice management API and sends personalized SMS reminders." Enhance → "AI agent that learns optimal reminder timing per patient." Replace → "Only if your PMS has no API."
- **Insurance verification:** Connect → "Build workflow connecting PMS + insurance portals via API." Enhance → "AI agent that pre-verifies and flags issues." Replace → "Only if using paper-based verification."

Follow the same `connect_and_automate` / `enhance_with_ai` / `targeted_upgrade` schema from Task 2.1.

**Step 1: Restructure all opportunities**
**Step 2: Validate JSON:** `python -c "import json; json.load(open('backend/src/knowledge/dental/opportunities.json'))"`
**Step 3: Commit**

```bash
git add backend/src/knowledge/dental/opportunities.json
git commit -m "feat: restructure dental opportunities to AIOS connect-first model"
```

---

### Task 2.3: Restructure Professional Services opportunities.json

**Files:**
- Modify: `backend/src/knowledge/professional-services/opportunities.json`

Same pattern. For professional services:

- **Client intake:** Connect → "Build Claude workflow connecting website form → CRM → practice management." Enhance → "AI agent that pre-qualifies leads and routes to right partner." Replace → "Only if using email-only intake."
- **Time tracking:** Connect → "Build workflow syncing calendar + project management → billing." Enhance → "AI that auto-categorizes time entries and catches revenue leakage." Replace → "Only if on spreadsheets."

**Step 1: Restructure all opportunities**
**Step 2: Validate JSON**
**Step 3: Commit**

```bash
git add backend/src/knowledge/professional-services/opportunities.json
git commit -m "feat: restructure prof-services opportunities to AIOS connect-first model"
```

---

### Task 2.4: Add `workflows.json` template to each industry

**Files:**
- Create: `backend/src/knowledge/ecommerce/workflows.json`
- Create: `backend/src/knowledge/dental/workflows.json`
- Create: `backend/src/knowledge/professional-services/workflows.json`

Each file contains pre-built AI workflow templates specific to the industry. Schema:

```json
{
  "industry": "ecommerce",
  "description": "Pre-built AI workflow templates for e-commerce businesses",
  "workflows": [
    {
      "id": "order-status-automation",
      "name": "Order Status Auto-Response",
      "description": "Connect Shopify order data to support tool — auto-respond to WISMO queries",
      "trigger": "Customer asks 'where is my order'",
      "connects": ["shopify", "support_tool"],
      "mcp_servers": ["shopify-mcp"],
      "build_time_hours": 4,
      "complexity": "low",
      "steps": [
        "Pull order status from Shopify API using order ID or email",
        "Format tracking info into customer-friendly response",
        "Auto-reply via support tool API or email",
        "Log interaction for CS team visibility"
      ],
      "prerequisites": ["Shopify store with API access", "Support tool with API (Gorgias, Zendesk, or email)"],
      "estimated_monthly_value": 800
    }
  ]
}
```

Create 3-5 workflows per industry based on the most common pain points.

**Step 1: Create ecommerce/workflows.json**
**Step 2: Create dental/workflows.json**
**Step 3: Create professional-services/workflows.json**
**Step 4: Validate all three:** `python -c "import json; [json.load(open(f'backend/src/knowledge/{i}/workflows.json')) for i in ['ecommerce', 'dental', 'professional-services']]"`
**Step 5: Commit**

```bash
git add backend/src/knowledge/*/workflows.json
git commit -m "feat: add AI workflow templates for all primary industries"
```

---

## Batch 3: B2B Platforms Vertical (New Industry)

### Task 3.1: Create b2b-platforms knowledge base files

**Files:**
- Create: `backend/src/knowledge/b2b-platforms/processes.json`
- Create: `backend/src/knowledge/b2b-platforms/opportunities.json`
- Create: `backend/src/knowledge/b2b-platforms/benchmarks.json`
- Create: `backend/src/knowledge/b2b-platforms/vendors.json`
- Create: `backend/src/knowledge/b2b-platforms/workflows.json`

**Step 1: Create processes.json**

Follow the schema from `ecommerce/processes.json`. Include these 7 processes:

1. `b2b-sales-crm` — B2B Sales & CRM Pipeline
2. `partner-channel-management` — Partner/Channel Management
3. `field-service-logistics` — Field Service & Logistics
4. `subscription-billing` — Subscription Billing & Revenue Ops
5. `iot-device-management` — IoT Device Management
6. `customer-success` — Customer Success & Retention
7. `marketing-lead-gen` — Marketing & Lead Generation

Each process should have `id`, `name`, `description`, `typical_time_spent`, `pain_level`, `automation_potential`, and `ai_opportunities` array following the existing schema.

**Step 2: Create opportunities.json**

Use the NEW `connect_and_automate` / `enhance_with_ai` / `targeted_upgrade` schema from Task 2.1. Include 10 opportunities:

1. `cross-system-sync-engine` — Wire HubSpot ↔ ERP ↔ IoT ↔ billing with AI workflows
2. `predictive-parts-inventory` — IoT usage data → forecast consumables → auto-reorder
3. `smart-technician-routing` — AI-optimized field service scheduling
4. `automated-installation-onboarding` — Partner submits install → auto-provision → auto-bill
5. `usage-billing-automation` — IoT drink data → auto-generate invoices per contract
6. `partner-performance-dashboard` — Aggregate partner data from existing sources
7. `predictive-churn-detection` — Usage drops → flag at-risk accounts
8. `automated-cs-playbooks` — Low usage → nudge, high usage → upsell, alert → outreach
9. `self-service-partner-portal` — Partners handle provisioning, reporting, billing queries
10. `bundle-optimization-intelligence` — Model optimal pricing tiers from usage data, maximize margin
11. `institutional-knowledge-capture` — Extract processes from Notion/Slack into structured playbooks

For each, lead with `connect_and_automate` showing how to build on existing HubSpot + ERP + custom IoT stack.

**Step 3: Create benchmarks.json**

Follow `ecommerce/benchmarks.json` schema. Include platform business KPIs:
- Net Revenue Retention (NRR), device uptime %, cost per install, partner activation rate, CAC, usage vs contracted tier, churn rate, support tickets per device, revenue per employee

Source benchmarks from industry reports. Mark as `"status": "UNVERIFIED"` where sources aren't confirmed.

**Step 4: Create vendors.json**

Follow `ecommerce/vendors.json` schema with categories:
- IoT Platform (Azure IoT Hub, AWS IoT Core)
- Field Service (Salesforce FSL, ServiceMax, Zuper)
- Subscription Billing (Chargebee, Zuora, Stripe Billing)
- Partner Management (Impartner, PartnerStack)
- Supply Chain (Katana, inFlow)
- Customer Success (Gainsight, Vitally, Planhat)

**Step 5: Create workflows.json**

5 workflow templates specific to B2B platform companies:
1. CRM-to-ERP deal sync
2. IoT usage alert → CS notification
3. Partner install request → auto-provision
4. Usage data → invoice generation
5. Device health monitoring → maintenance ticket

**Step 6: Validate all files**

Run: `python -c "import json; [json.load(open(f'backend/src/knowledge/b2b-platforms/{f}.json')) for f in ['processes', 'opportunities', 'benchmarks', 'vendors', 'workflows']]"`

**Step 7: Commit**

```bash
git add backend/src/knowledge/b2b-platforms/
git commit -m "feat: add b2b-platforms knowledge base with AIOS-first opportunities"
```

---

### Task 3.2: Create b2b-platforms quiz questions

**Files:**
- Create: `backend/src/knowledge/industry_questions/b2b_platforms.json`

**Step 1: Create quiz questions file**

Follow schema from `industry_questions/dental.json`. Include 8-10 questions:

1. Device fleet size (number)
2. Countries of operation (number)
3. Partner/distributor count (number)
4. Current IoT platform (text/choice)
5. Biggest operational bottleneck (choice: supply chain / field service / billing / CS)
6. Integration pain level — how much manual data sync between systems (1-10)
7. Technical capability level (choice: build custom / use automation tools / non-technical)
8. Monthly subscription revenue model (choice: fixed / usage-based / hybrid)
9. Current CRM and ERP tools (text)
10. Scaling ambition — headcount target vs revenue target

**Step 2: Validate JSON**
**Step 3: Commit**

```bash
git add backend/src/knowledge/industry_questions/b2b_platforms.json
git commit -m "feat: add adaptive quiz questions for b2b-platforms vertical"
```

---

### Task 3.3: Register b2b-platforms in knowledge/__init__.py

**Files:**
- Modify: `backend/src/knowledge/__init__.py`

**Step 1: Add industry mapping entries (after line 91)**

```python
    # B2B Platforms (Hardware-to-Platform, IoT, Connected Devices)
    "b2b-platforms": "b2b-platforms",
    "b2b-platform": "b2b-platforms",
    "b2b_platforms": "b2b-platforms",
    "b2b platforms": "b2b-platforms",
    "iot": "b2b-platforms",
    "iot-platform": "b2b-platforms",
    "iot_platform": "b2b-platforms",
    "hardware-platform": "b2b-platforms",
    "hardware_platform": "b2b-platforms",
    "connected-devices": "b2b-platforms",
    "connected_devices": "b2b-platforms",
    "device-platform": "b2b-platforms",
    "saas-hardware": "b2b-platforms",
    "water-tech": "b2b-platforms",
    "cleantech": "b2b-platforms",
    "hydration": "b2b-platforms",
```

**Step 2: Add to PRIMARY_INDUSTRIES (line 184-188)**

```python
PRIMARY_INDUSTRIES = [
    "professional-services",
    "dental",
    "ecommerce",
    "b2b-platforms",
]
```

**Step 3: Move home-services and marketing-agencies to LEGACY**

Remove `"home-services"` from SECONDARY_INDUSTRIES, move to LEGACY_INDUSTRIES.
`"marketing-agencies"` is already in LEGACY.

**Step 4: Add `load_industry_workflows` function**

After the `load_industry_data` function (around line 262), add:

```python
def load_industry_workflows(industry: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load AI workflow templates for an industry.

    Args:
        industry: Industry name (will be normalized)

    Returns:
        List of workflow templates or None if not found
    """
    normalized = normalize_industry(industry)
    file_path = KNOWLEDGE_BASE_PATH / normalized / "workflows.json"
    data = _load_json_file(file_path)
    return data.get("workflows", []) if data else None
```

**Step 5: Update `get_industry_context` to include workflows (around line 510-536)**

Add after `context["vendors"]`:
```python
        "workflows": load_industry_workflows(industry),
```

**Step 6: Run existing tests**

Run: `cd backend && python -m pytest tests/ -v -k "knowledge or industry" --no-header`
Expected: All pass

**Step 7: Commit**

```bash
git add backend/src/knowledge/__init__.py
git commit -m "feat: register b2b-platforms as primary industry, add workflow loading"
```

---

### Task 3.4: Create b2b-platforms seed file

**Files:**
- Create: `backend/src/cli/seeds/b2b-platforms.json`

**Step 1: Create seed file**

Follow schema from `seeds/ecommerce.json`. Seed company: "HydraFlow" — a smart water dispenser company (anonymized Aquablu).

```json
{
  "industry": "b2b-platforms",
  "description": "B2B hardware-to-platform businesses for CRB report generation",
  "tiers": {
    "scaling": {
      "description": "40-100 staff, IoT fleet + partner channel, custom apps + ERP + CRM",
      "defaults": {
        "budget": 5000,
        "hourly_cost": 55,
        "pain_points": ["system integration gaps", "scaling operations", "partner management complexity", "field service coordination"]
      }
    },
    "growth": {
      "description": "100-250 staff, multi-country operations, platform revenue model",
      "defaults": {
        "budget": 15000,
        "hourly_cost": 65,
        "pain_points": ["data silos across countries", "manual billing reconciliation", "partner onboarding bottleneck", "knowledge stuck in people's heads"]
      }
    }
  },
  "seeds": [
    {
      "name": "HydraFlow",
      "website": "https://www.hydraflow.example.com",
      "country": "NL",
      "profile": {
        "tier": "scaling",
        "staff_size": "51-100",
        "device_fleet_size": 2500,
        "countries": 16,
        "partner_count": 45,
        "revenue_model": "pay-per-use subscription",
        "has_custom_iot": true,
        "has_custom_billing": true,
        "has_custom_field_service_app": true,
        "current_tools": ["hubspot", "exact-online", "custom-iot-platform", "asana", "notion", "apollo", "claude-teams"],
        "pain_points": ["manual data sync between HubSpot and Exact", "supply chain scaling", "partner onboarding bottleneck", "CS scaling beyond manual account management"]
      },
      "workshop_transcript": [
        {"role": "assistant", "content": "Tell me about HydraFlow — what do you sell and who are your customers?"},
        {"role": "user", "content": "We make smart water dispensers for offices and hotels. Each dispenser is IoT-connected, tracks usage, and serves still, sparkling, and flavored water. We operate in 16 European countries through a partner channel — about 45 distributors. Revenue model is pay-per-drink: customers pay a monthly fee for a tier of drinks, and our margins are better when they buy a tier above their actual usage."},
        {"role": "assistant", "content": "Walk me through your tech stack — what systems do you use day to day?"},
        {"role": "user", "content": "HubSpot for CRM and CS tracking, Exact Online for finance, Apollo for outbound sales. Our IoT platform is fully custom — devices connect via KPN network to our databases, and we built AURA, our fleet management platform, for device monitoring and partner access. We also built a custom field service app with AI for technician routing. Billing is custom too — tracks per-drink usage and generates invoices based on contracted tiers. We use Asana for project management and Notion as our knowledge base. We're heavy Claude users — Teams plan."},
        {"role": "assistant", "content": "Where are the biggest bottlenecks as you scale?"},
        {"role": "user", "content": "Three areas. First, supply chain and ops — coordinating parts inventory, installations, and maintenance across 16 countries with growing device fleet. Second, customer success — we have amazing usage data but CS is still mostly manual. We know when usage drops but we don't act on it systematically. Third, the gap between systems — HubSpot doesn't talk to Exact, which doesn't talk to our IoT data. So much manual reconciliation. A deal closes in HubSpot but someone has to manually create the invoice in Exact, provision the device in AURA, and schedule the installation."},
        {"role": "assistant", "content": "You mentioned your margins are better when customers buy above their usage. How does that pricing work?"},
        {"role": "user", "content": "We have tiered drink bundles — Small (500 drinks), Medium (1000), Large (2000), Enterprise (5000+). We try to sell them into the tier above what they'd naturally use. Margins are significantly better on the excess. The challenge is we don't systematically track usage vs tier across the fleet to know who to upsell, who's at risk of downgrading, and who might churn because they're paying but not really using the dispenser."},
        {"role": "assistant", "content": "What's the team size and where's the growth heading?"},
        {"role": "user", "content": "60 people now. Goal is €100M revenue with fewer than 100 employees by 2028. That means we need to 10x revenue without 10x-ing headcount. Everything that's manual today has to be automated or AI-driven. We're already AI-forward — built custom apps, use Claude daily — but we need the architecture to connect it all. Right now it's held together with human glue."}
      ]
    }
  ]
}
```

**Step 2: Validate JSON**
**Step 3: Commit**

```bash
git add backend/src/cli/seeds/b2b-platforms.json
git commit -m "feat: add HydraFlow seed for b2b-platforms report generation"
```

---

### Task 3.5: Create b2b-platforms expertise store

**Files:**
- Create: `backend/src/expertise/data/industries/b2b-platforms.json`

**Step 1: Create expertise file**

Follow schema from `expertise/data/industries/dental.json`. Pre-seed with baseline data from brainstorming:

```json
{
  "industry": "b2b-platforms",
  "last_updated": "2026-02-26T12:00:00Z",
  "total_analyses": 1,
  "confidence": "low",
  "pain_points": {
    "system_integration_gaps": {
      "name": "Manual data sync between CRM, ERP, IoT, and billing systems",
      "frequency": 1,
      "avg_impact": "very high",
      "typical_causes": ["No native integrations between custom and SaaS tools", "Rapid growth outpacing system architecture"],
      "effective_solutions": ["Claude workflow connecting APIs", "MCP servers for each system", "Central context layer"],
      "last_seen": "2026-02-26T00:00:00Z"
    },
    "scaling_operations": {
      "name": "Processes that worked at 20 people breaking at 100",
      "frequency": 1,
      "avg_impact": "high",
      "typical_causes": ["Knowledge in people's heads", "Manual handoffs between teams", "No documented playbooks"],
      "effective_solutions": ["AI-powered knowledge capture", "Automated workflow triggers", "Self-service partner portal"],
      "last_seen": "2026-02-26T00:00:00Z"
    },
    "cs_scaling": {
      "name": "Customer success beyond manual account management",
      "frequency": 1,
      "avg_impact": "high",
      "typical_causes": ["Usage data exists but isn't acted on", "No predictive churn detection", "CS team linearly scaling with accounts"],
      "effective_solutions": ["Usage-based health scoring", "Automated CS playbooks", "Predictive churn AI agent"],
      "last_seen": "2026-02-26T00:00:00Z"
    }
  },
  "processes": {},
  "effective_patterns": [
    "Connect-first approach: wire existing tools before recommending replacements",
    "Custom IoT + custom billing already in place — build AI layer on top",
    "Partner channel is key revenue driver — automate onboarding and self-service"
  ],
  "anti_patterns": [
    "Recommending enterprise ERP migration to companies with working custom systems",
    "Suggesting generic CRM replacement when HubSpot + custom integrations work"
  ],
  "size_specific": {},
  "avg_ai_readiness": 72.0,
  "avg_potential_savings": 120000.0,
  "common_tech_stacks": ["HubSpot + Exact Online + Custom IoT + Custom Billing"]
}
```

**Step 2: Commit**

```bash
git add backend/src/expertise/data/industries/b2b-platforms.json
git commit -m "feat: add b2b-platforms expertise store with baseline data"
```

---

### Task 3.6: Populate general expertise store

**Files:**
- Modify: `backend/src/expertise/data/industries/general.json`

**Step 1: Read current file**

Run: `cat backend/src/expertise/data/industries/general.json`

**Step 2: Populate with solid B2B baseline data**

Add common pain points, processes, and patterns that apply to ANY B2B business:
- CRM data quality issues
- Manual reporting / data aggregation
- Email overload / communication silos
- Onboarding friction (employees and customers)
- Tool sprawl without integration

Add effective patterns:
- Connect existing tools before replacing
- Start with highest-ROI automation first
- Build on tools the team already knows
- Automate data sync between core systems

**Step 3: Commit**

```bash
git add backend/src/expertise/data/industries/general.json
git commit -m "feat: populate general expertise store with B2B baseline patterns"
```

---

## Batch 4: Backend — Recommendation System Evolution

### Task 4.1: Update the Three Options skill to support new schema

**Files:**
- Modify: `backend/src/skills/report-generation/three_options.py`

**Step 1: Read the full file**

Read: `backend/src/skills/report-generation/three_options.py`

**Step 2: Add support for new option keys**

The skill's LLM prompt currently asks for `off_the_shelf`, `best_in_class`, `custom_solution`. Update the prompt to request the AIOS options instead:

Change the prompt template to ask for:
- `connect_and_automate` — How to wire existing tools with AI workflows
- `enhance_with_ai` — AI agents/intelligence layer on top
- `targeted_upgrade` — Replace only if existing tool is a dead end

Keep backward compatibility: if the LLM returns old keys, map them:
```python
OPTION_KEY_MAPPING = {
    "off_the_shelf": "targeted_upgrade",
    "best_in_class": "enhance_with_ai",
    "custom_solution": "connect_and_automate",
}
```

**Step 3: Update the recommendation rationale prompt**

The prompt should emphasize:
- Lead with what can be built on existing stack
- Only suggest replacement when tool genuinely blocks integration
- Include Claude Code hours and MCP servers in connect option

**Step 4: Run tests**

Run: `cd backend && python -m pytest tests/ -v -k "three_options or recommendation" --no-header`

**Step 5: Commit**

```bash
git add backend/src/skills/report-generation/three_options.py
git commit -m "feat: update ThreeOptionsSkill to AIOS connect-first model"
```

---

### Task 4.2: Update report_service.py recommendation generation

**Files:**
- Modify: `backend/src/services/report_service.py`

**Step 1: Read recommendation-related sections**

Read lines around: 1837-1850 (ThreeOptionsSkill usage), 2304-2460 (fallback prompt), 2760-2780 (option processing)

**Step 2: Update the fallback recommendation prompt (around line 2304)**

Replace the `THREE OPTIONS PATTERN` prompt text with the new AIOS options framing:

```python
prompt = f"""Based on these findings, generate detailed recommendations with the AIOS OPTIONS pattern.

AIOS OPTIONS PATTERN (REQUIRED - Connect-First Philosophy)
==========================================================

For EACH recommendation, provide ALL THREE options in this priority:

1. connect_and_automate (ALWAYS first choice): How to wire existing tools together with AI workflows.
   Include: Claude Code build time, MCP servers needed, which existing tools are connected.

2. enhance_with_ai: Add an AI intelligence layer on top of existing data/workflows.
   Include: What the AI agent does, what data it needs, deployment timeline.

3. targeted_upgrade: Replace a specific tool ONLY if it genuinely blocks integration.
   Include: Why existing tool is a dead end (no API, broken, data trapped), what to replace with.

CRITICAL RULES:
- our_recommendation MUST be "connect_and_automate" unless the existing tool literally has no API
- NEVER recommend "targeted_upgrade" just because a "better" tool exists
- Every connect_and_automate option MUST include build_time and tools_used
- Include MCP servers where applicable
"""
```

**Step 3: Update option validation (around line 2437-2456)**

Change required keys from `["off_the_shelf", "best_in_class", "custom_solution"]` to `["connect_and_automate", "enhance_with_ai", "targeted_upgrade"]`.

Add backward compatibility: if old keys are found, map them using `OPTION_KEY_MAPPING`.

**Step 4: Update vendor matching (around line 2264)**

Change `for option_key in ["off_the_shelf", "best_in_class"]:` to include new keys and map them.

**Step 5: Run tests**

Run: `cd backend && python -m pytest tests/ -v -k "report" --no-header`

**Step 6: Commit**

```bash
git add backend/src/services/report_service.py
git commit -m "feat: update report generation to AIOS connect-first recommendations"
```

---

### Task 4.3: Update teaser_service.py

**Files:**
- Modify: `backend/src/services/teaser_service.py`

**Step 1: Read the file to find teaser generation prompts**
**Step 2: Update teaser framing**

The teaser preview (pre-payment) should show:
- "Here's your AIOS architecture blueprint" not "Here are tool recommendations"
- Top findings framed as "what you can build this week" not "what to buy"
- Tease the full connect → enhance → replace analysis

**Step 3: Run tests**
**Step 4: Commit**

```bash
git add backend/src/services/teaser_service.py
git commit -m "feat: update teaser to AIOS architecture blueprint framing"
```

---

### Task 4.4: Update playbook_generator.py

**Files:**
- Modify: `backend/src/services/playbook_generator.py`

**Step 1: Read the file**
**Step 2: Update playbook structure**

Playbooks should follow the AIOS implementation timeline:
- Week 1-2: Connect (wire existing tools with API integrations and Claude workflows)
- Week 3-4: Enhance (deploy first AI agents on connected data)
- Month 2+: Command Station (dashboards, monitoring, human oversight)
- Only if needed: Targeted upgrades for dead-end tools

**Step 3: Run tests**
**Step 4: Commit**

```bash
git add backend/src/services/playbook_generator.py
git commit -m "feat: update playbook generator to AIOS implementation timeline"
```

---

## Batch 5: Frontend — Report Components

### Task 5.1: Update NumberedRecommendations.tsx

**Files:**
- Modify: `frontend/src/components/report/NumberedRecommendations.tsx`

**Step 1: Read the full file**

**Step 2: Update the Recommendation interface (lines 4-27)**

Add new option types alongside old ones for backward compatibility:

```typescript
interface Recommendation {
  id: string
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  roi_percentage: number
  roi_calculation_failed?: boolean
  roi_calculation_note?: string
  payback_months: number
  options: {
    // New AIOS options (primary)
    connect_and_automate?: { approach: string; build_time: string; tools_used: string[]; mcp_servers?: string[]; monthly_cost: string; pros?: string[]; cons?: string[] }
    enhance_with_ai?: { approach: string; build_time: string; tools_used: string[]; monthly_cost: string; pros?: string[]; cons?: string[] }
    targeted_upgrade?: { when_needed: string; tools: string[]; cost_range: string; migration_time: string; pros?: string[]; cons?: string[] }
    // Legacy options (backward compat)
    off_the_shelf?: { name: string; vendor: string; monthly_cost: number; implementation_weeks: number; vendor_verified?: boolean; pricing_source?: string; pros?: string[]; cons?: string[] }
    best_in_class?: { name: string; vendor: string; monthly_cost: number; implementation_weeks: number; vendor_verified?: boolean; pricing_source?: string; pros?: string[]; cons?: string[] }
    custom_solution?: { approach: string; estimated_cost: { min: number; max: number }; implementation_weeks: number; pros?: string[]; cons?: string[] }
  }
  our_recommendation: string
  recommendation_rationale: string
  assumptions: string[]
  net_scores?: Record<string, number>
}
```

**Step 3: Update the rendering logic**

Detect which option format is present. If `connect_and_automate` exists, render with new AIOS layout:

- Option labels: "Connect & Automate" (green), "Enhance with AI" (blue), "Targeted Upgrade" (amber)
- Show build time and tools_used for connect option
- Show `when_needed` warning for targeted_upgrade
- Default recommended badge on connect_and_automate

If only old keys exist, fall back to existing rendering.

**Step 4: Commit**

```bash
git add frontend/src/components/report/NumberedRecommendations.tsx
git commit -m "feat: update recommendations UI for AIOS connect-first options"
```

---

### Task 5.2: Update ROICalculator.tsx

**Files:**
- Modify: `frontend/src/components/report/ROICalculator.tsx`

**Step 1: Read the full file**
**Step 2: Update ROI calculation to handle new option keys**

Where it references `rec.options?.best_in_class || rec.options?.off_the_shelf`, add:
```typescript
const option = rec.options?.connect_and_automate || rec.options?.enhance_with_ai || rec.options?.best_in_class || rec.options?.off_the_shelf
```

**Step 3: Update ROI framing**

ROI labels should say "Automation ROI" not "Software ROI". Cost basis should include build time, not just SaaS subscription.

**Step 4: Commit**

```bash
git add frontend/src/components/report/ROICalculator.tsx
git commit -m "feat: update ROI calculator for AIOS option types"
```

---

### Task 5.3: Update PlaybookTab.tsx

**Files:**
- Modify: `frontend/src/components/report/PlaybookTab.tsx`

**Step 1: Read the file**
**Step 2: Update option type labels**

Add new labels alongside existing ones:
```typescript
const optionLabels: Record<string, string> = {
  'connect_and_automate': 'Connect & Automate',
  'enhance_with_ai': 'Enhance with AI',
  'targeted_upgrade': 'Targeted Upgrade',
  'off_the_shelf': 'Off-the-Shelf',
  'best_in_class': 'Best-in-Class',
  'custom_solution': 'Custom Solution',
}
```

**Step 3: Commit**

```bash
git add frontend/src/components/report/PlaybookTab.tsx
git commit -m "feat: update playbook tab for AIOS option labels"
```

---

### Task 5.4: Update TieredFindings.tsx

**Files:**
- Modify: `frontend/src/components/report/TieredFindings.tsx`

**Step 1: Read the full file**
**Step 2: Add AIOS framing to finding cards**

If a finding has `connect_path` or the related recommendation uses `connect_and_automate`, show a badge: "Buildable on your current stack" with a tool icon.

**Step 3: Commit**

```bash
git add frontend/src/components/report/TieredFindings.tsx
git commit -m "feat: add AIOS connect badge to finding cards"
```

---

## Batch 6: Frontend — Landing & Industry Pages

### Task 6.1: Update LandingHome.tsx messaging

**Files:**
- Modify: `frontend/src/pages/LandingHome.tsx`

**Step 1: Read the file**
**Step 2: Update hero messaging**

Change value proposition from "find the right software" to AIOS architecture:
- Headline: "Build Your AI Operating System"
- Subheadline: "Connect what you have. Automate what slows you down."
- CTA: "Get Your Architecture Blueprint"

**Step 3: Update the INDUSTRIES array to include b2b-platforms**

```typescript
{
  slug: 'b2b-platforms',
  name: 'B2B Platforms',
  description: 'IoT devices, connected products, hardware-to-platform businesses',
  icon: <CpuChipIcon className="w-6 h-6" />,
  color: 'violet',
  ready: true,
  painPoints: ['System integration gaps', 'Scaling operations', 'Partner management', 'Field service coordination']
}
```

**Step 4: Update feature cards**

Replace "Software Recommendations" with "Architecture Blueprint" or "AI Workflow Templates"

**Step 5: Commit**

```bash
git add frontend/src/pages/LandingHome.tsx
git commit -m "feat: update landing page to AIOS architecture messaging"
```

---

### Task 6.2: Create B2BPlatforms.tsx industry page

**Files:**
- Create: `frontend/src/pages/industries/B2BPlatforms.tsx`

**Step 1: Copy Ecommerce.tsx as starting point**
**Step 2: Replace content for B2B Platforms**

PAIN_POINTS:
```typescript
const PAIN_POINTS = [
  {
    title: 'System Integration Gaps',
    problem: 'Manual data sync',
    description: 'CRM doesn\'t talk to ERP, ERP doesn\'t talk to IoT. Someone manually copies data between systems every day.',
    potential: 'Automate 90% of data sync',
  },
  {
    title: 'Scaling Operations',
    problem: 'Processes breaking',
    description: 'What worked at 20 employees is cracking at 60. Knowledge is in people\'s heads, not systems.',
    potential: 'Build automated playbooks',
  },
  {
    title: 'Partner Management',
    problem: 'Onboarding bottleneck',
    description: 'Every new distributor needs manual setup, training, portal access. It doesn\'t scale to 100+ partners.',
    potential: 'Self-service partner portal',
  },
  {
    title: 'Revenue Optimization',
    problem: 'Blind spots in usage data',
    description: 'You\'re sitting on IoT usage data that could drive upsells, prevent churn, and optimize pricing. But nobody\'s looking at it.',
    potential: 'AI-driven pricing intelligence',
  },
]
```

SAMPLE_FINDINGS with AIOS framing:
```typescript
const SAMPLE_FINDINGS = [
  {
    title: 'CRM ↔ ERP Auto-Sync',
    verdict: 'Connect',
    verdictColor: 'emerald',
    description: 'Build a Claude workflow that syncs deal closures from HubSpot → auto-generates invoices in Exact. Ships in 8 hours.',
    roi: '€24,000/year',
  },
  {
    title: 'Predictive Churn Agent',
    verdict: 'Enhance',
    verdictColor: 'blue',
    description: 'AI agent monitoring usage patterns across your fleet. Flags at-risk accounts before they churn.',
    roi: '€48,000/year',
  },
  {
    title: 'Enterprise CRM Migration',
    verdict: 'Skip',
    verdictColor: 'gray',
    description: 'HubSpot works fine with API integrations. Salesforce migration would cost 6 months and €200K. Not worth it.',
    roi: 'Negative ROI',
  },
]
```

**Step 3: Commit**

```bash
git add frontend/src/pages/industries/B2BPlatforms.tsx
git commit -m "feat: add B2B Platforms industry landing page"
```

---

### Task 6.3: Add B2BPlatforms route to App.tsx

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: Add import and route**

```typescript
import B2BPlatforms from './pages/industries/B2BPlatforms'

// In routes:
<Route path="/b2b-platforms" element={<B2BPlatforms />} />
```

**Step 2: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: add b2b-platforms route"
```

---

### Task 6.4: Update existing industry pages messaging

**Files:**
- Modify: `frontend/src/pages/industries/Ecommerce.tsx`
- Modify: `frontend/src/pages/industries/Dental.tsx`
- Modify: `frontend/src/pages/industries/ProfessionalServices.tsx`

**Step 1: Update SAMPLE_FINDINGS in each page**

Change verdict labels from "Proceed"/"Skip" to "Connect"/"Enhance"/"Skip" to match AIOS framing.

Update descriptions to lead with "build" or "connect" language instead of "buy" language.

**Step 2: Update any "Software" references to "AI Workflow" or "Architecture"**

E.g., `SOFTWARE` array → consider renaming or reframing as "Your Stack" showing what the quiz analyzes, not what we recommend.

**Step 3: Commit**

```bash
git add frontend/src/pages/industries/
git commit -m "feat: update industry page messaging to AIOS connect-first framing"
```

---

## Batch 7: Sample Reports & Cleanup

### Task 7.1: Update sample report (ecommerce)

**Files:**
- Modify: `backend/src/data/sample_report_ecommerce.json`

**Step 1: Read the file**
**Step 2: Update recommendations to use new option keys**

Change `off_the_shelf` / `best_in_class` / `custom_solution` to `connect_and_automate` / `enhance_with_ai` / `targeted_upgrade`.

Update `our_recommendation` values to lead with `connect_and_automate`.

Update verdict language: "High-Impact AI Workflows" not "High-Impact AI Opportunities".

**Step 3: Validate JSON**
**Step 4: Commit**

```bash
git add backend/src/data/sample_report_ecommerce.json
git commit -m "feat: update ecommerce sample report to AIOS model"
```

---

### Task 7.2: Update sample report (dental)

**Files:**
- Modify: `backend/src/data/sample_report_dental.json`

Same changes as Task 7.1 but for dental context.

**Step 1-4: Same pattern**
**Commit:**

```bash
git add backend/src/data/sample_report_dental.json
git commit -m "feat: update dental sample report to AIOS model"
```

---

### Task 7.3: Update sample report (main)

**Files:**
- Modify: `backend/src/data/sample_report.json`

Same changes as Task 7.1.

**Commit:**

```bash
git add backend/src/data/sample_report.json
git commit -m "feat: update main sample report to AIOS model"
```

---

### Task 7.4: Create b2b-platforms sample report

**Files:**
- Create: `backend/src/data/sample_report_b2b_platforms.json`

**Step 1: Create new sample report**

Follow schema from `sample_report_ecommerce.json` but for HydraFlow (the seed company). Include:
- Company profile matching the seed data
- AI readiness score: 72 (already AI-forward)
- 4-5 findings using AIOS framing
- Recommendations using `connect_and_automate` / `enhance_with_ai` / `targeted_upgrade`
- Verdict: "Connect your existing stack, build AI workflows, skip enterprise migrations"

**Step 2: Validate JSON**
**Step 3: Commit**

```bash
git add backend/src/data/sample_report_b2b_platforms.json
git commit -m "feat: add b2b-platforms sample report with AIOS model"
```

---

### Task 7.5: Clean up industry priority lists

**Files:**
- Modify: `backend/src/expertise/data/industries/home-services.json` (if exists)
- No file deletion — just ensure home-services and marketing-agencies are in LEGACY

**Step 1: Verify `__init__.py` changes from Task 3.3 are correct**

Run: `python -c "from backend.src.knowledge import list_primary_industries, list_legacy_industries; print('Primary:', list_primary_industries()); print('Legacy:', list_legacy_industries())"`

Expected:
- Primary: ['professional-services', 'dental', 'ecommerce', 'b2b-platforms']
- Legacy includes: 'home-services', 'marketing-agencies'

**Step 2: Commit if any cleanup needed**

---

## Batch 8: Integration & Verification

### Task 8.1: Update existing_stack.py for b2b-platforms

**Files:**
- Modify: `backend/src/config/existing_stack.py`

**Step 1: Read the file**
**Step 2: Add b2b-platforms tech stack patterns**

Add common B2B platform tech stacks (HubSpot + Exact + custom IoT, Salesforce + NetSuite + Azure IoT, etc.) so the quiz can recognize and categorize them.

**Step 3: Commit**

```bash
git add backend/src/config/existing_stack.py
git commit -m "feat: add b2b-platforms tech stack patterns"
```

---

### Task 8.2: End-to-end verification

**Step 1: Run backend tests**

Run: `cd backend && python -m pytest tests/ -v --no-header`
Expected: All pass

**Step 2: Verify all JSON files are valid**

Run: `python -c "
import json, glob
for f in glob.glob('backend/src/knowledge/*/*.json'):
    try: json.load(open(f))
    except Exception as e: print(f'FAIL: {f}: {e}')
print('Done')
"`

**Step 3: Verify knowledge loading**

Run: `python -c "
from backend.src.knowledge import get_industry_context, list_primary_industries
print(list_primary_industries())
ctx = get_industry_context('b2b-platforms')
print(f'Processes: {ctx.get(\"process_count\", 0)}')
print(f'Opportunities: {ctx.get(\"opportunity_count\", 0)}')
print(f'Workflows: {len(ctx.get(\"workflows\", []))}')
"`

Expected:
- Primary includes b2b-platforms
- Processes: 7
- Opportunities: 10+
- Workflows: 5

**Step 4: Verify frontend builds**

Run: `cd frontend && npx tsc --noEmit`
Expected: No type errors

**Step 5: Start frontend dev and verify b2b-platforms page loads**

Run: `cd frontend && npm run dev`
Navigate to: `http://localhost:5174/b2b-platforms`
Expected: B2B Platforms landing page renders with pain points and sample findings

---

## Execution Notes

### File Count
~40-50 files touched across 8 batches.

### Dependencies
- Batch 1 (docs) → must be first, defines vocabulary
- Batch 2 (KB schema) → depends on Batch 1 vocabulary
- Batch 3 (b2b-platforms) → can run parallel to Batch 2
- Batch 4 (backend) → depends on Batch 2 schema
- Batch 5 (FE components) → depends on Batch 4 option keys
- Batch 6 (FE pages) → can run parallel to Batch 5
- Batch 7 (sample reports) → depends on Batch 4 schema
- Batch 8 (verification) → last

### Parallel Opportunities
- Batches 2 & 3 can run in parallel
- Batches 5 & 6 can run in parallel
- Tasks within each batch are mostly sequential

### Critical Risk
The option key rename (`off_the_shelf` → `connect_and_automate` etc.) touches many files. Backward compatibility mapping is essential — old reports with old keys must still render correctly.
