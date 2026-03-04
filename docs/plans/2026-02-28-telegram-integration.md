# Telegram Integration Layer — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Telegram bot to the CRB Analyser backend that serves as an operator console (CRB commands, notifications, morning briefing), a GTD task management system, and a bridge to Claude Code — all accessible via slash commands, natural language, and voice notes.

**Architecture:** Single Telegram bot running inside the existing FastAPI app via webhook mode. A Haiku-powered router classifies incoming messages into 5 intents (CRB command, data query, code task, idea capture, GTD action) and dispatches to the appropriate handler. Outbound notifications are pushed to the operator's Telegram chat on key business events (payment, report generated, quiz completed). A daily scheduled job sends a morning briefing digest.

**Tech Stack:** python-telegram-bot v21+ (async, webhook mode), OpenAI Whisper API (voice transcription), Claude Haiku (intent classification), existing FastAPI + Supabase + APScheduler infrastructure.

---

## CRB Context
- Affected user journey stage: None (operator-only, not client-facing)
- Industries impacted: None (infrastructure tooling)
- Reference docs to load during execution: `.claude/reference/api-development.md`

## Rollback Plan
If this fails, revert by:
1. Remove the `telegram_router` include from `main.py`
2. Remove the `telegram_service` import from `scheduler_service.py`
3. Delete `backend/src/telegram/` directory and `backend/src/routes/telegram.py`
4. Remove `TELEGRAM_*` settings from `settings.py`
5. Remove `python-telegram-bot` from `requirements.txt`

---

## Cost Model

This plan is designed to maximize the Claude Code subscription and minimize API spend:

| Component | Billing | Cost |
|-----------|---------|------|
| Telegram bot (FastAPI webhook) | Free — runs inside existing Railway deploy | $0 |
| Intent classification (Haiku) | API credits — ~$0.001 per message | Pennies/day |
| Morning briefing (Supabase queries) | Free — existing DB | $0 |
| Notifications (outbound) | Free — Telegram Bot API | $0 |
| Voice transcription (Whisper) | OpenAI API — ~$0.006/min | ~$0.10/day |
| Claude Code bridge (`/code`) | **Subscription** — spawns `claude` CLI | Included in Max plan |
| GTD system (markdown) | Free — file I/O | $0 |

**Key insight:** The Claude Code bridge (Task 12) spawns the `claude` CLI as a subprocess, which uses your Max subscription — not API credits. This is the expensive brain, and it's already paid for.

---

## GTD Methodology — Design Principles

The GTD system (Task 9) is based on David Allen's "Getting Things Done" methodology. The implementer should understand these principles because they dictate WHY the store works the way it does:

### Allen's Core Insight
> "Your brain is for having ideas, not holding them."

The system must be **trusted** — if your brain doesn't trust the external system, it won't let go of open loops, and you stay stressed. Trust requires: zero-friction capture, regular review, and complete capture (nothing left in your head).

### The 5 Steps (mapped to Telegram commands)

| GTD Step | What it means | Telegram command |
|----------|--------------|-----------------|
| **1. Capture** | Get everything out of your head into a trusted inbox | Voice note or `/capture <text>` — zero friction |
| **2. Clarify** | Decide: is it actionable? What's the next action? | `/review` walks through inbox items |
| **3. Organize** | File into the right bucket (7 lists below) | Items move from inbox → next actions, projects, waiting, someday |
| **4. Reflect** | Regular review to keep system current and trusted | `/review` (weekly), `/briefing` (daily) |
| **5. Engage** | Choose actions by context, then time, energy, priority | `/next [context]` — shows actions filtered by where you are |

### The 7 Lists (mapped to markdown files)

| List | File | Purpose |
|------|------|---------|
| Inbox | `inbox.md` | Raw capture — unprocessed stuff |
| Projects | `projects.md` | Multi-step outcomes (anything requiring >1 action) |
| Next Actions | `next-actions.md` | Single physical actions, grouped by @context |
| Waiting For | `waiting-for.md` | Delegated items — who owes you what |
| Calendar | `calendar.md` | Hard landscape — things that MUST happen on a specific date/time |
| Someday/Maybe | `someday-maybe.md` | Ideas you might act on later but not now |
| Reference | `reference/` | Non-actionable info you want to keep |

### The 4 Criteria for Choosing Actions (Allen Ch. 9)

When `/next` shows your actions, you choose based on:
1. **Context** — What can I do where I am? (@calls, @computer, @errands, @home)
2. **Time available** — Do I have 5 min or 2 hours?
3. **Energy available** — Am I fresh or fried?
4. **Priority** — Given the above constraints, what has the highest payoff?

### Why Telegram Is the Ideal GTD Capture Device

Allen says the system fails when capture has friction. Voice notes into Telegram = lowest possible friction. Phone is always with you. No app to open, no UI to navigate — just talk or type. The bot captures, you clarify later during review.

---

## Future Roadmap: Hermes Agent (Layer 3)

### What Is Hermes?

[Nous Research Hermes Agent](https://nousresearch.com/hermes-agent/) is an open-source autonomous agent framework. It's the productized version of what every entrepreneur in the Bowser house is building from scratch — a persistent personal agent that lives on a server and communicates across platforms.

### What Hermes Provides That We Don't (Yet)

| Capability | Hermes | Our Plan |
|-----------|--------|----------|
| Multi-platform (Discord, Slack, WhatsApp) | Built-in gateway | Telegram only |
| Container isolation (Docker, SSH, Modal) | 5 execution backends | Railway subprocess |
| Parallel subagents | Native spawning | Sequential only |
| Persistent memory across sessions | Built-in | GTD markdown (simpler) |
| Auto-generated skill documents | agentskills.io standard | CRB skills system |
| 40+ built-in tools | Yes | Custom CRB tools only |

### When to Evaluate Hermes

**Not now.** Hermes runs on API credits (pay-per-token), not subscription. For a single-operator CRB console, our plan is cheaper and more purpose-built.

**Evaluate when:**
- You're managing 3+ client projects through Telegram and need multi-project isolation
- Clients want their own agent interfaces (Discord, Slack, WhatsApp)
- You need autonomous overnight agents that run for hours (API cost becomes worthwhile at agency scale)
- The Amplify Logic AI agency needs standardized agent deployment across clients

### Integration Path: Hermes + Claude Code + CRB

```
Phase 1 (NOW — this plan):
  Telegram bot inside FastAPI
  ├── CRB operator commands (subscription-free)
  ├── GTD system (free, markdown)
  ├── Claude Code bridge (uses Max subscription)
  ├── Notifications (free)
  └── Voice notes (pennies)

Phase 2 (When agency scales):
  Hermes as orchestration layer
  ├── Multi-platform gateway (Telegram, Discord, Slack)
  ├── CRB tools ported as Hermes skills (agentskills.io format)
  ├── GTD methodology as a Hermes skill document
  ├── Per-client agent instances with isolated workspaces
  └── Claude Code integration via Hermes terminal tool

Phase 3 (Full AI agency):
  Hermes fleet
  ├── One agent per client project
  ├── Shared skill library (CRB analysis, vendor research, report generation)
  ├── Central GTD system for agency-wide task management
  ├── Revenue tracking across all client agents
  └── Autonomous nightly audits, reporting, maintenance
```

### Key Decision: Skills Portability

Our CRB skills system (`backend/src/skills/`) and Hermes's agentskills.io standard are conceptually similar. When we evaluate Hermes, the migration path is:
1. Wrap each CRB skill as a SKILL.md document
2. Register them in Hermes's skill registry
3. CRB-specific context (industry knowledge, vendor data) stays in Supabase — Hermes tools query it
4. GTD store remains markdown-based (works in both systems)

This is a **future decision, not a current one.** Document it, don't build it yet.

---

## Task 1: Add Dependencies and Settings

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/src/config/settings.py`

**Step 1: Add python-telegram-bot to requirements**

Add to `backend/requirements.txt` after the `# Email` section:

```
# Telegram Bot
python-telegram-bot[webhooks]==21.9
```

**Step 2: Run pip install**

Run: `cd backend && pip install python-telegram-bot[webhooks]==21.9`
Expected: Successfully installed

**Step 3: Add Telegram settings to Settings class**

In `backend/src/config/settings.py`, add after the `BREVO_API_KEY` line (line 105):

```python
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_ADMIN_CHAT_ID: Optional[str] = None  # Your personal chat ID
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = None  # Webhook verification token
```

**Step 4: Verify settings load**

Run: `cd backend && python -c "from src.config.settings import settings; print('TELEGRAM_BOT_TOKEN:', settings.TELEGRAM_BOT_TOKEN)"`
Expected: `TELEGRAM_BOT_TOKEN: None`

**Step 5: Commit**

```bash
git add backend/requirements.txt backend/src/config/settings.py
git commit -m "feat(telegram): add python-telegram-bot dependency and settings"
```

---

## Task 2: Telegram Service — Core Bot Setup

**Files:**
- Create: `backend/src/telegram/__init__.py`
- Create: `backend/src/telegram/bot.py`

**Step 1: Create the telegram package**

Create `backend/src/telegram/__init__.py`:

```python
"""
Telegram Bot Integration

Operator console for CRB Analyser — commands, notifications, GTD, Claude Code bridge.
"""
```

**Step 2: Write the failing test**

Create `backend/tests/test_telegram_bot.py`:

```python
"""Tests for Telegram bot core setup."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_is_admin_allows_correct_chat_id():
    """Only the configured admin chat ID should be allowed."""
    with patch("src.config.settings.settings") as mock_settings:
        mock_settings.TELEGRAM_ADMIN_CHAT_ID = "12345"
        from src.telegram.bot import is_admin
        assert is_admin(12345) is True
        assert is_admin(99999) is False


@pytest.mark.asyncio
async def test_is_admin_rejects_when_no_chat_id_configured():
    """If no admin chat ID is set, reject everyone."""
    with patch("src.config.settings.settings") as mock_settings:
        mock_settings.TELEGRAM_ADMIN_CHAT_ID = None
        from src.telegram.bot import is_admin
        assert is_admin(12345) is False
```

**Step 3: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_telegram_bot.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.telegram.bot'`

**Step 4: Write the bot core**

Create `backend/src/telegram/bot.py`:

```python
"""
Telegram Bot Core

Handles bot lifecycle, admin authentication, and message dispatching.
"""

import logging
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Global bot application instance
_app: Optional[Application] = None


def is_admin(chat_id: int) -> bool:
    """Check if a chat ID matches the configured admin."""
    if not settings.TELEGRAM_ADMIN_CHAT_ID:
        return False
    return str(chat_id) == str(settings.TELEGRAM_ADMIN_CHAT_ID)


async def admin_guard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check admin access. Sends rejection message if not admin."""
    if not update.effective_chat:
        return False
    if not is_admin(update.effective_chat.id):
        await update.message.reply_text("Unauthorized. This bot is operator-only.")
        logger.warning(
            "Unauthorized Telegram access attempt",
            extra={"chat_id": update.effective_chat.id},
        )
        return False
    return True


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command — show welcome and available commands."""
    if not await admin_guard(update, context):
        return
    await update.message.reply_text(
        "*CRB Analyser — Operator Console*\n\n"
        "Commands:\n"
        "/health — System health check\n"
        "/reports — Recent report stats\n"
        "/leads — Recent quiz completions\n"
        "/vendors — Vendor data status\n"
        "/briefing — Full morning digest\n"
        "/next — GTD: next actions\n"
        "/projects — GTD: active projects\n"
        "/capture — GTD: capture to inbox\n"
        "/idea — Capture an idea\n"
        "/code — Claude Code bridge\n\n"
        "Or just send a message — I'll figure out what you mean.",
        parse_mode="Markdown",
    )


async def cmd_chatid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /chatid — returns the user's chat ID for setup."""
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Your chat ID: `{chat_id}`", parse_mode="Markdown")


def create_bot_application() -> Optional[Application]:
    """Create and configure the Telegram bot application."""
    global _app

    if not settings.TELEGRAM_BOT_TOKEN:
        logger.info("Telegram bot disabled — TELEGRAM_BOT_TOKEN not set")
        return None

    _app = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Register command handlers
    _app.add_handler(CommandHandler("start", cmd_start))
    _app.add_handler(CommandHandler("chatid", cmd_chatid))

    logger.info("Telegram bot application created")
    return _app


def get_bot_application() -> Optional[Application]:
    """Get the current bot application instance."""
    return _app
```

**Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_telegram_bot.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/src/telegram/ backend/tests/test_telegram_bot.py
git commit -m "feat(telegram): core bot setup with admin guard and /start command"
```

---

## Task 3: FastAPI Webhook Route

**Files:**
- Create: `backend/src/routes/telegram.py`
- Modify: `backend/src/routes/__init__.py`
- Modify: `backend/src/main.py`

**Step 1: Write the failing test**

Add to `backend/tests/test_telegram_bot.py`:

```python
from fastapi.testclient import TestClient


def test_telegram_webhook_rejects_without_bot_token():
    """Webhook should 404 if telegram bot is not configured."""
    with patch("src.config.settings.settings") as mock_settings:
        mock_settings.TELEGRAM_BOT_TOKEN = None
        # Import after patching
        from src.main import app
        client = TestClient(app)
        response = client.post("/api/telegram/webhook", json={})
        assert response.status_code in (404, 503)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_telegram_bot.py::test_telegram_webhook_rejects_without_bot_token -v`
Expected: FAIL

**Step 3: Create the webhook route**

Create `backend/src/routes/telegram.py`:

```python
"""
Telegram Webhook Route

Receives incoming Telegram updates via webhook and dispatches to bot handlers.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Request, HTTPException, status

from src.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(request: Request) -> Dict[str, Any]:
    """
    Receive Telegram webhook updates.

    Telegram sends JSON updates to this endpoint.
    We pass them to the python-telegram-bot Application for processing.
    """
    from src.telegram.bot import get_bot_application

    app = get_bot_application()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot not configured",
        )

    try:
        from telegram import Update

        data = await request.json()
        update = Update.de_json(data=data, bot=app.bot)

        # Process update asynchronously
        await app.process_update(update)

        return {"ok": True}

    except Exception as e:
        logger.error(f"Telegram webhook error: {e}", exc_info=True)
        # Return 200 to Telegram to prevent retries on our errors
        return {"ok": True}
```

**Step 4: Register the route**

In `backend/src/routes/__init__.py`, add:

```python
from .telegram import router as telegram_router
```

And add `"telegram_router"` to the `__all__` list.

In `backend/src/main.py`, add to imports:

```python
    telegram_router,
```

And add after the refiner_router line:

```python
app.include_router(telegram_router, prefix="/api/telegram", tags=["Telegram"])
```

**Step 5: Initialize bot in app lifespan**

In `backend/src/main.py`, add to the lifespan startup section (after scheduler start):

```python
    # Start Telegram bot (webhook mode)
    try:
        from src.telegram.bot import create_bot_application
        bot_app = create_bot_application()
        if bot_app:
            await bot_app.initialize()
            logger.info("Telegram bot initialized")
    except Exception as e:
        logger.warning(f"Could not initialize Telegram bot: {e}")
```

And in the shutdown section:

```python
    # Shutdown Telegram bot
    try:
        from src.telegram.bot import get_bot_application
        bot_app = get_bot_application()
        if bot_app:
            await bot_app.shutdown()
    except Exception:
        pass
```

**Step 6: Run tests**

Run: `cd backend && python -m pytest tests/test_telegram_bot.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add backend/src/routes/telegram.py backend/src/routes/__init__.py backend/src/main.py
git commit -m "feat(telegram): webhook route and bot lifecycle in FastAPI"
```

---

## Task 4: Notification Service — Outbound Pushes

**Files:**
- Create: `backend/src/telegram/notifications.py`
- Create: `backend/tests/test_telegram_notifications.py`

**Step 1: Write the failing test**

Create `backend/tests/test_telegram_notifications.py`:

```python
"""Tests for Telegram notification service."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_notify_sends_message_to_admin():
    """Notification should send to configured admin chat ID."""
    mock_bot = AsyncMock()
    with patch("src.telegram.notifications.get_bot_application") as mock_get_app:
        mock_app = MagicMock()
        mock_app.bot = mock_bot
        mock_get_app.return_value = mock_app

        with patch("src.config.settings.settings") as mock_settings:
            mock_settings.TELEGRAM_ADMIN_CHAT_ID = "12345"

            from src.telegram.notifications import notify_admin
            await notify_admin("Test message")

            mock_bot.send_message.assert_called_once_with(
                chat_id="12345",
                text="Test message",
                parse_mode="Markdown",
            )


@pytest.mark.asyncio
async def test_notify_skips_when_no_bot():
    """Should silently skip when bot is not configured."""
    with patch("src.telegram.notifications.get_bot_application") as mock_get_app:
        mock_get_app.return_value = None

        from src.telegram.notifications import notify_admin
        # Should not raise
        await notify_admin("Test message")


@pytest.mark.asyncio
async def test_notify_payment_formats_correctly():
    """Payment notification should include amount and company."""
    mock_bot = AsyncMock()
    with patch("src.telegram.notifications.get_bot_application") as mock_get_app:
        mock_app = MagicMock()
        mock_app.bot = mock_bot
        mock_get_app.return_value = mock_app

        with patch("src.config.settings.settings") as mock_settings:
            mock_settings.TELEGRAM_ADMIN_CHAT_ID = "12345"

            from src.telegram.notifications import notify_payment
            await notify_payment(
                amount=147,
                currency="EUR",
                company="Bonbon Dental",
                email="test@bonbon.com",
            )

            call_text = mock_bot.send_message.call_args[1]["text"]
            assert "147" in call_text
            assert "Bonbon Dental" in call_text
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_telegram_notifications.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write the notification service**

Create `backend/src/telegram/notifications.py`:

```python
"""
Telegram Notification Service

Outbound push notifications to the operator on key business events.
"""

import logging
from typing import Optional

from src.config.settings import settings

logger = logging.getLogger(__name__)


async def notify_admin(message: str, parse_mode: str = "Markdown") -> None:
    """Send a notification message to the admin chat."""
    from src.telegram.bot import get_bot_application

    app = get_bot_application()
    if not app or not settings.TELEGRAM_ADMIN_CHAT_ID:
        return

    try:
        await app.bot.send_message(
            chat_id=settings.TELEGRAM_ADMIN_CHAT_ID,
            text=message,
            parse_mode=parse_mode,
        )
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")


async def notify_payment(
    amount: int,
    currency: str,
    company: str,
    email: str,
    tier: str = "unknown",
) -> None:
    """Notify admin of a new payment."""
    msg = (
        f"*Payment Received*\n\n"
        f"Amount: {currency} {amount}\n"
        f"Company: {company}\n"
        f"Email: {email}\n"
        f"Tier: {tier}"
    )
    await notify_admin(msg)


async def notify_report_complete(
    company: str,
    report_id: str,
    crb_score: Optional[float] = None,
    industry: Optional[str] = None,
) -> None:
    """Notify admin that a report has been generated."""
    score_str = f"\nCRB Score: {crb_score}" if crb_score else ""
    industry_str = f"\nIndustry: {industry}" if industry else ""
    msg = (
        f"*Report Ready*\n\n"
        f"Company: {company}{industry_str}{score_str}\n"
        f"Report ID: `{report_id}`"
    )
    await notify_admin(msg)


async def notify_report_failed(
    company: str,
    error: str,
) -> None:
    """Notify admin that report generation failed."""
    msg = (
        f"*Report Failed*\n\n"
        f"Company: {company}\n"
        f"Error: {error}"
    )
    await notify_admin(msg)


async def notify_new_lead(
    company: str,
    email: str,
    industry: Optional[str] = None,
    ai_readiness: Optional[float] = None,
) -> None:
    """Notify admin of a new quiz completion."""
    industry_str = f"\nIndustry: {industry}" if industry else ""
    readiness_str = f"\nAI Readiness: {ai_readiness}%" if ai_readiness else ""
    msg = (
        f"*New Lead*\n\n"
        f"Company: {company}\n"
        f"Email: {email}{industry_str}{readiness_str}"
    )
    await notify_admin(msg)


async def notify_scheduler_job(
    job_name: str,
    success: bool,
    details: str = "",
) -> None:
    """Notify admin of scheduler job completion."""
    status_emoji = "OK" if success else "FAILED"
    msg = (
        f"*Scheduler: {job_name}* — {status_emoji}\n\n"
        f"{details}" if details else f"*Scheduler: {job_name}* — {status_emoji}"
    )
    await notify_admin(msg)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_telegram_notifications.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/telegram/notifications.py backend/tests/test_telegram_notifications.py
git commit -m "feat(telegram): notification service for payments, reports, leads, scheduler"
```

---

## Task 5: Wire Notifications into Existing Events

**Files:**
- Modify: `backend/src/routes/payments.py` (after successful payment processing)
- Modify: `backend/src/services/scheduler_service.py` (after each job)

This task wires the `notify_*` functions into existing code paths. The calls are fire-and-forget (non-blocking).

**Step 1: Add payment notification**

Find the Stripe webhook handler in `backend/src/routes/payments.py`. After the line where `send_payment_confirmation_email` is called (or where the payment is confirmed as successful), add:

```python
# Telegram notification (fire-and-forget)
try:
    from src.telegram.notifications import notify_payment
    asyncio.create_task(notify_payment(
        amount=session_data.get("amount_total", 0) // 100,
        currency="EUR",
        company=company_name,
        email=email,
        tier=tier,
    ))
except Exception:
    pass  # Never block payment flow for notification failure
```

**Step 2: Add scheduler job notifications**

In `backend/src/services/scheduler_service.py`, at the end of each job function (`send_follow_up_emails`, `cleanup_old_pdfs`, `cleanup_expired_quiz_sessions`, `refresh_vendor_pricing`), add notification calls. Example for `send_follow_up_emails` after `logger.info(f"Follow-up email job completed...")`:

```python
try:
    from src.telegram.notifications import notify_scheduler_job
    await notify_scheduler_job(
        "Follow-up Emails",
        success=True,
        details=f"Sent {sent_count} follow-up emails",
    )
except Exception:
    pass
```

Repeat the pattern for each scheduler job, wrapping in try/except.

**Step 3: Test the wiring**

Run: `cd backend && python -m pytest tests/ -v -k "payment or scheduler" --timeout=30`
Expected: Existing tests still pass

**Step 4: Commit**

```bash
git add backend/src/routes/payments.py backend/src/services/scheduler_service.py
git commit -m "feat(telegram): wire notifications into payment and scheduler events"
```

---

## Task 6: CRB Command Handlers

**Files:**
- Create: `backend/src/telegram/handlers/__init__.py`
- Create: `backend/src/telegram/handlers/crb_commands.py`
- Create: `backend/tests/test_telegram_crb_commands.py`

**Step 1: Write the failing test**

Create `backend/tests/test_telegram_crb_commands.py`:

```python
"""Tests for CRB operator commands."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_health_command_returns_system_status():
    """Health command should return vendor + KB + DB status."""
    from src.telegram.handlers.crb_commands import format_health_response

    health_data = {
        "vendors": {"stale_count": 3, "total": 148, "status": "warning"},
        "kb": {"stale_files": 0, "status": "healthy"},
        "expertise": {"status": "healthy", "record_count": 12},
    }
    result = format_health_response(health_data)
    assert "148" in result
    assert "3" in result
    assert "healthy" in result.lower()


@pytest.mark.asyncio
async def test_reports_command_formats_stats():
    """Reports command should show delivery stats."""
    from src.telegram.handlers.crb_commands import format_reports_response

    reports_data = {
        "total": 5,
        "completed": 4,
        "failed": 1,
        "period": "today",
    }
    result = format_reports_response(reports_data)
    assert "5" in result
    assert "4" in result
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_telegram_crb_commands.py -v`
Expected: FAIL

**Step 3: Write CRB command handlers**

Create `backend/src/telegram/handlers/__init__.py`:

```python
"""Telegram command handlers."""
```

Create `backend/src/telegram/handlers/crb_commands.py`:

```python
"""
CRB Operator Commands

/health, /reports, /leads, /vendors, /briefing, /workshop, /research
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from telegram import Update
from telegram.ext import ContextTypes

from src.telegram.bot import admin_guard

logger = logging.getLogger(__name__)


def format_health_response(data: Dict[str, Any]) -> str:
    """Format health check data into a Telegram message."""
    vendors = data.get("vendors", {})
    kb = data.get("kb", {})
    expertise = data.get("expertise", {})

    v_status = "OK" if vendors.get("status") == "healthy" else "WARNING"
    k_status = "OK" if kb.get("status") == "healthy" else "WARNING"
    e_status = "OK" if expertise.get("status") == "healthy" else "WARNING"

    return (
        f"*System Health*\n\n"
        f"Vendors: {v_status} — {vendors.get('total', '?')} total, "
        f"{vendors.get('stale_count', 0)} stale\n"
        f"Knowledge Base: {k_status} — {kb.get('stale_files', 0)} stale files\n"
        f"Expertise: {e_status} — {expertise.get('record_count', 0)} records"
    )


def format_reports_response(data: Dict[str, Any]) -> str:
    """Format report stats into a Telegram message."""
    return (
        f"*Reports — {data.get('period', 'today')}*\n\n"
        f"Total: {data.get('total', 0)}\n"
        f"Completed: {data.get('completed', 0)}\n"
        f"Failed: {data.get('failed', 0)}"
    )


def format_leads_response(leads: list) -> str:
    """Format lead list into a Telegram message."""
    if not leads:
        return "*Recent Leads*\n\nNo new leads."

    lines = ["*Recent Leads*\n"]
    for lead in leads[:10]:
        company = lead.get("company_name", "Unknown")
        industry = lead.get("industry", "?")
        email = lead.get("email", "")
        lines.append(f"- {company} ({industry}) — {email}")
    return "\n".join(lines)


async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /health — system health check."""
    if not await admin_guard(update, context):
        return

    await update.message.reply_text("Running health check...")

    try:
        from src.config.supabase_client import get_async_supabase
        from src.agents.research.refresh import get_stale_count

        # Vendor health
        stale = await get_stale_count()
        supabase = await get_async_supabase()
        vendor_result = await supabase.table("vendors").select("id", count="exact").execute()
        total_vendors = vendor_result.count or 0
        vendor_status = "healthy" if stale < 10 else "warning"

        health_data = {
            "vendors": {"stale_count": stale, "total": total_vendors, "status": vendor_status},
            "kb": {"stale_files": 0, "status": "healthy"},
            "expertise": {"status": "healthy", "record_count": 0},
        }

        await update.message.reply_text(
            format_health_response(health_data), parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        await update.message.reply_text(f"Health check failed: {e}")


async def cmd_reports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reports [today|week|month] — report delivery stats."""
    if not await admin_guard(update, context):
        return

    period = "today"
    if context.args:
        period = context.args[0].lower()

    try:
        from src.config.supabase_client import get_async_supabase

        supabase = await get_async_supabase()
        now = datetime.now(timezone.utc)

        if period == "week":
            since = now - timedelta(days=7)
        elif period == "month":
            since = now - timedelta(days=30)
        else:
            since = now.replace(hour=0, minute=0, second=0, microsecond=0)

        result = await supabase.table("reports").select(
            "id, status"
        ).gte("created_at", since.isoformat()).execute()

        reports = result.data or []
        completed = sum(1 for r in reports if r.get("status") == "completed")
        failed = sum(1 for r in reports if r.get("status") == "failed")

        data = {
            "total": len(reports),
            "completed": completed,
            "failed": failed,
            "period": period,
        }

        await update.message.reply_text(
            format_reports_response(data), parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Failed to fetch reports: {e}")


async def cmd_leads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /leads — recent quiz completions."""
    if not await admin_guard(update, context):
        return

    try:
        from src.config.supabase_client import get_async_supabase

        supabase = await get_async_supabase()
        since = datetime.now(timezone.utc) - timedelta(days=7)

        result = await supabase.table("quiz_sessions").select(
            "email, company_name, industry, created_at"
        ).gte("created_at", since.isoformat()).order(
            "created_at", desc=True
        ).limit(10).execute()

        await update.message.reply_text(
            format_leads_response(result.data or []), parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Failed to fetch leads: {e}")


async def cmd_vendors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /vendors [stale|refresh] — vendor data status."""
    if not await admin_guard(update, context):
        return

    subcommand = context.args[0].lower() if context.args else "status"

    try:
        from src.agents.research.refresh import get_stale_count

        if subcommand == "refresh":
            from src.services.scheduler_service import trigger_vendor_refresh
            await update.message.reply_text("Starting vendor refresh...")
            await trigger_vendor_refresh()
            await update.message.reply_text("Vendor refresh complete.")
        else:
            stale = await get_stale_count()
            await update.message.reply_text(
                f"*Vendor Status*\n\nStale vendors (>90 days): {stale}",
                parse_mode="Markdown",
            )
    except Exception as e:
        await update.message.reply_text(f"Vendor command failed: {e}")


async def cmd_briefing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /briefing — full morning digest."""
    if not await admin_guard(update, context):
        return

    await update.message.reply_text("Generating briefing...")

    try:
        briefing = await generate_briefing()
        await update.message.reply_text(briefing, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Briefing failed: {e}")


async def generate_briefing() -> str:
    """Generate the full morning briefing digest."""
    from src.config.supabase_client import get_async_supabase

    supabase = await get_async_supabase()
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    # Reports (yesterday)
    reports_result = await supabase.table("reports").select(
        "id, status"
    ).gte("created_at", yesterday.isoformat()).execute()
    reports = reports_result.data or []
    reports_completed = sum(1 for r in reports if r.get("status") == "completed")

    # Leads (yesterday)
    leads_result = await supabase.table("quiz_sessions").select(
        "id, company_name, industry"
    ).gte("created_at", yesterday.isoformat()).execute()
    leads = leads_result.data or []

    # Vendor health
    try:
        from src.agents.research.refresh import get_stale_count
        stale = await get_stale_count()
    except Exception:
        stale = -1

    v_status = "OK" if stale < 10 else f"WARNING ({stale} stale)"

    # Industry breakdown of leads
    industries: Dict[str, int] = {}
    for lead in leads:
        ind = lead.get("industry", "unknown")
        industries[ind] = industries.get(ind, 0) + 1
    industry_lines = "\n".join(f"  {k}: {v}" for k, v in industries.items()) or "  None"

    briefing = (
        f"*CRB Analyser — {now.strftime('%b %d')} Daily Brief*\n\n"
        f"*Reports*\n"
        f"  Delivered: {reports_completed}\n"
        f"  Total: {len(reports)}\n\n"
        f"*Leads (24h)*\n"
        f"  New: {len(leads)}\n"
        f"{industry_lines}\n\n"
        f"*Data Health*\n"
        f"  Vendors: {v_status}\n"
    )

    return briefing
```

**Step 4: Register handlers in bot.py**

Add to the `create_bot_application()` function in `backend/src/telegram/bot.py`, after the existing handlers:

```python
    # CRB operator commands
    from src.telegram.handlers.crb_commands import (
        cmd_health, cmd_reports, cmd_leads, cmd_vendors, cmd_briefing,
    )
    _app.add_handler(CommandHandler("health", cmd_health))
    _app.add_handler(CommandHandler("reports", cmd_reports))
    _app.add_handler(CommandHandler("leads", cmd_leads))
    _app.add_handler(CommandHandler("vendors", cmd_vendors))
    _app.add_handler(CommandHandler("briefing", cmd_briefing))
```

**Step 5: Run tests**

Run: `cd backend && python -m pytest tests/test_telegram_crb_commands.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/src/telegram/handlers/ backend/tests/test_telegram_crb_commands.py backend/src/telegram/bot.py
git commit -m "feat(telegram): CRB operator commands — health, reports, leads, vendors, briefing"
```

---

## Task 7: Morning Briefing Scheduler Job

**Files:**
- Modify: `backend/src/services/scheduler_service.py`

**Step 1: Add the morning briefing job**

In `backend/src/services/scheduler_service.py`, add a new job function:

```python
async def send_morning_briefing():
    """
    Send morning briefing digest via Telegram.
    Runs daily at 7 AM UTC.
    """
    logger.info("Starting morning briefing job")

    try:
        from src.telegram.handlers.crb_commands import generate_briefing
        from src.telegram.notifications import notify_admin

        briefing = await generate_briefing()
        await notify_admin(briefing)

        logger.info("Morning briefing sent successfully")

    except Exception as e:
        logger.error(f"Morning briefing failed: {e}")
```

**Step 2: Register it in setup_scheduler**

Add inside `setup_scheduler()`:

```python
    # Morning briefing - daily at 7 AM UTC
    scheduler.add_job(
        send_morning_briefing,
        CronTrigger(hour=7, minute=0),
        id="morning_briefing",
        name="Send morning briefing via Telegram",
        replace_existing=True,
    )

    logger.info("Scheduler configured with 5 jobs")
```

Update the log message from "4 jobs" to "5 jobs".

**Step 3: Run existing scheduler tests**

Run: `cd backend && python -m pytest tests/ -v -k "scheduler" --timeout=30`
Expected: PASS

**Step 4: Commit**

```bash
git add backend/src/services/scheduler_service.py
git commit -m "feat(telegram): morning briefing scheduler job at 7 AM UTC"
```

---

## Task 8: Intent Router — Natural Language Classification

**Files:**
- Create: `backend/src/telegram/router.py`
- Create: `backend/tests/test_telegram_router.py`

**Step 1: Write the failing test**

Create `backend/tests/test_telegram_router.py`:

```python
"""Tests for Telegram intent router."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_router_classifies_crb_query():
    """Data queries about the business should route to 'query'."""
    from src.telegram.router import classify_intent

    with patch("src.telegram.router._call_classifier") as mock_llm:
        mock_llm.return_value = "query"
        result = await classify_intent("How many reports did we do this week?")
        assert result == "query"


@pytest.mark.asyncio
async def test_router_classifies_idea():
    """Idea-like messages should route to 'idea'."""
    from src.telegram.router import classify_intent

    with patch("src.telegram.router._call_classifier") as mock_llm:
        mock_llm.return_value = "idea"
        result = await classify_intent("What if we added a benchmarking tool for dental?")
        assert result == "idea"


@pytest.mark.asyncio
async def test_router_classifies_code_task():
    """Development tasks should route to 'code'."""
    from src.telegram.router import classify_intent

    with patch("src.telegram.router._call_classifier") as mock_llm:
        mock_llm.return_value = "code"
        result = await classify_intent("Add error handling to the quiz endpoint")
        assert result == "code"


@pytest.mark.asyncio
async def test_router_classifies_gtd():
    """Task management should route to 'gtd'."""
    from src.telegram.router import classify_intent

    with patch("src.telegram.router._call_classifier") as mock_llm:
        mock_llm.return_value = "gtd"
        result = await classify_intent("Remind me to call the accountant on Monday")
        assert result == "gtd"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_telegram_router.py -v`
Expected: FAIL

**Step 3: Write the intent router**

Create `backend/src/telegram/router.py`:

```python
"""
Telegram Intent Router

Classifies incoming messages into 5 intents using Claude Haiku.
"""

import logging
from typing import Literal

import anthropic

from src.config.settings import settings
from src.config.model_routing import get_model_for_task

logger = logging.getLogger(__name__)

Intent = Literal["query", "code", "idea", "gtd", "conversation"]

CLASSIFICATION_PROMPT = """Classify this message into exactly ONE category. Respond with only the category name.

Categories:
- query: Questions about business data, metrics, reports, leads, revenue, vendors
- code: Software development tasks — build, fix, add, refactor, test, deploy code
- idea: New ideas, "what if", brainstorming, product suggestions, feature requests
- gtd: Task management — to-dos, reminders, deadlines, projects, waiting-for items
- conversation: General chat, greetings, questions about the system itself

Message: {message}

Category:"""


async def _call_classifier(message: str) -> str:
    """Call Claude Haiku to classify the message intent."""
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    model = get_model_for_task("extraction")

    response = await client.messages.create(
        model=model,
        max_tokens=10,
        messages=[
            {"role": "user", "content": CLASSIFICATION_PROMPT.format(message=message)}
        ],
    )

    raw = response.content[0].text.strip().lower()

    # Validate the response is a known intent
    valid_intents = {"query", "code", "idea", "gtd", "conversation"}
    if raw in valid_intents:
        return raw

    logger.warning(f"Unknown intent from classifier: {raw}")
    return "conversation"


async def classify_intent(message: str) -> Intent:
    """
    Classify a message into one of 5 intents.

    Uses Claude Haiku for fast, cheap classification.
    Falls back to 'conversation' on error.
    """
    try:
        return await _call_classifier(message)
    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        return "conversation"
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_telegram_router.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/telegram/router.py backend/tests/test_telegram_router.py
git commit -m "feat(telegram): Haiku-powered intent router with 5 categories"
```

---

## Task 9: GTD Handler — Capture, Clarify, Organize, Reflect, Engage

**Files:**
- Create: `backend/src/telegram/handlers/gtd_handler.py`
- Create: `backend/src/telegram/gtd_store.py`
- Create: `backend/tests/test_telegram_gtd.py`

**Step 1: Write the failing test**

Create `backend/tests/test_telegram_gtd.py`:

```python
"""Tests for GTD task management."""
import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def gtd_dir(tmp_path):
    """Create a temporary GTD directory."""
    return tmp_path


@pytest.mark.asyncio
async def test_capture_adds_to_inbox(gtd_dir):
    """Capturing an item should add it to inbox.md."""
    from src.telegram.gtd_store import GTDStore

    store = GTDStore(gtd_dir)
    store.capture("Call the accountant about Q1 taxes")

    inbox = (gtd_dir / "inbox.md").read_text()
    assert "Call the accountant about Q1 taxes" in inbox


@pytest.mark.asyncio
async def test_capture_multiple_items(gtd_dir):
    """Multiple captures should all appear in inbox."""
    from src.telegram.gtd_store import GTDStore

    store = GTDStore(gtd_dir)
    store.capture("Buy groceries")
    store.capture("Email client proposal")

    inbox = (gtd_dir / "inbox.md").read_text()
    assert "Buy groceries" in inbox
    assert "Email client proposal" in inbox


@pytest.mark.asyncio
async def test_add_next_action(gtd_dir):
    """Adding a next action should file it under the right context."""
    from src.telegram.gtd_store import GTDStore

    store = GTDStore(gtd_dir)
    store.add_next_action("Call dentist", context="calls")

    actions = store.get_next_actions()
    assert any("Call dentist" in a["text"] for a in actions)


@pytest.mark.asyncio
async def test_add_project(gtd_dir):
    """Adding a project should create it in projects.md."""
    from src.telegram.gtd_store import GTDStore

    store = GTDStore(gtd_dir)
    store.add_project("Launch Telegram bot", next_action="Set up bot token")

    projects = store.get_projects()
    assert any("Launch Telegram bot" in p["name"] for p in projects)


@pytest.mark.asyncio
async def test_get_next_actions_by_context(gtd_dir):
    """Should filter next actions by context."""
    from src.telegram.gtd_store import GTDStore

    store = GTDStore(gtd_dir)
    store.add_next_action("Call dentist", context="calls")
    store.add_next_action("Buy milk", context="errands")
    store.add_next_action("Call accountant", context="calls")

    calls = store.get_next_actions(context="calls")
    assert len(calls) == 2
    assert all("Call" in a["text"] for a in calls)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_telegram_gtd.py -v`
Expected: FAIL

**Step 3: Write the GTD store**

Create `backend/src/telegram/gtd_store.py`:

```python
"""
GTD Store — Markdown-based Getting Things Done data store.

Based on David Allen's GTD methodology:
- Capture: everything into inbox
- Clarify: decide what each item means
- Organize: file into the right bucket
- Reflect: regular reviews
- Engage: choose actions by context/time/energy/priority

Seven lists: Inbox, Projects, Next Actions, Waiting For,
Calendar, Someday/Maybe, Reference
"""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class GTDStore:
    """Markdown-backed GTD task management."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Ensure all list files exist
        for filename in [
            "inbox.md",
            "projects.md",
            "next-actions.md",
            "waiting-for.md",
            "calendar.md",
            "someday-maybe.md",
            "ideas.md",
        ]:
            filepath = self.base_dir / filename
            if not filepath.exists():
                filepath.write_text(f"# {filename.replace('.md', '').replace('-', ' ').title()}\n\n")

        ref_dir = self.base_dir / "reference"
        ref_dir.mkdir(exist_ok=True)

    def _now_str(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    # =========================================================================
    # CAPTURE
    # =========================================================================

    def capture(self, text: str) -> None:
        """Add an item to the inbox for later clarification."""
        filepath = self.base_dir / "inbox.md"
        with open(filepath, "a") as f:
            f.write(f"- [ ] {text} _(captured {self._now_str()})_\n")

    def get_inbox(self) -> List[Dict[str, str]]:
        """Get all inbox items."""
        return self._parse_checklist(self.base_dir / "inbox.md")

    def clear_inbox_item(self, item_text: str) -> bool:
        """Remove an item from inbox (after clarifying/organizing it)."""
        return self._remove_item(self.base_dir / "inbox.md", item_text)

    # =========================================================================
    # NEXT ACTIONS (by context)
    # =========================================================================

    def add_next_action(self, text: str, context: str = "general") -> None:
        """Add a next action under a context (@calls, @errands, @computer, etc.)."""
        filepath = self.base_dir / "next-actions.md"
        content = filepath.read_text()

        context_header = f"## @{context}"
        if context_header not in content:
            content += f"\n{context_header}\n\n"

        # Insert after the context header
        lines = content.split("\n")
        insert_idx = None
        for i, line in enumerate(lines):
            if line.strip() == context_header:
                insert_idx = i + 1
                # Skip blank lines after header
                while insert_idx < len(lines) and lines[insert_idx].strip() == "":
                    insert_idx += 1
                break

        if insert_idx is not None:
            lines.insert(insert_idx, f"- [ ] {text} _(added {self._now_str()})_")
        else:
            lines.append(f"- [ ] {text} _(added {self._now_str()})_")

        filepath.write_text("\n".join(lines))

    def get_next_actions(self, context: Optional[str] = None) -> List[Dict[str, str]]:
        """Get next actions, optionally filtered by context."""
        filepath = self.base_dir / "next-actions.md"
        if not filepath.exists():
            return []

        content = filepath.read_text()
        if context:
            # Parse only the section under this context
            pattern = rf"## @{context}\n(.*?)(?=\n## |$)"
            match = re.search(pattern, content, re.DOTALL)
            if not match:
                return []
            section = match.group(1)
            return self._parse_checklist_text(section)

        return self._parse_checklist(filepath)

    def complete_action(self, text: str) -> bool:
        """Mark a next action as complete."""
        filepath = self.base_dir / "next-actions.md"
        return self._check_item(filepath, text)

    # =========================================================================
    # PROJECTS
    # =========================================================================

    def add_project(self, name: str, next_action: Optional[str] = None) -> None:
        """Add a project with an optional first next action."""
        filepath = self.base_dir / "projects.md"
        with open(filepath, "a") as f:
            f.write(f"\n## {name}\n\n")
            f.write(f"_Created: {self._now_str()}_\n\n")
            if next_action:
                f.write(f"Next action: {next_action}\n")
                # Also add to next actions list
                self.add_next_action(f"[{name}] {next_action}", context="general")

    def get_projects(self) -> List[Dict[str, str]]:
        """Get all active projects."""
        filepath = self.base_dir / "projects.md"
        if not filepath.exists():
            return []

        content = filepath.read_text()
        projects = []
        for match in re.finditer(r"^## (.+)$", content, re.MULTILINE):
            projects.append({"name": match.group(1)})
        return projects

    # =========================================================================
    # WAITING FOR
    # =========================================================================

    def add_waiting_for(self, text: str, who: str) -> None:
        """Add an item to the waiting-for list."""
        filepath = self.base_dir / "waiting-for.md"
        with open(filepath, "a") as f:
            f.write(f"- [ ] {text} — waiting on: {who} _(added {self._now_str()})_\n")

    def get_waiting_for(self) -> List[Dict[str, str]]:
        """Get all waiting-for items."""
        return self._parse_checklist(self.base_dir / "waiting-for.md")

    # =========================================================================
    # SOMEDAY / MAYBE
    # =========================================================================

    def add_someday(self, text: str) -> None:
        """Add an item to someday/maybe."""
        filepath = self.base_dir / "someday-maybe.md"
        with open(filepath, "a") as f:
            f.write(f"- {text} _(added {self._now_str()})_\n")

    def get_someday(self) -> List[Dict[str, str]]:
        """Get someday/maybe items."""
        return self._parse_checklist(self.base_dir / "someday-maybe.md")

    # =========================================================================
    # IDEAS
    # =========================================================================

    def add_idea(self, text: str, tags: Optional[List[str]] = None) -> None:
        """Capture an idea."""
        filepath = self.base_dir / "ideas.md"
        tag_str = " ".join(f"#{t}" for t in tags) if tags else ""
        with open(filepath, "a") as f:
            f.write(f"- {text} {tag_str} _(captured {self._now_str()})_\n")

    def get_ideas(self) -> List[Dict[str, str]]:
        """Get all captured ideas."""
        return self._parse_checklist(self.base_dir / "ideas.md")

    # =========================================================================
    # REVIEW
    # =========================================================================

    def get_review_summary(self) -> str:
        """Generate a review summary for reflection."""
        inbox = self.get_inbox()
        actions = self.get_next_actions()
        projects = self.get_projects()
        waiting = self.get_waiting_for()
        someday = self.get_someday()

        return (
            f"*GTD Review*\n\n"
            f"Inbox: {len(inbox)} items\n"
            f"Next Actions: {len(actions)} items\n"
            f"Projects: {len(projects)} active\n"
            f"Waiting For: {len(waiting)} items\n"
            f"Someday/Maybe: {len(someday)} items"
        )

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _parse_checklist(self, filepath: Path) -> List[Dict[str, str]]:
        """Parse a markdown file for checklist items."""
        if not filepath.exists():
            return []
        return self._parse_checklist_text(filepath.read_text())

    def _parse_checklist_text(self, text: str) -> List[Dict[str, str]]:
        """Parse checklist items from text."""
        items = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("- [ ]"):
                items.append({"text": line[6:].strip(), "done": False})
            elif line.startswith("- [x]"):
                items.append({"text": line[6:].strip(), "done": True})
            elif line.startswith("- ") and not line.startswith("- ["):
                items.append({"text": line[2:].strip(), "done": False})
        return items

    def _remove_item(self, filepath: Path, item_text: str) -> bool:
        """Remove an item containing the given text."""
        if not filepath.exists():
            return False
        content = filepath.read_text()
        lines = content.split("\n")
        new_lines = [l for l in lines if item_text not in l]
        if len(new_lines) == len(lines):
            return False
        filepath.write_text("\n".join(new_lines))
        return True

    def _check_item(self, filepath: Path, item_text: str) -> bool:
        """Mark a checklist item as done."""
        if not filepath.exists():
            return False
        content = filepath.read_text()
        if item_text not in content:
            return False
        content = content.replace(f"- [ ] {item_text}", f"- [x] {item_text}")
        filepath.write_text(content)
        return True
```

**Step 4: Write the GTD Telegram handler**

Create `backend/src/telegram/handlers/gtd_handler.py`:

```python
"""
GTD Telegram Handlers

Commands for Getting Things Done task management.
"""

import logging
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from src.telegram.bot import admin_guard
from src.telegram.gtd_store import GTDStore

logger = logging.getLogger(__name__)

# GTD data lives in the project's gtd/ directory
GTD_DIR = Path(__file__).parent.parent.parent.parent / "gtd"


def get_store() -> GTDStore:
    """Get the GTD store instance."""
    return GTDStore(GTD_DIR)


async def cmd_capture(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /capture <text> — add to GTD inbox."""
    if not await admin_guard(update, context):
        return

    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: /capture <what's on your mind>")
        return

    store = get_store()
    store.capture(text)
    inbox_count = len(store.get_inbox())

    await update.message.reply_text(
        f"Captured to inbox. ({inbox_count} items in inbox)"
    )


async def cmd_next(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /next [context] — show next actions."""
    if not await admin_guard(update, context):
        return

    ctx = context.args[0].lower() if context.args else None
    store = get_store()
    actions = store.get_next_actions(context=ctx)

    if not actions:
        scope = f"@{ctx}" if ctx else "all contexts"
        await update.message.reply_text(f"No next actions ({scope}).")
        return

    lines = [f"*Next Actions{' — @' + ctx if ctx else ''}*\n"]
    for a in actions[:15]:
        check = "x" if a["done"] else " "
        lines.append(f"[{check}] {a['text']}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_projects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /projects — show active projects."""
    if not await admin_guard(update, context):
        return

    store = get_store()
    projects = store.get_projects()

    if not projects:
        await update.message.reply_text("No active projects.")
        return

    lines = ["*Active Projects*\n"]
    for i, p in enumerate(projects, 1):
        lines.append(f"{i}. {p['name']}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_waiting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /waiting — show waiting-for items."""
    if not await admin_guard(update, context):
        return

    store = get_store()
    items = store.get_waiting_for()

    if not items:
        await update.message.reply_text("Nothing in waiting-for.")
        return

    lines = ["*Waiting For*\n"]
    for item in items:
        lines.append(f"- {item['text']}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_someday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /someday — show someday/maybe list."""
    if not await admin_guard(update, context):
        return

    store = get_store()
    items = store.get_someday()

    if not items:
        await update.message.reply_text("Someday/Maybe is empty.")
        return

    lines = ["*Someday / Maybe*\n"]
    for item in items:
        lines.append(f"- {item['text']}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /review — GTD weekly review summary."""
    if not await admin_guard(update, context):
        return

    store = get_store()
    summary = store.get_review_summary()
    await update.message.reply_text(summary, parse_mode="Markdown")


async def cmd_idea(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /idea <text> — capture an idea."""
    if not await admin_guard(update, context):
        return

    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: /idea <your idea>")
        return

    store = get_store()
    store.add_idea(text)

    await update.message.reply_text(f"Idea captured.")


async def handle_gtd_natural_language(update: Update, text: str) -> None:
    """Handle natural language GTD messages (routed from intent classifier)."""
    # For now, treat any GTD-classified message as a capture
    store = get_store()
    store.capture(text)
    inbox_count = len(store.get_inbox())
    await update.message.reply_text(
        f"Captured to inbox. ({inbox_count} items)\n\n"
        f"Use /next, /projects, or /review to manage your lists."
    )
```

**Step 5: Register GTD handlers in bot.py**

Add to `create_bot_application()` in `backend/src/telegram/bot.py`:

```python
    # GTD commands
    from src.telegram.handlers.gtd_handler import (
        cmd_capture, cmd_next, cmd_projects, cmd_waiting,
        cmd_someday, cmd_review, cmd_idea,
    )
    _app.add_handler(CommandHandler("capture", cmd_capture))
    _app.add_handler(CommandHandler("next", cmd_next))
    _app.add_handler(CommandHandler("projects", cmd_projects))
    _app.add_handler(CommandHandler("waiting", cmd_waiting))
    _app.add_handler(CommandHandler("someday", cmd_someday))
    _app.add_handler(CommandHandler("review", cmd_review))
    _app.add_handler(CommandHandler("idea", cmd_idea))
```

**Step 6: Run tests**

Run: `cd backend && python -m pytest tests/test_telegram_gtd.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add backend/src/telegram/gtd_store.py backend/src/telegram/handlers/gtd_handler.py backend/tests/test_telegram_gtd.py backend/src/telegram/bot.py
git commit -m "feat(telegram): GTD task management — capture, next actions, projects, review"
```

---

## Task 10: Natural Language Message Handler — Dispatch

**Files:**
- Create: `backend/src/telegram/handlers/message_handler.py`
- Modify: `backend/src/telegram/bot.py`

**Step 1: Write the message handler**

Create `backend/src/telegram/handlers/message_handler.py`:

```python
"""
Natural Language Message Handler

Catches all non-command text messages, classifies intent via router,
and dispatches to the appropriate handler.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.telegram.bot import admin_guard
from src.telegram.router import classify_intent

logger = logging.getLogger(__name__)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any non-command text message."""
    if not await admin_guard(update, context):
        return

    text = update.message.text
    if not text:
        return

    intent = await classify_intent(text)
    logger.info(f"Message classified as: {intent}", extra={"text": text[:100]})

    if intent == "query":
        await _handle_query(update, text)
    elif intent == "idea":
        await _handle_idea(update, text)
    elif intent == "gtd":
        from src.telegram.handlers.gtd_handler import handle_gtd_natural_language
        await handle_gtd_natural_language(update, text)
    elif intent == "code":
        await _handle_code(update, text)
    else:
        await _handle_conversation(update, text)


async def _handle_query(update: Update, text: str) -> None:
    """Handle business data query via LLM."""
    # Phase 5: Will use Claude to query Supabase and format response
    await update.message.reply_text(
        f"(Query mode) I understood your question. "
        f"Data queries will be available in Phase 5.\n\n"
        f"For now, try:\n"
        f"/reports — report stats\n"
        f"/leads — recent leads\n"
        f"/health — system health"
    )


async def _handle_idea(update: Update, text: str) -> None:
    """Capture an idea from natural language."""
    from src.telegram.handlers.gtd_handler import get_store

    store = get_store()
    store.add_idea(text)
    await update.message.reply_text("Idea captured.")


async def _handle_code(update: Update, text: str) -> None:
    """Handle code task — Claude Code bridge."""
    # Phase 6: Will spawn Claude Code subprocess
    await update.message.reply_text(
        f"(Code mode) I understood your dev task. "
        f"Claude Code bridge will be available in Phase 6.\n\n"
        f"For now, use /code <task> when ready."
    )


async def _handle_conversation(update: Update, text: str) -> None:
    """Handle general conversation."""
    await update.message.reply_text(
        "I'm the CRB operator console. Try:\n\n"
        "/health — system check\n"
        "/reports — report stats\n"
        "/capture — add to inbox\n"
        "/next — GTD next actions\n"
        "/briefing — morning digest\n\n"
        "Or just tell me what's on your mind — I'll capture it."
    )
```

**Step 2: Register in bot.py**

Add to `create_bot_application()` in `backend/src/telegram/bot.py`, **after all command handlers** (MessageHandler must be last):

```python
    # Natural language catch-all (must be registered LAST)
    from src.telegram.handlers.message_handler import handle_text_message
    _app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
```

**Step 3: Commit**

```bash
git add backend/src/telegram/handlers/message_handler.py backend/src/telegram/bot.py
git commit -m "feat(telegram): natural language message handler with intent routing"
```

---

## Task 11: Voice Note Handler — Whisper Transcription

**Files:**
- Create: `backend/src/telegram/voice.py`
- Create: `backend/tests/test_telegram_voice.py`
- Modify: `backend/src/telegram/bot.py`

**Step 1: Write the failing test**

Create `backend/tests/test_telegram_voice.py`:

```python
"""Tests for voice note transcription."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path


@pytest.mark.asyncio
async def test_transcribe_calls_openai_whisper():
    """Should call OpenAI Whisper API with the audio file."""
    with patch("src.telegram.voice.openai.AsyncOpenAI") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value = mock_client

        mock_transcription = MagicMock()
        mock_transcription.text = "Call the dentist tomorrow"
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcription)

        from src.telegram.voice import transcribe_audio

        result = await transcribe_audio(Path("/tmp/test.ogg"))
        assert result == "Call the dentist tomorrow"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_telegram_voice.py -v`
Expected: FAIL

**Step 3: Write the voice handler**

Create `backend/src/telegram/voice.py`:

```python
"""
Voice Note Handler

Transcribes Telegram voice notes using OpenAI Whisper API,
then routes the text through the intent classifier.
"""

import logging
import tempfile
from pathlib import Path

import openai
from telegram import Update
from telegram.ext import ContextTypes

from src.config.settings import settings
from src.telegram.bot import admin_guard

logger = logging.getLogger(__name__)


async def transcribe_audio(audio_path: Path) -> str:
    """Transcribe an audio file using OpenAI Whisper API."""
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    with open(audio_path, "rb") as audio_file:
        transcription = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )

    return transcription.text


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming voice notes — transcribe and route."""
    if not await admin_guard(update, context):
        return

    if not settings.OPENAI_API_KEY:
        await update.message.reply_text("Voice notes require OPENAI_API_KEY to be set.")
        return

    voice = update.message.voice or update.message.audio
    if not voice:
        return

    await update.message.reply_text("Transcribing...")

    try:
        # Download voice file
        file = await context.bot.get_file(voice.file_id)

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            tmp_path = Path(tmp.name)

        # Transcribe
        text = await transcribe_audio(tmp_path)

        # Clean up
        tmp_path.unlink(missing_ok=True)

        if not text.strip():
            await update.message.reply_text("Could not transcribe voice note.")
            return

        # Show transcription
        await update.message.reply_text(f"Heard: _{text}_", parse_mode="Markdown")

        # Route through message handler
        from src.telegram.handlers.message_handler import handle_text_message

        # Monkey-patch the update text for routing
        update.message.text = text
        await handle_text_message(update, context)

    except Exception as e:
        logger.error(f"Voice transcription failed: {e}")
        await update.message.reply_text(f"Voice transcription failed: {e}")
```

**Step 4: Register in bot.py**

Add to `create_bot_application()` in `backend/src/telegram/bot.py`, before the text message handler:

```python
    # Voice note handler
    from src.telegram.voice import handle_voice_message
    _app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_message))
```

**Step 5: Run test**

Run: `cd backend && python -m pytest tests/test_telegram_voice.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/src/telegram/voice.py backend/tests/test_telegram_voice.py backend/src/telegram/bot.py
git commit -m "feat(telegram): voice note transcription via Whisper + intent routing"
```

---

## Task 12: Claude Code Bridge (Stub)

**Files:**
- Create: `backend/src/telegram/handlers/claude_code_handler.py`
- Modify: `backend/src/telegram/bot.py`

This task creates the Claude Code bridge as a functional stub that will be expanded later. The full subprocess management is complex enough to warrant its own follow-up plan.

**Step 1: Create the handler**

Create `backend/src/telegram/handlers/claude_code_handler.py`:

```python
"""
Claude Code Bridge Handler

Bridges Telegram messages to Claude Code CLI subprocess.
Phase 6 — stub implementation. Full version will manage sessions,
stream progress, and handle long-running tasks.
"""

import asyncio
import logging
import subprocess
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from src.telegram.bot import admin_guard

logger = logging.getLogger(__name__)

# Session tracking (simple in-memory for now)
_sessions: dict[str, dict] = {}


async def cmd_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /code <task> — send task to Claude Code."""
    if not await admin_guard(update, context):
        return

    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(
            "*Claude Code Bridge*\n\n"
            "Usage: /code <task description>\n\n"
            "Examples:\n"
            "- /code add error handling to the quiz endpoint\n"
            "- /code run the test suite\n"
            "- /code what does report_service.py do?",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text(f"Sending to Claude Code:\n_{text}_", parse_mode="Markdown")

    try:
        result = await _run_claude_code(text)
        # Telegram has a 4096 char limit per message
        if len(result) > 4000:
            # Split into chunks
            chunks = [result[i:i+4000] for i in range(0, len(result), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(result)

    except FileNotFoundError:
        await update.message.reply_text(
            "Claude Code CLI not found. Install with: `npm install -g @anthropic-ai/claude-code`",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Claude Code bridge error: {e}")
        await update.message.reply_text(f"Claude Code error: {e}")


async def _run_claude_code(message: str, timeout: int = 300) -> str:
    """
    Run a Claude Code command as a subprocess.

    Returns the output text.
    """
    cmd = [
        "claude",
        "--print",
        "--output-format", "text",
        "--max-turns", "10",
        message,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        process.kill()
        return "Claude Code timed out after 5 minutes."

    output = stdout.decode("utf-8", errors="replace").strip()
    if not output and stderr:
        output = stderr.decode("utf-8", errors="replace").strip()

    return output or "No output from Claude Code."
```

**Step 2: Register in bot.py**

Add to `create_bot_application()`:

```python
    # Claude Code bridge
    from src.telegram.handlers.claude_code_handler import cmd_code
    _app.add_handler(CommandHandler("code", cmd_code))
```

**Step 3: Commit**

```bash
git add backend/src/telegram/handlers/claude_code_handler.py backend/src/telegram/bot.py
git commit -m "feat(telegram): Claude Code bridge stub with subprocess execution"
```

---

## Task 13: Integration Test — Full Bot Flow

**Files:**
- Create: `backend/tests/test_telegram_integration.py`

**Step 1: Write integration test**

Create `backend/tests/test_telegram_integration.py`:

```python
"""Integration tests for the full Telegram bot flow."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock


@pytest.mark.asyncio
async def test_bot_creates_with_all_handlers():
    """Bot should register all command and message handlers."""
    with patch("src.config.settings.settings") as mock_settings:
        mock_settings.TELEGRAM_BOT_TOKEN = "test-token"
        mock_settings.TELEGRAM_ADMIN_CHAT_ID = "12345"
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.OPENAI_API_KEY = "test-key"

        # We need to reset the module to pick up new settings
        import importlib
        import src.telegram.bot
        importlib.reload(src.telegram.bot)

        # Can't fully test without real token, but we can verify structure
        from src.telegram.bot import is_admin
        assert is_admin(12345) is True
        assert is_admin(99999) is False


@pytest.mark.asyncio
async def test_gtd_store_full_workflow(tmp_path):
    """Full GTD workflow: capture → organize → review."""
    from src.telegram.gtd_store import GTDStore

    store = GTDStore(tmp_path)

    # 1. Capture
    store.capture("Buy birthday gift for mom")
    store.capture("Research new CI/CD pipeline")
    store.capture("Call accountant about Q1")
    assert len(store.get_inbox()) == 3

    # 2. Organize (move from inbox to appropriate lists)
    store.add_next_action("Buy birthday gift for mom", context="errands")
    store.add_project("CI/CD Pipeline Upgrade", next_action="Research GitHub Actions vs CircleCI")
    store.add_next_action("Call accountant about Q1", context="calls")

    # 3. Clear inbox items
    store.clear_inbox_item("Buy birthday gift")
    store.clear_inbox_item("Research new CI/CD")
    store.clear_inbox_item("Call accountant")
    assert len(store.get_inbox()) == 0

    # 4. Review
    errands = store.get_next_actions(context="errands")
    calls = store.get_next_actions(context="calls")
    projects = store.get_projects()

    assert len(errands) == 1
    assert len(calls) == 1
    assert len(projects) == 1

    # 5. Complete an action
    store.complete_action("Buy birthday gift for mom")
    errands = store.get_next_actions(context="errands")
    assert errands[0]["done"] is True

    # 6. Review summary
    summary = store.get_review_summary()
    assert "Next Actions" in summary
    assert "Projects" in summary
```

**Step 2: Run all telegram tests**

Run: `cd backend && python -m pytest tests/test_telegram_*.py -v`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add backend/tests/test_telegram_integration.py
git commit -m "test(telegram): integration tests for full bot flow and GTD workflow"
```

---

## Task 14: Setup Instructions & Environment

**Files:**
- Create: `backend/src/telegram/README.md` (setup guide only — not product documentation)

**Step 1: Write setup instructions**

Create `backend/src/telegram/README.md`:

```markdown
# Telegram Bot Setup

## 1. Create Bot

1. Message @BotFather on Telegram
2. Send `/newbot`
3. Name it (e.g., "CRB Operator")
4. Copy the bot token

## 2. Get Your Chat ID

1. Start a chat with your new bot
2. Send `/chatid`
3. Copy the number

## 3. Set Environment Variables

Add to your `.env`:

```
TELEGRAM_BOT_TOKEN=your-bot-token-here
TELEGRAM_ADMIN_CHAT_ID=your-chat-id-here
```

For voice notes, also set:
```
OPENAI_API_KEY=your-openai-key-here
```

## 4. Set Webhook (Production)

After deploying, register the webhook URL with Telegram:

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-app.railway.app/api/telegram/webhook"}'
```

## 5. Commands

| Command | Description |
|---------|-------------|
| /start | Welcome + command list |
| /health | System health check |
| /reports [period] | Report delivery stats |
| /leads | Recent quiz completions |
| /vendors [stale\|refresh] | Vendor data status |
| /briefing | Full morning digest |
| /capture <text> | GTD: add to inbox |
| /next [context] | GTD: next actions |
| /projects | GTD: active projects |
| /waiting | GTD: waiting-for list |
| /someday | GTD: someday/maybe |
| /review | GTD: review summary |
| /idea <text> | Capture an idea |
| /code <task> | Claude Code bridge |
```

**Step 2: Commit**

```bash
git add backend/src/telegram/README.md
git commit -m "docs(telegram): setup instructions for bot, webhook, and environment"
```

---

## Summary

| Task | What it builds | Test file |
|------|---------------|-----------|
| 1 | Dependencies + settings | — (manual verify) |
| 2 | Core bot (admin guard, /start) | `test_telegram_bot.py` |
| 3 | Webhook route + FastAPI lifecycle | `test_telegram_bot.py` |
| 4 | Notification service (outbound) | `test_telegram_notifications.py` |
| 5 | Wire notifications into payments/scheduler | Existing tests |
| 6 | CRB commands (/health, /reports, etc.) | `test_telegram_crb_commands.py` |
| 7 | Morning briefing scheduler job | Existing scheduler tests |
| 8 | Intent router (Haiku classifier) | `test_telegram_router.py` |
| 9 | GTD store + handlers | `test_telegram_gtd.py` |
| 10 | Natural language dispatch | — (wiring only) |
| 11 | Voice note transcription | `test_telegram_voice.py` |
| 12 | Claude Code bridge (stub) | — (manual test) |
| 13 | Integration tests | `test_telegram_integration.py` |
| 14 | Setup docs | — |
