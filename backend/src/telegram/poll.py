"""
Local development polling mode for the Telegram bot.

Usage: cd backend && python -m src.telegram.poll

This runs the bot using polling (no webhook needed).
For production, use the webhook route instead.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()  # Load .env before importing settings

from src.config.settings import settings
from src.telegram.bot import create_bot_application

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _init_services() -> None:
    """Initialize backend services (Supabase, Redis) for full bot functionality."""
    try:
        from src.config.supabase_client import init_supabase
        await init_supabase()
        logger.info("Supabase connected")
    except Exception as e:
        logger.warning(f"Supabase not available: {e}")

    try:
        from src.config.redis_client import init_redis
        await init_redis()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis not available: {e}")


async def _shutdown_services() -> None:
    """Clean up backend services."""
    try:
        from src.config.supabase_client import close_supabase
        await close_supabase()
    except Exception:
        pass
    try:
        from src.config.redis_client import close_redis
        await close_redis()
    except Exception:
        pass


def main() -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        print("Set TELEGRAM_BOT_TOKEN in your .env file first")
        sys.exit(1)

    print(f"Starting bot in polling mode...")
    print(f"Admin chat ID: {settings.TELEGRAM_ADMIN_CHAT_ID or 'NOT SET — send /chatid to get yours'}")
    print(f"Supabase URL: {'SET' if settings.SUPABASE_URL else 'NOT SET'}")
    print(f"Anthropic API: {'SET' if settings.ANTHROPIC_API_KEY else 'NOT SET'}")

    # Initialize backend services
    asyncio.get_event_loop().run_until_complete(_init_services())

    app = create_bot_application()
    if app:
        try:
            app.run_polling(drop_pending_updates=True)
        finally:
            asyncio.get_event_loop().run_until_complete(_shutdown_services())


if __name__ == "__main__":
    main()
