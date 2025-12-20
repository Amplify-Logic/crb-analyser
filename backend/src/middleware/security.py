"""
Security Middleware

Rate limiting, request validation, and security headers.
"""

import ipaddress
import logging
import time
from collections import OrderedDict, defaultdict
from typing import Dict, Optional, Tuple

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.settings import settings

logger = logging.getLogger(__name__)


def validate_ip_address(ip: str) -> bool:
    """Validate that a string is a valid IP address (IPv4 or IPv6)."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def escape_redis_key(ip: str) -> str:
    """Escape IP address for safe use in Redis keys."""
    # Replace colons with underscores for IPv6 addresses
    return ip.replace(":", "_").replace(".", "_")


class LRUCache:
    """
    Simple LRU cache with max size to prevent memory leaks.
    Used for in-memory rate limiting fallback.
    """

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._cache: OrderedDict[str, list] = OrderedDict()

    def get(self, key: str) -> list:
        """Get or create a list for the key, moving it to end (most recent)."""
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]

        # Evict oldest if at capacity
        while len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[key] = []
        return self._cache[key]

    def cleanup_expired(self, window_seconds: int) -> int:
        """Remove expired entries. Returns count of cleaned entries."""
        current_time = time.time()
        keys_to_delete = []

        for key, timestamps in self._cache.items():
            # Filter to only keep recent timestamps
            valid = [t for t in timestamps if current_time - t < window_seconds]
            if not valid:
                keys_to_delete.append(key)
            else:
                self._cache[key] = valid

        for key in keys_to_delete:
            del self._cache[key]

        return len(keys_to_delete)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-based rate limiting middleware with in-memory fallback.

    Uses sliding window algorithm for accurate rate limiting.
    Falls back to bounded LRU in-memory storage if Redis is unavailable.
    """

    # Rate limit key prefix (uses escaped IP)
    RATE_LIMIT_KEY = "ratelimit:{ip}"

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        # Bounded in-memory fallback with LRU eviction
        self.requests = LRUCache(max_size=settings.RATE_LIMIT_MAX_MEMORY_ENTRIES)
        self._redis = None
        self._redis_checked = False
        self._last_cleanup = time.time()

    async def _get_redis(self):
        """Lazy load Redis client."""
        if not self._redis_checked:
            try:
                from src.config.redis_client import get_redis
                self._redis = await get_redis()
            except Exception:
                self._redis = None
            self._redis_checked = True
        return self._redis

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/health"]:
            return await call_next(request)

        # Get client identifier
        client_ip = self._get_client_ip(request)

        # Try Redis-based rate limiting
        redis = await self._get_redis()
        if redis:
            is_limited, retry_after = await self._check_redis_rate_limit(redis, client_ip)
        else:
            is_limited, retry_after = self._check_memory_rate_limit(client_ip)

        if is_limited:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "type": "rate_limit_exceeded",
                        "message": "Too many requests. Please try again later.",
                        "status_code": 429,
                        "retry_after": retry_after,
                    }
                },
                headers={"Retry-After": str(retry_after)}
            )

        return await call_next(request)

    async def _check_redis_rate_limit(self, redis, client_ip: str) -> Tuple[bool, int]:
        """
        Check rate limit using Redis sliding window.

        Returns (is_limited, retry_after_seconds).
        """
        try:
            # Escape IP for safe Redis key
            safe_ip = escape_redis_key(client_ip)
            key = self.RATE_LIMIT_KEY.format(ip=safe_ip)
            current = await redis.incr(key)

            # Set expiry on first request
            if current == 1:
                await redis.expire(key, self.window_seconds)

            if current > self.requests_per_minute:
                ttl = await redis.ttl(key)
                return True, max(ttl, 1)

            return False, 0

        except Exception as e:
            logger.warning(f"Redis rate limit error: {e}, falling back to memory")
            return self._check_memory_rate_limit(client_ip)

    def _check_memory_rate_limit(self, client_ip: str) -> Tuple[bool, int]:
        """
        Check rate limit using bounded in-memory LRU storage.

        Returns (is_limited, retry_after_seconds).
        """
        current_time = time.time()

        # Periodic cleanup (every 60 seconds)
        if current_time - self._last_cleanup > 60:
            cleaned = self.requests.cleanup_expired(self.window_seconds)
            if cleaned > 0:
                logger.debug(f"Cleaned {cleaned} expired rate limit entries")
            self._last_cleanup = current_time

        # Get timestamps for this IP (LRU managed)
        timestamps = self.requests.get(client_ip)

        # Clean old requests for this IP
        valid_timestamps = [
            req_time for req_time in timestamps
            if current_time - req_time < self.window_seconds
        ]

        # Check limit
        if len(valid_timestamps) >= self.requests_per_minute:
            # Calculate retry after based on oldest request
            oldest = min(valid_timestamps) if valid_timestamps else current_time
            retry_after = int(self.window_seconds - (current_time - oldest)) + 1
            return True, max(retry_after, 1)

        # Record request
        valid_timestamps.append(current_time)
        # Update the cache with cleaned timestamps
        self.requests._cache[client_ip] = valid_timestamps
        return False, 0

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract and validate client IP from request.

        Validates IP format to prevent spoofing attacks.
        """
        ip = None

        # Check for forwarded headers (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP (client IP)
            candidate = forwarded.split(",")[0].strip()
            if validate_ip_address(candidate):
                ip = candidate
            else:
                logger.warning(f"Invalid IP in X-Forwarded-For: {candidate}")

        # Try X-Real-IP header
        if not ip:
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                candidate = real_ip.strip()
                if validate_ip_address(candidate):
                    ip = candidate
                else:
                    logger.warning(f"Invalid IP in X-Real-IP: {candidate}")

        # Fall back to direct connection
        if not ip:
            if request.client and request.client.host:
                ip = request.client.host
            else:
                ip = "unknown"

        return ip


class EndpointRateLimiter:
    """
    Per-endpoint rate limiter for sensitive operations.

    Usage:
        limiter = EndpointRateLimiter()

        @router.post("/create")
        async def create_something(request: Request):
            await limiter.check(request, "create", limit=10, window=3600)
            # ... endpoint logic
    """

    RATE_LIMIT_KEY = "ratelimit:{endpoint}:{ip}"

    def __init__(self):
        self._redis = None
        self._memory: Dict[str, list] = defaultdict(list)

    async def _get_redis(self):
        """Lazy load Redis client."""
        if not self._redis:
            try:
                from src.config.redis_client import get_redis
                self._redis = await get_redis()
            except Exception:
                pass
        return self._redis

    async def check(
        self,
        request: Request,
        endpoint: str,
        limit: int,
        window: int,
    ) -> None:
        """
        Check rate limit for a specific endpoint.

        Raises HTTPException if limit exceeded.

        Args:
            request: FastAPI request
            endpoint: Endpoint identifier
            limit: Max requests in window
            window: Time window in seconds
        """
        client_ip = self._get_client_ip(request)
        redis = await self._get_redis()

        if redis:
            is_limited, retry_after = await self._check_redis(
                redis, endpoint, client_ip, limit, window
            )
        else:
            is_limited, retry_after = self._check_memory(
                endpoint, client_ip, limit, window
            )

        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limited",
                    "message": f"Rate limit exceeded for {endpoint}. Try again in {retry_after}s.",
                    "retry_after": retry_after,
                }
            )

    async def _check_redis(
        self, redis, endpoint: str, client_ip: str, limit: int, window: int
    ) -> tuple[bool, int]:
        """Check rate limit using Redis."""
        try:
            key = self.RATE_LIMIT_KEY.format(endpoint=endpoint, ip=client_ip)
            current = await redis.incr(key)

            if current == 1:
                await redis.expire(key, window)

            if current > limit:
                ttl = await redis.ttl(key)
                return True, max(ttl, 1)

            return False, 0
        except Exception:
            return self._check_memory(endpoint, client_ip, limit, window)

    def _check_memory(
        self, endpoint: str, client_ip: str, limit: int, window: int
    ) -> tuple[bool, int]:
        """Check rate limit using in-memory storage."""
        key = f"{endpoint}:{client_ip}"
        current_time = time.time()

        self._memory[key] = [
            t for t in self._memory[key] if current_time - t < window
        ]

        if len(self._memory[key]) >= limit:
            oldest = min(self._memory[key]) if self._memory[key] else current_time
            retry_after = int(window - (current_time - oldest)) + 1
            return True, max(retry_after, 1)

        self._memory[key].append(current_time)
        return False, 0

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"


# Singleton endpoint rate limiter
endpoint_limiter = EndpointRateLimiter()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Only add HSTS in production
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


def setup_security(app):
    """Setup all security middleware."""
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.RATE_LIMIT_PER_MINUTE
    )
