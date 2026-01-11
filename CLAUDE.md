# CRB Analyser - Development Guide

> **For domain concepts** → [PRODUCT.md](./PRODUCT.md)
> **For business strategy** → [STRATEGY.md](./STRATEGY.md)

---

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

## Project Commands

Use these commands at conversation start and during development:

| Command | When to Use |
|---------|-------------|
| `/prime` | Start of any new conversation - loads essential context |
| `/plan-feature` | Before implementing a feature - creates structured plan |
| `/execute [plan.md]` | After context reset - executes a plan with minimal context |
| `/create-prd` | After discussing a product idea - generates PRD |
| `/evolve` | After fixing a bug - improves rules/commands to prevent recurrence |

### Context Reset Workflow

**Always reset context between planning and execution:**

```
1. Plan the feature (/plan-feature)
      ↓
2. Output plan to docs/plans/[date]-[feature].md
      ↓
3. CLEAR CONTEXT (new conversation or /clear)
      ↓
4. Execute with only the plan (/execute docs/plans/[plan].md)
```

This keeps context light during execution for better reasoning.

---

## Task-Specific Reference

Load these ONLY when working on the relevant task type:

| Working On | Read This |
|------------|-----------|
| API routes, backend services | `.claude/reference/api-development.md` |
| React components, frontend pages | `.claude/reference/frontend-development.md` |
| Report generation, findings | `.claude/reference/report-quality.md` |
| Vendor database, research agents | `.claude/reference/vendor-management.md` |
| Writing or fixing tests | `.claude/reference/testing.md` |

**Do NOT load all references.** Only load what's relevant to the current task.

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

> **Full framework details** → [PRODUCT.md](./PRODUCT.md)

Core principle: **The analysis must make the best option obvious.**

- **6 Costs**: Financial, Time, Opportunity, Complexity, Risk, Brand/Trust
- **4 Benefits**: Financial, Time, Strategic, Quality
- **NET SCORE** = Benefit - Cost - (Risk ÷ 10)
- **Three Options**: Off-the-Shelf, Best-in-Class, Custom Build
- **Connect vs Replace**: Integrate existing tools OR migrate to new ones

When working on report generation, load `.claude/reference/report-quality.md`.

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

> **Full patterns** → `.claude/reference/testing.md`

### Running Tests
```bash
# Backend
cd backend && pytest
cd backend && pytest -v tests/test_report_service.py  # Single file

# Frontend
cd frontend && npm test
```

### Critical Paths (80%+ coverage required)
- Authentication flow
- Payment processing
- Report generation
- Quiz session management

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

> **Full patterns** → `.claude/reference/api-development.md`

```python
# Response format
{"data": {...}, "message": "optional"}
{"error": {"code": "...", "message": "...", "status": 400}}
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

> **Full details** → `.claude/reference/vendor-management.md`

Quick commands:
- "Add vendor: [url]" - Research and add new vendor
- "Refresh vendor: [slug]" - Re-fetch pricing and update
- "List stale vendors" - Show vendors not verified in 90+ days

CLI: `python -m backend.src.agents.research.cli [discover|refresh] --help`

Admin UI: `http://localhost:5174/admin/vendors`

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

## System Evolution

> "Don't just fix the bug - fix the system that allowed the bug."

After fixing any bug or issue, run `/evolve` to analyze what could prevent it:

| Layer | What to Improve |
|-------|-----------------|
| Rules | Add constraint to CLAUDE.md or reference files |
| Commands | Add validation step to plan-feature or execute |
| Reference | Document the pattern in task-specific docs |

**Evolution log:** `docs/evolution-log.md` tracks all system improvements.

**Habit:** Every bug is an opportunity to make the AI coding system stronger.

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
