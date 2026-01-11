# Prime Command

Prime the conversation with essential project context. Run this at the start of any new conversation.

## Usage

```
/prime
```

## Superpowers Reminder

After priming, remember to use superpowers skills throughout the session:

| When | Skill |
|------|-------|
| Before coding any feature | `superpowers:brainstorming` |
| Writing code | `superpowers:test-driven-development` |
| Writing tests | `superpowers:testing-anti-patterns` |
| Debugging | `superpowers:systematic-debugging` |
| Before claiming done | `superpowers:verification-before-completion` |
| After major steps | `superpowers:requesting-code-review` |

## Instructions

Read the following files to understand the project:

1. **CLAUDE.md** - Development guidelines, commands, reference pointers
2. **PRODUCT.md** - Domain model, CRB framework, target industries
3. **STRATEGY.md** - Business strategy, decision framework

Then provide a brief summary:
- Current focus area
- Key services involved
- Any blockers or recent issues from git log

## After Priming

Check for pending work:
- `docs/handoffs/` - Recent session summaries
- `docs/plans/` - Pending feature plans
- `docs/evolution-log.md` - Recent system improvements

Ask: "What would you like to work on?"

## Context Management

Keep context light. Load task-specific reference ONLY when needed:

| Task Type | Load Reference |
|-----------|----------------|
| API development | `.claude/reference/api-development.md` |
| Frontend work | `.claude/reference/frontend-development.md` |
| Report generation | `.claude/reference/report-quality.md` |
| Vendor database | `.claude/reference/vendor-management.md` |
| Testing | `.claude/reference/testing.md` |

## Quick Reference

After priming, the main project commands available:

| Command | Purpose |
|---------|---------|
| `/plan-feature` | Create implementation plan (uses brainstorming + write-plan skills) |
| `/execute [plan.md]` | Execute plan after context reset |
| `/create-prd` | Generate PRD from discussion |
| `/evolve` | Improve system after fixing bugs |
