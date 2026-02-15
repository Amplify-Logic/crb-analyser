# Observability & Development Tools Guide

This document explains observability tools (BetterStack) and development automation (Claude Code Hooks) for CRB Analyser. Written as a learning resource.

---

## Part 1: Why Observability Matters

### The Problem Without Observability

Imagine a user completes the quiz, pays €147, but never receives their report. Without observability:

1. **You don't know it happened** - User has to email you
2. **You can't find the cause** - Was it Stripe? Claude API? Database? Network?
3. **You can't see patterns** - Is this happening to 1% of users? 10%?
4. **You can't prove it's fixed** - After deploying a fix, how do you know?

### What Observability Provides

| Tool | What It Does | CRB Example |
|------|--------------|-------------|
| **Logs** | Record events as they happen | "Quiz completed", "Payment received", "Report started" |
| **Metrics** | Aggregate numbers over time | "Average report generation: 45s", "95th percentile: 120s" |
| **Traces** | Follow a request through services | Quiz → Payment → Report Generation → PDF → Email |
| **Alerts** | Notify when things go wrong | "Report generation failed 3 times in 5 minutes" |
| **Error Tracking** | Capture and group errors | "TypeError in vendor_matching.py line 47 (happened 23 times)" |

### Real CRB Scenario

```
User Journey:
1. Completes quiz (quiz_session: abc123)
2. Pays via Stripe (payment_intent: pi_xyz)
3. Report generation starts
4. Claude API call fails (rate limit)
5. User sees "Error generating report"

With Observability:
- Search logs for quiz_session=abc123
- See the full trace: quiz → payment → report → FAILED
- Click into the error: "Claude API rate limit exceeded"
- See it's happening to 5% of users during peak hours
- Get Slack alert before users start emailing
```

---

## Part 2: BetterStack

### What Is BetterStack?

BetterStack is an integrated observability platform. Think of it as:
- **Logs** - Like a searchable, structured console.log for production
- **Uptime** - Checks if your site is up every 30 seconds
- **Incidents** - Alerts you via Slack/phone when things break
- **Status Page** - Shows users if there's a known issue

### Why BetterStack vs Alternatives?

| Tool | Cost | Strengths | Weaknesses |
|------|------|-----------|------------|
| **Datadog** | $$$$ | Full-featured, industry standard | Very expensive at scale |
| **Sentry** | $$$ | Great error tracking | Logs are secondary |
| **Logfire** | $$ | Python-native, Pydantic integration | Newer, smaller ecosystem |
| **BetterStack** | $ | 30x cheaper than Datadog, unified | Less mature tracing |

**BetterStack's pitch**: "Ingest all your logs, not just a sample, at 1/30th the cost."

### How BetterStack Works

```
Your App                    BetterStack
┌─────────────────┐        ┌─────────────────┐
│ Python Logger   │───────>│ Log Ingestion   │
│ (logtail-python)│  HTTPS │                 │
└─────────────────┘        │ Stores in       │
                           │ ClickHouse DB   │
                           │                 │
                           │ Query with SQL  │
                           │ Get Alerts      │
                           └─────────────────┘
```

### What We Log

```python
# Request lifecycle
logger.info("quiz_started", quiz_session_id="abc123", industry="dental")
logger.info("quiz_completed", quiz_session_id="abc123", question_count=7)
logger.info("payment_completed", quiz_session_id="abc123", amount_eur=147)
logger.info("report_generation_started", quiz_session_id="abc123", tier="quick")
logger.info("report_generated", quiz_session_id="abc123", duration_s=45.2, findings=8)

# Errors
logger.error("claude_api_failed", quiz_session_id="abc123", error="rate_limit", model="sonnet")
logger.error("stripe_webhook_failed", event_type="checkout.completed", error="missing_metadata")
```

### Querying Logs (SQL)

```sql
-- Find all failures in the last hour
SELECT * FROM logs
WHERE level = 'error'
AND dt > now() - INTERVAL 1 HOUR
ORDER BY dt DESC;

-- Calculate report generation p95
SELECT quantile(0.95)(duration_s) as p95_duration
FROM logs
WHERE message = 'report_generated'
AND dt > now() - INTERVAL 24 HOUR;

-- Find a specific user's journey
SELECT * FROM logs
WHERE quiz_session_id = 'abc123'
ORDER BY dt ASC;
```

### Setting Up BetterStack

1. **Create Account**: https://betterstack.com (free tier available)
2. **Create Source**: Logs → Sources → Create → Python
3. **Get Token**: Copy the source token (looks like `xxxxxxxxxxxxxxx`)
4. **Set Environment Variable**: `BETTERSTACK_SOURCE_TOKEN=xxxxx`

---

## Part 3: Claude Code Hooks

### What Are Hooks?

Hooks are scripts that run automatically when Claude Code does something. They're like GitHub Actions but for your AI coding assistant.

```
Before Claude runs `npm install`:
  → Your hook runs
  → Hook returns exit code 2 with message "Use pnpm instead"
  → Claude sees the error and uses pnpm instead
```

### Why Hooks Matter

Without hooks, you have to manually:
- Watch every command Claude runs
- Catch mistakes after they happen
- Remember to tell Claude your preferences each session

With hooks:
- Automatic enforcement of project standards
- Prevention of mistakes before they happen
- Consistent behavior across sessions

### Hook Types

| Type | When It Runs | Use Case |
|------|--------------|----------|
| `PreToolUse` | Before a tool executes | Block/modify commands |
| `PostToolUse` | After a tool executes | Audit logging, validation |
| `Notification` | When Claude sends a notification | Phone alerts, sounds |
| `Stop` | When Claude stops | Cleanup, summary |
| `SubAgentStop` | When a sub-agent finishes | Chain tasks |

### How Hooks Work

```
┌─────────────────┐
│ Claude wants to │
│ run `npm install`│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PreToolUse Hook │ ← Your script runs here
│ (checks command)│
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
 Exit 0    Exit 2
 (allow)   (block + message)
    │         │
    ▼         ▼
┌─────────┐ ┌─────────────────┐
│ Command │ │ Claude sees     │
│ runs    │ │ error message   │
└─────────┘ │ and adjusts     │
            └─────────────────┘
```

### Exit Codes

| Code | Meaning | Effect |
|------|---------|--------|
| 0 | Success | Tool proceeds |
| 1 | Error | Hook failed (not shown to Claude) |
| 2 | Block | Error message shown to Claude, tool blocked |

### Hook Input (JSON)

When your hook script runs, it receives JSON on stdin:

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm install lodash",
    "description": "Install lodash package"
  },
  "session_id": "abc123"
}
```

### Example: Enforce pnpm

```bash
#!/bin/bash
# .claude/hooks/enforce-pnpm.sh

# Read the JSON input
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // ""')

# Check if it's using npm
if [[ "$command" == npm* ]]; then
  echo "Please use pnpm instead of npm in this project."
  exit 2
fi

exit 0
```

### Example: Block Sensitive Files

```bash
#!/bin/bash
# .claude/hooks/protect-secrets.sh

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')

# Block access to secret files
if [[ "$file_path" == *".env"* ]] || [[ "$file_path" == *"credentials"* ]]; then
  echo "Access to sensitive files is blocked. These files contain secrets."
  exit 2
fi

exit 0
```

### Example: Audit Logging

```bash
#!/bin/bash
# .claude/hooks/audit-log.sh

# Log all commands to a file for review
input=$(cat)
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "$timestamp $input" >> ~/.claude-audit.log

exit 0  # Always allow, just log
```

### Example: Notification Sound

```bash
#!/bin/bash
# .claude/hooks/notify-sound.sh

# Play a sound when Claude needs input (macOS)
afplay /System/Library/Sounds/Ping.aiff &

exit 0
```

---

## Part 4: CRB-Specific Configuration

### Our Hooks Strategy

| Hook | Purpose | Type |
|------|---------|------|
| enforce-pnpm | Ensure pnpm over npm | PreToolUse (Bash) |
| protect-secrets | Block .env, credentials | PreToolUse (Read, Edit, Write) |
| enforce-structlog | Flag print() usage | PostToolUse (Edit, Write) |
| audit-commands | Log all bash commands | PostToolUse (Bash) |
| completion-sound | Audio when done | Notification |

### Our BetterStack Strategy

**What to log:**
- All HTTP requests (already in middleware)
- Business events (quiz, payment, report)
- Claude API calls (token usage, latency)
- Errors with full context

**What NOT to log:**
- PII (emails, names) - redact these
- Full request bodies (too much volume)
- Health checks (noise)

**Alerts to set up:**
- Report generation failure rate > 5%
- Payment webhook failures
- Claude API errors
- Uptime checks on /api/health

---

## Part 5: Implementation Status

### Current State

- [x] Request logging middleware (`request_logger.py`)
- [x] Logfire integration (optional)
- [x] Sentry integration (optional)
- [x] Structured logging helpers (`observability.py`)
- [ ] BetterStack integration
- [ ] Claude Code hooks

### Files Changed

| File | Change |
|------|--------|
| `.claude/settings.local.json` | Added hooks configuration |
| `.claude/hooks/*.sh` | Hook scripts |
| `backend/src/config/observability.py` | BetterStack handler |
| `backend/src/config/settings.py` | BetterStack token |
| `backend/requirements.txt` | logtail-python |

---

## Quick Reference

### BetterStack Commands

```bash
# Test log ingestion
curl -X POST "https://in.logs.betterstack.com" \
  -H "Authorization: Bearer $BETTERSTACK_SOURCE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test log", "level": "info"}'
```

### Hook Debugging

```bash
# Test a hook manually
echo '{"tool_name": "Bash", "tool_input": {"command": "npm install"}}' | .claude/hooks/enforce-pnpm.sh
echo $?  # Should print 2 (blocked)

# View audit log
tail -f ~/.claude-audit.log
```

### Useful Log Queries

```sql
-- Conversion funnel
SELECT
  COUNT(*) FILTER (WHERE message = 'quiz_started') as started,
  COUNT(*) FILTER (WHERE message = 'quiz_completed') as completed,
  COUNT(*) FILTER (WHERE message = 'payment_completed') as paid
FROM logs
WHERE dt > now() - INTERVAL 7 DAY;

-- Slowest reports
SELECT quiz_session_id, duration_s
FROM logs
WHERE message = 'report_generated'
ORDER BY duration_s DESC
LIMIT 10;
```

---

## Learning Resources

- [BetterStack Python Guide](https://betterstack.com/community/guides/logging/structlog/)
- [Claude Code Hooks Docs](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Structlog Best Practices](https://www.structlog.org/en/stable/getting-started.html)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
