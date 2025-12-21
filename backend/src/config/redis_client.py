"""
Redis Client Configuration

Async Redis client for caching with:
- Thread-safe initialization using asyncio.Lock
- Exponential backoff reconnection
- Configurable connection pooling
"""

import asyncio
import logging
from typing import Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Global Redis client instance and lock
_redis_client: Optional[Redis] = None
_redis_lock = asyncio.Lock()
_connection_attempts = 0
_last_connection_error: Optional[str] = None


async def get_redis() -> Optional[Redis]:
    """
    Get the async Redis client with thread-safe initialization.

    Creates a connection pool on first call, reuses it thereafter.
    Returns None if connection fails (graceful degradation).
    """
    global _redis_client, _connection_attempts, _last_connection_error

    # Fast path - already connected
    if _redis_client is not None:
        try:
            # Verify connection is still alive
            await _redis_client.ping()
            return _redis_client
        except Exception:
            # Connection lost, need to reconnect
            logger.warning("Redis connection lost, attempting reconnect...")
            _redis_client = None

    # Thread-safe initialization with lock
    async with _redis_lock:
        # Double-check after acquiring lock
        if _redis_client is not None:
            return _redis_client

        # Attempt connection with exponential backoff
        for attempt in range(settings.REDIS_RETRY_ATTEMPTS):
            try:
                client = aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=settings.REDIS_MAX_CONNECTIONS,
                )
                # Test connection
                await client.ping()

                _redis_client = client
                _connection_attempts = 0
                _last_connection_error = None

                # Mask password in URL for logging
                safe_url = _mask_redis_url(settings.REDIS_URL)
                logger.info(f"Redis connected: {safe_url}")
                return _redis_client

            except Exception as e:
                _connection_attempts += 1
                _last_connection_error = str(e)
                delay = settings.REDIS_RETRY_DELAY * (2 ** attempt)

                if attempt < settings.REDIS_RETRY_ATTEMPTS - 1:
                    logger.warning(
                        f"Redis connection attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Redis connection failed after {settings.REDIS_RETRY_ATTEMPTS} "
                        f"attempts: {e}. Caching disabled."
                    )

        return None


def _mask_redis_url(url: str) -> str:
    """Mask password in Redis URL for safe logging."""
    if "@" in url and ":" in url:
        # redis://user:password@host:port -> redis://user:***@host:port
        try:
            prefix = url.split("://")[0]
            rest = url.split("://")[1]
            if "@" in rest:
                auth_part, host_part = rest.rsplit("@", 1)
                if ":" in auth_part:
                    user = auth_part.split(":")[0]
                    return f"{prefix}://{user}:***@{host_part}"
        except Exception:
            pass
    return url


async def close_redis():
    """Close Redis connection properly."""
    global _redis_client

    async with _redis_lock:
        if _redis_client:
            try:
                await _redis_client.close()
                await _redis_client.connection_pool.disconnect()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                _redis_client = None
                logger.info("Redis connection closed")


async def init_redis():
    """Initialize Redis connection on startup."""
    client = await get_redis()
    if client is None:
        logger.warning(
            "Redis unavailable at startup. Application will run with caching disabled."
        )


def get_redis_status() -> dict:
    """Get Redis connection status for health checks."""
    return {
        "connected": _redis_client is not None,
        "connection_attempts": _connection_attempts,
        "last_error": _last_connection_error,
        "max_connections": settings.REDIS_MAX_CONNECTIONS,
    }
