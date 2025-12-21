"""
Scheduler Service

Background job scheduler for periodic tasks like follow-up emails and storage cleanup.
Uses APScheduler for in-process scheduling.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def send_follow_up_emails():
    """
    Send follow-up emails to users who received reports 7 days ago.
    Runs daily at 10 AM.
    """
    logger.info("Starting follow-up email job")

    try:
        from src.config.supabase_client import get_async_supabase
        from src.services.email import send_follow_up_email

        supabase = await get_async_supabase()

        # Find reports completed 7 days ago that haven't received follow-up
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        eight_days_ago = datetime.utcnow() - timedelta(days=8)

        # Query reports completed between 7-8 days ago without follow-up
        result = await supabase.table("reports").select(
            "id, quiz_session_id, executive_summary"
        ).gte(
            "generation_completed_at", eight_days_ago.isoformat()
        ).lte(
            "generation_completed_at", seven_days_ago.isoformat()
        ).is_(
            "follow_up_sent_at", "null"
        ).eq(
            "status", "completed"
        ).execute()

        if not result.data:
            logger.info("No reports need follow-up emails")
            return

        sent_count = 0
        for report in result.data:
            try:
                # Get email from quiz session
                quiz_result = await supabase.table("quiz_sessions").select(
                    "email"
                ).eq("id", report["quiz_session_id"]).single().execute()

                if not quiz_result.data or not quiz_result.data.get("email"):
                    continue

                email = quiz_result.data["email"]
                executive_summary = report.get("executive_summary", {})
                top_opportunities = executive_summary.get("top_opportunities", [])
                top_opportunity = top_opportunities[0] if top_opportunities else None

                # Send follow-up email
                success = await send_follow_up_email(
                    to_email=email,
                    report_id=report["id"],
                    days_since=7,
                    top_opportunity=top_opportunity,
                )

                if success:
                    # Mark follow-up as sent
                    await supabase.table("reports").update({
                        "follow_up_sent_at": datetime.utcnow().isoformat()
                    }).eq("id", report["id"]).execute()
                    sent_count += 1
                    logger.info(f"Follow-up sent for report {report['id']}")

            except Exception as e:
                logger.error(f"Failed to send follow-up for report {report['id']}: {e}")
                continue

        logger.info(f"Follow-up email job completed. Sent {sent_count} emails.")

    except Exception as e:
        logger.error(f"Follow-up email job failed: {e}")


async def cleanup_old_pdfs():
    """
    Clean up PDFs older than 30 days from storage.
    Runs daily at 3 AM.
    """
    logger.info("Starting storage cleanup job")

    try:
        from src.services.storage_service import get_storage_service

        service = get_storage_service()
        deleted_count = await service.cleanup_old_files(days_old=30)

        logger.info(f"Storage cleanup completed. Deleted {deleted_count} files.")

    except Exception as e:
        logger.error(f"Storage cleanup job failed: {e}")


async def cleanup_expired_quiz_sessions():
    """
    Clean up quiz sessions that expired without payment.
    Runs daily at 4 AM.
    """
    logger.info("Starting expired quiz session cleanup")

    try:
        from src.config.supabase_client import get_async_supabase

        supabase = await get_async_supabase()

        # Delete quiz sessions older than 7 days that were never paid
        cutoff = datetime.utcnow() - timedelta(days=7)

        result = await supabase.table("quiz_sessions").delete().lt(
            "created_at", cutoff.isoformat()
        ).in_(
            "status", ["pending_payment", "expired"]
        ).execute()

        deleted_count = len(result.data) if result.data else 0
        logger.info(f"Expired quiz cleanup completed. Deleted {deleted_count} sessions.")

    except Exception as e:
        logger.error(f"Expired quiz cleanup failed: {e}")


def setup_scheduler():
    """
    Set up all scheduled jobs.
    Call this during application startup.
    """
    scheduler = get_scheduler()

    # Follow-up emails - daily at 10 AM UTC
    scheduler.add_job(
        send_follow_up_emails,
        CronTrigger(hour=10, minute=0),
        id="follow_up_emails",
        name="Send 7-day follow-up emails",
        replace_existing=True,
    )

    # Storage cleanup - daily at 3 AM UTC
    scheduler.add_job(
        cleanup_old_pdfs,
        CronTrigger(hour=3, minute=0),
        id="storage_cleanup",
        name="Clean up old PDFs",
        replace_existing=True,
    )

    # Expired quiz cleanup - daily at 4 AM UTC
    scheduler.add_job(
        cleanup_expired_quiz_sessions,
        CronTrigger(hour=4, minute=0),
        id="quiz_cleanup",
        name="Clean up expired quiz sessions",
        replace_existing=True,
    )

    logger.info("Scheduler configured with 3 jobs")
    return scheduler


def start_scheduler():
    """Start the scheduler if not already running."""
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")
        _scheduler = None


# Manual trigger functions for testing/admin
async def trigger_follow_up_emails():
    """Manually trigger follow-up email job."""
    await send_follow_up_emails()


async def trigger_storage_cleanup():
    """Manually trigger storage cleanup job."""
    await cleanup_old_pdfs()


async def trigger_quiz_cleanup():
    """Manually trigger quiz session cleanup job."""
    await cleanup_expired_quiz_sessions()
