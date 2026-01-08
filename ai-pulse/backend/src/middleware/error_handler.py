"""
Error Handler Middleware

Centralized error handling and response formatting.
"""

import logging
import traceback
from typing import Union

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from src.config.settings import settings

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API error class."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_type: str = "api_error",
        details: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}
        super().__init__(message)


class NotFoundError(APIError):
    """Resource not found error."""

    def __init__(self, resource: str, resource_id: str = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(
            message=message,
            status_code=404,
            error_type="not_found"
        )


class ValidationErrorAPI(APIError):
    """Validation error."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=422,
            error_type="validation_error",
            details=details
        )


class AuthorizationError(APIError):
    """Authorization error."""

    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(
            message=message,
            status_code=403,
            error_type="authorization_error"
        )


def format_error_response(
    error_type: str,
    message: str,
    status_code: int,
    details: dict = None
) -> dict:
    """Format error response consistently."""
    response = {
        "error": {
            "type": error_type,
            "message": message,
            "status_code": status_code
        }
    }
    if details:
        response["error"]["details"] = details
    return response


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            error_type=exc.error_type,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details
        )
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            error_type="http_error",
            message=str(exc.detail),
            status_code=exc.status_code
        )
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    errors = exc.errors() if hasattr(exc, 'errors') else []

    formatted_errors = []
    for error in errors:
        loc = " -> ".join(str(l) for l in error.get("loc", []))
        formatted_errors.append({
            "field": loc,
            "message": error.get("msg", "Validation error"),
            "type": error.get("type", "value_error")
        })

    return JSONResponse(
        status_code=422,
        content=format_error_response(
            error_type="validation_error",
            message="Request validation failed",
            status_code=422,
            details={"errors": formatted_errors}
        )
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())

    if settings.is_development:
        message = f"Internal server error: {str(exc)}"
    else:
        message = "An unexpected error occurred. Please try again later."

    return JSONResponse(
        status_code=500,
        content=format_error_response(
            error_type="internal_error",
            message=message,
            status_code=500
        )
    )


def setup_error_handlers(app: FastAPI):
    """Register all error handlers."""
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
