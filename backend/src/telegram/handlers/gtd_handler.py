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

    await update.message.reply_text("Idea captured.")


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
