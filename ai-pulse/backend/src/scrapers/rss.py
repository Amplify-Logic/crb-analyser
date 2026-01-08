"""
RSS Feed Scraper
"""

import logging
import hashlib
from datetime import datetime
from typing import List

import feedparser
import httpx

from src.config.settings import settings
from src.config.sources import Source
from src.models.enums import ContentType
from .base import BaseScraper, ScrapedArticle

logger = logging.getLogger(__name__)


class RssScraper(BaseScraper):
    """Scraper for RSS and Atom feeds."""

    async def fetch(self, source: Source) -> List[ScrapedArticle]:
        """Fetch articles from an RSS feed."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(source.url)
                response.raise_for_status()

            feed = feedparser.parse(response.text)

            if feed.bozo and not feed.entries:
                raise ValueError(f"Invalid feed: {feed.bozo_exception}")

            articles = []
            for entry in feed.entries[:settings.MAX_ARTICLES_PER_SOURCE]:
                article = self._parse_entry(entry, source)
                if article:
                    articles.append(article)

            self._log_success(source, len(articles))
            return articles

        except Exception as e:
            self._log_error(source, e)
            return []

    def _parse_entry(self, entry: dict, source: Source) -> ScrapedArticle | None:
        """Parse a single feed entry."""
        try:
            # Get required fields
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()

            if not title or not link:
                return None

            # Generate unique ID
            external_id = entry.get("id") or entry.get("guid") or self._hash_url(link)

            # Get published date
            published = None
            for date_field in ["published", "updated", "created"]:
                if date_field in entry:
                    published = self._parse_date(entry[date_field])
                    if published:
                        break

            if not published:
                published = datetime.utcnow()

            # Get description
            description = ""
            if "summary" in entry:
                description = self._clean_html(entry["summary"])
            elif "description" in entry:
                description = self._clean_html(entry["description"])
            elif "content" in entry and entry["content"]:
                description = self._clean_html(entry["content"][0].get("value", ""))

            description = self._truncate(description)

            # Get thumbnail
            thumbnail_url = None
            if "media_thumbnail" in entry and entry["media_thumbnail"]:
                thumbnail_url = entry["media_thumbnail"][0].get("url")
            elif "media_content" in entry and entry["media_content"]:
                for media in entry["media_content"]:
                    if media.get("medium") == "image":
                        thumbnail_url = media.get("url")
                        break

            # Determine content type
            content_type = self._detect_content_type(entry, source)

            # Get author
            author = entry.get("author", entry.get("dc_creator"))

            # Get tags
            tags = []
            if "tags" in entry:
                tags = [t.get("term", "") for t in entry["tags"] if t.get("term")]

            return ScrapedArticle(
                external_id=external_id,
                title=title,
                url=link,
                content_type=content_type,
                published_at=published,
                description=description,
                thumbnail_url=thumbnail_url,
                author=author,
                tags=tags,
            )

        except Exception as e:
            logger.warning(f"Failed to parse entry: {e}")
            return None

    def _parse_date(self, date_input) -> datetime | None:
        """Parse date from feed entry."""
        if isinstance(date_input, datetime):
            return date_input

        if hasattr(date_input, "timetuple"):
            # feedparser's time struct
            import time
            return datetime.fromtimestamp(time.mktime(date_input))

        if isinstance(date_input, str):
            return self._parse_datetime(date_input)

        return None

    def _detect_content_type(self, entry: dict, source: Source) -> ContentType:
        """Detect content type from entry."""
        link = entry.get("link", "").lower()

        if "arxiv.org" in link:
            return ContentType.PAPER

        if any(x in link for x in ["youtube.com", "youtu.be"]):
            return ContentType.VIDEO

        return ContentType.ARTICLE

    def _hash_url(self, url: str) -> str:
        """Generate hash-based ID from URL."""
        return hashlib.md5(url.encode()).hexdigest()
