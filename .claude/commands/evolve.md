# Evolve Command

Improve the AI coding system after fixing a bug. Every bug is an opportunity to make the system stronger.

## Usage

```
/evolve
```

Run this immediately after fixing any bug or issue.

## Philosophy

> "Don't just fix the bug - fix the system that allowed the bug."

## Superpowers Integration

This command complements superpowers debugging skills:

| Skill | Purpose |
|-------|---------|
| `superpowers:systematic-debugging` | Find and fix the bug |
| `superpowers:root-cause-tracing` | Understand deep causes |
| **`/evolve`** | Prevent the bug CLASS forever |

The debugging skills help you FIX the bug. `/evolve` helps you prevent the entire CLASS of bugs.

## Instructions

### 1. Classify the Bug

What TYPE of bug was this?

| Bug Class | Example |
|-----------|---------|
| Validation | Missing input check, wrong format |
| Integration | API contract mismatch, wrong endpoint |
| State | Race condition, stale data |
| Logic | Wrong calculation, missing edge case |
| Configuration | Missing env var, wrong setting |

### 2. Identify System Gap

What could have PREVENTED this?

| Gap Type | Fix Location |
|----------|--------------|
| Missing rule | CLAUDE.md or reference doc |
| Missing step | Command template |
| Missing pattern | Reference doc |
| Missing test | Testing reference |

### 3. Check Each Layer

#### Rules (CLAUDE.md, .claude/reference/)
- Is there a rule that should have prevented this?
- Is an existing rule unclear?
- Should we add an anti-pattern?

#### Commands (.claude/commands/)
- Should a command include additional validation?
- Is there a missing command?
- Should the plan template include this check?

#### Reference Docs (.claude/reference/)
- Is there missing context for this task type?
- Should we document this pattern?

### 4. Propose Changes

```markdown
## Proposed System Updates

### 1. Add to [file]
**Section:** [section name]
**Add:**
- [specific rule or pattern]

### 2. Update [command].md
**Add to checklist:**
- [ ] Check for [specific thing]
```

### 5. Implement and Log

After user approval:
1. Make the edits
2. Log in `docs/evolution-log.md`:

```markdown
## [Date] - [Brief Description]

**Symptom:** What went wrong

**Root cause:** Why it happened

**Bug class:** [Validation / Integration / State / Logic / Configuration]

**System fix:**
- [File changed]: [What was added/modified]

**Prevents:** [What class of bugs this prevents]
```

## Anti-Patterns for Evolution

- Adding rules for one-time issues (only patterns)
- Making rules too specific (should be generalizable)
- Adding process without removing friction elsewhere
- Forgetting to update related docs

## After Evolving

Confirm to user:
> "System improved. Added [description] to [file]. Logged in docs/evolution-log.md.
> This prevents [bug class] in the future."
