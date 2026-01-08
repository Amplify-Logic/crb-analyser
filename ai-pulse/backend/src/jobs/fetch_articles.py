"""
Fetch Articles Job

Fetches articles from all configured sources.
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Tuple

from src.config.sources import (
    get_enabled_sources,
    get_sources_by_type,
    SourceType,
    Source,
)
from src.config.settings import settings
from src.config.observability import log_scraper_run
from src.scrapers import (
    RssScraper,
    YouTubeScraper,
    RedditScraper,
    TwitterScraper,
    ScrapedArticle,
)
from src.scoring.rules import RuleScorer

logger = logging.getLogger(__name__)


async def fetch_all_articles() -> dict:
    """
    Fetch articles from all enabled sources.

    Returns summary of fetch results.
    """
    start_time = datetime.utcnow()
    logger.info("Starting article fetch job")

    results = {
        "sources_checked": 0,
        "articles_fetched": 0,
        "errors": 0,
        "by_type": {},
    }

    # Fetch from each source type
    tasks = [
        fetch_rss_sources(),
        fetch_youtube_sources(),
        fetch_reddit_sources(),
        fetch_twitter_sources(),
    ]

    type_results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, (source_type, result) in enumerate(zip(
        ["rss", "youtube", "reddit", "twitter"],
        type_results
    )):
        if isinstance(result, Exception):
            logger.error(f"Error fetching {source_type} sources: {result}")
            results["errors"] += 1
            results["by_type"][source_type] = {"error": str(result)}
        else:
            results["sources_checked"] += result["sources"]
            results["articles_fetched"] += result["articles"]
            results["by_type"][source_type] = result

    duration = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        f"Article fetch job completed in {duration:.2f}s. "
        f"Sources: {results['sources_checked']}, "
        f"Articles: {results['articles_fetched']}, "
        f"Errors: {results['errors']}"
    )

    return results


async def fetch_rss_sources() -> dict:
    """Fetch from all RSS sources."""
    sources = get_sources_by_type(SourceType.RSS)
    scraper = RssScraper(timeout=settings.SCRAPER_TIMEOUT)

    return await _fetch_sources(sources, scraper, "rss")


async def fetch_youtube_sources() -> dict:
    """Fetch from all YouTube sources."""
    if not settings.YOUTUBE_API_KEY:
        return {"sources": 0, "articles": 0, "skipped": "No API key"}

    sources = get_sources_by_type(SourceType.YOUTUBE)
    scraper = YouTubeScraper(timeout=settings.SCRAPER_TIMEOUT)

    return await _fetch_sources(sources, scraper, "youtube")


async def fetch_reddit_sources() -> dict:
    """Fetch from all Reddit sources."""
    sources = get_sources_by_type(SourceType.REDDIT)
    scraper = RedditScraper(timeout=settings.SCRAPER_TIMEOUT)

    return await _fetch_sources(sources, scraper, "reddit")


async def fetch_twitter_sources() -> dict:
    """Fetch from all Twitter sources."""
    if not settings.TWITTER_BEARER_TOKEN:
        return {"sources": 0, "articles": 0, "skipped": "No API key"}

    sources = get_sources_by_type(SourceType.TWITTER)
    scraper = TwitterScraper(timeout=settings.SCRAPER_TIMEOUT)

    return await _fetch_sources(sources, scraper, "twitter")


async def _fetch_sources(
    sources: List[Source],
    scraper,
    source_type: str,
) -> dict:
    """Fetch from a list of sources using a scraper."""
    total_articles = 0
    errors = 0

    for source in sources:
        start = datetime.utcnow()

        try:
            articles = await scraper.fetch(source)
            total_articles += len(articles)

            duration = (datetime.utcnow() - start).total_seconds()
            log_scraper_run(
                source_name=source.name,
                articles_found=len(articles),
                duration_seconds=duration,
                success=True,
            )

            # Rate limit between sources
            await asyncio.sleep(settings.SCRAPER_RATE_LIMIT_DELAY)

        except Exception as e:
            errors += 1
            duration = (datetime.utcnow() - start).total_seconds()
            log_scraper_run(
                source_name=source.name,
                articles_found=0,
                duration_seconds=duration,
                success=False,
                error=str(e),
            )

    return {
        "sources": len(sources),
        "articles": total_articles,
        "errors": errors,
    }


# CLI entry point
if __name__ == "__main__":
    import asyncio

    async def main():
        result = await fetch_all_articles()
        print(f"Fetch results: {result}")

    asyncio.run(main())
