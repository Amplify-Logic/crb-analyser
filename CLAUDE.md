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
| Database, migrations, env vars | `.claude/reference/database.md` |
| Skills system, agent tools | `.claude/reference/skills.md` |
| Knowledge base, curated insights | `.claude/reference/knowledge-base.md` |

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
Landing → Quiz (5-7 questions) → AI Readiness Score + Teaser
    ↓
Stripe Checkout (€147)
    ↓
90-min Workshop (deep context gathering)
    ↓
Human-Reviewed Report (24-48 hour delivery)
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `Quiz.tsx` | Multi-step wizard with progress tracking |
| `quiz.py` | Backend routes, session management |
| `quiz_engine.py` | Adaptive question selection, confidence scoring |
| `teaser_service.py` | Generate report preview before payment |
| `workshop.py` | 90-minute deep-dive session management |

### Quiz Session States
```
created → in_progress → completed → payment_pending → paid → workshop_complete → report_delivered
```

### Launch Pricing
| Tier | Price | Includes |
|------|-------|----------|
| **CRB Report** | €147 | Quiz + 90-min workshop + human-reviewed report (24-48hr delivery) |

**Future tiers** (add only after 50+ reports delivered):
- Report + Call (€497) - add 60-min strategy call
- Sprint (€1,997) - add 2-week implementation help

---

## CRB Analysis Framework

> **Full framework details** → [PRODUCT.md](./PRODUCT.md) and [FRAMEWORK.md](./FRAMEWORK.md)

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
> See `.claude/reference/api-development.md` for error handling patterns.
> Key: use `APIError` subclasses from `backend/src/middleware/error_handler.py` (`NotFoundError`, `ValidationErrorAPI`, `AuthorizationError`).

### Logging
> See `.claude/reference/api-development.md` for logging patterns.
> Key: use `structlog.get_logger()` and always include context kwargs.

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

## Active Hooks

Claude Code hooks are configured in `.claude/settings.local.json`. These run automatically and may block operations.

### PreToolUse (runs before tool execution)

| Hook | Triggers On | Purpose |
|------|-------------|---------|
| `enforce-pnpm.sh` | Bash | Blocks npm commands, enforces pnpm |
| `protect-secrets.sh` | Bash, Read, Edit, Write | Blocks access to `.env`, credentials, secrets |

### PostToolUse (runs after tool execution)

| Hook | Triggers On | Purpose |
|------|-------------|---------|
| `audit-commands.sh` | Bash | Logs executed commands |
| `report_validator.py` | Write, Edit | Validates report JSON structure and quality |
| `vendor_validator.py` | Write, Edit | Validates vendor data format |
| `roi_math_validator.py` | Write, Edit | Validates ROI/financial calculations |
| `benchmark_source_validator.py` | Write, Edit | Checks benchmark data sources |
| `playbook_validator.py` | Write, Edit | Validates implementation playbooks |
| `industry_data_validator.py` | Write, Edit | Validates industry-specific data |

**If a hook blocks your operation:** Check which validator failed and fix the data issue. Don't try to bypass hooks.

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

## Browser Automation

Playwright-based browser automation for UI testing, enhanced scraping, and vendor research.

### Setup
```bash
pip install playwright
playwright install chromium
# Or: make playwright-install
```

### Skills

| Skill | Purpose | LLM? |
|-------|---------|------|
| `playwright-browser` | Core browser automation (navigate, screenshot, scrape) | No |
| `enhanced-scraper` | Site scraping with Playwright + httpx fallback | No |
| `vendor-site-scraper` | Vendor pricing extraction via Playwright + Claude | Yes |

### Commands

| Command | Purpose |
|---------|---------|
| `/ui-test` | Run agentic UI tests against user stories |
| `/research-vendor` | Discover and scrape vendor pricing |

### CLI Flag
```bash
# Use Playwright for JS-rendered scraping in report generation
cd backend && python -m src.cli.generate_report --playwright --url https://example.com
# Or: make generate-report-playwright ARGS="--url https://example.com"
```

### User Stories
UI test stories live in `tests/ui/stories/*.yaml`. Add new stories by creating a YAML file — they're auto-discovered by `/ui-test`.

### Makefile Targets
```bash
make playwright-install          # Install Chromium
make ui-test                     # Run UI tests
make generate-report-playwright  # Generate report with Playwright scraping
make test-all                    # Full test suite including UI
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
| Insight Service | `backend/src/services/insight_service.py` |
| Software Research | `backend/src/services/software_research_service.py` |
| **Skills** | |
| Base | `backend/src/skills/base.py` |
| Registry | `backend/src/skills/registry.py` |
| Vendor Matching | `backend/src/skills/analysis/vendor_matching.py` |
| Browser (Playwright) | `backend/src/skills/browser/playwright_browser.py` |
| Enhanced Scraper | `backend/src/skills/browser/enhanced_scraper.py` |
| Vendor Scraper | `backend/src/skills/browser/vendor_scraper.py` |
| **Research Agents** | |
| Discover | `backend/src/agents/research/discover.py` |
| Refresh | `backend/src/agents/research/refresh.py` |
| CLI | `backend/src/agents/research/cli.py` |
| **Routes** | |
| Quiz | `backend/src/routes/quiz.py` |
| Interview | `backend/src/routes/interview.py` |
| Workshop | `backend/src/routes/workshop.py` |
| Admin Research | `backend/src/routes/admin_research.py` |
| Admin Insights | `backend/src/routes/admin_insights.py` |
| **Knowledge** | |
| Knowledge Base | `backend/src/knowledge/__init__.py` |
| Expertise | `backend/src/expertise/__init__.py` |
| **Frontend** | |
| Auth Context | `frontend/src/contexts/AuthContext.tsx` |
| Quiz Page | `frontend/src/pages/Quiz.tsx` |
| Report Viewer | `frontend/src/pages/ReportViewer.tsx` |
| Admin Dashboard | `frontend/src/pages/admin/AdminDashboard.tsx` |

---

## Common Tasks

### Add a new API route
→ See `.claude/reference/api-development.md`

### Add a new Agent tool
→ See `.claude/reference/skills.md`

### Add a new frontend page
1. Create page: `frontend/src/pages/<Name>.tsx`
2. Add route in `App.tsx`
3. Create API service if needed: `frontend/src/services/<name>.ts`
4. Add to navigation if appropriate

---

## Model Routing (Jan 2026)

Models are routed by task type using `backend/src/config/model_routing.py`.

### Model Tiers

| Tier | Claude | Gemini | Use Case |
|------|--------|--------|----------|
| Fast | `claude-haiku-4-5-20251001` | `gemini-3-flash-preview` | Extraction, validation, classification |
| Balanced | `claude-sonnet-4-5-20250929` | - | Generation tasks (quick tier) |
| Premium | `claude-opus-4-5-20251101` | `gemini-3-pro-preview` | Complex analysis, full tier reports |

### Usage
```python
from src.config.model_routing import get_model_for_task

model = get_model_for_task("generate_findings", tier="quick")  # Returns Sonnet
model = get_model_for_task("generate_findings", tier="full")   # Returns Opus
```

**DO NOT use:** `claude-3-5-*`, `gemini-2.0-*`, `gemini-1.5-*`

---

## System Evolution

> "Don't just fix the bug - fix the system that allowed the bug."

After fixing any bug or issue, run `/evolve` to analyze what could prevent it.

**Evolution log:** `docs/evolution-log.md` tracks all system improvements.

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
