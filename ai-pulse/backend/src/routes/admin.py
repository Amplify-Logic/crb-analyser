"""
Admin Routes
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends

from src.config.supabase_client import get_async_supabase
from src.middleware.auth import CurrentUser, require_admin
from src.models.schemas import AdminStatsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    current_user: CurrentUser = Depends(require_admin),
):
    """Get admin dashboard statistics."""
    supabase = await get_async_supabase()

    # Total users
    users_result = await supabase.table("users").select(
        "id", count="exact"
    ).execute()
    total_users = users_result.count or 0

    # Active subscribers
    active_result = await supabase.table("users").select(
        "id", count="exact"
    ).eq("subscription_status", "active").execute()
    active_subscribers = active_result.count or 0

    # Total articles
    articles_result = await supabase.table("articles").select(
        "id", count="exact"
    ).execute()
    total_articles = articles_result.count or 0

    # Articles today
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())

    articles_today_result = await supabase.table("articles").select(
        "id", count="exact"
    ).gte("fetched_at", today_start.isoformat()).execute()
    articles_today = articles_today_result.count or 0

    # Digests sent today
    digests_today_result = await supabase.table("digest_sends").select(
        "id", count="exact"
    ).gte("sent_at", today_start.isoformat()).execute()
    digests_sent_today = digests_today_result.count or 0

    # Open rate (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)

    sent_result = await supabase.table("digest_sends").select(
        "id", count="exact"
    ).gte("sent_at", week_ago.isoformat()).execute()

    opened_result = await supabase.table("digest_sends").select(
        "id", count="exact"
    ).gte("sent_at", week_ago.isoformat()).not_.is_("opened_at", "null").execute()

    total_sent = sent_result.count or 0
    total_opened = opened_result.count or 0
    open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0

    return AdminStatsResponse(
        total_users=total_users,
        active_subscribers=active_subscribers,
        total_articles=total_articles,
        articles_today=articles_today,
        digests_sent_today=digests_sent_today,
        open_rate=round(open_rate, 2),
    )


@router.post("/trigger-digest")
async def trigger_digest(
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Manually trigger digest generation.

    Useful for testing or catching up after issues.
    """
    # Import here to avoid circular imports
    from src.jobs.send_digests import generate_and_send_digests

    try:
        result = await generate_and_send_digests(force=True)
        return {
            "status": "success",
            "message": f"Digest triggered successfully",
            "details": result,
        }
    except Exception as e:
        logger.error(f"Manual digest trigger failed: {e}")
        return {
            "status": "error",
            "message": str(e),
        }


@router.post("/trigger-scrape")
async def trigger_scrape(
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Manually trigger article scraping.

    Useful for testing or refreshing content.
    """
    from src.jobs.fetch_articles import fetch_all_articles

    try:
        result = await fetch_all_articles()
        return {
            "status": "success",
            "message": f"Scrape triggered successfully",
            "details": result,
        }
    except Exception as e:
        logger.error(f"Manual scrape trigger failed: {e}")
        return {
            "status": "error",
            "message": str(e),
        }
