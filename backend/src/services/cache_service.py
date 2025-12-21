"""
Cache Service

Redis-based caching for vendors, benchmarks, and reports.
"""

import json
import logging
from typing import Optional, Any, List
from datetime import datetime

from src.config.redis_client import get_redis
from src.config.settings import settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis caching service for frequently accessed data.

    Provides get/set/invalidate operations with TTL management.
    TTLs are now configurable via settings.py.
    """

    # Cache key patterns with environment namespace
    KEY_PREFIX = f"{settings.APP_ENV}:" if settings.APP_ENV != "production" else ""
    VENDOR_KEY = KEY_PREFIX + "vendor:{slug}"
    VENDOR_LIST_KEY = KEY_PREFIX + "vendors:list:{category}:{industry}:{page}"
    BENCHMARK_KEY = KEY_PREFIX + "benchmark:{industry}:{metric}"
    REPORT_KEY = KEY_PREFIX + "report:{id}"
    QUIZ_SESSION_KEY = KEY_PREFIX + "quiz:{id}"

    # TTLs from settings (configurable per environment)
    @property
    def VENDOR_TTL(self) -> int:
        return settings.CACHE_TTL_VENDOR

    @property
    def VENDOR_LIST_TTL(self) -> int:
        return settings.CACHE_TTL_VENDOR_LIST

    @property
    def BENCHMARK_TTL(self) -> int:
        return settings.CACHE_TTL_BENCHMARK

    @property
    def REPORT_TTL(self) -> int:
        return settings.CACHE_TTL_REPORT

    @property
    def QUIZ_SESSION_TTL(self) -> int:
        return settings.CACHE_TTL_QUIZ

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a cached value by key.

        Returns None if not found or Redis unavailable.
        """
        try:
            redis = await get_redis()
            if not redis:
                return None

            cached = await redis.get(key)
            if cached:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(cached)

            logger.debug(f"Cache MISS: {key}")
            return None

        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set a cached value with TTL.

        Returns True if successful.
        """
        try:
            redis = await get_redis()
            if not redis:
                return False

            ttl = ttl or settings.CACHE_TTL_SECONDS
            await redis.setex(key, ttl, json.dumps(value, default=str))
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a cached value."""
        try:
            redis = await get_redis()
            if not redis:
                return False

            await redis.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True

        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Returns count of deleted keys.
        """
        try:
            redis = await get_redis()
            if not redis:
                return 0

            keys = await redis.keys(pattern)
            if keys:
                count = await redis.delete(*keys)
                logger.debug(f"Cache DELETE pattern {pattern}: {count} keys")
                return count
            return 0

        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    # =========================================================================
    # Vendor caching
    # =========================================================================

    async def get_vendor(self, slug: str) -> Optional[dict]:
        """Get cached vendor by slug."""
        key = self.VENDOR_KEY.format(slug=slug)
        return await self.get(key)

    async def set_vendor(self, slug: str, data: dict) -> bool:
        """Cache a vendor."""
        key = self.VENDOR_KEY.format(slug=slug)
        return await self.set(key, data, self.VENDOR_TTL)

    async def invalidate_vendor(self, slug: str) -> None:
        """
        Invalidate vendor cache.

        Also invalidates related list caches.
        """
        await self.delete(self.VENDOR_KEY.format(slug=slug))
        # Invalidate all vendor list caches
        await self.delete_pattern("vendors:list:*")

    async def get_vendor_list(
        self, category: str = "all", industry: str = "all", page: int = 1
    ) -> Optional[dict]:
        """Get cached vendor list."""
        key = self.VENDOR_LIST_KEY.format(
            category=category, industry=industry, page=page
        )
        return await self.get(key)

    async def set_vendor_list(
        self, data: dict, category: str = "all", industry: str = "all", page: int = 1
    ) -> bool:
        """Cache a vendor list."""
        key = self.VENDOR_LIST_KEY.format(
            category=category, industry=industry, page=page
        )
        return await self.set(key, data, self.VENDOR_LIST_TTL)

    # =========================================================================
    # Benchmark caching
    # =========================================================================

    async def get_benchmark(self, industry: str, metric: str = "all") -> Optional[dict]:
        """Get cached benchmark data."""
        key = self.BENCHMARK_KEY.format(industry=industry, metric=metric)
        return await self.get(key)

    async def set_benchmark(
        self, data: dict, industry: str, metric: str = "all"
    ) -> bool:
        """Cache benchmark data."""
        key = self.BENCHMARK_KEY.format(industry=industry, metric=metric)
        return await self.set(key, data, self.BENCHMARK_TTL)

    async def invalidate_benchmarks(self, industry: str = None) -> None:
        """Invalidate benchmark caches."""
        if industry:
            await self.delete_pattern(f"benchmark:{industry}:*")
        else:
            await self.delete_pattern("benchmark:*")

    # =========================================================================
    # Report caching
    # =========================================================================

    async def get_report(self, report_id: str) -> Optional[dict]:
        """Get cached report."""
        key = self.REPORT_KEY.format(id=report_id)
        return await self.get(key)

    async def set_report(self, report_id: str, data: dict) -> bool:
        """Cache a report."""
        key = self.REPORT_KEY.format(id=report_id)
        return await self.set(key, data, self.REPORT_TTL)

    async def invalidate_report(self, report_id: str) -> None:
        """Invalidate report cache."""
        await self.delete(self.REPORT_KEY.format(id=report_id))

    # =========================================================================
    # Quiz session caching
    # =========================================================================

    async def get_quiz_session(self, session_id: str) -> Optional[dict]:
        """Get cached quiz session."""
        key = self.QUIZ_SESSION_KEY.format(id=session_id)
        return await self.get(key)

    async def set_quiz_session(self, session_id: str, data: dict) -> bool:
        """Cache a quiz session."""
        key = self.QUIZ_SESSION_KEY.format(id=session_id)
        return await self.set(key, data, self.QUIZ_SESSION_TTL)

    async def invalidate_quiz_session(self, session_id: str) -> None:
        """Invalidate quiz session cache."""
        await self.delete(self.QUIZ_SESSION_KEY.format(id=session_id))

    # =========================================================================
    # Stats and monitoring
    # =========================================================================

    async def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns key counts by type and memory usage.
        """
        try:
            redis = await get_redis()
            if not redis:
                return {"available": False}

            # Count keys by type
            vendor_keys = len(await redis.keys("vendor:*"))
            benchmark_keys = len(await redis.keys("benchmark:*"))
            report_keys = len(await redis.keys("report:*"))
            quiz_keys = len(await redis.keys("quiz:*"))

            # Get memory info
            info = await redis.info("memory")

            return {
                "available": True,
                "keys": {
                    "vendors": vendor_keys,
                    "benchmarks": benchmark_keys,
                    "reports": report_keys,
                    "quiz_sessions": quiz_keys,
                    "total": vendor_keys + benchmark_keys + report_keys + quiz_keys,
                },
                "memory": {
                    "used_memory_human": info.get("used_memory_human"),
                    "used_memory_peak_human": info.get("used_memory_peak_human"),
                },
            }

        except Exception as e:
            logger.warning(f"Get cache stats error: {e}")
            return {"available": False, "error": str(e)}

    async def flush_all(self) -> bool:
        """
        Flush all cached data.

        Use with caution - clears entire cache.
        """
        try:
            redis = await get_redis()
            if not redis:
                return False

            await redis.flushdb()
            logger.info("Cache flushed")
            return True

        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False


# Singleton instance
cache_service = CacheService()
