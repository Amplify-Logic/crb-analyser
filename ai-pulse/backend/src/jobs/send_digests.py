"""
Send Digests Job

Generates and sends daily digests to subscribers.
"""

import logging
from datetime import datetime
from typing import List, Optional

from src.config.supabase_client import get_async_supabase
from src.config.settings import settings
from src.config.observability import log_digest_sent
from src.config.sources import get_enabled_sources, Source
from src.scrapers.base import ScrapedArticle
from src.scoring.rules import RuleScorer, ScoredArticle
from src.services.digest_service import DigestService
from src.services.email import send_digest_email
from src.services.email.templates.digest import render_digest_html, render_digest_text

logger = logging.getLogger(__name__)


async def send_scheduled_digests() -> dict:
    """
    Send digests to users based on their preferred time.

    Called hourly by scheduler. Checks which users should
    receive their digest at this hour based on timezone.
    """
    current_hour = datetime.utcnow().hour
    logger.info(f"Checking for scheduled digests at hour {current_hour} UTC")

    results = {
        "checked": 0,
        "sent": 0,
        "errors": 0,
    }

    # Check each preferred time
    for preferred_time in ["morning", "lunch", "evening"]:
        digest_service = DigestService()
        users = await digest_service.get_users_for_digest(
            preferred_time=preferred_time,
            timezone_hour=current_hour,
        )

        results["checked"] += len(users)

        if users:
            # Generate digest for this batch
            digest_result = await generate_and_send_digests(
                users=users,
                force=False,
            )
            results["sent"] += digest_result.get("sent", 0)
            results["errors"] += digest_result.get("errors", 0)

    logger.info(
        f"Scheduled digest check complete. "
        f"Checked: {results['checked']}, Sent: {results['sent']}, "
        f"Errors: {results['errors']}"
    )

    return results


async def generate_and_send_digests(
    users: Optional[List[dict]] = None,
    force: bool = False,
) -> dict:
    """
    Generate a digest and send to specified users.

    Args:
        users: List of user records to send to. If None, gets all active.
        force: If True, sends even if digest already sent today.

    Returns:
        Summary of send results.
    """
    start_time = datetime.utcnow()
    logger.info("Starting digest generation")

    results = {
        "digest_id": None,
        "sent": 0,
        "errors": 0,
        "skipped": 0,
    }

    # Get users if not provided
    if users is None:
        supabase = await get_async_supabase()
        user_result = await supabase.table("users").select("*").eq(
            "subscription_status", "active"
        ).execute()
        users = user_result.data

    if not users:
        logger.info("No users to send digest to")
        return results

    # Fetch recent articles from DB
    supabase = await get_async_supabase()
    articles_result = await supabase.table("articles").select(
        "*, sources(*)"
    ).order("score", desc=True).limit(100).execute()

    if not articles_result.data:
        logger.warning("No articles found for digest")
        return results

    # Convert to ScoredArticle format
    scored_articles = []
    for row in articles_result.data:
        # Create a minimal ScrapedArticle
        article = ScrapedArticle(
            external_id=row["external_id"],
            title=row["title"],
            url=row["url"],
            content_type=row["content_type"],
            published_at=datetime.fromisoformat(row["published_at"].replace("Z", "+00:00")),
            description=row.get("description"),
            thumbnail_url=row.get("thumbnail_url"),
            views=row.get("views"),
            likes=row.get("likes"),
            comments=row.get("comments"),
        )

        # Create source
        source_data = row.get("sources", {})
        source = Source(
            slug=source_data.get("slug", "unknown"),
            name=source_data.get("name", "Unknown"),
            source_type=source_data.get("source_type", "rss"),
            url=source_data.get("url", ""),
            category=source_data.get("category", "ai_news"),
            priority=source_data.get("priority", 5),
        )

        scored_articles.append(ScoredArticle(
            article=article,
            source=source,
            novelty_score=row.get("novelty_score", 0.5),
            impact_score=row.get("impact_score", 0.5),
            relevance_score=0.5,
            final_score=row.get("score", 0.5),
            is_filtered=False,
        ))

    # Create digest
    digest_service = DigestService()
    digest = await digest_service.create_digest(
        scored_articles=scored_articles,
        use_ai=True,
    )

    if not digest:
        logger.error("Failed to create digest")
        return results

    results["digest_id"] = digest["id"]

    # Get summaries for email
    summaries = {}
    for scored in scored_articles[:settings.DIGEST_TOP_ITEMS]:
        # Get summary from DB or use description
        article_id = scored.article.external_id
        for row in articles_result.data:
            if row["external_id"] == article_id:
                summaries[article_id] = row.get("summary") or scored.article.description or ""
                break

    # Send to each user
    for user in users:
        try:
            html_content = render_digest_html(
                articles=scored_articles[:settings.DIGEST_TOP_ITEMS],
                summaries=summaries,
                digest_id=digest["id"],
                user_id=user["id"],
            )
            text_content = render_digest_text(
                articles=scored_articles[:settings.DIGEST_TOP_ITEMS],
                summaries=summaries,
            )

            success = await send_digest_email(
                to_email=user["email"],
                to_name=user.get("name"),
                subject=digest["subject_line"],
                html_content=html_content,
                text_content=text_content,
            )

            if success:
                await digest_service.record_send(
                    digest_id=digest["id"],
                    user_id=user["id"],
                    status="sent",
                )
                results["sent"] += 1
            else:
                results["errors"] += 1

        except Exception as e:
            logger.error(f"Failed to send digest to {user['email']}: {e}")
            results["errors"] += 1

    # Log results
    duration = (datetime.utcnow() - start_time).total_seconds()
    log_digest_sent(
        digest_id=digest["id"],
        recipient_count=results["sent"],
        duration_seconds=duration,
        success=results["errors"] == 0,
        error=f"{results['errors']} errors" if results["errors"] else None,
    )

    logger.info(
        f"Digest send complete. Sent: {results['sent']}, "
        f"Errors: {results['errors']}, Duration: {duration:.2f}s"
    )

    return results


# CLI entry point
if __name__ == "__main__":
    import asyncio

    async def main():
        result = await generate_and_send_digests(force=True)
        print(f"Digest results: {result}")

    asyncio.run(main())
