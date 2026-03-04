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
