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
- query: Questions asking for information, analysis, advice, or strategy — about business, reports, leads, vendors, metrics, improvements, or how to do something better
- code: Software development tasks — build, fix, add, refactor, test, deploy code
- idea: Statements (not questions) proposing something new — "we should...", "what if we built...", "feature idea:", product suggestions
- gtd: Task management — to-dos, reminders, deadlines, projects, waiting-for items
- conversation: Greetings, small talk, or questions about the bot itself

If a message is a question (even a strategic one), classify as "query" not "idea".

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
