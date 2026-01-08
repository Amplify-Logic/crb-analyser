"""
Cleanup Job

Removes old articles and data.
"""

import logging
from datetime import datetime, timedelta

from src.config.supabase_client import get_async_supabase
from src.config.settings import settings

logger = logging.getLogger(__name__)


async def cleanup_old_articles() -> dict:
    """
    Clean up articles older than retention period.

    Called weekly by scheduler.
    """
    logger.info("Starting article cleanup")

    supabase = await get_async_supabase()

    cutoff_date = datetime.utcnow() - timedelta(days=settings.ARTICLE_RETENTION_DAYS)

    # Delete old articles not in any digest
    result = await supabase.table("articles").delete().lt(
        "published_at", cutoff_date.isoformat()
    ).execute()

    deleted_count = len(result.data) if result.data else 0

    logger.info(f"Cleaned up {deleted_count} old articles")

    return {
        "deleted_articles": deleted_count,
        "cutoff_date": cutoff_date.isoformat(),
    }


async def cleanup_old_digests() -> dict:
    """
    Clean up old digest records.

    Keeps digest metadata but removes detailed stats.
    """
    logger.info("Starting digest cleanup")

    # Keep digests for 90 days
    supabase = await get_async_supabase()
    cutoff_date = datetime.utcnow() - timedelta(days=90)

    # Delete old digest_sends records
    result = await supabase.table("digest_sends").delete().lt(
        "sent_at", cutoff_date.isoformat()
    ).execute()

    deleted_count = len(result.data) if result.data else 0

    logger.info(f"Cleaned up {deleted_count} old digest send records")

    return {
        "deleted_sends": deleted_count,
    }
