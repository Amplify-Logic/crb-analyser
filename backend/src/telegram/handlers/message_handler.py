"""
Natural Language Message Handler

Catches all non-command text messages, classifies intent via router,
and dispatches to the appropriate handler.
"""

import logging

import anthropic
from telegram import Update
from telegram.ext import ContextTypes

from src.config.model_routing import get_model_for_task
from src.config.settings import settings
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

    await route_text(update, text)


async def route_text(update: Update, text: str) -> None:
    """Classify and route a text string. Called by both text and voice handlers."""
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
    try:
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        model = get_model_for_task("generation")

        response = await client.messages.create(
            model=model,
            max_tokens=800,
            system=(
                "You are the CRB Analyser operator assistant. The CRB Analyser is an AI-native "
                "consulting agency that generates Cost-Risk-Benefit reports for SMBs evaluating "
                "automation and AI adoption. Answer the operator's business questions concisely "
                "and actionably. If you don't have specific data, say so and suggest which "
                "command might help (/reports, /leads, /health, /vendors, /briefing)."
            ),
            messages=[{"role": "user", "content": text}],
        )

        reply = response.content[0].text.strip()
        # Telegram 4096 char limit
        if len(reply) > 4000:
            reply = reply[:4000] + "..."
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Query handler failed: {e}")
        await update.message.reply_text(
            "Couldn't process that query. Try /reports or /leads for data."
        )


async def _handle_idea(update: Update, text: str) -> None:
    """Capture an idea from natural language."""
    from src.telegram.handlers.gtd_handler import get_store

    store = get_store()
    store.add_idea(text)
    await update.message.reply_text("Idea captured.")


async def _handle_code(update: Update, text: str) -> None:
    """Handle code task — launch via Claude Code bridge."""
    await _launch_code_task(update, text)


async def _launch_code_task(update: Update, text: str) -> None:
    """Launch a Claude Code task from natural language / voice input."""
    from src.telegram.handlers.claude_code_handler import (
        check_safety,
        rate_limiter,
        task_tracker,
        session_manager,
        MAX_CONCURRENT_TASKS,
    )
    import asyncio

    # Safety check
    safety = check_safety(text)
    if safety.is_blocked:
        await update.message.reply_text(f"Blocked: {safety.reason}")
        return

    # Rate limit
    if not rate_limiter.is_allowed():
        await update.message.reply_text(
            "Rate limit reached. Try again later."
        )
        return

    # Concurrent limit
    if task_tracker.active_count() >= MAX_CONCURRENT_TASKS:
        await update.message.reply_text(
            f"Too many active tasks ({MAX_CONCURRENT_TASKS} max). "
            "Use /tasks to see running tasks."
        )
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0
    rate_limiter.record()
    task_id = task_tracker.create_task(text, chat_id=chat_id)

    existing_session = session_manager.get_session_id(chat_id)

    await update.message.reply_text(
        f"Code task #{task_id} started.\n\n{text}"
    )

    from src.telegram.handlers.claude_code_handler import _run_background_task

    asyncio.create_task(
        _run_background_task(update, task_id, text, session_id=existing_session),
        name=f"claude-code-voice-{task_id}",
    )


async def _handle_conversation(update: Update, text: str) -> None:
    """Handle general conversation with an LLM response."""
    try:
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        model = get_model_for_task("extraction")

        response = await client.messages.create(
            model=model,
            max_tokens=500,
            system=(
                "You are the CRB Analyser operator console on Telegram. "
                "You help the operator manage their AI consulting business. "
                "Keep replies short (2-4 sentences). Be direct and useful. "
                "If the user seems to want a specific command, suggest the right one:\n"
                "/health, /reports, /leads, /vendors, /briefing, /next, /projects, "
                "/capture, /idea, /code"
            ),
            messages=[{"role": "user", "content": text}],
        )

        reply = response.content[0].text.strip()
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Conversation handler failed: {e}")
        await update.message.reply_text(
            "Something went wrong. Try a command like /health or /briefing."
        )
