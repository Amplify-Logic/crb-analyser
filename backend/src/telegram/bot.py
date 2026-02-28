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
        "/code — Claude Code bridge\n"
        "/tasks — Active Claude Code tasks\n"
        "/cancel — Cancel a running task\n"
        "/undo — Revert last git commit\n\n"
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

    # CRB operator commands
    from src.telegram.handlers.crb_commands import (
        cmd_health, cmd_reports, cmd_leads, cmd_vendors, cmd_briefing,
    )
    _app.add_handler(CommandHandler("health", cmd_health))
    _app.add_handler(CommandHandler("reports", cmd_reports))
    _app.add_handler(CommandHandler("leads", cmd_leads))
    _app.add_handler(CommandHandler("vendors", cmd_vendors))
    _app.add_handler(CommandHandler("briefing", cmd_briefing))

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

    # Claude Code bridge
    from src.telegram.handlers.claude_code_handler import (
        cmd_code, cmd_code_new, cmd_tasks, cmd_cancel, cmd_undo,
    )
    _app.add_handler(CommandHandler("code", cmd_code))
    _app.add_handler(CommandHandler("code_new", cmd_code_new))
    _app.add_handler(CommandHandler("tasks", cmd_tasks))
    _app.add_handler(CommandHandler("cancel", cmd_cancel))
    _app.add_handler(CommandHandler("undo", cmd_undo))

    # Voice note handler
    from src.telegram.voice import handle_voice_message
    _app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_message))

    # Natural language catch-all (must be registered LAST)
    from src.telegram.handlers.message_handler import handle_text_message
    _app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    logger.info("Telegram bot application created")
    return _app


def get_bot_application() -> Optional[Application]:
    """Get the current bot application instance."""
    return _app
