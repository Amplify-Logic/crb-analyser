# CRB Analyser - Development Guide

## Quick Start

```bash
# Backend (port 8383)
cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383

# Frontend (port 5174)
cd frontend && npm run dev

# Redis (required)
brew services start redis
```

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + Python 3.12 |
| Frontend | React 18 + Vite + TypeScript |
| Database | Supabase (PostgreSQL + RLS) |
| Cache | Redis |
| AI | Anthropic Claude API |
| Payments | Stripe |
| Deploy | Railway |

---

## Architecture

```
Frontend (React)           Backend (FastAPI)
├── Landing                ├── /api/auth, clients, audits
├── Quiz Flow (anonymous)  ├── /api/quiz, interview, workshop
├── Report Preview/Viewer  ├── /api/reports, payments
├── Dashboard (auth'd)     ├── /api/vendors, expertise
└── Admin (vendors, KB)    └── /api/admin_*, health

CRB Agent: Discovery → Research → Analysis → Modeling → Report

Skills System: analysis/, interview/, workshop/, report-generation/

Data: Supabase (quiz_sessions, reports, vendors) + Redis (cache) + Knowledge Base
```

---

## Quiz Flow (Main Conversion Path)

The anonymous quiz is the primary user acquisition funnel.

```
Landing → Quiz (5-7 questions) → [Optional: Voice Interview]
    ↓
AI Readiness Score + Report Teaser
    ↓
Stripe Checkout → Full Report Access
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `Quiz.tsx` | Multi-step wizard with progress tracking |
| `quiz.py` | Backend routes, session management |
| `quiz_engine.py` | Adaptive question selection, confidence scoring |
| `teaser_service.py` | Generate report preview before payment |

### Quiz Session States
```
created → in_progress → completed → payment_pending → paid
```

### Pricing Tiers (EUR)
| Tier | Price | Model | Includes |
|------|-------|-------|----------|
| **CRB Report** | €147 | Sonnet | Self-service analysis, interactive report |
| **Report + Call** | €497 | Opus | + 60-min strategy call, priority support |
| **Sprint** | €1,997 | Opus | + 2-week implementation help, 3x calls |

---

## CRB Analysis Framework

The Cost-Risk-Benefit framework is the core analytical methodology. **The analysis must make the best option obvious** - not just list pros/cons.

### The Six Dimensions of Cost

Cost is NOT just money. Analyze all six dimensions:

| Dimension | What to Measure | Questions to Ask |
|-----------|-----------------|------------------|
| **Financial** | Direct €, indirect €, ongoing € | Subscription? Implementation? Hidden fees? |
| **Time** | Hours to implement, learn, maintain | Time to value? Learning curve? Ongoing drain? |
| **Opportunity** | What you can't do if you do this | What else could this budget/time fund? |
| **Complexity** | Mental load, integration difficulty | How many systems touched? Training needed? |
| **Risk** | What could go wrong, reversibility | What if it fails? How hard to undo? |
| **Brand/Trust** | Customer perception, team morale | Will customers notice? Will team resist? |

### The Four Dimensions of Benefit

| Dimension | What to Measure | Questions to Ask |
|-----------|-----------------|------------------|
| **Financial** | Revenue increase, cost savings | How much saved/earned? When does ROI hit? |
| **Time** | Hours freed, speed improvements | Hours/week saved? How much faster? |
| **Strategic** | Market position, competitive edge | Does this differentiate? Does it compound? |
| **Quality** | Customer experience, team satisfaction | Will customers notice? Will team be happier? |

### Risk Categories

| Risk Type | Key Question | Mitigation |
|-----------|--------------|------------|
| **Implementation** | Will this actually work? | Pilot first, phased rollout |
| **Adoption** | Will the team use it? | Training, change management |
| **Vendor** | Will they exist in 2 years? | Exit strategy, data portability |
| **Security** | What data is exposed? | Audit, compliance check |
| **Integration** | Will it break existing systems? | Sandbox testing |

### Scoring System

Each option gets scored to make comparison objective:

```
Option A: [Tool Name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COSTS                          Score (1-5, lower = better)
├── Financial: €X/month        ██░░░ 2
├── Time to Value: X weeks     ███░░ 3
├── Complexity: X integrations ██░░░ 2
├── Risk: [description]        █░░░░ 1
├── Opportunity: [trade-off]   ██░░░ 2
└── Brand Impact: [effect]     █░░░░ 1
                      COST SCORE: 11/30

BENEFITS                       Score (1-5, higher = better)
├── Financial: €X saved/month  ████░ 4
├── Time: X hrs/week freed     █████ 5
├── Strategic: [advantage]     ███░░ 3
└── Quality: [improvement]     ████░ 4
                   BENEFIT SCORE: 16/20

RISK SCORE: (Probability × Impact, summed)  9/30

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NET SCORE: Benefit - Cost - (Risk÷10) = +4.1
CONFIDENCE: MEDIUM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Making the Answer Obvious

The comparison summary must make the winner clear:

```
COMPARISON SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Option A: HubSpot Free         NET: +4.1  ◀━━ RECOMMENDED
Option B: Salesforce           NET: +1.2
Option C: Custom Build         NET: -2.3

WHY OPTION A WINS:
✓ Lowest time-to-value (2 weeks vs 8 weeks)
✓ Free tier covers current needs
✓ Team already familiar with interface

WHAT YOU'RE TRADING OFF:
△ Less customization than Option C
△ May outgrow free tier in 12-18 months
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Connect vs Replace Strategy

When recommending automation, always present both paths:

| Strategy | When to Recommend | Example |
|----------|-------------------|---------|
| **Connect** (Integrate) | Current tools are good, just need automation | Keep Dentrix, add n8n for reminders |
| **Replace** (Migrate) | Current tools are fundamentally broken | Move from spreadsheets to HubSpot |

**Decision Factors:**
- Current tool quality → Good = Connect, Broken = Replace
- Team size → Large = Connect (change risk), Small = Replace (can adapt)
- Data complexity → High = Connect (migration risk), Low = Replace
- Budget → Limited = Connect, Available = Replace

---

## Report Quality Standards

### Anti-Slop Rules

The report is worthless if it sounds like generic AI output.

❌ **NEVER use these phrases:**
| Banned Phrase | Replace With |
|---------------|--------------|
| "Streamline operations" | "Reduce invoice processing from 4 hours to 30 minutes" |
| "Enhance efficiency" | "Save €2,400/month on manual data entry" |
| "Leverage AI capabilities" | "Use Claude to draft client emails (€15/month)" |
| "Transform your business" | "Free up 10 hours/week for billable work" |
| "Unlock potential" | "Increase capacity from 40 to 55 clients/month" |
| "Optimize workflows" | "Cut appointment scheduling from 15 to 2 minutes" |
| "Drive growth" | "Add €4,200/month revenue with automated follow-ups" |

### Specificity Requirements

Every claim needs backing:
- **ROI figures**: Source + calculation + confidence level
- **Vendor recommendations**: Pricing verified within 90 days
- **Benchmarks**: Source URL + date + industry specificity
- **Time estimates**: Based on similar implementations, not guesses
- **Ranges over false precision**: "€1,200-€1,800/month" not "€1,547/month"

### Teaser vs Full Report

| Element | Teaser (Free) | Full Report (€147+) |
|---------|---------------|---------------------|
| AI Readiness Score | ✅ Full | ✅ Full |
| Top 3 Opportunities | Headlines only | Full CRB analysis |
| Vendor Recommendations | "We found 5 tools" | Names + pricing + comparison |
| Implementation Roadmap | ❌ | ✅ with timeline |
| Quick Wins | Count only | Detailed steps |
| ROI Calculations | Total only | Per-finding breakdown |

---

## Quality Assurance

### Before Shipping Report Changes

```bash
# Run these checks before any report generation PR
- [ ] Generate reports for 3 different industries
- [ ] Search output for banned phrases (grep -i "streamline\|leverage\|enhance")
- [ ] Verify all ROI figures have confidence levels
- [ ] Check vendor pricing is < 90 days old
- [ ] Confirm benchmarks have sources
```

### Report Review Checklist

- [ ] Would a dentist/plumber/lawyer understand this without jargon?
- [ ] Are recommendations actionable THIS WEEK?
- [ ] Does every number have a source or confidence level?
- [ ] Is the €147 price clearly justified by the value shown?
- [ ] Does the best option emerge obviously from the analysis?

### Common Quality Issues

| Issue | How to Detect | How to Fix |
|-------|---------------|------------|
| Generic findings | Search for "improve", "enhance", "optimize" | Replace with specific metrics |
| Unverified benchmarks | `verified_date` missing or > 6 months | Update from source or mark UNVERIFIED |
| Stale vendor pricing | `verified_at` > 90 days | Run vendor refresh |
| Missing confidence | ROI without HIGH/MED/LOW | Add confidence scoring |
| Unclear winner | All options look equal | Sharpen the scoring, highlight trade-offs |

---

## Development Rules

### Code Quality
- **Read before edit** - Never modify code you haven't read
- **No premature abstractions** - Don't abstract until used 3+ times
- **Type everything** - `mypy --strict` must pass, no untyped functions
- **Test critical paths** - Auth, payments, report generation require 80%+ coverage

### Error Handling
```python
# All custom errors inherit from base
class CRBError(Exception):
    def __init__(self, message: str, code: str, status: int = 500):
        self.message = message
        self.code = code  # e.g., "VENDOR_NOT_FOUND"
        self.status = status

# Routes return consistent format
{"error": {"code": "VENDOR_NOT_FOUND", "message": "...", "status": 404}}
```

### Logging
```python
import structlog
logger = structlog.get_logger()

# Always include context
logger.info("analysis_started", audit_id=audit_id, industry=industry)
logger.error("vendor_fetch_failed", vendor_id=vendor_id, error=str(e))
```

### Security
- RLS on all Supabase tables
- Pydantic validation on all inputs
- No raw errors to users in production
- Rate limit all endpoints
- Never log secrets or PII

### Performance
- Cache KB data 1hr, vendor pricing 15min
- Never cache user-specific data without key isolation
- Stream long operations with SSE
- Lazy load findings (paginate)

---

## Git Workflow

### Branches
```
main              # Production-ready
feat/xxx          # New features
fix/xxx           # Bug fixes
refactor/xxx      # Code improvements
```

### Commits
```
feat: add vendor comparison tool
fix: correct ROI calculation for dental industry
refactor: extract PDF generation to service
docs: update API patterns in CLAUDE.md
test: add integration tests for payment flow
```

### PR Checklist
- [ ] Tests pass locally
- [ ] Types check (`mypy --strict`)
- [ ] No console.log/print statements
- [ ] Error handling follows pattern
- [ ] Migrations are reversible

---

## Testing

### Framework
- Backend: `pytest` + `pytest-asyncio`
- Frontend: `vitest` + `@testing-library/react`

### Structure
```
backend/tests/
├── conftest.py         # Shared fixtures
├── test_*.py           # Test files (flat structure)
└── skills/             # Skill-specific tests

frontend/src/
└── __tests__/          # Co-located with components
```

### Running Tests
```bash
# Backend
cd backend && pytest
cd backend && pytest -v tests/test_report_service.py  # Single file
cd backend && pytest -k "test_calculate"              # By name pattern

# Frontend
cd frontend && npm test
```

### Patterns
```python
# Unit test - fast, isolated
def test_calculate_roi_with_high_confidence():
    result = calculate_roi(base=10000, confidence="HIGH")
    assert result == 10000  # 1.0 factor

# Integration test - with mocks
async def test_get_vendor_caches_result(mock_supabase, mock_redis):
    service = VendorService(mock_supabase, mock_redis)
    await service.get_vendor("123")
    mock_redis.setex.assert_called_once()
```

---

## Anti-Patterns (Don't Do This)

### Code
- ❌ Catching bare `Exception` - catch specific errors
- ❌ `# type: ignore` without explanation comment
- ❌ Raw SQL without parameterization
- ❌ Business logic in route handlers (use services)
- ❌ Circular imports between modules

### Testing
- ❌ Tests that depend on execution order
- ❌ Mocking the thing you're testing
- ❌ Tests without assertions
- ❌ Sleeping instead of polling/waiting

### Architecture
- ❌ Direct Supabase calls outside repository layer
- ❌ Storing secrets in code or committed .env
- ❌ Hardcoded IDs or magic strings

---

## Key Files

| Area | File |
|------|------|
| **Config** | |
| Settings | `backend/src/config/settings.py` |
| Model Routing | `backend/src/config/model_routing.py` |
| Existing Stack | `backend/src/config/existing_stack.py` |
| **Core Services** | |
| Reports | `backend/src/services/report_service.py` |
| Quiz Engine | `backend/src/services/quiz_engine.py` |
| Teaser | `backend/src/services/teaser_service.py` |
| Token Analytics | `backend/src/services/token_analytics.py` |
| Vendor Service | `backend/src/services/vendor_service.py` |
| Software Research | `backend/src/services/software_research_service.py` |
| **Skills** | |
| Base | `backend/src/skills/base.py` |
| Registry | `backend/src/skills/registry.py` |
| Vendor Matching | `backend/src/skills/analysis/vendor_matching.py` |
| Quick Wins | `backend/src/skills/analysis/quick_win_identifier.py` |
| Automation Summary | `backend/src/skills/report-generation/automation_summary.py` |
| **Research Agents** | |
| Discover | `backend/src/agents/research/discover.py` |
| Refresh | `backend/src/agents/research/refresh.py` |
| CLI | `backend/src/agents/research/cli.py` |
| **Routes** | |
| Quiz | `backend/src/routes/quiz.py` |
| Interview | `backend/src/routes/interview.py` |
| Workshop | `backend/src/routes/workshop.py` |
| Admin Research | `backend/src/routes/admin_research.py` |
| **Knowledge** | |
| Knowledge Base | `backend/src/knowledge/__init__.py` |
| Expertise | `backend/src/expertise/__init__.py` |
| **Frontend** | |
| Auth Context | `frontend/src/contexts/AuthContext.tsx` |
| Quiz Page | `frontend/src/pages/Quiz.tsx` |
| Report Viewer | `frontend/src/pages/ReportViewer.tsx` |
| Vendor Admin | `frontend/src/pages/admin/VendorAdmin.tsx` |
| Automation Roadmap | `frontend/src/components/report/AutomationRoadmap.tsx` |

---

## Common Tasks

### Add a new API route
1. Create file: `backend/src/routes/<name>.py`
2. Define Pydantic models for request/response
3. Add auth: `current_user = Depends(get_current_user)`
4. Register in `main.py`: `app.include_router(router, prefix="/api/<name>")`
5. Add tests: `backend/tests/test_<name>.py`

### Add a new Agent tool
1. Define schema in `tools/schemas.py`
2. Implement in `tools/<category>_tools.py`
3. Register in `tool_registry.py` with phase mapping
4. Add unit test for tool logic
5. Update Agent Tools table below

### Add a new frontend page
1. Create page: `frontend/src/pages/<Name>.tsx`
2. Add route in `App.tsx`
3. Create API service if needed: `frontend/src/services/<name>.ts`
4. Add to navigation if appropriate

---

## API Patterns

```python
# Auth dependency
@router.get("/audits")
async def list_audits(
    current_user: CurrentUser = Depends(get_current_user),
    supabase: AsyncClient = Depends(get_async_supabase)
):
    # current_user.workspace_id for multi-tenant isolation
    ...

# Response format
{"data": {...}, "message": "optional"}
{"error": {"code": "...", "message": "...", "status": 400}}

# SSE Streaming
@router.get("/audits/{id}/progress")
async def stream_progress(id: str):
    async def generate():
        async for update in agent.run_analysis(id):
            yield f"data: {json.dumps(update)}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## Agent Tools

| Phase | Tools |
|-------|-------|
| Discovery | analyze_intake_responses, map_business_processes, identify_tech_stack |
| Research | search_industry_benchmarks, search_vendor_solutions, scrape_vendor_pricing |
| Analysis | score_automation_potential, calculate_finding_impact, identify_ai_opportunities |
| Modeling | calculate_roi, compare_vendors, generate_timeline |
| Report | generate_executive_summary, generate_full_report |

---

## Skills System

Skills are modular, testable units of AI-powered logic. They replace inline prompts with structured, reusable components.

### Structure
```
backend/src/skills/
├── base.py                    # BaseSkill, LLMSkill, SyncSkill classes
├── registry.py                # Skill discovery and registration
├── analysis/                  # Finding analysis
│   ├── vendor_matching.py     # Match findings to vendors
│   ├── quick_win_identifier.py
│   └── math_validator.py      # Validate ROI calculations
├── interview/                 # Voice interview
│   └── confidence.py          # Track interview confidence
├── workshop/                  # 90-minute workshop
│   ├── question_skill.py      # Generate contextual questions
│   ├── milestone_skill.py     # Track workshop milestones
│   └── signal_detector.py     # Detect buying signals
└── report-generation/         # Report sections
    ├── exec_summary.py
    ├── finding_generation.py
    ├── three_options.py       # Generate 3 options per finding
    └── verdict.py             # Go/No-Go recommendation
```

### Creating a Skill
```python
from src.skills.base import LLMSkill

class MySkill(LLMSkill[MyOutputModel]):
    name = "my-skill"
    description = "What this skill does"

    async def execute(self, context: SkillContext) -> MyOutputModel:
        prompt = self._build_prompt(context)
        return await self._call_llm(prompt, MyOutputModel)
```

### Skill Types
| Type | Use Case |
|------|----------|
| `LLMSkill` | Needs Claude API (generation, analysis) |
| `SyncSkill` | Pure logic, no async (validators, formatters) |
| `BaseSkill` | Custom async logic (API calls, DB queries) |

### Key Patterns
- Skills return Pydantic models (type-safe outputs)
- Skills are discovered automatically via `registry.py`
- Test skills in `tests/skills/test_<skill_name>.py`

---

## Database Schema

```
# Core Flow
quiz_sessions → reports → findings, recommendations, playbook
     ↓
  payments (Stripe)

# Vendor System (Supabase)
vendors ← industry_vendor_tiers (T1/T2/T3 per industry)
    ↓
vendor_audit_log

# Knowledge (Vector)
knowledge_embeddings (pgvector for RAG)

# Legacy (being deprecated)
workspace → clients → audits
```

### Key Tables

| Table | Purpose |
|-------|---------|
| `quiz_sessions` | Anonymous quiz responses, industry, scores |
| `reports` | Generated reports with token_usage, generation trace |
| `vendors` | Vendor catalog with pricing, features, ratings |
| `industry_vendor_tiers` | Which vendors are T1/T2/T3 for each industry |
| `knowledge_embeddings` | Vector embeddings for RAG retrieval |

---

## Frontend Routes

```
# Public
/                   Landing page
/login, /signup     Auth
/terms, /privacy    Legal pages

# Anonymous Quiz Flow (main conversion path)
/quiz               Multi-step quiz wizard
/quiz/interview     Voice interview (optional)
/quiz/adaptive      Adaptive follow-up questions
/quiz/preview       Report teaser before payment
/checkout           Stripe checkout
/checkout/success   Post-payment redirect

# Authenticated
/dashboard          List audits
/report/:id         Full report viewer
/interview          90-minute workshop
/workshop           Workshop facilitation

# Admin (requires auth)
/admin/vendors      Vendor database management
/admin/knowledge    Knowledge base editor
```

---

## Environment Variables

```bash
# Backend (required)
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SECRET_KEY=
ANTHROPIC_API_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# Backend (optional)
REDIS_URL=redis://localhost:6379
BRAVE_API_KEY=              # Web search
TAVILY_API_KEY=             # Alternative search
BREVO_API_KEY=              # Email service
OPENAI_API_KEY=             # For embeddings/GPT
GOOGLE_AI_API_KEY=          # Gemini models
DEEPSEEK_API_KEY=           # Budget model option
LOGFIRE_TOKEN=              # Observability

# Frontend
VITE_API_BASE_URL=http://localhost:8383
VITE_STRIPE_PUBLISHABLE_KEY=
```

---

## Debugging

```bash
# Verbose backend logs
uvicorn src.main:app --reload --port 8383 --log-level debug

# Check Redis
redis-cli KEYS "*"
redis-cli GET "key_name"

# Supabase logs
# Check dashboard: https://app.supabase.com/project/_/logs
```

| Issue | Check |
|-------|-------|
| Auth failing | JWT token expiry, Supabase config, RLS policies |
| Stream not updating | SSE connection, CORS headers, nginx buffering |
| Report failing | Claude API key, tool errors in logs, rate limits |
| Payment failing | Stripe keys (test vs live), webhook URL, event types |

---

## Model Routing (Jan 2026)

Models are routed by task type using `backend/src/config/model_routing.py`.

### Model Tiers

| Tier | Claude | Gemini | Use Case |
|------|--------|--------|----------|
| Fast | `claude-haiku-4-5-20251001` | `gemini-3-flash-preview` | Extraction, validation, classification |
| Balanced | `claude-sonnet-4-5-20250929` | - | Generation tasks (quick tier) |
| Premium | `claude-opus-4-5-20251101` | `gemini-3-pro-preview` | Complex analysis, full tier reports |

### Task Routing

```python
# Fast tasks (Haiku)
"parse_quiz_responses", "extract_industry", "validate_json", "classify_finding"

# Premium tasks (Opus) - full tier only
"generate_executive_summary", "generate_findings", "synthesize_report"

# Quick tier overrides → Sonnet instead of Opus for cost savings
```

### Usage
```python
from src.config.model_routing import get_model_for_task, CLAUDE_MODELS

model = get_model_for_task("generate_findings", tier="quick")  # Returns Sonnet
model = get_model_for_task("generate_findings", tier="full")   # Returns Opus
```

### Token Tracking
```python
from src.config.model_routing import TokenTracker

tracker = TokenTracker()
tracker.add_usage("task_name", model_id, input_tokens, output_tokens)
summary = tracker.get_summary()  # Includes cost estimate
```

**DO NOT use:** `claude-3-5-*`, `gemini-2.0-*`, `gemini-1.5-*`

---

## Knowledge Base Management

### Structure
```
backend/src/knowledge/
├── vendors/              # Vendor pricing (refresh monthly)
├── [industry]/           # Industry-specific data
│   ├── processes.json
│   ├── opportunities.json
│   ├── benchmarks.json
│   └── vendors.json
└── patterns/             # Cross-industry patterns
```

### Add a New Industry
1. Create folder: `backend/src/knowledge/<industry-slug>/`
2. Add required files:
   - `processes.json` - Common workflows, pain points
   - `opportunities.json` - AI automation opportunities
   - `benchmarks.json` - Industry metrics with sources
   - `vendors.json` - Relevant software for this industry
3. Register in `backend/src/knowledge/__init__.py`
4. Add to PRODUCT.md industry list

### Verify/Refresh Data
```bash
# Check what needs refresh
grep -r "verified_date" backend/src/knowledge/ | grep "2024"

# Update vendor pricing
python -m backend.src.services.vendor_refresh_service
```

### Data Quality Rules
- Every stat needs `"source"` and `"verified_date": "YYYY-MM"`
- Unverified data: `"status": "UNVERIFIED"` → shows ⚠️ in reports
- Pricing: verify against vendor website, not AI-generated

---

## Vendor Database Management

The vendor knowledge base is stored in Supabase. Claude Code can directly manage vendors.

### Adding a New Vendor

1. Fetch the vendor's website and pricing page using WebFetch
2. Extract: name, pricing tiers, features, integrations, company sizes
3. Determine category from: `crm`, `customer_support`, `ai_sales_tools`, `automation`, `analytics`, `ecommerce`, `finance`, `hr_payroll`, `marketing`, `project_management`, `ai_assistants`, `ai_agents`, `ai_content_creation`, `dev_tools`
4. Insert into Supabase `vendors` table
5. Log action in `vendor_audit_log`

### Vendor Schema (Required Fields)

| Field | Type | Description |
|-------|------|-------------|
| slug | TEXT | Unique lowercase-hyphenated identifier |
| name | TEXT | Display name |
| category | TEXT | One of the categories above |
| website | TEXT | Full URL |
| description | TEXT | 1-2 sentences |
| pricing | JSONB | `{model, tiers[], starting_price, free_tier}` |

### Quick Commands

| Command | Action |
|---------|--------|
| "Add vendor: [url]" | Research and add new vendor |
| "Refresh vendor: [slug]" | Re-fetch pricing and update |
| "Set [slug] as tier 1 for [industry]" | Add to industry tier list |
| "Mark [slug] as deprecated" | Soft delete vendor |
| "List stale vendors" | Show vendors not verified in 90+ days |

### Supabase Access Pattern

```python
from src.config.supabase_client import get_async_supabase

supabase = await get_async_supabase()

# Insert vendor
await supabase.table("vendors").insert({
    "slug": "vendor-name",
    "name": "Vendor Name",
    "category": "crm",
    "website": "https://vendor.com",
    "description": "What the vendor does",
    "pricing": {"model": "subscription", "starting_price": 49, "free_tier": True},
    "status": "active",
}).execute()

# Update vendor
await supabase.table("vendors").update({
    "pricing": {...},
    "verified_at": datetime.utcnow().isoformat(),
    "verified_by": "claude-code",
}).eq("slug", "vendor-slug").execute()

# Log audit entry
await supabase.table("vendor_audit_log").insert({
    "vendor_slug": "vendor-slug",
    "action": "create",
    "changed_by": "claude-code",
    "changes": {"field": {"old": None, "new": "value"}},
}).execute()

# Set industry tier
await supabase.table("industry_vendor_tiers").upsert({
    "industry": "dental",
    "vendor_id": vendor_id,
    "tier": 1,
    "boost_score": 0,
}).execute()
```

### Admin UI

Access: `http://localhost:5174/admin/vendors` (requires login)

Features:
- View/search/filter vendors
- Edit vendor details
- Manage industry tiers (T1/T2/T3)
- View audit log
- Mark vendors as verified

### CLI Helper

```bash
# Run vendor CLI
python -m backend.src.scripts.vendor_cli add "https://vendor.com"
python -m backend.src.scripts.vendor_cli refresh "vendor-slug"
python -m backend.src.scripts.vendor_cli list-stale
```

---

## Research Agent System

Automated vendor discovery and data refresh to keep the knowledge base current.

### Architecture

```
backend/src/agents/research/
├── __init__.py
├── cli.py              # Command-line interface
├── discover.py         # Find new vendors for an industry
├── refresh.py          # Update existing vendor data
├── schemas.py          # Pydantic models for research data
└── sources/
    ├── __init__.py
    ├── vendor_site.py  # Scrape vendor websites
    └── web_search.py   # Search for vendor info
```

### Usage

```bash
# Discover vendors for an industry
python -m backend.src.agents.research.cli discover --industry dental

# Refresh stale vendors (not verified in X days)
python -m backend.src.agents.research.cli refresh --stale-days 90

# Refresh a specific vendor
python -m backend.src.agents.research.cli refresh --vendor hubspot
```

### Adding New Industries

1. Run discovery: `python -m backend.src.agents.research.cli discover --industry {slug}`
2. Review output in `vendor_audit_output.json`
3. Approve/reject in admin UI (`/admin/vendors`)
4. Set tier rankings (T1/T2/T3) for approved vendors
5. Verify pricing manually for T1 vendors

### Data Flow

```
Discovery Agent
    ↓
Searches web for "{industry} software tools"
    ↓
Extracts vendor info (name, website, pricing, features)
    ↓
Validates against existing vendors (dedup)
    ↓
Creates pending entries in Supabase
    ↓
Admin reviews and approves
    ↓
Vendor available in recommendations
```

### Refresh Cadence

| Vendor Tier | Refresh Frequency | Manual Verification |
|-------------|-------------------|---------------------|
| T1 (primary) | Weekly | Monthly |
| T2 (secondary) | Bi-weekly | Quarterly |
| T3 (alternatives) | Monthly | As needed |

---

## Database Migrations

### Location
```
backend/supabase/migrations/
├── 001_initial_schema.sql      # Core tables
├── 002_company_research.sql    # Research data
├── 003_quiz_sessions.sql       # Anonymous quiz
├── 004_reports.sql             # Report storage
├── 007_add_missing_report_columns.sql
├── 008_vector_embeddings.sql   # pgvector for RAG
├── 009_anonymous_flow.sql      # Anonymous user support
├── 010_update_report_status_constraint.sql
├── 011_add_generation_trace.sql
├── 012_vendor_database.sql     # Vendor tables
├── 013_adaptive_quiz.sql       # Adaptive quiz confidence
├── 014_workshop_columns.sql    # Workshop support
├── 015_vendor_api_openness.sql # Vendor API/integration scores
├── 016_existing_stack.sql      # User's current tech stack
└── 017_automation_summary.sql  # Automation roadmap data
```

### Create Migration
```bash
# Create new migration file
touch backend/supabase/migrations/XXX_description.sql

# Apply locally
supabase db push

# Apply to production
supabase db push --linked
```

### Rules
- Migrations must be reversible (include rollback comments)
- Never delete columns in production without deprecation period
- Test migration on local DB first
- Backup before applying to production

---

## Auto-Claude + Superpowers

**Disabled (Auto-Claude handles):** git-worktrees, parallel-agents, execute-plan, subagent-development

**Enabled (use always):** TDD, systematic-debugging, verification-before-completion, testing-anti-patterns, root-cause-tracing, brainstorming, code-reviewer

**Workflow:** Brainstorm → Create spec → Auto-Claude dispatches → TDD in each terminal → QA review → Merge → Human review

---

## Shortcuts

| Short | Meaning | Short | Meaning |
|-------|---------|-------|---------|
| CW | Context Window | HO | Handoff doc |
| KB | Knowledge Base | FE/BE | Frontend/Backend |
| TDD | Test-Driven Dev | RLS | Row Level Security |
| SSE | Server-Sent Events | PR | Pull Request |

See also: [PRODUCT.md](./PRODUCT.md) for domain concepts, [STRATEGY.md](./STRATEGY.md) for business context.
