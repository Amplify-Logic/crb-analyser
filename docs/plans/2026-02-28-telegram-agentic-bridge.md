# Telegram Agentic Bridge — Handoff Doc

> **Created:** 2026-02-28 | **Status:** Ready for implementation | **Priority:** High
> **Context:** Session where we stood up Telegram bot in polling mode, fixed 5 bugs, and proved the `/code` bridge works end-to-end.

---

## What Was Done This Session

### Bugs Fixed

| # | Bug | Root Cause | Fix |
|---|-----|-----------|-----|
| 1 | Voice notes crash: `Attribute 'text' of class 'Message' can't be set!` | python-telegram-bot v20+ makes Message immutable | Extracted `route_text(update, text)` in message_handler.py; voice.py calls it directly |
| 2 | `/leads` fails: `column quiz_sessions.industry does not exist` | Old code selected `industry` column; table stores it in `answers` JSONB | Already fixed in code; restart picked up the fix |
| 3 | `/briefing` fails: same `industry` column error | Same root cause as #2 | Same fix |
| 4 | `/code` fails: `Claude Code cannot be launched inside another Claude Code session` | `CLAUDECODE` env var inherited by subprocess | Strip `CLAUDECODE` from subprocess env in claude_code_handler.py |
| 5 | Conversation handler dead end — "Hi" returns canned command list | `_handle_conversation()` was static text | Replaced with Claude Haiku LLM call |
| 6 | Voice questions classified as `idea` instead of `query` | Router prompt too vague — "What can we do to improve..." matched "what if" | Sharpened classification prompt; added rule: "If a message is a question, classify as query not idea" |
| 7 | Query handler dead end — "Data queries available in Phase 5" | `_handle_query()` was a stub | Replaced with Claude Sonnet LLM call with CRB business context |

### Files Modified

```
backend/src/telegram/voice.py                         # Voice routing fix
backend/src/telegram/handlers/message_handler.py      # route_text(), LLM conversation + query handlers
backend/src/telegram/handlers/claude_code_handler.py  # CLAUDECODE env var fix
backend/src/telegram/router.py                        # Sharpened classification prompt
.claude/skills/telegram/SKILL.md                      # New skill for bot dev loop
```

### What Works Now

- **All CRB commands:** /health, /reports, /leads, /vendors, /briefing
- **GTD system:** /capture, /next, /projects, /waiting, /someday, /idea, /review
- **Voice notes:** Transcribe via Whisper, route through intent classifier
- **Natural language:** Questions get LLM answers, ideas get captured
- **`/code` bridge:** Spawns `claude --print`, returns analysis (read-only, up to 5 min)
- **Notifications:** Payments, reports, leads, scheduler jobs push to Telegram

---

## The Big Upgrade: Full Agentic Bridge

### Current State (Read-Only)

```
User: /code fix the quiz validation bug
  → Bot: "Sending to Claude Code..."
  → Subprocess: claude --print --output-format text --max-turns 10 "fix the quiz..."
  → [5 min silence]
  → Bot: [text analysis, no changes made]
```

**Limitations:**
- `--print` = read-only analysis, no file edits, no bash commands
- No streaming — user stares at nothing for minutes
- No progress feedback — no idea what's happening
- 5 min timeout — complex tasks get killed
- No session memory — each call is independent
- No background execution — blocks the bot for other commands

### Target State (Full Agentic)

```
User: /code fix the quiz validation bug
  → Bot: "Starting task #42. I'll update you as I go."
  → [Background]: claude --output-format stream-json --max-turns 25 "fix the quiz..."
  → Bot: "Reading quiz.py and test files..."
  → Bot: "Found the bug — missing validation on line 342"
  → Bot: "Editing quiz.py..."
  → Bot: "Running tests... 47/47 passed"
  → Bot: "Done. Fixed quiz validation — added input sanitization. [diff summary]"
```

---

## Implementation Plan

### Task 1: Streaming Progress to Telegram

**What:** Replace `process.communicate()` (wait-for-all) with line-by-line stdout reading. Parse `stream-json` output and send meaningful progress to Telegram.

**Key changes:**
- `--output-format stream-json` instead of `--output-format text`
- Read stdout line-by-line with `async for line in process.stdout`
- Parse JSON events: `assistant`, `tool_use`, `result`, `error`
- Throttle Telegram updates (max 1 per 5 seconds to avoid rate limits)
- Show: "Reading file X...", "Editing file Y...", "Running command Z..."

**Files:**
- `backend/src/telegram/handlers/claude_code_handler.py` — rewrite `_run_claude_code()`

### Task 2: Drop `--print` for Full Agentic Mode

**What:** Remove `--print` flag so Claude Code can edit files, run bash, use all tools.

**Key changes:**
- Remove `--print` from command
- Add `--dangerously-skip-permissions` for autonomous operation (operator-only bot, admin-gated)
- Increase `--max-turns` to 25-50
- Increase timeout to 15-30 minutes
- Add `--append-system-prompt` with CRB context (model routing rules, file structure)

**Risk:** This lets Claude Code make real changes to the codebase from Telegram. Mitigated by:
- Admin guard (only operator's chat ID)
- Git: all changes are committed and reversible
- Can add `--allowedTools` to restrict dangerous operations

**Files:**
- `backend/src/telegram/handlers/claude_code_handler.py`

### Task 3: Background Execution with Task Tracking

**What:** Don't block the bot while Claude Code runs. Execute in background, track tasks, notify on completion.

**Key changes:**
- Create task tracking: `_active_tasks: dict[str, TaskInfo]` with task ID, status, start time, output buffer
- Run subprocess in `asyncio.create_task()` (non-blocking)
- Return task ID immediately: "Started task #42"
- Store streaming output in buffer
- Send completion notification with summary
- Add `/tasks` command — list active/recent tasks
- Add `/cancel <id>` — kill a running task

**Files:**
- `backend/src/telegram/handlers/claude_code_handler.py` — background execution
- `backend/src/telegram/bot.py` — register /tasks and /cancel commands

### Task 4: Session Memory / Conversation Context

**What:** Let Claude Code remember previous interactions so the operator can iterate.

**Key changes:**
- Option A: Use `--resume` flag with session ID (Claude Code native sessions)
- Option B: Use `--continue` to continue the last conversation
- Track session ID per Telegram chat
- Add `/code-new` to start fresh session, `/code` continues last one
- Pass previous task summary as context to new calls

**Files:**
- `backend/src/telegram/handlers/claude_code_handler.py` — session management

### Task 5: Smart Output Formatting

**What:** Claude Code output is verbose. Format it for Telegram's constraints.

**Key changes:**
- Parse stream-json to extract: files changed, commands run, test results, final summary
- Format diff summaries (not full diffs — Telegram isn't a code review tool)
- Collapse verbose output into expandable sections
- Use Telegram markdown formatting
- For very long output: save full log, send summary + "Full log saved to /tmp/task-42.log"

**Files:**
- `backend/src/telegram/handlers/claude_code_handler.py` — output formatting

### Task 6: Voice-to-Code Pipeline

**What:** Send a voice note → transcription → Claude Code executes it as a coding task.

**Key changes:**
- When voice message classifies as `code` intent, route to `/code` handler
- Already partially works (router classifies, message_handler routes)
- Need to wire `route_text()` code intent to actually call `cmd_code()` logic
- Add "thinking..." feedback while transcription + classification happens

**Files:**
- `backend/src/telegram/handlers/message_handler.py` — wire code intent
- `backend/src/telegram/voice.py` — feedback UX

### Task 7: Safety Rails

**What:** Prevent catastrophic operations from Telegram.

**Key changes:**
- Blocklist for dangerous patterns: `rm -rf`, `git push --force`, `DROP TABLE`, `--no-verify`
- Confirmation flow for destructive ops: "This will push to main. Reply /confirm to proceed."
- Rate limiting: max 3 concurrent tasks, max 10 tasks per hour
- Auto-commit after changes with descriptive message
- `/undo` command — `git revert` last Claude Code commit

**Files:**
- `backend/src/telegram/handlers/claude_code_handler.py` — safety checks
- `backend/src/telegram/bot.py` — register /confirm, /undo commands

---

## Architecture Diagram

```
Telegram (Voice/Text)
    │
    ▼
Intent Router (Haiku) ──→ query/idea/gtd/conversation handlers
    │
    ▼ (code intent)
Claude Code Bridge
    │
    ├─ Parse & validate input
    ├─ Safety rail check
    ├─ Spawn background task
    │     │
    │     ▼
    │   claude --output-format stream-json
    │   --max-turns 25
    │   --dangerously-skip-permissions
    │   --append-system-prompt "CRB context..."
    │     │
    │     ├─ Stream: progress → Telegram (throttled)
    │     ├─ Stream: tool_use → "Editing file X..."
    │     └─ Stream: result → format summary → Telegram
    │
    ├─ Track task state (id, status, output)
    ├─ /tasks — list active
    ├─ /cancel — kill task
    └─ /undo — revert last commit
```

## Execution Order

| Phase | Tasks | Effort | Unlocks |
|-------|-------|--------|---------|
| **A** | Task 1 (streaming) + Task 2 (drop --print) | 2-3 hrs | Real agentic execution with progress |
| **B** | Task 3 (background) + Task 5 (formatting) | 2-3 hrs | Non-blocking, readable output |
| **C** | Task 7 (safety) | 1-2 hrs | Safe for daily use |
| **D** | Task 4 (sessions) + Task 6 (voice-to-code) | 2-3 hrs | Full command center UX |

**Phase A is the game-changer.** Everything else is polish.

---

## Quick Start

```bash
# Load context
/prime

# Execute this plan
/execute docs/plans/2026-02-28-telegram-agentic-bridge.md

# Or start the bot for testing
/telegram
```

## Key Decisions Needed

1. **Permission model:** `--dangerously-skip-permissions` (full auto) vs `--allowedTools` (restricted)?
   - Recommendation: Start with full auto, add safety rails (Task 7) as guardrails instead
2. **Session persistence:** In-memory (lost on restart) vs Redis (durable)?
   - Recommendation: In-memory for now, migrate to Redis if needed
3. **Max concurrent tasks:** How many parallel Claude Code instances?
   - Recommendation: 3 (each uses ~250MB RAM + API tokens)
4. **Auto-commit:** Should Claude Code auto-commit after changes?
   - Recommendation: Yes, with descriptive messages — makes /undo trivial
