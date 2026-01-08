"""Middleware module for AI Pulse."""

from .auth import (
    CurrentUser,
    get_current_user,
    get_optional_user,
    require_admin,
    require_subscriber,
)
from .error_handler import (
    APIError,
    NotFoundError,
    ValidationErrorAPI,
    AuthorizationError,
    setup_error_handlers,
)
from .request_logger import RequestLoggingMiddleware, setup_request_logging

__all__ = [
    "CurrentUser",
    "get_current_user",
    "get_optional_user",
    "require_admin",
    "require_subscriber",
    "APIError",
    "NotFoundError",
    "ValidationErrorAPI",
    "AuthorizationError",
    "setup_error_handlers",
    "RequestLoggingMiddleware",
    "setup_request_logging",
]
