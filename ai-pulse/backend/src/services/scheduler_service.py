"""
Scheduler Service

APScheduler-based job scheduling for periodic tasks.
"""

import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """Get the scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


def setup_scheduler() -> None:
    """Set up scheduled jobs."""
    scheduler = get_scheduler()

    # Article fetching - every 4 hours
    scheduler.add_job(
        "src.jobs.fetch_articles:fetch_all_articles",
        CronTrigger(hour="*/4"),
        id="fetch_articles",
        name="Fetch articles from all sources",
        replace_existing=True,
    )

    # Digest sending - every hour (checks timezone/preference)
    scheduler.add_job(
        "src.jobs.send_digests:send_scheduled_digests",
        CronTrigger(minute=0),
        id="send_digests",
        name="Send scheduled digests",
        replace_existing=True,
    )

    # Cleanup old articles - weekly on Sunday
    scheduler.add_job(
        "src.jobs.cleanup:cleanup_old_articles",
        CronTrigger(day_of_week="sun", hour=3),
        id="cleanup_articles",
        name="Clean up old articles",
        replace_existing=True,
    )

    logger.info("Scheduler jobs configured")


def start_scheduler() -> None:
    """Start the scheduler."""
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def shutdown_scheduler() -> None:
    """Shutdown the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler shutdown")
    _scheduler = None
