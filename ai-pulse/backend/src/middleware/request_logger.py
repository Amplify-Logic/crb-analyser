"""
Request Logging Middleware

Logs all incoming requests with timing, status, and optional request IDs.
"""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Slow request thresholds (ms)
SLOW_REQUEST_WARNING = 1000  # 1 second
SLOW_REQUEST_ERROR = 5000  # 5 seconds


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests with timing information.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check for correlation ID from upstream, or generate new one
        correlation_id = request.headers.get("X-Correlation-ID")
        request_id = correlation_id or str(uuid.uuid4())

        # Store request ID in state for access in routes
        request.state.request_id = request_id

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Record start time
        start_time = time.perf_counter()

        # Log incoming request
        logger.info(
            f"[{request_id}] -> {request.method} {request.url.path} "
            f"from {client_ip}"
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[{request_id}] x {request.method} {request.url.path} "
                f"EXCEPTION after {duration_ms:.2f}ms: {str(e)}"
            )
            raise

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = request_id

        # Log based on status code and duration
        status = response.status_code

        # Flag slow requests
        if duration_ms >= SLOW_REQUEST_ERROR:
            logger.error(
                f"[{request_id}] SLOW REQUEST: {request.method} {request.url.path} "
                f"took {duration_ms:.2f}ms (threshold: {SLOW_REQUEST_ERROR}ms)"
            )
        elif duration_ms >= SLOW_REQUEST_WARNING:
            logger.warning(
                f"[{request_id}] Slow request: {request.method} {request.url.path} "
                f"took {duration_ms:.2f}ms"
            )

        if status >= 500:
            logger.error(
                f"[{request_id}] x {request.method} {request.url.path} "
                f"{status} in {duration_ms:.2f}ms"
            )
        elif status >= 400:
            logger.warning(
                f"[{request_id}] ! {request.method} {request.url.path} "
                f"{status} in {duration_ms:.2f}ms"
            )
        else:
            # Skip logging health checks at INFO level to reduce noise
            if request.url.path in ["/health", "/api/health"]:
                logger.debug(
                    f"[{request_id}] ok {request.method} {request.url.path} "
                    f"{status} in {duration_ms:.2f}ms"
                )
            else:
                logger.info(
                    f"[{request_id}] ok {request.method} {request.url.path} "
                    f"{status} in {duration_ms:.2f}ms"
                )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers or connection."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"


def setup_request_logging(app):
    """Add request logging middleware to the app."""
    app.add_middleware(RequestLoggingMiddleware)
