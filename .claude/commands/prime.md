# Prime Command

Prime the conversation with essential project context. Run this at the start of any new conversation.

## Usage

```
/prime
```

## Instructions

**CLAUDE.md is already in context** — do NOT re-read it.

### Step 1: Check recent activity

Run these in parallel:
- `git log --oneline -10` — recent commits, current focus
- `ls -t docs/handoffs/ | head -3` — most recent handoff files
- `ls -t docs/plans/ | head -5` — recent plans

### Step 2: Read the latest handoff

Read only the **most recent** file from `docs/handoffs/` to understand where things left off.

### Step 3: Situational context (read only if needed)

| File | Read when... |
|------|-------------|
| `PRODUCT.md` | Task involves CRB framework, domain model, or industry logic |
| `STRATEGY.md` | Task involves business decisions, pricing, or positioning |

**Do NOT read these by default.** Most tasks (bug fixes, features, refactors) don't need them.

### Step 4: Summarize

Provide a brief summary:
- Current branch and recent focus (from git log)
- Last session's state (from handoff)
- Any in-flight plans worth noting (from plan filenames)

Then ask: **"What would you like to work on?"**

## Context Management

Keep context light. Load task-specific references ONLY when the task requires them — see CLAUDE.md for the reference table.
