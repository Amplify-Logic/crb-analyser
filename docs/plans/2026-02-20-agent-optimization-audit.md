# Agent Optimization Audit Report

> **Date**: 2026-02-20
> **Purpose**: Assess project setup for optimal continuous development with Claude Code, agent teams, and sub-agents
> **Methodology**: 6 parallel analysis agents covering config, structure, testing, skills, docs, and DX

---

## Executive Summary

**Overall Score: 7.8/10** - Well above average. The project has strong foundations (documentation, skills system, type safety) but has accumulated structural debt in file sizes and has gaps in testing/tooling that create agent friction.

**Top 3 wins already in place:**
1. Task-specific reference routing in CLAUDE.md (agents load only what they need)
2. Skills system with auto-discovery and type-safe registry (58 skills)
3. Domain documentation (PRODUCT.md, FRAMEWORK.md) is best-in-class

**Top 3 improvements with highest ROI:**
1. Fix CLAUDE.md accuracy (error handling section doesn't match actual code)
2. Seed MEMORY.md with project learnings (zero memory = zero cross-session learning)
3. Add backend linting (ruff) - prevents style drift across agent sessions

---

## Dimension Scores

| Dimension | Score | Key Issue |
|-----------|-------|-----------|
| CLAUDE.md & Config | 8.5/10 | Duplication with references, hooks undocumented |
| Codebase Structure | 7.0/10 | 3 god files over 2,400 lines each |
| Testing Infrastructure | 6.0/10 | Frontend 2% covered, CI doesn't enforce tests |
| Skills/Agent System | 8.0/10 | Skills excellent, no agent framework pattern |
| Documentation Quality | 8.6/10 | Excellent domain docs, skills.md too brief |
| DX & Tooling | 7.5/10 | No auto-formatting, no backend linting |

---

## Findings by Priority

### TIER 1 - High ROI, Low Effort (Do first)

#### 1.1 CLAUDE.md Error Handling Section Doesn't Match Code
- **Problem**: CLAUDE.md documents `CRBError(message, code, status)` but codebase uses `APIError` from `middleware/error_handler.py` with subclasses `NotFoundError`, `ValidationErrorAPI`, `AuthorizationError`
- **Impact**: Agents write wrong error handling patterns, then get blocked by validators
- **Fix**: Update CLAUDE.md to match actual implementation
- **Effort**: 10 minutes

#### 1.2 MEMORY.md Is Empty
- **Problem**: Zero cross-session learning despite 25+ executed plans
- **Impact**: Every new conversation starts from scratch; known pitfalls get repeated
- **Fix**: Seed MEMORY.md with project patterns, common issues, architectural decisions
- **Effort**: 15 minutes

#### 1.3 Add Backend Linting (ruff)
- **Problem**: No Python linting tool configured. Style drifts across agent sessions.
- **Impact**: Inconsistent code quality, import ordering varies
- **Fix**: Add `ruff` to requirements.txt + `ruff.toml` config
- **Effort**: 15 minutes

#### 1.4 Document Hooks in CLAUDE.md
- **Problem**: 6 domain-specific validators run on every Write/Edit but agents don't know they exist
- **Impact**: Agents are surprised by hook failures, waste turns debugging phantom errors
- **Fix**: Add "Hooks" section to CLAUDE.md listing validators and their triggers
- **Effort**: 10 minutes

#### 1.5 CI Doesn't Enforce Tests Properly
- **Problem**: Backend tests run with `|| true` (failures are silent). Frontend tests not run at all. mypy not in CI.
- **Impact**: Regressions ship silently, agents can't trust CI as quality gate
- **Fix**: Remove `|| true`, add `npm run test:run`, add `mypy` to CI pipeline
- **Effort**: 15 minutes

---

### TIER 2 - Medium ROI, Medium Effort (Do second)

#### 2.1 Remove Duplication Between CLAUDE.md and References
- **Problem**: Error handling pattern (10 lines) and logging pattern (8 lines) appear in both CLAUDE.md and api-development.md. Anti-patterns partially duplicated across 3 files.
- **Impact**: Wasted context window tokens (~200 tokens per load); risk of docs diverging
- **Fix**: Keep patterns in references, replace CLAUDE.md sections with one-line cross-references
- **Effort**: 20 minutes

#### 2.2 Expand skills.md Reference
- **Problem**: Only 76 lines. Covers structure but not enough detail for adding agents or understanding Tool vs Skill distinction.
- **Impact**: Agents must read base.py source code to understand the system
- **Fix**: Expand with: Tool vs Skill distinction, agent pattern, skill creation walkthrough
- **Effort**: 30 minutes

#### 2.3 Add pytest.ini Configuration
- **Problem**: No pytest.ini exists. Test markers (unit, integration, slow) not defined. No strict mode.
- **Impact**: Agents can't selectively run fast tests; slow tests block iteration speed
- **Fix**: Create `backend/pytest.ini` with markers and options
- **Effort**: 10 minutes

#### 2.4 Add Makefile for Common Tasks
- **Problem**: Agents must know separate commands for backend (pytest, mypy) and frontend (npm test, npm run lint). No unified interface.
- **Impact**: Extra cognitive overhead per agent turn; mistakes in command format
- **Fix**: Create root-level Makefile with `test`, `lint`, `typecheck`, `dev` targets
- **Effort**: 15 minutes

---

### TIER 3 - High ROI, Higher Effort (Plan separately)

#### 3.1 Split God Files
- **Problem**: Three files are too large for efficient agent editing
  - `backend/src/services/report_service.py` - 3,523 lines
  - `backend/src/routes/quiz.py` - 2,417 lines
  - `frontend/src/pages/Quiz.tsx` - 2,446 lines
- **Impact**: Agents load 2,000+ lines of context to edit 10 lines. Higher chance of edit conflicts. Context thrashing across turns.
- **Fix**: Split into focused modules (see Appendix A)
- **Effort**: 2-4 hours per file, requires careful testing
- **Note**: DO NOT do this casually. Each split needs its own plan with test verification.

#### 3.2 Frontend Test Infrastructure
- **Problem**: 2 test files for 104 source files (1.9% coverage)
- **Impact**: Agents can't do TDD for frontend features; no safety net for UI changes
- **Fix**: Establish test patterns for pages, hooks, services. Start with Quiz.tsx and ReportViewer.tsx.
- **Effort**: 8-10 hours for foundation + patterns

#### 3.3 Add Agent Base Class + Registry
- **Problem**: Agents (CRBAgent, PreResearchAgent) are hand-crafted with no shared pattern. No auto-discovery like skills have.
- **Impact**: Adding a 3rd agent requires reading existing agent code rather than following a pattern
- **Fix**: Create BaseAgent + AgentRegistry mirroring the skills pattern
- **Effort**: 2-3 hours

---

### NOT RECOMMENDED (Complexity exceeds value)

| Suggestion | Why Skip |
|------------|----------|
| OpenAPI/Swagger setup | FastAPI already auto-generates `/docs` endpoint. Adding custom OpenAPI config adds maintenance for minimal agent benefit. |
| Pre-commit hooks (husky) | Claude Code hooks already cover validation. Adding git-level hooks creates double-checking overhead. |
| Glossary.md | Domain terms are well-defined in PRODUCT.md and FRAMEWORK.md where they're used. A separate glossary creates sync burden. |
| Architecture Decision Records | Evolution log already serves this purpose. ADRs would duplicate it. |
| Agent composition framework | Only 2 agents exist. Framework is premature. Document the pattern first, abstract later. |

---

## Executable Plan

### Batch 1: Quick Fixes (45 minutes total)

**Task 1.1**: Update CLAUDE.md error handling to match actual code
- File: `CLAUDE.md` lines 169-180
- Replace `CRBError` example with actual `APIError` pattern from `backend/src/middleware/error_handler.py`

**Task 1.2**: Seed MEMORY.md with project knowledge
- File: `/Users/larsmusic/.claude/projects/-Users-larsmusic-CRB-Analyser-crb-analyser/memory/MEMORY.md`
- Content: Project patterns, common pitfalls, key architectural decisions, model routing notes

**Task 1.3**: Add ruff for backend linting
- Add `ruff==0.4.4` to `backend/requirements.txt`
- Create `backend/ruff.toml` with sensible defaults (line-length 120, select standard rules)

**Task 1.4**: Document hooks in CLAUDE.md
- Add "Active Hooks" section after "Development Rules" with table of validators and when they trigger

**Task 1.5**: Fix CI test enforcement
- File: `.github/workflows/deploy.yml`
- Remove `|| true` from pytest command
- Add `npm run test:run` for frontend
- Add `mypy` check (non-blocking initially with `|| true` until existing issues fixed)

### Batch 2: Documentation Improvements (1 hour)

**Task 2.1**: Deduplicate CLAUDE.md
- Replace error handling code block with: `> See .claude/reference/api-development.md for error handling patterns`
- Replace logging code block with: `> See .claude/reference/api-development.md for logging patterns`
- Keep anti-patterns section but remove items covered in references

**Task 2.2**: Expand skills.md
- Add section: "Tools vs Skills vs Agents" with clear distinction
- Add section: "Adding a New Agent" with template
- Add section: "Skill/Tool Relationship" explaining how Tools call Skills

**Task 2.3**: Add pytest.ini
- File: `backend/pytest.ini`
- Content: asyncio_mode, testpaths, markers (unit/integration/slow), strict options

**Task 2.4**: Create root Makefile
- Targets: `test-backend`, `test-frontend`, `test` (both), `lint`, `typecheck`, `dev`

### Batch 3: Structural (Plan separately per file)

**Task 3.1-3.3**: God file splits - Each requires its own `/plan-feature` cycle
**Task 3.4**: Frontend test foundation - Requires its own `/plan-feature` cycle
**Task 3.5**: Agent base class - Requires its own `/plan-feature` cycle

---

## Appendix A: God File Split Strategy

### report_service.py (3,523 lines) → 4 files
```
backend/src/services/report/
├── __init__.py          # Public API (re-exports)
├── generator.py         # Main orchestration (~800 lines)
├── findings.py          # Finding generation + processing (~1,000 lines)
├── recommendations.py   # Recommendation synthesis (~700 lines)
└── formatting.py        # Report formatting + PDF prep (~500 lines)
```

### quiz.py routes (2,417 lines) → 3 files
```
backend/src/routes/quiz/
├── __init__.py          # Router aggregation
├── sessions.py          # Session CRUD + management (~800 lines)
├── questions.py         # Question flow + adaptive logic (~900 lines)
└── research.py          # Research integration (~700 lines)
```

### Quiz.tsx (2,446 lines) → 4 files
```
frontend/src/pages/Quiz/
├── index.tsx            # Main page shell + routing (~300 lines)
├── QuizForm.tsx         # Question rendering + form logic (~800 lines)
├── useQuizState.ts      # State management hook (~600 lines)
└── QuizProgress.tsx     # Progress tracking + navigation (~400 lines)
```

---

## Appendix B: Proposed MEMORY.md Seed

```markdown
# CRB Analyser - Agent Memory

## Project Patterns
- Error handling uses `APIError` (not CRBError) from `middleware/error_handler.py`
- Skills auto-discovered by registry; agents are manually imported
- Model routing: use `get_model_for_task()` - never hardcode model names
- All costs in EUR; CRB formula: NET = Benefit - Cost - (Risk / 10)

## Common Pitfalls
- report_service.py is 3,500+ lines - read specific methods, not the whole file
- Quiz.tsx is 2,400+ lines - same approach
- CI uses `|| true` on tests - don't trust green CI without local verification
- Frontend has almost no tests - verify UI changes manually

## Architecture Decisions
- Skills = reusable code components (auto-discovered, type-safe)
- Tools = agent actions (registered per phase, OpenAI schema format)
- Agents = orchestrators (hand-crafted, phase-based)
- Knowledge base = JSON files in backend/src/knowledge/ (not DB)

## Hook Validators
- report_validator.py: Checks report quality on Write/Edit
- vendor_validator.py: Validates vendor data
- roi_math_validator.py: Validates financial calculations
- benchmark_source_validator.py: Checks data sources
- playbook_validator.py: Validates implementation playbooks
- industry_data_validator.py: Validates industry-specific data
```

---

## Appendix C: Proposed ruff.toml

```toml
line-length = 120
target-version = "py312"

[lint]
select = ["E", "F", "I", "W"]
ignore = ["E501"]  # Line length handled separately

[lint.isort]
known-first-party = ["src"]
```

---

## Appendix D: Proposed Makefile

```makefile
.PHONY: test test-backend test-frontend lint typecheck dev

test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest tests/ -v

test-frontend:
	cd frontend && npx vitest run

lint:
	cd backend && python -m ruff check src/
	cd frontend && npm run lint

typecheck:
	cd backend && python -m mypy src/ --ignore-missing-imports
	cd frontend && npx tsc --noEmit

dev:
	@echo "Start backend: cd backend && source venv/bin/activate && uvicorn src.main:app --reload --port 8383"
	@echo "Start frontend: cd frontend && npm run dev"
	@echo "Start Redis: brew services start redis"
```

---

## Appendix E: Proposed pytest.ini

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests (fast, no external deps)
    integration: Integration tests (may need Redis/Supabase)
    slow: Slow tests (LLM calls, network)
```
