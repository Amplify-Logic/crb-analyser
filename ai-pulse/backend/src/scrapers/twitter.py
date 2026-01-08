"""
Twitter/X Scraper

Uses Twitter API v2 (requires Bearer token - $100/month Basic tier).
"""

import logging
from datetime import datetime
from typing import List, Optional

import httpx

from src.config.settings import settings
from src.config.sources import Source
from src.models.enums import ContentType
from .base import BaseScraper, ScrapedArticle

logger = logging.getLogger(__name__)

TWITTER_API_BASE = "https://api.twitter.com/2"


class TwitterScraper(BaseScraper):
    """Scraper for Twitter/X using API v2."""

    async def fetch(self, source: Source) -> List[ScrapedArticle]:
        """Fetch tweets from a Twitter account."""
        if not settings.TWITTER_BEARER_TOKEN:
            logger.warning("Twitter Bearer token not configured, skipping")
            return []

        handle = source.twitter_handle
        if not handle:
            logger.error(f"No Twitter handle specified for {source.name}")
            return []

        try:
            # Get user ID from handle
            user_id = await self._get_user_id(handle)
            if not user_id:
                return []

            # Get recent tweets
            tweets = await self._get_user_tweets(user_id, handle)

            self._log_success(source, len(tweets))
            return tweets

        except Exception as e:
            self._log_error(source, e)
            return []

    async def _get_user_id(self, handle: str) -> Optional[str]:
        """Get Twitter user ID from handle."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{TWITTER_API_BASE}/users/by/username/{handle}",
                headers={"Authorization": f"Bearer {settings.TWITTER_BEARER_TOKEN}"},
            )

            if response.status_code == 404:
                logger.warning(f"Twitter user not found: @{handle}")
                return None

            response.raise_for_status()
            data = response.json()

            return data.get("data", {}).get("id")

    async def _get_user_tweets(self, user_id: str, handle: str) -> List[ScrapedArticle]:
        """Get recent tweets from a user."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{TWITTER_API_BASE}/users/{user_id}/tweets",
                params={
                    "max_results": min(settings.MAX_ARTICLES_PER_SOURCE, 100),
                    "tweet.fields": "created_at,public_metrics,entities",
                    "expansions": "attachments.media_keys",
                    "media.fields": "url,preview_image_url",
                },
                headers={"Authorization": f"Bearer {settings.TWITTER_BEARER_TOKEN}"},
            )
            response.raise_for_status()

        data = response.json()
        tweets_data = data.get("data", [])
        media_map = self._build_media_map(data.get("includes", {}).get("media", []))

        tweets = []
        for tweet in tweets_data:
            article = self._parse_tweet(tweet, handle, media_map)
            if article:
                tweets.append(article)

        return tweets

    def _build_media_map(self, media_list: List[dict]) -> dict:
        """Build a map of media_key to media info."""
        return {
            m["media_key"]: m
            for m in media_list
        }

    def _parse_tweet(
        self,
        tweet: dict,
        handle: str,
        media_map: dict
    ) -> ScrapedArticle | None:
        """Parse a single tweet."""
        try:
            tweet_id = tweet.get("id")
            text = tweet.get("text", "")

            if not tweet_id or not text:
                return None

            # Skip retweets
            if text.startswith("RT @"):
                return None

            # Parse timestamp
            created_at = tweet.get("created_at")
            published_at = self._parse_datetime(created_at) if created_at else datetime.utcnow()

            # Get metrics
            metrics = tweet.get("public_metrics", {})

            # Get thumbnail from media
            thumbnail = None
            attachments = tweet.get("attachments", {})
            media_keys = attachments.get("media_keys", [])
            for key in media_keys:
                if key in media_map:
                    media = media_map[key]
                    thumbnail = media.get("preview_image_url") or media.get("url")
                    break

            # Extract hashtags as tags
            tags = []
            entities = tweet.get("entities", {})
            for hashtag in entities.get("hashtags", []):
                tags.append(hashtag.get("tag", ""))

            # Generate title from first line or truncate
            title = text.split("\n")[0]
            if len(title) > 100:
                title = title[:97] + "..."

            return ScrapedArticle(
                external_id=tweet_id,
                title=title,
                url=f"https://twitter.com/{handle}/status/{tweet_id}",
                content_type=ContentType.TWEET,
                published_at=published_at,
                description=self._truncate(text),
                thumbnail_url=thumbnail,
                views=None,  # Not available in Basic tier
                likes=metrics.get("like_count"),
                comments=metrics.get("reply_count"),
                author=f"@{handle}",
                tags=tags,
            )

        except Exception as e:
            logger.warning(f"Failed to parse tweet: {e}")
            return None
