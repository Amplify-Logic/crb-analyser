# CRB Analyser - AI Coding Workflow Guide

How to use the agentic coding system effectively.

---

## TL;DR - Daily Workflow

```
1. Start conversation     → /prime
2. Discuss what to build  → superpowers:brainstorming
3. Ready to plan?         → /plan-feature (uses superpowers:write-plan)
4. Plan approved?         → CLEAR CONTEXT (new conversation)
5. Execute                → /execute docs/plans/[your-plan].md
6. Fixed a bug?           → /evolve
```

---

## Two Systems Working Together

This project uses **two complementary systems**:

### Superpowers (Core Skills)
Universal AI coding skills that work on any project:

| Skill | When to Use |
|-------|-------------|
| `superpowers:brainstorming` | Before coding anything - refines ideas |
| `superpowers:write-plan` | Creates detailed implementation plans |
| `superpowers:execute-plan` | Executes plans with checkpoints |
| `superpowers:test-driven-development` | Always - write test first |
| `superpowers:testing-anti-patterns` | When writing tests |
| `superpowers:systematic-debugging` | When something breaks |
| `superpowers:root-cause-tracing` | For deep/tricky bugs |
| `superpowers:verification-before-completion` | Before claiming "done" |
| `superpowers:requesting-code-review` | After major steps |

### Project Commands (CRB-Specific)
Wrappers that add CRB context to superpowers:

| Command | Superpowers It Uses |
|---------|---------------------|
| `/prime` | None - loads CRB context |
| `/plan-feature` | brainstorming → write-plan |
| `/execute` | execute-plan + TDD |
| `/create-prd` | None - CRB-specific format |
| `/evolve` | Complements systematic-debugging |

**The project commands call superpowers automatically.** You don't need to invoke both.

---

## The Commands

### `/prime` - Start Every Conversation

**When:** First thing in any new Claude Code conversation.

**What it does:** Loads essential project context (CLAUDE.md, PRODUCT.md, current roadmap).

**Example:**
```
You: /prime
Claude: [Reads project files, understands current state]
Claude: "I've loaded the CRB Analyser context. Based on the PRD and current roadmap,
         the next priority appears to be [X]. What would you like to work on?"
```

---

### `/plan-feature` - Before Building Anything

**When:** After discussing a feature and agreeing on what to build.

**What it does:** Creates a structured implementation plan with tasks, files to modify, and verification steps.

**Output:** Saves to `docs/plans/[date]-[feature-slug].md`

**Example:**
```
You: I want to add a dark mode toggle to the report viewer
Claude: [Discussion about approach, components affected]
You: /plan-feature
Claude: [Creates structured plan with tasks]
Claude: "Plan saved to docs/plans/2026-01-08-dark-mode-toggle.md"
```

---

### `/execute [plan-path]` - Run After Context Reset

**When:** After clearing context, to execute a plan with minimal noise.

**What it does:** Reads ONLY the plan file and executes it task by task.

**Why clear context first?** Keeps the context window light during coding, leaving room for Claude to reason about implementation details.

**Example:**
```
[New conversation or /clear]
You: /execute docs/plans/2026-01-08-dark-mode-toggle.md
Claude: [Reads plan, starts executing tasks one by one]
```

---

### `/create-prd` - Document a Product Idea

**When:** After brainstorming a new feature or product with Claude.

**What it does:** Generates a complete Product Requirements Document from the conversation.

**Output:** Saves to specified path (default: `docs/plans/PRD-[slug].md`)

**Example:**
```
You: I want to add a feature where users can compare vendors side by side
Claude: [Discussion about requirements, UX, edge cases]
You: /create-prd
Claude: [Generates PRD with user stories, architecture, success metrics]
```

---

### `/evolve` - After Fixing Any Bug

**When:** Immediately after fixing a bug or issue.

**What it does:** Analyzes what went wrong and suggests improvements to:
- Rules (CLAUDE.md or reference files)
- Commands (validation steps, checklists)
- Reference docs (new patterns to document)

**Output:** Updates `docs/evolution-log.md` with the improvement.

**Example:**
```
You: [Just fixed a bug where vendor pricing wasn't being validated]
You: /evolve
Claude: "The bug occurred because there's no validation step in the vendor
         update flow. I'll add a pricing validation rule to
         .claude/reference/vendor-management.md and log this in evolution-log.md"
```

---

## The Context Reset Pattern

This is the most important workflow to internalize.

### Why Reset Context?

- Planning uses lots of context (exploring code, discussing options)
- Execution needs room for reasoning about implementation
- A "heavy" context window = worse code quality

### The Pattern

```
PLANNING PHASE (conversation 1)
├── /prime
├── Discuss the feature
├── Explore the codebase
├── /plan-feature
└── Output: docs/plans/[plan].md

─────────── CONTEXT RESET ───────────

EXECUTION PHASE (conversation 2)
├── /execute docs/plans/[plan].md
├── Claude reads ONLY the plan
├── Implements task by task
└── Verifies each task before moving on
```

### How to Reset

**Option 1:** Start a new conversation
```
[Close terminal, open new one]
claude
/execute docs/plans/your-plan.md
```

**Option 2:** Use /clear (keeps same session)
```
/clear
/execute docs/plans/your-plan.md
```

---

## Reference Files - When to Load What

Reference files contain detailed patterns for specific task types. Claude will load them automatically when working on relevant tasks (based on the CLAUDE.md reference section).

| If You're Working On | Claude Should Load |
|----------------------|-------------------|
| API routes, backend services | `.claude/reference/api-development.md` |
| React components, pages | `.claude/reference/frontend-development.md` |
| Report generation, findings | `.claude/reference/report-quality.md` |
| Vendor database, research | `.claude/reference/vendor-management.md` |
| Writing tests, fixing test failures | `.claude/reference/testing.md` |

### Manual Loading

If Claude doesn't auto-load the right reference, just ask:
```
You: "Load the testing reference before we write these tests"
You: "Check the report-quality reference for anti-slop rules"
```

---

## System Evolution - The Habit

**The principle:** Every bug is an opportunity to make the system stronger.

### After Fixing Any Bug

1. Run `/evolve`
2. Claude analyzes what allowed the bug
3. Claude suggests a system improvement
4. Improvement gets logged in `docs/evolution-log.md`

### What Gets Improved

| Layer | Example Improvement |
|-------|---------------------|
| **Rules** | "Add rule: always validate vendor pricing format before insert" |
| **Commands** | "Add step to /plan-feature: identify affected test files" |
| **Reference** | "Document the async Supabase pattern in api-development.md" |

### Why This Matters

Over time, your AI coding system gets smarter:
- Fewer repeated mistakes
- Better code quality
- Faster development

The evolution log (`docs/evolution-log.md`) tracks all improvements so you can see the system getting better.

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│  CRB ANALYSER - COMMAND QUICK REFERENCE                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  PROJECT COMMANDS (CRB-specific)                        │
│  /prime              Start of conversation              │
│  /plan-feature       Before implementing                │
│  /execute [path]     After context reset                │
│  /create-prd         After discussing product idea      │
│  /evolve             After fixing a bug                 │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  SUPERPOWERS (Always available)                         │
│  superpowers:brainstorming          Refine ideas        │
│  superpowers:test-driven-development  TDD always        │
│  superpowers:systematic-debugging   Fix bugs            │
│  superpowers:verification-before-completion  Check done │
│  superpowers:requesting-code-review Review work         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  WORKFLOW                                               │
│                                                         │
│  Prime → Brainstorm → Plan → RESET → Execute → Evolve  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  KEY FILES                                              │
│                                                         │
│  docs/plans/              Feature plans live here       │
│  docs/evolution-log.md    System improvements log       │
│  .claude/commands/        Command definitions           │
│  .claude/reference/       Task-specific patterns        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Example: Complete Feature Workflow

### Day 1: Planning

```bash
# Start Claude Code
claude

# Load context
/prime

# Discuss the feature
You: "I want to add email notifications when a report is ready"
Claude: [Asks clarifying questions, explores notification options]

# Create the plan
You: /plan-feature
Claude: [Creates docs/plans/2026-01-08-email-notifications.md]

# Review and approve the plan
You: "Looks good, let's do it tomorrow"
```

### Day 2: Execution

```bash
# Fresh conversation (context reset)
claude

# Execute the plan
/execute docs/plans/2026-01-08-email-notifications.md

# Claude implements task by task
Claude: [Implements email service]
Claude: [Adds API endpoint]
Claude: [Updates report generation to trigger email]
Claude: [Adds tests]
Claude: "All tasks complete. Tests passing."
```

### After Finding a Bug

```bash
You: "The email wasn't sending because the BREVO_API_KEY wasn't being checked"
You: [Fix the bug]

# Improve the system
/evolve

Claude: "I'll add a startup check for required API keys to the
         api-development.md reference file and log this improvement."
```

---

## Tips

### Project Commands
1. **Don't skip /prime** - It's tempting to dive in, but context matters

2. **Plans are artifacts** - They live in `docs/plans/` and can be re-executed if interrupted

3. **Context reset is non-negotiable** - Heavy context = bad code. Reset between plan and execute.

4. **Evolve religiously** - The 30 seconds you spend on `/evolve` saves hours of repeated bugs

### Superpowers
5. **Superpowers are mandatory** - If a superpowers skill applies, it MUST be used

6. **TDD is non-negotiable** - Write the test first, watch it fail, then implement

7. **Verify before "done"** - Always use `verification-before-completion` before claiming success

8. **Brainstorm before coding** - Even if you think you know what to build, brainstorming finds gaps

### Both Systems
9. **Project commands call superpowers** - You don't need to invoke both manually

10. **Reference files are for Claude** - You don't need to read them, but you can if curious

11. **Evolution log is your history** - Review it occasionally to see how the system improved
