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
