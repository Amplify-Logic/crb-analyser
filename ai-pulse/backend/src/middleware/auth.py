"""
Authentication Middleware

Handles JWT validation and user extraction from Supabase Auth.
Supports both Bearer token (Authorization header) and HTTP-only cookies.
"""

import logging
from typing import Optional
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.config.settings import settings
from src.config.supabase_client import get_async_supabase

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

# Cookie name for HTTP-only auth
COOKIE_NAME = "aipulse_auth_token"


@dataclass
class CurrentUser:
    """Authenticated user context."""
    id: str
    email: str
    subscription_status: str = "inactive"  # active, inactive, past_due, canceled
    role: str = "user"  # user, admin
    timezone: str = "UTC"
    preferred_time: str = "lunch"  # morning, lunch, evening
    currency: str = "USD"


def get_token_from_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials]
) -> Optional[str]:
    """Extract token from either Authorization header or HTTP-only cookie."""
    # First try Authorization header
    if credentials:
        return credentials.credentials

    # Then try HTTP-only cookie
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token

    return None


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> CurrentUser:
    """
    Extract and validate the current user from JWT token.

    Checks both Authorization header (Bearer token) and HTTP-only cookies.
    """
    token = get_token_from_request(request, credentials)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify token with Supabase
        supabase = await get_async_supabase()
        user_response = await supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = user_response.user

        # Get user details from users table
        user_record = await supabase.table("users").select(
            "subscription_status, role, timezone, preferred_time, currency"
        ).eq("id", user.id).single().execute()

        subscription_status = "inactive"
        role = "user"
        timezone = "UTC"
        preferred_time = "lunch"
        currency = "USD"

        if user_record.data:
            subscription_status = user_record.data.get("subscription_status", "inactive")
            role = user_record.data.get("role", "user")
            timezone = user_record.data.get("timezone", "UTC")
            preferred_time = user_record.data.get("preferred_time", "lunch")
            currency = user_record.data.get("currency", "USD")

        return CurrentUser(
            id=user.id,
            email=user.email,
            subscription_status=subscription_status,
            role=role,
            timezone=timezone,
            preferred_time=preferred_time,
            currency=currency,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[CurrentUser]:
    """
    Get current user if authenticated, None otherwise.

    Use for routes that work both authenticated and anonymous.
    """
    token = get_token_from_request(request, credentials)
    if not token:
        return None

    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


async def require_subscriber(
    user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Require user to have an active subscription.

    Use for subscriber-only routes.
    """
    if user.subscription_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required"
        )
    return user


async def require_admin(
    user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Require user to have admin role.

    Use for admin-only routes.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user
