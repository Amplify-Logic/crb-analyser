# AI + Automation Layer Design

**Date:** 2026-01-04
**Status:** Design Prompt
**Priority:** High - Core Value Proposition Shift

---

## The Problem

Our current vendor recommendations are **2020-level thinking**:
- "You need a CRM? Here's Salesforce vs HubSpot"
- "You need scheduling? Here's Calendly vs Acuity"

This misses the **2026 reality**:
- Most businesses already have software (often the wrong one, or underutilized)
- The value isn't in switching software - it's in **connecting and extending** it
- AI can now build custom tools for narrow problems in hours, not months
- Workflow automation (n8n, Make, Zapier) is the glue layer

---

## The Shift: From "Buy This" to "Connect + Extend"

### Old Model (What We Do Now)
```
Finding: "High no-show rate"
→ Recommendation: "Buy Weave ($250/mo)"
```

### New Model (What We Should Do)
```
Finding: "High no-show rate"
→ Analysis: What software do they already have?
→ Question: Does it have an API?
→ Recommendations:
   1. Quick Win: n8n workflow to send SMS reminders via existing system + Twilio
   2. AI Tool: Claude Code script to analyze no-show patterns and predict risk
   3. Integration: Connect their PMS → n8n → AI prediction → personalized outreach
   4. If software is closed: THEN recommend Weave (API-first alternative)
```

---

## Core Automation Stack (2026)

### Tier 1: Workflow Orchestration
| Tool | Use Case | Pricing | Notes |
|------|----------|---------|-------|
| **n8n** | Self-hosted workflows, complex logic | Free (self-host) or $20/mo | Open source, unlimited workflows |
| **Make** | Visual automation, non-technical users | $9-16/mo | Great templates, 1000+ integrations |
| **Zapier** | Simple triggers, enterprise clients | $20-100/mo | Easiest onboarding, most integrations |

### Tier 2: AI Development
| Tool | Use Case | Pricing | Notes |
|------|----------|---------|-------|
| **Claude Code** | Build custom CLI tools, scripts, agents | API costs | Best for complex logic, file handling |
| **Cursor** | AI-assisted coding for non-devs | $20/mo | Good for modifying existing code |
| **Windsurf** | Lightweight AI coding | $15/mo | Alternative to Cursor |
| **Replit Agent** | Deploy simple web apps | $25/mo | Good for prototypes |

### Tier 3: AI APIs
| Tool | Use Case | Pricing | Notes |
|------|----------|---------|-------|
| **Claude API** | Text analysis, generation, reasoning | ~$3-15/M tokens | Best for complex tasks |
| **OpenAI API** | General purpose, vision | ~$2-60/M tokens | Good ecosystem |
| **Deepgram** | Speech-to-text | $0.0043/min | Best accuracy/price |
| **ElevenLabs** | Text-to-speech | $5-22/mo | Natural voices |

### Tier 4: Integration Platforms
| Tool | Use Case | Pricing | Notes |
|------|----------|---------|-------|
| **Supabase** | Database + auth for custom tools | Free-$25/mo | Postgres + real-time |
| **Vercel** | Deploy custom dashboards | Free-$20/mo | Easy Next.js hosting |
| **Railway** | Deploy backend services | $5-20/mo | Simple container hosting |

---

## New Vendor Evaluation Criteria

### Must-Have: API Openness Score

Every vendor needs an **API Openness Score (1-5)**:

| Score | Meaning | Example |
|-------|---------|---------|
| 5 | Full REST API, webhooks, OAuth | Stripe, Twilio, HubSpot |
| 4 | Good API, some limitations | Salesforce, Zendesk |
| 3 | Basic API, limited endpoints | Many dental PMS |
| 2 | Zapier/Make only, no direct API | Some legacy software |
| 1 | Closed system, no integrations | Avoid recommending |

### New Vendor Schema Fields

```json
{
  "api_openness_score": 4,
  "api_documentation_url": "https://...",
  "has_webhooks": true,
  "has_oauth": true,
  "zapier_integration": true,
  "make_integration": true,
  "n8n_integration": true,
  "api_rate_limits": "1000/min",
  "custom_tool_examples": [
    "Patient risk scoring with Claude API",
    "Automated appointment optimization"
  ],
  "integration_complexity": "medium",
  "requires_developer": false
}
```

---

## Recommendation Framework

### Step 1: Inventory Existing Stack
Before recommending anything, ask:
- What software are they already using?
- Do those tools have APIs?
- What's their technical capability? (Can they use n8n? Claude Code?)

### Step 2: Score Integration Potential
For each existing tool:
- API available? → Can automate
- Webhooks? → Can trigger workflows
- Data export? → Can analyze with AI

### Step 3: Recommend Automation Layer

**Pattern A: Connect Existing Tools**
```
Their CRM → n8n → AI Analysis → Their Email Tool
Cost: $0-50/mo + API costs
Time: 2-4 hours to build
```

**Pattern B: Build Narrow AI Tool**
```
Problem: "We spend 2 hours/day categorizing support tickets"
Solution: Claude Code script that:
  - Reads tickets from API
  - Categorizes with Claude
  - Updates ticket + routes to right person
Cost: ~$20/mo in API calls
Time: 4-8 hours to build
```

**Pattern C: Replace Closed Software**
```
Only if existing software has API score < 3
AND the problem can't be solved with automation layer
THEN recommend API-first alternative
```

---

## Example Transformations

### Dental Practice: No-Show Problem

**Old Recommendation:**
> "Switch to Weave ($250/mo) for automated reminders"

**New Recommendation:**
```
1. ASSESS: What PMS do they use? (Open Dental, Dentrix, etc.)

2. IF Open Dental (API score: 4):
   → Build n8n workflow:
     - Trigger: Daily at 6 AM
     - Action: Query tomorrow's appointments via API
     - Action: Check patient history for no-show risk (Claude API)
     - Action: High-risk patients get personal call reminder
     - Action: Normal patients get SMS via Twilio
   → Cost: ~$30/mo (Twilio + Claude API)
   → Setup: 4 hours with Claude Code

3. IF Dentrix (API score: 2):
   → Use Dentrix → Zapier → SMS flow (limited but works)
   → OR recommend Open Dental migration for long-term flexibility

4. BONUS: AI Risk Scoring
   → Claude Code script analyzes:
     - Patient history
     - Appointment type
     - Day/time patterns
     - Weather (API)
   → Outputs: Risk score per patient
   → Action: Proactive outreach to high-risk
```

### Recruiting Agency: Candidate Sourcing

**Old Recommendation:**
> "Use Bullhorn ($custom) or Manatal ($15/user)"

**New Recommendation:**
```
1. ASSESS: What ATS do they have? What's their sourcing process?

2. BUILD: AI Sourcing Agent (Claude Code)
   → Connects to LinkedIn (via their existing tools)
   → Analyzes job requirements
   → Scores candidates with Claude
   → Drafts personalized outreach
   → Schedules in their calendar via API

3. CONNECT: n8n Workflow
   → New job posted → triggers sourcing agent
   → Agent finds candidates → posts to Slack for review
   → Approved → auto-sends outreach
   → Response received → updates ATS via API

4. ONLY IF ATS is closed:
   → Recommend Manatal (API score: 5, $15/mo)
```

### Home Services: Scheduling Chaos

**Old Recommendation:**
> "Get ServiceTitan ($custom) or Jobber ($39/mo)"

**New Recommendation:**
```
1. ASSESS: What are they using now? Google Calendar? Paper?

2. IF using any calendar with API:
   → Build: AI Scheduling Optimizer
     - Reads all appointments + locations
     - Calculates optimal routes (Google Maps API)
     - Suggests schedule changes
     - Auto-reschedules with customer consent (SMS)

3. BUILD: Custom Dispatch Board (Claude Code + Vercel)
   → Simple web app showing:
     - Today's jobs on map
     - Tech locations (GPS)
     - Suggested next job per tech
   → Cost: ~$25/mo (Vercel + APIs)
   → Time: 8-12 hours to build

4. IF they need full FSM and have budget:
   → Recommend Jobber (API score: 4)
   → Immediately build automation layer on top
```

---

## Implementation Plan

### Phase 1: Update Vendor Schema ✅ COMPLETED (2026-01-04)
- [x] Add `api_openness_score` to all vendors
- [x] Add `has_webhooks`, `has_oauth` fields
- [x] Add `zapier_integration`, `make_integration`, `n8n_integration`
- [x] Add `api_rate_limits`, `custom_tool_examples` fields
- [ ] Document API capabilities for top 50 vendors (use `audit_vendor_apis.py`)

**Files Changed:**
- `backend/supabase/migrations/015_vendor_api_openness.sql` - Database migration
- `backend/src/models/vendor.py` - Pydantic models with new fields
- `backend/src/services/vendor_service.py` - API openness scoring in recommendations
- `frontend/src/pages/admin/VendorAdmin.tsx` - Admin UI for editing API fields
- `backend/src/scripts/audit_vendor_apis.py` - CLI tool for auditing vendors

**New Vendor Service Methods:**
- `get_automation_ready_vendors()` - Get vendors with high API openness
- `get_vendors_needing_api_audit()` - Find vendors without scores
- `update_vendor_api_info()` - Update API fields for a vendor

**CLI Usage:**
```bash
cd backend
python -m src.scripts.audit_vendor_apis list   # List unrated vendors
python -m src.scripts.audit_vendor_apis stats  # Show statistics
python -m src.scripts.audit_vendor_apis bulk   # Update known vendors
python -m src.scripts.audit_vendor_apis rate <slug> <score>
```

### Phase 2-4: SUPERSEDED

**See:** `docs/plans/2026-01-07-connect-vs-replace-design.md`

The original Phase 2-4 was replaced with a more focused approach:

- ~~Phase 2: Create Automation Templates~~ → Templates without users
- ~~Phase 3: Update Recommendation Engine~~ → Merged into new design
- ~~Phase 4: Report Format Changes~~ → Merged into new design

**New Approach: Connect vs Replace**

Instead of building templates, we:
1. Capture existing software stack in quiz
2. Research unknown software capabilities automatically
3. Show "Connect" path (use existing tools) vs "Replace" path (switch software)
4. Add Automation Roadmap summary with tier-aware messaging

This keeps the report as the product while using automation potential to drive value.

---

## New Report Section: "Automation Layer"

```markdown
## Automation Opportunities

Based on your current stack, here's how we can automate without switching software:

### 1. No-Show Prevention (Est. 4 hours to build)

Your Stack: Open Dental + Google Calendar

Automation Flow:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Open Dental │ ──▶ │    n8n      │ ──▶ │  Twilio SMS │
│  (API)      │     │  (workflow) │     │  (reminders)│
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Claude API  │
                    │ (risk score)│
                    └─────────────┘

Cost: ~$30/mo | ROI: $4,200/mo (based on 70% no-show reduction)

### 2. Custom AI Tool: Patient Risk Scorer

We can build a Claude Code script that:
- Analyzes patient history from Open Dental
- Predicts no-show probability (0-100%)
- Triggers different reminder sequences based on risk
- Learns from outcomes over time

Build time: 6 hours | Ongoing cost: ~$15/mo in API calls
```

---

## Key Mindset Shifts

| Old Thinking | New Thinking |
|--------------|--------------|
| "What software should they buy?" | "What can we automate with what they have?" |
| "This vendor is best for X" | "This vendor has the best API for building on top of" |
| "Recommend the market leader" | "Recommend the most open/extensible option" |
| "One tool per problem" | "Orchestration layer connecting many tools" |
| "They need a developer" | "Claude Code can build this in hours" |

---

## Success Metrics

- % of recommendations that include automation vs pure software switch
- Time-to-value: Hours to implement automation vs weeks to switch software
- Cost savings: Automation layer vs new software subscription
- API utilization: Are clients actually connecting their tools?

---

## Questions for Next Session

1. Should we add an "automation potential" score to each finding?
2. How do we assess client's technical capability? (Can they use n8n?)
3. Should we offer to build the automation as a service?
4. How do we template Claude Code scripts for common problems?
5. What's the minimum viable "automation layer" for each industry?

---

## Prompt for Next Session

```
I need to implement the AI + Automation Layer vision for CRB Analyser.

Read: docs/handoffs/2026-01-04-ai-automation-layer-design.md

Key tasks:
1. Update vendor schema to include API openness scores
2. Create automation templates for n8n/Make workflows
3. Build Claude Code script templates for common narrow AI tools
4. Update recommendation engine to prioritize automation over software switches
5. Add "Automation Opportunities" section to report format

Start with Phase 1: Updating the vendor schema with API fields.
```
