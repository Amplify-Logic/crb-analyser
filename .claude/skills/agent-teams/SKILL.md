---
name: agent-teams
description: Multi-agent parallel builds using Claude Code agent teams. Use when a plan has 3+ independent components that can be built in parallel by separate agents. NOT for single-file changes, sequential tasks, or work that touches shared files.
---

# Agent Teams — Contract-First Parallel Builds

## When to Use (ALL must be true)

1. You have a **plan file** with clearly separable components
2. Components have **independent file ownership** (no two agents edit the same file)
3. At least **3 independent work streams** exist
4. The work is **substantial enough** to justify coordination overhead (~30+ min of single-agent work)

## When NOT to Use

- Bug fixes (use single session + `superpowers:systematic-debugging`)
- Features touching 1-3 files (use single session or `/execute`)
- Work requiring sequential steps (use `/execute` with plan)
- UI testing (use `/ui-test` with bowser-qa-agents)
- Research tasks (use subagents via Task tool)
- Anything where agents would edit the same files

## Decision Matrix

```
Single file change?          → Single session
Sequential steps?            → /execute [plan]
Independent research?        → Subagents (Task tool)
UI validation?               → /ui-test (bowser QA)
3+ independent modules?      → Agent Teams (this skill)
```

## Workflow

### Phase 1: Analyze Plan

Read the plan file. Identify:

1. **Independent components** — modules/features that don't share files
2. **Integration points** — where components must agree on interfaces
3. **Cross-cutting concerns** — things that span boundaries (auth, error handling, types)
4. **Optimal team size** — 2-5 agents (prefer fewer; more agents = more coordination cost)

### Phase 2: Define Contracts (BEFORE spawning agents)

For every integration point, specify:

- **API endpoints**: exact URLs with method, trailing slashes, query params
- **Data shapes**: exact JSON/TypeScript types, not prose descriptions
- **Events/streams**: exact event names and payload shapes
- **Error responses**: status codes and error body format
- **Shared types**: Pydantic models, TypeScript interfaces, or DB schemas

Write contracts as a markdown section that each agent receives.

**Contract quality checklist:**
- [ ] URLs exact (including trailing slashes)
- [ ] Response shapes are JSON, not prose
- [ ] Error responses specified per status code
- [ ] Shared model fields match exactly across agents
- [ ] Storage semantics clear (what gets cached, what doesn't)

### Phase 3: Assign Ownership

For each agent, define explicitly:

| Agent | Owns (exclusive) | Must NOT modify | Produces contract | Consumes contract |
|-------|-------------------|-----------------|-------------------|-------------------|
| Name  | List of files/dirs | List of files/dirs | What it exports | What it imports |

**Rules:**
- Every file touched by the plan must have exactly ONE owner
- Cross-cutting concerns get a single owner (usually the lead or most relevant agent)
- Shared types/models: one agent creates them, others import read-only

### Phase 4: Spawn and Execute

Use `TeamCreate` to create the team, then spawn teammates via Task tool with `team_name` parameter.

Each agent's prompt MUST include:
1. The full plan section relevant to their component
2. The integration contracts they produce and consume
3. Their exclusive file list and what NOT to touch
4. Acceptance criteria for their component
5. Cross-cutting concerns assigned to them

Spawn all agents in a single message for parallel execution.

**Agent configuration:**
- Use `mode: "plan"` if the component is risky or architectural
- Use Sonnet for straightforward implementation tasks to save cost
- Use Opus for complex logic, architecture decisions, or debugging

### Phase 5: Coordinate

The lead agent:
- Relays messages between agents when contracts need clarification
- Mediates if an agent needs to deviate from a contract
- Does NOT implement tasks itself (delegates everything)
- Monitors task list and reassigns stuck work

If the lead starts implementing instead of delegating:
> "Wait for your teammates to complete their tasks before proceeding."

### Phase 6: Validate

1. **Individual validation**: each agent runs their own tests and reports completion
2. **Contract verification**: lead checks that interfaces match across agents
3. **Integration test**: lead starts all services and runs end-to-end verification
4. **Cleanup**: shut down teammates, delete team

## CRB-Specific Patterns

### Common Team Compositions

**Full-stack feature:**
| Agent | Owns | Notes |
|-------|------|-------|
| Backend | `backend/src/routes/`, `backend/src/services/` (new files only) | FastAPI routes + services |
| Frontend | `frontend/src/pages/`, `frontend/src/components/` (new files only) | React components |
| Tests | `backend/tests/`, `frontend/src/` (test files only) | Both layers |

**Report enhancement:**
| Agent | Owns | Notes |
|-------|------|-------|
| Analysis | `backend/src/skills/analysis/` | New analysis skills |
| Generation | `backend/src/services/report_service.py` (specific methods only) | Report output |
| Frontend | `frontend/src/components/report/` | Report display |

**Multi-vendor research:**
| Agent | Owns | Notes |
|-------|------|-------|
| Researcher 1-N | Each gets distinct vendor categories | Use subagents instead if purely research |

### Files That Must NEVER Be Split

These files are too coupled for multi-agent work. Single owner only:
- `backend/src/services/report_service.py` (3,500+ lines, deeply coupled)
- `frontend/src/pages/Quiz.tsx` (2,400+ lines)
- `backend/src/routes/quiz.py` (2,400+ lines)
- Any migration file
- `CLAUDE.md`, `PRODUCT.md`, `STRATEGY.md`

### Integration with Existing Workflow

```
/plan-feature → plan.md
      ↓
  Review plan for parallelizable components
      ↓
  If 3+ independent components → /build-with-agent-team plan.md
  If sequential/coupled        → /execute plan.md
      ↓
  After build → /ui-test (bowser QA validates the result)
```

## Relationship to Other Tools

| Tool | Purpose | Communication |
|------|---------|---------------|
| **Agent Teams** (this) | Parallel BUILDING of independent components | Agents talk to each other |
| **Subagents** (Task tool) | Quick research, isolated tasks, code review | Report to caller only |
| **Bowser QA** (/ui-test) | UI VALIDATION after building | Independent per-story agents |
| **/execute** | Sequential plan execution in single session | N/A |

**Agent teams BUILD. Bowser QA VALIDATES. They're sequential, not alternatives.**
