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
├── Landing/Dashboard      ├── /api/auth, clients, audits
├── Intake Wizard          ├── /api/findings, reports
├── Progress/Report View   ├── /api/vendors, payments
└── Settings               └── /api/health

CRB Agent: Discovery → Research → Analysis → Modeling → Report

Data: Supabase (clients, audits, findings) + Redis (cache) + Vendor KB (moat)
```

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
| Config | `backend/src/config/settings.py` |
| Auth | `backend/src/middleware/auth.py` |
| Agent | `backend/src/agents/crb_agent.py` |
| Tools | `backend/src/tools/tool_registry.py` |
| ROI | `backend/src/services/roi_calculator.py` |
| Reports | `backend/src/services/report_service.py` |
| PDF | `backend/src/services/report_generator.py` |
| Expertise | `backend/src/expertise/__init__.py` |
| Knowledge | `backend/src/knowledge/__init__.py` |
| Auth (FE) | `frontend/src/contexts/AuthContext.tsx` |
| API Client | `frontend/src/services/apiClient.ts` |

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

## Database Schema

```
workspace → clients → audits → findings → recommendations
                            → reports
vendor_catalog, industry_benchmarks  -- Our moat
```

---

## Frontend Routes

```
/                   Landing
/login, /signup     Auth
/dashboard          List audits
/new-audit          Start audit
/intake/:id         Questionnaire
/audit/:id          Detail, progress, findings, report
/settings           Account, billing
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
BRAVE_API_KEY=
TAVILY_API_KEY=
SENDGRID_API_KEY=
LOGFIRE_TOKEN=

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

## Approved Models (Dec 2025)

| Model | ID | Use |
|-------|-----|-----|
| Haiku 4.5 | `claude-haiku-4-5-20251001` | Fast tasks, research |
| Sonnet 4.5 | `claude-sonnet-4-5-20250929` | Analysis, reasoning |
| Opus 4.5 | `claude-opus-4-5-20251101` | Complex tasks, reports |
| Gemini 3 Flash | `gemini-3-flash-preview` | Fast, cost-effective |
| Gemini 3 Pro | `gemini-3-pro-preview` | Quality, reasoning |

**DO NOT use:** `claude-3-5-*`, `gemini-2.0-*`, `gemini-1.5-*`

> ⚠️ **VERIFY MODEL IDs:** Check `backend/src/config/model_routing.py` for actual IDs in use.
> Some code may still use older IDs like `claude-3-5-haiku-20241022`. Consolidate before production.

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

## Database Migrations

### Location
```
backend/supabase/migrations/
├── 001_initial_schema.sql
├── 002_add_findings.sql
└── ...
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
