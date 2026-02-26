---
name: build-with-agent-team
description: Orchestrate parallel multi-agent builds from a plan file using Claude Code agent teams
arguments:
  - name: plan-path
    description: Path to the plan markdown file (e.g., docs/plans/2026-02-21-feature.md)
    required: true
  - name: num-agents
    description: Number of agents to spawn (auto-determined if omitted)
    required: false
---

# Build with Agent Team

You are orchestrating a parallel build using Claude Code agent teams.

## Prerequisites Check

1. Verify `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is enabled (it's in `~/.claude/settings.json`)
2. Read the plan file: `$ARGUMENTS`

If no plan path provided, tell the user:
> "Usage: `/build-with-agent-team docs/plans/[plan-file].md [num-agents]`"
> "Create a plan first with `/plan-feature`."

## Step 1: Analyze the Plan

Read the plan file. Identify:

- **Independent components**: modules/features that don't share files
- **Integration points**: where components agree on interfaces (API contracts, shared types, DB schemas)
- **Cross-cutting concerns**: auth, error handling, logging, types that span boundaries
- **File ownership**: which files each component touches

**Gate check**: If fewer than 3 independent components exist, tell the user:
> "This plan has [N] independent components. Agent teams add overhead — recommend using `/execute [plan]` instead for sequential execution."

Only proceed if user confirms they still want a team.

## Step 2: Define Contracts

Before spawning any agents, write integration contracts for every boundary:

For API boundaries:
- Exact endpoint URLs (method, path, trailing slashes)
- Request/response JSON shapes (not prose)
- Error response format per status code
- Auth requirements

For shared data:
- Pydantic model definitions (backend)
- TypeScript interface definitions (frontend)
- Database schema if new tables

For events/streaming:
- SSE event types with exact payload JSON
- WebSocket message formats

Present contracts to user for review before proceeding.

## Step 3: Assign File Ownership

Create an ownership table:

| Agent | Role | Exclusive Files | Must NOT Touch | Produces | Consumes |
|-------|------|-----------------|----------------|----------|----------|

Rules:
- Every file in the plan has exactly ONE owner
- `report_service.py`, `Quiz.tsx`, `quiz.py` routes — single owner only (too coupled to split)
- Shared types: one agent creates, others import
- Migrations: single owner only

## Step 4: Determine Build Phases

Not all agents can start simultaneously. Identify dependencies:

```
Phase 1: Foundation (DB schemas, shared types, models)
Phase 2: Core (services, routes — after contracts from Phase 1)
Phase 3: Integration (frontend consuming backend, or cross-service work)
Phase 4: Validation (lead runs E2E)
```

Agents within the same phase run in parallel. Phases run sequentially.

## Step 5: Create Team and Spawn Agents

1. Use `TeamCreate` with a descriptive team name based on the feature
2. Use `TaskCreate` to create tasks from the plan (one per deliverable, not one per agent)
3. Spawn teammates via `Task` tool with `team_name` parameter

Each agent's spawn prompt MUST include:
- Their section of the plan
- Integration contracts (what they produce AND consume)
- Exclusive file list and off-limits files
- Acceptance criteria for their component
- Cross-cutting concerns assigned to them
- Instruction to use TDD (`superpowers:test-driven-development`)

Agent configuration:
- Use `mode: "plan"` for architectural/risky components
- Use Sonnet for straightforward implementation
- Use Opus for complex logic or debugging

## Step 6: Monitor and Coordinate

As lead, you:
- **DO** relay messages between agents when contracts need clarification
- **DO** mediate contract deviations
- **DO** reassign stuck tasks
- **DO** update user on progress
- **DO NOT** implement tasks yourself — delegate everything
- **DO NOT** let agents modify files outside their ownership

If an agent gets stuck:
1. Check if it's a contract issue (mediate)
2. Check if it's a dependency issue (unblock or reassign)
3. Check if it's a knowledge issue (provide context)

## Step 7: Validate and Cleanup

Once all agents report completion:

1. **Contract verification**: check that interfaces match across agents
2. **Build check**: ensure everything compiles/type-checks
3. **Test run**: run full test suite
4. **Shut down teammates**: send shutdown requests to all agents
5. **Clean up team**: use `TeamDelete`

After cleanup, suggest:
> "Build complete. Run `/ui-test` to validate the UI with Bowser QA agents."

## CRB-Specific Notes

- Load `.claude/reference/` docs relevant to each agent's domain
- All costs in EUR, CRB formula: NET = Benefit - Cost - (Risk / 10)
- Error handling: use `APIError` subclasses
- Logging: `structlog.get_logger()` with context kwargs
- Frontend: pnpm only (enforced by hook)
- Backend: FastAPI + Pydantic, mypy --strict
