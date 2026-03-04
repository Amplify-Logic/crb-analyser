# CRB Analyser - Development Guide

> **Domain concepts** → [PRODUCT.md](./PRODUCT.md) | **Business strategy** → [STRATEGY.md](./STRATEGY.md) | **Infrastructure** → [INFRASTRUCTURE.md](./INFRASTRUCTURE.md)

---

## Project Commands

| Command | When to Use |
|---------|-------------|
| `/prime` | Start of conversation - loads recent context |
| `/plan-feature` | Before implementing a feature |
| `/execute [plan.md]` | After context reset - executes a plan |
| `/create-prd` | After discussing a product idea |
| `/evolve` | After fixing a bug - prevents recurrence |
| `/build-with-agent-team [plan]` | 3+ independent components, no shared files |
| `/ui-test` | Validate UI with parallel Bowser QA agents |

**Default to `/execute`.** Only use agent teams when components are truly independent.

**Context reset between planning and execution:** `/plan-feature` → save to `docs/plans/` → clear context → `/execute [plan]`

---

## Task-Specific Reference

Load ONLY when working on the relevant task type:

| Working On | Read This |
|------------|-----------|
| API routes, backend services | `.claude/reference/api-development.md` |
| React components, frontend pages | `.claude/reference/frontend-development.md` |
| Report generation, findings | `.claude/reference/report-quality.md` |
| Vendor database, research agents | `.claude/reference/vendor-management.md` |
| Writing or fixing tests | `.claude/reference/testing.md` |
| Database, migrations, env vars | `.claude/reference/database.md` + [INFRASTRUCTURE.md](./INFRASTRUCTURE.md) |
| Skills system, agent tools | `.claude/reference/skills.md` |
| Knowledge base, curated insights | `.claude/reference/knowledge-base.md` |
| Browser automation, Cowork, Bowser QA | `.claude/reference/computer-use.md` |

**Do NOT load all references.** Only load what's relevant.

---

## Tech Stack

FastAPI + Python 3.12 | React 18 + Vite + TypeScript | Supabase (PostgreSQL + RLS) | Redis | Anthropic Claude API | Stripe | Railway

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

## Development Rules

### Code Quality
- **Type everything** — `mypy --strict` must pass
- **Test critical paths** — Auth, payments, report generation require 80%+ coverage

### Error Handling
Use `APIError` subclasses from `backend/src/middleware/error_handler.py`: `NotFoundError`, `ValidationErrorAPI`, `AuthorizationError`. See `.claude/reference/api-development.md` for patterns.

### Logging
Use `structlog.get_logger()` with context kwargs. See `.claude/reference/api-development.md`.

### Security
- RLS on all Supabase tables
- Pydantic validation on all inputs
- No raw errors to users in production
- Never log secrets or PII

### Performance
- Cache KB data 1hr, vendor pricing 15min
- Never cache user-specific data without key isolation

### Anti-Patterns (project-specific)
- No direct Supabase calls outside repository layer
- No business logic in route handlers (use services)
- No hardcoded IDs or magic strings
- No `# type: ignore` without explanation

---

## Active Hooks

Configured in `.claude/settings.local.json`. These run automatically and may block operations.

### PreToolUse

| Hook | Triggers On | Purpose |
|------|-------------|---------|
| `enforce-pnpm.sh` | Bash | Blocks npm, enforces pnpm |
| `protect-secrets.sh` | Bash, Read, Edit, Write | Blocks access to `.env`, credentials, secrets |

### PostToolUse

| Hook | Triggers On | Purpose |
|------|-------------|---------|
| `audit-commands.sh` | Bash | Logs executed commands |
| `report_validator.py` | Write, Edit | Validates report JSON structure and quality |
| `vendor_validator.py` | Write, Edit | Validates vendor data format |
| `roi_math_validator.py` | Write, Edit | Validates ROI/financial calculations |
| `benchmark_source_validator.py` | Write, Edit | Checks benchmark data sources |
| `playbook_validator.py` | Write, Edit | Validates implementation playbooks |
| `industry_data_validator.py` | Write, Edit | Validates industry-specific data |

**If a hook blocks:** Fix the data issue. Don't bypass hooks.

---

## Git Workflow

Branches: `main` | `feat/xxx` | `fix/xxx` | `refactor/xxx`

Commits: `feat:` | `fix:` | `refactor:` | `docs:` | `test:`

PR checklist: tests pass, `mypy --strict` passes, no console.log/print, error handling follows pattern, migrations reversible.

---

## Testing

```bash
cd backend && pytest                                    # All backend
cd backend && pytest -v tests/test_report_service.py    # Single file
cd frontend && npm test                                 # Frontend
```

---

## Model Routing

Use `get_model_for_task()` from `backend/src/config/model_routing.py` — never hardcode model names.

| Tier | Claude | Use Case |
|------|--------|----------|
| Fast | haiku-4-5 | Extraction, validation, classification |
| Balanced | sonnet-4-5 | Generation (quick tier) |
| Premium | opus-4-5 | Complex analysis (full tier) |

**DO NOT use:** `claude-3-5-*`, `gemini-2.0-*`, `gemini-1.5-*`

---

## Superpowers

**Enabled:** TDD, systematic-debugging, verification-before-completion, testing-anti-patterns, root-cause-tracing, brainstorming, code-reviewer

**Workflow:** Brainstorm → Create spec → TDD → QA review → Human review

---

## System Evolution

> "Don't just fix the bug — fix the system that allowed the bug."

After fixing any bug, run `/evolve`. Log: `docs/evolution-log.md`
