---
name: telegram
description: Start the Telegram bot in polling mode, watch logs for errors, and iterate on fixes. Use when developing or debugging the Telegram bot locally. Keywords - telegram, bot, polling, debug, iterate.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob
---

# Telegram Bot — Local Dev Loop

## Purpose

Run the Telegram bot in polling mode, monitor its output, and iterate on code fixes. After each fix, the bot restarts automatically so you can test immediately from Telegram.

## Prerequisites

The bot requires two env vars in `backend/.env`:

- `TELEGRAM_BOT_TOKEN` — from @BotFather
- `TELEGRAM_ADMIN_CHAT_ID` — your chat ID (send `/chatid` to the bot to get it)

## Workflow

### Phase 1: Start the Bot

1. Verify env vars are set (don't print their values):

```bash
cd backend && python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('TOKEN:', 'SET' if os.getenv('TELEGRAM_BOT_TOKEN') else 'MISSING'); print('CHAT_ID:', 'SET' if os.getenv('TELEGRAM_ADMIN_CHAT_ID') else 'MISSING')"
```

If either is MISSING, tell the user and stop.

2. Start the bot in the background:

```bash
cd backend && python -m src.telegram.poll 2>&1 | tee /tmp/telegram-bot.log &
```

Save the PID: `echo $!` — you'll need it to restart.

3. Wait 3 seconds, then tail the log to confirm startup:

```bash
tail -20 /tmp/telegram-bot.log
```

Look for "Starting bot in polling mode..." confirmation. If you see errors, diagnose and fix before continuing.

### Phase 2: Monitor and Fix

When the user reports an issue from Telegram (e.g. "I sent /report and got an error"):

1. **Check the log** for the error:

```bash
tail -50 /tmp/telegram-bot.log
```

2. **Find the root cause** — read the relevant source files in `backend/src/telegram/`. Key files:

| File | Purpose |
|------|---------|
| `bot.py` | Application setup, handler registration |
| `handlers.py` | Command and message handlers |
| `router.py` | Intent routing (Haiku-based) |
| `gtd.py` | GTD system commands |
| `claude_bridge.py` | Claude Code CLI bridge |
| `poll.py` | Polling mode entry point |

3. **Fix the code** using Edit tool.

4. **Restart the bot** — kill the old process and start fresh:

```bash
# Kill the old bot process
kill $(cat /tmp/telegram-bot.pid 2>/dev/null) 2>/dev/null; pkill -f "src.telegram.poll" 2>/dev/null

# Clear the log
> /tmp/telegram-bot.log

# Restart
cd backend && python -m src.telegram.poll 2>&1 | tee /tmp/telegram-bot.log &
echo $! > /tmp/telegram-bot.pid

# Confirm startup
sleep 3 && tail -20 /tmp/telegram-bot.log
```

5. Tell the user: "Bot restarted — try again in Telegram."

### Phase 3: Repeat

Continue the monitor → fix → restart cycle. Each iteration:
- Check logs first (the error is almost always in the log)
- Fix the minimal amount of code needed
- Restart and confirm no startup errors
- Let the user test from Telegram

## Startup Command (Quick Reference)

```bash
# First start
cd backend && pkill -f "src.telegram.poll" 2>/dev/null
cd backend && python -m src.telegram.poll 2>&1 | tee /tmp/telegram-bot.log &
echo $! > /tmp/telegram-bot.pid

# Check logs
tail -f /tmp/telegram-bot.log

# Restart after fix
kill $(cat /tmp/telegram-bot.pid 2>/dev/null) 2>/dev/null; pkill -f "src.telegram.poll" 2>/dev/null
> /tmp/telegram-bot.log
cd backend && python -m src.telegram.poll 2>&1 | tee /tmp/telegram-bot.log &
echo $! > /tmp/telegram-bot.pid
sleep 3 && tail -20 /tmp/telegram-bot.log
```

## Shutdown

When done, clean up:

```bash
kill $(cat /tmp/telegram-bot.pid 2>/dev/null) 2>/dev/null
pkill -f "src.telegram.poll" 2>/dev/null
rm -f /tmp/telegram-bot.pid /tmp/telegram-bot.log
```

## Rules

- **Never print env var values** — only check if they're SET or MISSING
- **Always restart after code changes** — the polling process doesn't hot-reload
- **Check logs before guessing** — the error trace is your primary diagnostic
- **Minimal fixes** — don't refactor while debugging; fix the issue and move on
- **Load reference docs as needed** — if fixing routes, read `.claude/reference/api-development.md`; if fixing telegram-specific code, read the source files directly
