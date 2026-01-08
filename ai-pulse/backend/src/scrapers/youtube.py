"""
YouTube Scraper

Uses YouTube Data API v3 to fetch videos from channels.
"""

import logging
import re
from datetime import datetime
from typing import List, Optional

import httpx

from src.config.settings import settings
from src.config.sources import Source
from src.models.enums import ContentType
from .base import BaseScraper, ScrapedArticle

logger = logging.getLogger(__name__)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


class YouTubeScraper(BaseScraper):
    """Scraper for YouTube channels using Data API v3."""

    async def fetch(self, source: Source) -> List[ScrapedArticle]:
        """Fetch videos from a YouTube channel."""
        if not settings.YOUTUBE_API_KEY:
            logger.warning("YouTube API key not configured, skipping")
            return []

        try:
            channel_id = source.channel_id
            if not channel_id:
                channel_id = await self._resolve_channel_id(source.url)
                if not channel_id:
                    logger.error(f"Could not resolve channel ID for {source.url}")
                    return []

            # Get uploads playlist ID
            playlist_id = await self._get_uploads_playlist(channel_id)
            if not playlist_id:
                return []

            # Get videos from playlist
            videos = await self._get_playlist_videos(playlist_id)

            # Get video statistics
            if videos:
                video_ids = [v.external_id for v in videos]
                stats = await self._get_video_stats(video_ids)

                for video in videos:
                    if video.external_id in stats:
                        s = stats[video.external_id]
                        video.views = s.get("views")
                        video.likes = s.get("likes")
                        video.comments = s.get("comments")

            self._log_success(source, len(videos))
            return videos

        except Exception as e:
            self._log_error(source, e)
            return []

    async def _resolve_channel_id(self, url: str) -> Optional[str]:
        """Resolve channel ID from URL or handle."""
        # Extract handle from URL
        handle_match = re.search(r'@([\w-]+)', url)
        if handle_match:
            handle = handle_match.group(1)
            return await self._get_channel_by_handle(handle)

        # Extract channel ID from URL
        id_match = re.search(r'channel/(UC[\w-]+)', url)
        if id_match:
            return id_match.group(1)

        return None

    async def _get_channel_by_handle(self, handle: str) -> Optional[str]:
        """Get channel ID from handle."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{YOUTUBE_API_BASE}/channels",
                params={
                    "key": settings.YOUTUBE_API_KEY,
                    "forHandle": handle,
                    "part": "id",
                }
            )
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            if items:
                return items[0]["id"]

        return None

    async def _get_uploads_playlist(self, channel_id: str) -> Optional[str]:
        """Get the uploads playlist ID for a channel."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{YOUTUBE_API_BASE}/channels",
                params={
                    "key": settings.YOUTUBE_API_KEY,
                    "id": channel_id,
                    "part": "contentDetails",
                }
            )
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            if items:
                return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

        return None

    async def _get_playlist_videos(self, playlist_id: str) -> List[ScrapedArticle]:
        """Get videos from a playlist."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{YOUTUBE_API_BASE}/playlistItems",
                params={
                    "key": settings.YOUTUBE_API_KEY,
                    "playlistId": playlist_id,
                    "part": "snippet",
                    "maxResults": min(settings.MAX_ARTICLES_PER_SOURCE, 50),
                }
            )
            response.raise_for_status()
            data = response.json()

        videos = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            video_id = snippet.get("resourceId", {}).get("videoId")

            if not video_id:
                continue

            # Skip private/deleted videos
            if snippet.get("title") == "Private video":
                continue

            published_str = snippet.get("publishedAt", "")
            published = self._parse_datetime(published_str)

            thumbnail = None
            thumbnails = snippet.get("thumbnails", {})
            for size in ["high", "medium", "default"]:
                if size in thumbnails:
                    thumbnail = thumbnails[size].get("url")
                    break

            videos.append(ScrapedArticle(
                external_id=video_id,
                title=snippet.get("title", ""),
                url=f"https://www.youtube.com/watch?v={video_id}",
                content_type=ContentType.VIDEO,
                published_at=published or datetime.utcnow(),
                description=self._truncate(snippet.get("description", "")),
                thumbnail_url=thumbnail,
                author=snippet.get("channelTitle"),
            ))

        return videos

    async def _get_video_stats(self, video_ids: List[str]) -> dict:
        """Get statistics for videos."""
        if not video_ids:
            return {}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{YOUTUBE_API_BASE}/videos",
                params={
                    "key": settings.YOUTUBE_API_KEY,
                    "id": ",".join(video_ids[:50]),
                    "part": "statistics,contentDetails",
                }
            )
            response.raise_for_status()
            data = response.json()

        stats = {}
        for item in data.get("items", []):
            video_id = item["id"]
            statistics = item.get("statistics", {})

            stats[video_id] = {
                "views": int(statistics.get("viewCount", 0)),
                "likes": int(statistics.get("likeCount", 0)),
                "comments": int(statistics.get("commentCount", 0)),
            }

            # Parse duration
            duration = item.get("contentDetails", {}).get("duration", "")
            stats[video_id]["duration"] = self._parse_duration(duration)

        return stats

    def _parse_duration(self, duration: str) -> int:
        """Parse ISO 8601 duration to seconds."""
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds
