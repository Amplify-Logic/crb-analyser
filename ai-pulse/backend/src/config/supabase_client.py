"""
Supabase Client Configuration
"""

import logging
from functools import lru_cache
from typing import Optional

from supabase import create_client, Client
from supabase._async.client import AsyncClient, create_client as create_async_client

from .settings import settings

logger = logging.getLogger(__name__)


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
