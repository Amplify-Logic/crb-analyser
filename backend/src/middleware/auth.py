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
from jose import JWTError, jwt

from src.config.settings import settings
from src.config.supabase_client import get_async_supabase

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

# Cookie name must match what's set in auth routes
COOKIE_NAME = "crb_auth_token"


@dataclass
class CurrentUser:
    """Authenticated user context."""
    id: str
    email: str
    workspace_id: Optional[str] = None
    role: str = "user"


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

    Use as FastAPI dependency:
        @router.get("/protected")
        async def protected_route(user: CurrentUser = Depends(get_current_user)):
            ...
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

        # Get workspace_id from user metadata or users table
        workspace_id = None
        role = "user"

        # Try to get from app_metadata first
        if user.app_metadata:
            workspace_id = user.app_metadata.get("workspace_id")
            role = user.app_metadata.get("role", "user")

        # If not in metadata, query users table
        if not workspace_id:
            user_record = await supabase.table("users").select(
                "workspace_id, role"
            ).eq("id", user.id).single().execute()

            if user_record.data:
                workspace_id = user_record.data.get("workspace_id")
                role = user_record.data.get("role", "user")

        return CurrentUser(
            id=user.id,
            email=user.email,
            workspace_id=workspace_id,
            role=role
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


async def require_workspace(
    user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Require user to have a workspace assigned.

    Use for routes that require workspace context.
    """
    if not user.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must belong to a workspace"
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
