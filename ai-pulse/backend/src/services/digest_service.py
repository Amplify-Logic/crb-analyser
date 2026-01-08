"""
Digest Service

Generates and manages daily digests.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from src.config.supabase_client import get_async_supabase
from src.config.settings import settings
from src.scoring.rules import ScoredArticle
from src.scoring.ai_scorer import AIScorer

logger = logging.getLogger(__name__)


class DigestService:
    """Service for creating and managing digests."""

    def __init__(self):
        self.ai_scorer = AIScorer()

    async def create_digest(
        self,
        scored_articles: List[ScoredArticle],
        use_ai: bool = True,
    ) -> dict:
        """
        Create a new digest from scored articles.

        Returns digest dict with id, articles, subject_line, etc.
        """
        # Refine scores with AI if enabled
        if use_ai and settings.GOOGLE_API_KEY:
            scored_articles = await self.ai_scorer.refine_scores(
                scored_articles,
                top_n=50,
            )

        # Get top articles
        top_articles = scored_articles[:settings.DIGEST_TOP_ITEMS]

        if not top_articles:
            logger.warning("No articles to include in digest")
            return None

        # Generate summaries for top articles
        summaries = {}
        if use_ai and settings.ANTHROPIC_API_KEY:
            summaries = await self.ai_scorer.generate_summaries(
                top_articles,
                top_n=settings.DIGEST_TOP_ITEMS,
            )

        # Create digest record
        supabase = await get_async_supabase()

        digest_id = str(uuid.uuid4())
        article_ids = []

        # Store articles if not already in DB
        for scored in top_articles:
            article = scored.article
            source = scored.source

            # Check if article exists
            existing = await supabase.table("articles").select("id").eq(
                "external_id", article.external_id
            ).eq("source_id", source.slug).execute()

            if existing.data:
                article_ids.append(existing.data[0]["id"])
            else:
                # Insert new article
                article_record = {
                    "id": str(uuid.uuid4()),
                    "source_id": source.slug,
                    "external_id": article.external_id,
                    "content_type": article.content_type.value,
                    "title": article.title,
                    "description": article.description,
                    "url": article.url,
                    "thumbnail_url": article.thumbnail_url,
                    "published_at": article.published_at.isoformat(),
                    "fetched_at": datetime.utcnow().isoformat(),
                    "views": article.views,
                    "likes": article.likes,
                    "comments": article.comments,
                    "score": scored.final_score,
                    "novelty_score": scored.novelty_score,
                    "impact_score": scored.impact_score,
                    "summary": summaries.get(article.external_id),
                    "categories": [source.category.value],
                    "is_processed": True,
                }
                result = await supabase.table("articles").insert(article_record).execute()
                article_ids.append(result.data[0]["id"])

        # Generate subject line
        subject_line = self._generate_subject_line(top_articles)

        # Create digest record
        digest = {
            "id": digest_id,
            "created_at": datetime.utcnow().isoformat(),
            "article_ids": article_ids,
            "subject_line": subject_line,
            "stats": {
                "sources_checked": len(set(s.source.slug for s in scored_articles)),
                "items_found": len(scored_articles),
                "items_selected": len(top_articles),
            },
        }

        await supabase.table("digests").insert(digest).execute()

        return digest

    def _generate_subject_line(self, articles: List[ScoredArticle]) -> str:
        """Generate digest subject line."""
        if not articles:
            return "AI Pulse Daily Digest"

        # Use the top article's title
        top_title = articles[0].article.title
        if len(top_title) > 50:
            top_title = top_title[:47] + "..."

        return f"AI Pulse: {top_title}"

    async def get_users_for_digest(
        self,
        preferred_time: str,
        timezone_hour: int,
    ) -> List[dict]:
        """
        Get users who should receive digest at this time.

        Args:
            preferred_time: 'morning', 'lunch', or 'evening'
            timezone_hour: Current hour in UTC

        Returns:
            List of user records
        """
        supabase = await get_async_supabase()

        # Map preferred time to hour
        time_to_hour = {
            "morning": 7,
            "lunch": 12,
            "evening": 18,
        }

        target_hour = time_to_hour.get(preferred_time, 12)

        # Calculate which timezones should receive now
        # If it's 14:00 UTC and target is 12, we want UTC+2
        offset = target_hour - timezone_hour

        # Get users with matching preferences and active subscription
        result = await supabase.table("users").select("*").eq(
            "subscription_status", "active"
        ).eq(
            "preferred_time", preferred_time
        ).execute()

        # Filter by timezone (simplified - just check if hour matches)
        users = []
        for user in result.data:
            user_tz = user.get("timezone", "UTC")
            # TODO: Proper timezone handling
            users.append(user)

        return users

    async def record_send(
        self,
        digest_id: str,
        user_id: str,
        status: str = "sent",
    ) -> None:
        """Record that a digest was sent to a user."""
        supabase = await get_async_supabase()

        await supabase.table("digest_sends").insert({
            "id": str(uuid.uuid4()),
            "digest_id": digest_id,
            "user_id": user_id,
            "sent_at": datetime.utcnow().isoformat(),
            "status": status,
        }).execute()

    async def record_open(self, digest_id: str, user_id: str) -> None:
        """Record that a user opened a digest."""
        supabase = await get_async_supabase()

        await supabase.table("digest_sends").update({
            "opened_at": datetime.utcnow().isoformat(),
            "status": "opened",
        }).eq("digest_id", digest_id).eq("user_id", user_id).execute()

    async def record_click(self, digest_id: str, user_id: str) -> None:
        """Record that a user clicked a link in a digest."""
        supabase = await get_async_supabase()

        await supabase.table("digest_sends").update({
            "clicked_at": datetime.utcnow().isoformat(),
            "status": "clicked",
        }).eq("digest_id", digest_id).eq("user_id", user_id).execute()
