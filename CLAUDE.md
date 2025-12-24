# CRB Analyser - Development Guide

## Shortcut Terms

Quick communication shortcuts between user and Claude Code:

| Shortcut | Meaning |
|----------|---------|
| **CW** | Context Window (remaining conversation capacity) |
| **HO** | Handoff document needed |
| **KB** | Knowledge Base (`backend/src/knowledge/`) |
| **PM** | Practice Management (software) |
| **FSM** | Field Service Management (software) |
| **DSO** | Dental Service Organization |
| **3O** | Three Options (off-shelf/best-in-class/custom) |
| **2P** | Two Pillars (Customer Value + Business Health) |
| **ROI-CA** | ROI Confidence-Adjusted |
| **TDD** | Test-Driven Development |
| **LGTM** | Looks Good To Me (approve) |
| **WIP** | Work In Progress |
| **PR** | Pull Request |
| **FE** | Frontend |
| **BE** | Backend |
| **DB** | Database |
| **API** | API endpoint |
| **SSE** | Server-Sent Events (streaming) |
| **RLS** | Row Level Security (Supabase) |

---

## Quick Start

```bash
# Backend (port 8383)
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383

# Frontend (port 5174)
cd frontend && npm run dev

# Redis (required for caching)
brew services start redis
```

---

## Project Overview

**CRB Analyser** is an AI-powered business audit microservice delivering Cost/Risk/Benefit analysis for AI implementation.

| Component | Technology |
|-----------|------------|
| Backend | FastAPI + Python 3.12 |
| Frontend | React 18 + Vite + TypeScript |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth (JWT) |
| Cache | Redis |
| AI | Anthropic Claude API |
| Payments | Stripe |
| Email | SendGrid |
| Monitoring | Logfire + Langfuse |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CRB ANALYSER                           │
├─────────────────────────────────────────────────────────────┤
│  FRONTEND (React + Vite)          BACKEND (FastAPI)         │
│  ├── Landing                      ├── /api/auth             │
│  ├── Dashboard                    ├── /api/clients          │
│  ├── Intake Wizard                ├── /api/audits           │
│  ├── Progress View                ├── /api/findings         │
│  ├── Report Viewer                ├── /api/reports          │
│  └── Settings                     ├── /api/intake           │
│                                   ├── /api/vendors          │
│                                   ├── /api/payments         │
│                                   └── /api/health           │
├─────────────────────────────────────────────────────────────┤
│  CRB AGENT                                                  │
│  ├── Discovery Tools (analyze intake, map processes)        │
│  ├── Research Tools (benchmarks, vendors, web search)       │
│  ├── Analysis Tools (scoring, impact, risk)                 │
│  ├── Modeling Tools (ROI, comparison, timeline)             │
│  └── Report Tools (summary, full report, PDF)               │
├─────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                 │
│  ├── Supabase: clients, audits, findings, recommendations   │
│  ├── Redis: caching, sessions, rate limiting                │
│  └── Vendor DB: pricing, benchmarks (our moat)              │
└─────────────────────────────────────────────────────────────┘
```

---

## Solution Philosophy: Automation vs Custom Software

CRB Analyser recommends solutions across a spectrum. Understanding when to recommend each approach is critical.

### The Spectrum

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         SOLUTION SPECTRUM                                 │
├────────────────┬─────────────────────┬───────────────────────────────────┤
│   AUTOMATION   │   HYBRID            │   CUSTOM SOFTWARE                 │
│   (Connect)    │   (Enhance)         │   (Build)                         │
├────────────────┼─────────────────────┼───────────────────────────────────┤
│ n8n, Make,     │ Automation +        │ Custom platform like              │
│ Zapier         │ Claude Code         │ Aquablu's Atlas Service Hub       │
│                │ enhancements        │                                   │
├────────────────┼─────────────────────┼───────────────────────────────────┤
│ Connect        │ Connect + Add       │ Full control over:                │
│ existing       │ AI intelligence     │ - Data ownership                  │
│ software       │ where needed        │ - Feature design                  │
│ together       │                     │ - User experience                 │
│                │                     │ - Competitive moat                │
└────────────────┴─────────────────────┴───────────────────────────────────┘
```

### When to Recommend Each

#### Automation (n8n, Make, Zapier)
**Recommend when:**
- Problem is workflow coordination between existing tools
- Standard integrations exist
- Speed to deploy matters most
- Budget is constrained
- No unique data/logic requirements

**Example:** "Connect HubSpot to Slack notifications when deals close"

#### Hybrid (Automation + AI Enhancement)
**Recommend when:**
- Core workflow is standard, but needs intelligent processing
- Claude Code can add AI layer to automation
- Custom logic needed at specific steps
- Want benefits of both approaches

**Example:** "n8n workflow that routes support tickets, but Claude API classifies urgency and drafts responses"

#### Custom Software
**Recommend when:**
- Data ownership/access is strategic
- Features need to work exactly as envisioned
- Building a competitive advantage
- Existing tools don't fit the mental model
- Long-term cost of SaaS subscriptions > build cost
- Integration complexity would be higher than building

**Example:** "Aquablu's Atlas Service Hub - custom platform because they need precise control over service delivery workflows and client data"

### Decision Framework

```
┌─────────────────────────────────────────────────────────────┐
│ Does the solution require unique data ownership or          │
│ features that create competitive advantage?                 │
├─────────────────────────────────────────────────────────────┤
│ YES → Consider CUSTOM SOFTWARE                              │
│ NO  ↓                                                       │
├─────────────────────────────────────────────────────────────┤
│ Can existing tools be connected to solve the problem?       │
├─────────────────────────────────────────────────────────────┤
│ YES → AUTOMATION (n8n/Make/Zapier)                          │
│       Does it need AI intelligence at any step?             │
│       YES → HYBRID (add Claude Code/API)                    │
│ NO  → Consider CUSTOM SOFTWARE                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Recommendation Framework: Three Options

Every recommendation MUST present three options to give clients real choice:

### Option Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    THREE OPTIONS MODEL                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  OPTION A: Off-the-Shelf                                    │
│  ├── Fastest to deploy                                      │
│  ├── Lowest risk                                            │
│  ├── Proven solution                                        │
│  └── Trade-off: Less customization                          │
│                                                             │
│  OPTION B: Best-in-Class                                    │
│  ├── Premium vendor/solution                                │
│  ├── Full feature set                                       │
│  ├── Better support/ecosystem                               │
│  └── Trade-off: Higher cost                                 │
│                                                             │
│  OPTION C: Custom Solution                                  │
│  ├── Build with AI/APIs (Claude, etc.)                      │
│  ├── Full control and ownership                             │
│  ├── Competitive advantage potential                        │
│  ├── Includes: tech stack, dev hours, resources             │
│  └── Trade-off: Higher effort, needs technical capability   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  OUR RECOMMENDATION                                         │
│  └── Which option we prefer and WHY                         │
└─────────────────────────────────────────────────────────────┘
```

### Custom Solution Details

When recommending custom solutions, include:
- **Build Tools:** Claude Code, Cursor, VS Code
- **Model Recommendation:** Which Claude model and why (Opus for complex reasoning, Sonnet for balanced, Haiku for speed/cost)
- **Skills Required:** Python, API integration, frontend, etc.
- **Dev Hours Estimate:** Realistic range
- **Recommended Stack:** e.g., FastAPI + React + Supabase + Railway
- **Key APIs:** Specific integrations needed
- **Resources:** Documentation, tutorials, communities

### Two Pillars Assessment

Each finding is rated on two dimensions:
- **Customer Value Score (1-10):** How does this help their customers?
- **Business Health Score (1-10):** How does this strengthen the business?

These inform prioritization - high scores on both = urgent, high on one = important, low on both = deprioritize.

---

## Agent Decision Logic

### Model Selection by Phase

The CRB Agent uses different models for different tasks:

| Phase | Model | Reason |
|-------|-------|--------|
| Discovery | Haiku | Fast extraction, structured data |
| Research | Haiku | Quick searches, data gathering |
| Analysis | Sonnet | Deeper reasoning, pattern recognition |
| Modeling | Sonnet | Complex ROI calculations, comparisons |
| Report | Tier-based | Quality scales with customer tier |

### Confidence Scoring Rules

```
HIGH Confidence (30% of findings):
├── Quiz answer directly mentions the issue
├── Multiple data points support the finding
├── Calculation uses user-provided numbers
└── Benchmark directly applies to their situation

MEDIUM Confidence (50% of findings):
├── Quiz answer implies the issue
├── Industry pattern likely applies
├── Calculation with reasonable assumptions
└── One strong supporting data point

LOW Confidence (20% of findings):
├── Industry pattern suggests possibility
├── Significant assumptions required
├── Hypothesis worth validating
└── Limited data available
```

### Confidence-Adjusted ROI

ROI estimates are adjusted based on confidence:
```python
adjusted_roi = base_roi * confidence_factor
# HIGH:   confidence_factor = 1.0  (100%)
# MEDIUM: confidence_factor = 0.85 (85%)
# LOW:    confidence_factor = 0.70 (70%)
```

**Display requirement:** Always show "Estimated ROI" with confidence level, never claim certainty.

---

## Industry Support

> Target industries locked: December 2025

### Target Customer Profile: "Passion-Driven Service Businesses"

All target industries share these characteristics:
- Owner-operators who make fast decisions
- Relationship-driven (clients = humans, not logos)
- Passion/craft-based (people love what they do)
- Clear operational pain (admin eats creative/service time)
- Pleasant to work with (not corporate bureaucracy)
- Mid-market sweet spot ($500K - $20M revenue)
- Local/regional focus

### Primary Industries (Launch Priority)

| Industry | Slug | Score | Key Metrics ✅ |
|----------|------|-------|-------------|
| **Professional Services** (Legal, Accounting, Consulting) | `professional-services` | 89/100 | 71% GenAI adoption, 7.4% B2B conversion, 37% cost savings |
| **Home Services** (HVAC, Plumbing, Electrical) | `home-services` | 85/100 | 70% AI adoption in FSM ✅, 2.5 hrs/day admin waste ✅ |
| **Dental** (Practices & DSOs) | `dental` | 85/100 | 35% using AI ✅, $3.1B market by 2034 ✅ |

### Secondary Industries (Phase 2)

| Industry | Slug | Score | Key Metrics ✅ |
|----------|------|-------|-------------|
| **Recruiting/Staffing** | `recruiting` | 82/100 | 61-67% using AI ✅, 50% time-to-hire reduction ✅ |
| **Coaching** (businesses, not solopreneurs) | `coaching` | 80/100 | $7.3B market ✅, 75% admin time savings ✅ |
| **Veterinary/Pet Care** | `veterinary` | 80/100 | 39% using AI ✅, productivity gains reported |

### Expansion Industries (Phase 3)

| Industry | Slug | Score | Key Metrics ⚠️ |
|----------|------|-------|-------------|
| **Physical Therapy/Chiropractic** | `physical-therapy` | 79/100 | 80% believe AI will integrate, $43B market |
| **MedSpa/Beauty** | `medspa` | 78/100 | 58% cloud adoption, only 10% market consolidated |

**✅ Verified Dec 2024** - Stats marked ✅ verified via web search against 2024-2025 sources. ⚠️ Phase 3 stats still need verification.

### Key Sources (Verified Dec 2024)
- Home Services: [Zuper FSM Trends 2025](https://www.zuper.co/field-service/field-service-management-trends-2025), [Housecall Pro 2024](https://www.housecallpro.com/resources/home-services-industry-trends/)
- Dental: [GoTu AI in Dentistry 2025](https://gotu.com/dental-practices/ai-in-dentistry-2025/), [InsightAce Market Report](https://www.insightaceanalytic.com/report/ai-in-dentistry-market/3004)
- Recruiting: [StaffingHub 2025](https://staffinghub.com/state-of-staffing/ai-isnt-optional-anymore-how-staffing-firms-are-using-it-to-win-in-2025/), [LinkedIn Future of Recruiting](https://business.linkedin.com/talent-solutions/resources/future-of-recruiting)
- Coaching: [ICF Global Coaching Study 2025](https://coachingfederation.org/resources/research/global-coaching-study/)
- Veterinary: [AAHA/Digitail Survey 2024](https://avmajournals.avma.org/view/journals/ajvr/86/S1/ajvr.24.10.0293.xml)

### Knowledge Base Status

| Industry | Status | Files | Verification |
|----------|--------|-------|--------------|
| `professional-services` | ✅ Complete | processes, opportunities, benchmarks, vendors | ⚠️ Needs verification (created Dec 2024) |
| `home-services` | ✅ Complete | processes, opportunities, benchmarks, vendors | ✅ Dec 2024 |
| `dental` | ✅ Complete | processes, opportunities, benchmarks, vendors | ✅ Dec 2024 |
| `recruiting` | ✅ Complete | processes, opportunities, benchmarks, vendors | ✅ Dec 2024 |
| `coaching` | ✅ Complete | processes, opportunities, benchmarks, vendors | ✅ Dec 2024 |
| `veterinary` | ✅ Complete | processes, opportunities, benchmarks, vendors | ✅ Dec 2024 |
| `physical-therapy` | 🚧 Needed | - | - |
| `medspa` | 🚧 Needed | - | - |

**⚠️ VERIFICATION REQUIRED:** All knowledge base data must be verified against current (2025) sources before use in production reports. See "Data Verification Policy" below.

### Target Countries (Launch Markets)

| Country | Language | Rationale |
|---------|----------|-----------|
| **Netherlands** | English/Dutch | Home market, iterate fast |
| **Germany** | German/English | Biggest EU economy, strong Mittelstand |
| **United Kingdom** | English | Large professional services sector |
| **Ireland** | English | Tech-savvy, strong professional services hub |

**Phase 2 Expansion:** France, Nordics, Benelux, Spain

### Dropped Industries

These are no longer targets (removed from knowledge base Dec 2024):
- ~~Music Studios~~ (budget constraints)
- ~~Marketing Agencies~~ (DIY mentality, competitive)
- ~~E-commerce~~ (not passion-driven service)
- ~~Retail~~ (not passion-driven service)
- ~~Tech Companies~~ (DIY mentality)
- ~~Gyms/Fitness~~ (thin margins)
- ~~Hotels/Hospitality~~ (slow enterprise decisions)

### Unified Positioning

> "We help passion-driven service professionals - from lawyers to plumbers, dentists to dog trainers - get the AI clarity they need to stop wasting time on admin and get back to the work they love."

### Limited Support (Other Industries)

Industries not in our target list fall back to general patterns:
- Generic benchmarks applied
- No industry-specific quick wins
- No industry-specific anti-patterns
- Vendor matching less precise

**Recommendation:** For unsupported industries, acknowledge limitations and focus on universal efficiency opportunities. Consider whether they fit the "passion-driven service business" profile.

---

## Solution Ecosystem

### Automation Tools (for connecting existing software)

| Tool | Best For | Knowledge Base |
|------|----------|----------------|
| **n8n** | Self-hosted, complex workflows, developers | `vendors/automation.json` |
| **Make** | Visual workflows, mid-complexity | `vendors/automation.json` |
| **Zapier** | Simple integrations, non-technical users | `vendors/automation.json` |

### AI Development Tools (for custom solutions)

| Tool | Use Case |
|------|----------|
| **Claude Code** | AI-assisted development, code generation |
| **Cursor** | AI-native IDE for building |
| **Claude API** | Add AI to any application |

### Deployment & Infrastructure

| Service | Purpose | Knowledge Base |
|---------|---------|----------------|
| **Railway** | Easy deployment, auto-scaling | `vendors/dev_tools.json` |
| **Vercel** | Frontend deployment, edge functions | `vendors/dev_tools.json` |
| **Supabase** | Database, auth, real-time | `vendors/dev_tools.json` |
| **Redis** | Caching, sessions | Infrastructure |

### LLM Provider Pricing

Stored in `knowledge/ai_tools/llm_providers.json`:
- Claude (Opus, Sonnet, Haiku) pricing
- GPT-4, GPT-3.5 pricing
- Other providers for comparison

Used for custom solution cost estimates.

---

## Self-Improving Agent (Expertise System)

The CRB Agent learns from each analysis to improve future recommendations.

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    LEARNING LOOP                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. BEFORE Analysis                                         │
│     └── Load expertise for client's industry                │
│         (pain_points, effective_patterns, anti_patterns)    │
│                                                             │
│  2. DURING Analysis                                         │
│     └── Track tools used, errors, phase completion          │
│                                                             │
│  3. AFTER Analysis                                          │
│     └── Update expertise store with:                        │
│         - Which findings were generated                     │
│         - Which recommendations were made                   │
│         - Any patterns observed                             │
│                                                             │
│  4. NEXT Analysis (same industry)                           │
│     └── Injected expertise improves prompts                 │
│         - Known pain points surface faster                  │
│         - Effective patterns prioritized                    │
│         - Anti-patterns avoided                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Expertise Data Structure

```python
IndustryExpertise:
├── pain_points        # Common issues + frequency + solutions that worked
├── processes          # Typical workflows + automation potential observed
├── effective_patterns # Recommendations that succeeded
├── anti_patterns      # What NOT to recommend (learned from failures)
├── size_specific      # Insights by company size (SMB vs enterprise)
└── avg_metrics        # Trends over time (avg savings, ROI, etc.)
```

### Files

- `backend/src/expertise/__init__.py` - Expertise store implementation
- `backend/src/expertise/schemas.py` - Data structures

**This is a competitive advantage** - the more analyses we run, the better our recommendations become for each industry.

---

## Development Rules

### 1. Code Quality
- **Read before edit** - Never modify code you haven't read
- **No over-engineering** - Only build what's needed now
- **Type everything** - Full type hints in Python, TypeScript strict mode
- **Test critical paths** - Auth, payments, report generation

### 2. CRB-Specific Rules
- **NO MOCK DATA OR GUESSING** - Every statistic, benchmark, and claim in the knowledge base MUST be verified against real, current sources. If you cannot verify a claim, mark it as "UNVERIFIED" or remove it.
- **Every claim needs a verifiable source** - Include the actual source (study name, vendor website, industry report) and verification date. "Industry patterns" is NOT acceptable without a real source.
- **Transparent calculations** - Show assumptions in ROI math. All ROI figures are **estimates** - display confidence level and key assumptions visibly.
- **Confidence affects ROI** - Apply confidence-based adjustments: HIGH (100%), MEDIUM (85%), LOW (70%). Always label as "Estimated ROI" with confidence indicator.
- **Validate vendors** - Pricing from curated knowledge base (refreshed via vendor_refresh_service). Mark "Last verified: [date]" on vendor data. Verify pricing via vendor websites.
- **Confidence distribution** - Each report should have ~30% HIGH, ~50% MEDIUM, ~20% LOW confidence findings. If everything is HIGH, we're not being honest about uncertainty.

### 2b. Data Verification Policy

**CRITICAL: No unverified data in production.**

| Data Type | Verification Method | Refresh Frequency |
|-----------|--------------------|--------------------|
| Vendor pricing | Check vendor website directly | Monthly |
| Industry benchmarks | Cite specific study/report with year | Quarterly |
| AI adoption stats | Link to survey/study source | Quarterly |
| Market size | Link to market research report | Annually |
| ROI claims | Must show calculation with sources | Per-use |

**Before adding ANY data to knowledge base:**
1. Find a real, verifiable source (not AI-generated)
2. Include source name, URL if available, and date
3. Add `"verified_date": "YYYY-MM"` to the data
4. If cannot verify, mark as `"status": "UNVERIFIED"`

**Unverified data handling:**
- NEVER present unverified data as fact
- Mark with ⚠️ in reports
- Apply LOW confidence automatically
- Prioritize verification before production use

### 3. Security
- **RLS everywhere** - All tables have Row Level Security
- **Validate inputs** - Pydantic models for all requests
- **Sanitize outputs** - No raw errors to users in production
- **Rate limit** - All endpoints rate-limited

### 4. Performance
- **Cache aggressively** - Tool results, LLM responses, benchmarks
- **Stream responses** - SSE for long-running operations
- **Lazy load** - Don't load all findings at once

---

## Key Files Reference

| Area | File | Purpose |
|------|------|---------|
| **Config** | `backend/src/config/settings.py` | Environment variables |
| **Supabase** | `backend/src/config/supabase_client.py` | DB client singleton |
| **Auth** | `backend/src/middleware/auth.py` | JWT validation |
| **Agent** | `backend/src/agents/crb_agent.py` | Main analysis agent |
| **Tools** | `backend/src/tools/tool_registry.py` | Tool definitions |
| **ROI** | `backend/src/services/roi_calculator.py` | ROI calculations |
| **Reports** | `backend/src/services/report_service.py` | Report generation (1500+ lines) |
| **PDF** | `backend/src/services/report_generator.py` | PDF generation |
| **Expertise** | `backend/src/expertise/__init__.py` | Self-improving agent store |
| **Knowledge** | `backend/src/knowledge/__init__.py` | Industry data loader |
| **Assumptions** | `backend/src/models/assumptions.py` | ROI assumption tracking |
| **Recommendations** | `backend/src/models/recommendation.py` | Three Options model |
| **Vendor Refresh** | `backend/src/services/vendor_refresh_service.py` | Live pricing updates |
| **Auth (FE)** | `frontend/src/contexts/AuthContext.tsx` | Auth state |
| **API Client** | `frontend/src/services/apiClient.ts` | HTTP client |

---

## Database Schema

### Core Tables

```sql
clients        -- Businesses being audited
audits         -- CRB analysis projects
findings       -- Discovered issues/opportunities
recommendations -- Proposed solutions with ROI
reports        -- Generated PDF reports
vendor_catalog -- Vendor pricing database (our moat)
industry_benchmarks -- Industry metrics (our moat)
```

### Key Relationships

```
workspace
    └── clients
            └── audits
                    ├── findings
                    │       └── recommendations
                    └── reports
```

### Knowledge Base Structure

```
backend/src/knowledge/
├── vendors/                    # Vendor pricing database (our moat)
│   ├── ai_assistants.json
│   ├── analytics.json
│   ├── automation.json        # n8n, Make, Zapier, etc.
│   ├── crm.json
│   ├── customer_support.json
│   ├── dev_tools.json         # Railway, Vercel, Supabase
│   ├── scheduling.json        # For home services, dental, etc.
│   ├── finance.json
│   ├── hr_payroll.json
│   ├── marketing.json
│   └── project_management.json
│
├── ai_tools/
│   └── llm_providers.json     # Claude, GPT pricing for custom solutions
│
│   # PRIMARY INDUSTRIES (Launch) - All 6 complete
├── professional-services/     # ✅ Complete (Legal, Accounting, Consulting)
│   ├── processes.json
│   ├── opportunities.json
│   ├── benchmarks.json
│   └── vendors.json
├── home-services/             # ✅ Complete (HVAC, Plumbing, Electrical)
├── dental/                    # ✅ Complete (Practices & DSOs)
├── recruiting/                # ✅ Complete (Staffing agencies)
├── coaching/                  # ✅ Complete (Business coaching)
├── veterinary/                # ✅ Complete (Vet clinics, pet care)
│
│   # EXPANSION INDUSTRIES (Phase 3) - Not yet created
├── physical-therapy/          # 🚧 TODO: PT, Chiropractic
├── medspa/                    # 🚧 TODO: MedSpa, Beauty
│
└── patterns/
    └── ai_implementation_playbook.json
```

**Vendor data refresh:** Use `vendor_refresh_service.py` to update pricing. Mark "Last verified: [date]" in reports.

**Industry knowledge structure:** Each industry folder needs:
- `processes.json` - Common workflows and pain points
- `opportunities.json` - AI automation opportunities
- `benchmarks.json` - Industry-specific metrics
- `vendors.json` - Relevant software for that industry

---

## API Patterns

### Authentication
All protected routes use `Depends(get_current_user)`:
```python
@router.get("/audits")
async def list_audits(
    current_user: CurrentUser = Depends(get_current_user),
    supabase: AsyncClient = Depends(get_async_supabase)
):
    # current_user.workspace_id for multi-tenant isolation
```

### Response Format
```python
# Success
{"data": {...}, "message": "optional"}

# Error
{"error": {"type": "validation_error", "message": "...", "status_code": 400}}
```

### Streaming (SSE)
For long-running operations:
```python
@router.get("/audits/{id}/progress")
async def stream_progress(id: str):
    async def generate():
        async for update in agent.run_analysis(id):
            yield f"data: {json.dumps(update)}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## CRB Agent Tools

### Discovery (Phase 1)
| Tool | Purpose |
|------|---------|
| `analyze_intake_responses` | Parse questionnaire, extract pain points |
| `map_business_processes` | Create process flow from descriptions |
| `identify_tech_stack` | Detect current tools from intake |

### Research (Phase 2)
| Tool | Purpose |
|------|---------|
| `search_industry_benchmarks` | Find relevant metrics |
| `search_vendor_solutions` | Find matching vendors |
| `scrape_vendor_pricing` | Get current pricing |
| `validate_source_credibility` | Score source reliability |

### Analysis (Phase 3)
| Tool | Purpose |
|------|---------|
| `score_automation_potential` | Rate process (0-100) |
| `calculate_finding_impact` | Estimate cost/time |
| `identify_ai_opportunities` | Find AI use cases |
| `assess_implementation_risk` | Evaluate risk factors |

### Modeling (Phase 4)
| Tool | Purpose |
|------|---------|
| `calculate_roi` | Full ROI with assumptions |
| `compare_vendors` | Side-by-side comparison |
| `generate_timeline` | Implementation roadmap |

### Report (Phase 5)
| Tool | Purpose |
|------|---------|
| `generate_executive_summary` | Key findings synthesis |
| `generate_full_report` | Complete PDF artifact |

---

## Frontend Routes

```
/                   Landing (public)
/login              Login
/signup             Signup
/pricing            Pricing tiers

/dashboard          List audits
/new-audit          Start audit, select tier
/intake/:id         Multi-step questionnaire

/audit/:id          Audit detail
/audit/:id/progress Live progress view
/audit/:id/findings Review findings
/audit/:id/report   View/download report

/settings           Account settings
/settings/billing   Subscription management
```

---

## Design System

### Colors (Semantic)
| Color | Usage |
|-------|-------|
| **Blue** | Primary actions, links |
| **Green** | Success, savings, positive ROI |
| **Yellow** | Warnings, medium risk |
| **Red** | Errors, high risk, costs |
| **Purple** | AI/analysis related |
| **Gray** | Neutral, secondary text |

### Components
- `rounded-2xl` for cards
- `rounded-xl` for buttons
- `font-light` for body text
- `backdrop-blur-sm` for overlays

---

## Environment Variables

### Backend (.env)
```bash
# Required
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SECRET_KEY=
ANTHROPIC_API_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# Optional but recommended
REDIS_URL=redis://localhost:6379
BRAVE_API_KEY=
TAVILY_API_KEY=
SENDGRID_API_KEY=
LOGFIRE_TOKEN=
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=http://localhost:8383
VITE_STRIPE_PUBLISHABLE_KEY=
```

---

## Testing

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test

# E2E (when ready)
npm run test:e2e
```

### Critical Test Coverage
- [ ] Auth flow (signup, login, logout)
- [ ] Payment flow (checkout, webhook)
- [ ] Audit creation and progress
- [ ] Report generation
- [ ] ROI calculations

---

## Deployment

### Railway (Production)
```bash
# Backend
railway link
railway up

# Frontend
railway link
railway up
```

### Health Checks
- Backend: `GET /health`
- Frontend: `GET /`

---

## Common Tasks

### Add a new tool
1. Define in `tools/tool_registry.py`
2. Implement in appropriate `tools/*_tools.py`
3. Register in agent tool list
4. Add tests

### Add a new API route
1. Create route file in `routes/`
2. Add Pydantic models
3. Register in `main.py`
4. Add auth dependency
5. Add tests

### Add a new frontend page
1. Create page in `pages/`
2. Add route in `App.tsx`
3. Create service functions if needed
4. Add to navigation if appropriate

---

## Debugging

### Backend logs
```bash
# Development
uvicorn src.main:app --reload --port 8383 --log-level debug

# Check Logfire dashboard for production
```

### Frontend
- React DevTools
- Network tab for API calls
- Check Sentry for errors

### Common Issues

| Issue | Solution |
|-------|----------|
| Auth not working | Check JWT token, Supabase config |
| Streaming not updating | Check SSE connection, CORS |
| Report not generating | Check Claude API key, tool errors |
| Payment failing | Check Stripe keys, webhook URL |

---

## Reference: MMAI Source Files

When adapting code, reference these MMAI files:

| Component | MMAI Path |
|-----------|-----------|
| Supabase client | `mmai-backend/src/config/supabase_client.py` |
| Auth middleware | `mmai-backend/src/middleware/auth.py` |
| Security middleware | `mmai-backend/src/middleware/security.py` |
| Error handler | `mmai-backend/src/middleware/error_handler.py` |
| Cache service | `mmai-backend/src/services/cache_service.py` |
| Knowledge pipeline | `mmai-backend/src/services/knowledge/pipeline.py` |
| Agent pattern | `mmai-backend/src/agents/maestro_agent.py` |
| Model routing | `mmai-backend/src/agents/conservative_4tier_routing.py` |
| Stripe routes | `mmai-backend/src/routes/stripe_routes.py` |
| Auth context | `mmai-frontend/src/contexts/AuthContext.tsx` |
| API client | `mmai-frontend/src/services/apiClient.ts` |
| Tool stream hook | `mmai-frontend/src/hooks/useToolStream.ts` |
| Wizard pattern | `mmai-frontend/src/components/onboarding/OnboardingWizard.tsx` |

---

## Hybrid Mode: Auto-Claude + Superpowers

This project uses **Auto-Claude** for orchestration and parallel agent management, combined with **Superpowers** discipline skills for code quality.

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     AUTO-CLAUDE UI                           │
│         (Kanban, 12 terminals, visual management)            │
├─────────────────────────────────────────────────────────────┤
│  Each Claude Code terminal loads this CLAUDE.md             │
│  → Superpowers discipline skills remain active              │
│  → Orchestration skills are disabled (Auto-Claude handles)  │
└─────────────────────────────────────────────────────────────┘
```

### Superpowers Skills Configuration

**DISABLED** (Auto-Claude handles these):
| Skill | Reason |
|-------|--------|
| `using-git-worktrees` | Auto-Claude manages worktrees in `.worktrees/` |
| `dispatching-parallel-agents` | Auto-Claude orchestrates parallel execution |
| `execute-plan` | Use Auto-Claude's spec system instead |
| `subagent-driven-development` | Auto-Claude handles task dispatch |

**ENABLED** (Use these in every terminal):
| Skill | Purpose |
|-------|---------|
| `test-driven-development` | Write tests first, always |
| `systematic-debugging` | Four-phase debugging framework |
| `verification-before-completion` | Run verification before claiming done |
| `testing-anti-patterns` | Prevent bad testing practices |
| `root-cause-tracing` | Trace bugs to source |
| `brainstorming` | Refine ideas before implementation |
| `code-reviewer` | Review implementation quality |

### Starting Auto-Claude

```bash
# Terminal 1: Start the UI
cd "/Users/larsmusic/CRB Analyser/Auto-Claude/auto-claude-ui"
pnpm dev

# Or build and run the desktop app
pnpm build:mac
open dist/mac-arm64/Auto\ Claude.app
```

### Workflow

1. **Brainstorm** in Claude Code (use superpowers brainstorming skill)
2. **Create spec** in Auto-Claude UI
3. **Auto-Claude dispatches** parallel agents to terminals
4. **Each agent follows TDD** (superpowers skill active)
5. **Auto-Claude QA reviews** the implementation
6. **Auto-Claude merges** to main branch
7. **You do final human review**

### Auto-Claude Location

Auto-Claude is installed at: `/Users/larsmusic/CRB Analyser/Auto-Claude`

---

## Checklist: MVP Ready

### Backend
- [ ] Auth working (signup, login, logout)
- [ ] Clients CRUD
- [ ] Audits CRUD with status tracking
- [ ] Intake submission and storage
- [ ] CRB agent runs analysis
- [ ] Findings generated
- [ ] Recommendations with ROI
- [ ] PDF report generation
- [ ] Stripe checkout works
- [ ] Webhook processes payments

### Frontend
- [ ] Landing page
- [ ] Auth flow complete
- [ ] Dashboard shows audits
- [ ] Intake wizard works
- [ ] Progress streaming
- [ ] Report viewer
- [ ] PDF download
- [ ] Payment flow

### Infrastructure
- [ ] Supabase tables with RLS
- [ ] Redis caching
- [ ] Railway deployment
- [ ] Environment variables set
- [ ] Health checks passing
