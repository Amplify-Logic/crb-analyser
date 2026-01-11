"""
Supabase Client Configuration

Includes retry logic with exponential backoff for resilient database operations.
"""

import asyncio
import logging
from functools import lru_cache, wraps
from typing import Optional, Callable, TypeVar, Any

from supabase import create_client, Client
from supabase._async.client import AsyncClient, create_client as create_async_client

from .settings import settings

logger = logging.getLogger(__name__)

# Retry configuration
SUPABASE_MAX_RETRIES = 3
SUPABASE_BASE_DELAY = 1.0  # seconds

T = TypeVar('T')


def with_retry(
    max_retries: int = SUPABASE_MAX_RETRIES,
    base_delay: float = SUPABASE_BASE_DELAY,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for Supabase operations with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles each retry)
        exceptions: Tuple of exceptions to catch and retry

    Usage:
        @with_retry(max_retries=3)
        async def my_db_operation():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"Supabase operation '{func.__name__}' failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"Supabase operation '{func.__name__}' failed after {max_retries} attempts: {e}"
                        )

            raise last_exception  # type: ignore

        return wrapper  # type: ignore
    return decorator


class SupabaseClientManager:
    """Manages Supabase client instances."""

    _sync_client: Optional[Client] = None
    _async_client: Optional[AsyncClient] = None

    @classmethod
    def get_sync_client(cls) -> Client:
        """Get or create synchronous Supabase client."""
        if cls._sync_client is None:
            if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set"
                )
            cls._sync_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Supabase sync client initialized")
        return cls._sync_client

    @classmethod
    async def get_async_client(cls) -> AsyncClient:
        """Get or create asynchronous Supabase client."""
        if cls._async_client is None:
            if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set"
                )
            cls._async_client = await create_async_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Supabase async client initialized")
        return cls._async_client

    @classmethod
    async def close_async_client(cls) -> None:
        """Close async client connection."""
        if cls._async_client is not None:
            cls._async_client = None
            logger.info("Supabase async client closed")


@lru_cache()
def get_supabase() -> Client:
    """Get synchronous Supabase client (cached)."""
    return SupabaseClientManager.get_sync_client()


async def get_async_supabase() -> AsyncClient:
    """Get asynchronous Supabase client (FastAPI dependency)."""
    return await SupabaseClientManager.get_async_client()


async def init_supabase() -> None:
    """Initialize Supabase clients on startup."""
    try:
        get_supabase()
        await get_async_supabase()
        logger.info("Supabase clients initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase: {e}")
        raise


async def close_supabase() -> None:
    """Close Supabase clients on shutdown."""
    await SupabaseClientManager.close_async_client()
    logger.info("Supabase clients closed")
