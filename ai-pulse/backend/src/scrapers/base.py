"""
Base Scraper

Abstract base class for all content scrapers.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from src.config.sources import Source
from src.models.enums import ContentType

logger = logging.getLogger(__name__)


@dataclass
class ScrapedArticle:
    """Article data scraped from a source."""
    external_id: str
    title: str
    url: str
    content_type: ContentType
    published_at: datetime
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    duration_seconds: Optional[int] = None
    author: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class BaseScraper(ABC):
    """Abstract base class for scrapers."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    @abstractmethod
    async def fetch(self, source: Source) -> List[ScrapedArticle]:
        """
        Fetch articles from a source.

        Args:
            source: The source configuration

        Returns:
            List of scraped articles
        """
        pass

    def _log_success(self, source: Source, count: int):
        """Log successful scrape."""
        logger.info(f"Scraped {count} articles from {source.name}")

    def _log_error(self, source: Source, error: Exception):
        """Log scrape error."""
        logger.error(f"Failed to scrape {source.name}: {error}")

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse various datetime formats."""
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        import re
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()

    def _truncate(self, text: str, max_length: int = 500) -> str:
        """Truncate text to max length."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
