"""
Health check routes with dependency verification.

Provides:
- /health - Basic liveness probe (for load balancers)
- /api/health - Detailed health check with dependencies
- /api/health/ready - Readiness probe (all dependencies healthy)
"""

import time
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
import redis.asyncio as redis

from src.config.settings import settings
from src.config.supabase_client import get_async_supabase

logger = logging.getLogger(__name__)

router = APIRouter()

APP_VERSION = "0.1.0"


async def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client for health checks."""
    try:
        client = redis.from_url(settings.REDIS_URL)
        return client
    except Exception as e:
        logger.warning(f"Could not create Redis client: {e}")
        return None


@router.get("/health")
async def basic_health():
    """
    Basic health check for load balancers.
    Returns 200 if the service is running.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": APP_VERSION
    }


@router.get("/api/health")
async def detailed_health():
    """
    Detailed health check with environment info.
    Does not check dependencies (use /api/health/ready for that).
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/api/health/ready")
async def readiness_check():
    """
    Readiness probe - checks all critical dependencies.
    Returns 200 only if all dependencies are healthy.
    Use this for Kubernetes readiness probes.
    """
    checks = {}
    overall_healthy = True

    # Database check (Supabase)
    try:
        start = time.time()
        supabase = await get_async_supabase()
        # Simple query to verify connection
        await supabase.table("quiz_sessions").select("id").limit(1).execute()
        latency_ms = round((time.time() - start) * 1000, 2)
        checks["database"] = {
            "status": "healthy",
            "latency_ms": latency_ms
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e)[:100]  # Truncate error message
        }
        overall_healthy = False

    # Redis check
    try:
        start = time.time()
        redis_client = await get_redis_client()
        if redis_client:
            await redis_client.ping()
            await redis_client.close()
            latency_ms = round((time.time() - start) * 1000, 2)
            checks["redis"] = {
                "status": "healthy",
                "latency_ms": latency_ms
            }
        else:
            checks["redis"] = {
                "status": "unavailable",
                "message": "Redis not configured"
            }
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        checks["redis"] = {
            "status": "unhealthy",
            "error": str(e)[:100]
        }
        # Redis is not critical for basic operation
        # Don't set overall_healthy = False

    # API Keys check (just verify they're configured)
    api_checks = {
        "anthropic": bool(settings.ANTHROPIC_API_KEY),
        "stripe": bool(settings.STRIPE_SECRET_KEY),
        "supabase": bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY)
    }
    checks["api_keys"] = {
        "status": "healthy" if all(api_checks.values()) else "degraded",
        "configured": api_checks
    }

    # Overall status
    status = "healthy" if overall_healthy else "unhealthy"
    status_code = 200 if overall_healthy else 503

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={
            "status": status,
            "service": settings.APP_NAME,
            "version": APP_VERSION,
            "environment": settings.APP_ENV,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        }
    )


@router.get("/api/health/live")
async def liveness_check():
    """
    Liveness probe - just checks if the process is running.
    Use this for Kubernetes liveness probes.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
