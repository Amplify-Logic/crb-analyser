"""
Reddit Scraper

Uses Reddit's JSON API (no authentication required).
"""

import logging
from datetime import datetime
from typing import List

import httpx

from src.config.settings import settings
from src.config.sources import Source
from src.models.enums import ContentType
from .base import BaseScraper, ScrapedArticle

logger = logging.getLogger(__name__)

REDDIT_USER_AGENT = "AI-Pulse/1.0 (Content Aggregator)"


class RedditScraper(BaseScraper):
    """Scraper for Reddit using JSON API."""

    async def fetch(self, source: Source) -> List[ScrapedArticle]:
        """Fetch posts from a subreddit."""
        subreddit = source.subreddit
        if not subreddit:
            logger.error(f"No subreddit specified for {source.name}")
            return []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Use .json endpoint for unauthenticated access
                response = await client.get(
                    f"https://www.reddit.com/r/{subreddit}/hot.json",
                    params={"limit": settings.MAX_ARTICLES_PER_SOURCE},
                    headers={"User-Agent": REDDIT_USER_AGENT},
                )
                response.raise_for_status()

            data = response.json()
            posts = data.get("data", {}).get("children", [])

            articles = []
            for post in posts:
                article = self._parse_post(post.get("data", {}))
                if article:
                    articles.append(article)

            self._log_success(source, len(articles))
            return articles

        except Exception as e:
            self._log_error(source, e)
            return []

    def _parse_post(self, post: dict) -> ScrapedArticle | None:
        """Parse a single Reddit post."""
        try:
            # Skip stickied/pinned posts
            if post.get("stickied"):
                return None

            # Skip posts with low score
            score = post.get("score", 0)
            if score < 10:
                return None

            post_id = post.get("id")
            title = post.get("title", "").strip()
            permalink = post.get("permalink", "")

            if not post_id or not title:
                return None

            # Determine if it's a self post or link
            is_self = post.get("is_self", False)

            if is_self:
                url = f"https://www.reddit.com{permalink}"
                content_type = ContentType.POST
            else:
                url = post.get("url", f"https://www.reddit.com{permalink}")
                # Check if it's a video link
                if any(x in url for x in ["youtube.com", "youtu.be", "v.redd.it"]):
                    content_type = ContentType.VIDEO
                else:
                    content_type = ContentType.POST

            # Parse timestamp
            created_utc = post.get("created_utc", 0)
            published_at = datetime.utcfromtimestamp(created_utc) if created_utc else datetime.utcnow()

            # Get description
            description = post.get("selftext", "")
            if not description:
                description = post.get("title", "")
            description = self._clean_html(description)
            description = self._truncate(description)

            # Get thumbnail
            thumbnail = post.get("thumbnail")
            if thumbnail in ["self", "default", "nsfw", "spoiler", ""]:
                thumbnail = None

            # Get flair as tags
            tags = []
            flair = post.get("link_flair_text")
            if flair:
                tags.append(flair)

            return ScrapedArticle(
                external_id=post_id,
                title=title,
                url=url,
                content_type=content_type,
                published_at=published_at,
                description=description,
                thumbnail_url=thumbnail,
                views=None,  # Reddit doesn't expose views
                likes=score,
                comments=post.get("num_comments"),
                author=post.get("author"),
                tags=tags,
            )

        except Exception as e:
            logger.warning(f"Failed to parse Reddit post: {e}")
            return None
