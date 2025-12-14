"""
Authentication Routes

Handles user signup, login, logout, and profile management.
Uses Supabase Auth for authentication and HTTP-only cookies for security.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.config.supabase_client import get_async_supabase
from src.middleware.auth import get_current_user, get_optional_user, CurrentUser
from src.models.auth import (
    SignupRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
    UserProfile,
    UpdateProfileRequest,
    ResetPasswordRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Cookie configuration
COOKIE_NAME = "crb_auth_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days in seconds


def set_auth_cookie(response: Response, token: str) -> None:
    """Set HTTP-only auth cookie."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """Clear auth cookie."""
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )


@router.post("/signup", response_model=AuthResponse)
async def signup(
    request: SignupRequest,
    response: Response,
):
    """
    Create a new user account.

    Creates user in Supabase Auth, creates workspace, and links user to workspace.
    Sets HTTP-only cookie with auth token.
    """
    try:
        supabase = await get_async_supabase()

        # Create user in Supabase Auth
        auth_response = await supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "full_name": request.full_name or "",
                }
            }
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )

        user = auth_response.user

        # Create workspace for new user
        workspace_result = await supabase.table("workspaces").insert({
            "name": f"{request.full_name or request.email}'s Workspace",
        }).execute()

        if not workspace_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create workspace"
            )

        workspace_id = workspace_result.data[0]["id"]

        # Create user record linked to workspace
        await supabase.table("users").insert({
            "id": user.id,
            "email": user.email,
            "full_name": request.full_name,
            "workspace_id": workspace_id,
            "role": "owner",
        }).execute()

        # Set auth cookie
        if auth_response.session:
            set_auth_cookie(response, auth_response.session.access_token)

        logger.info(f"User created: {user.email}")

        return AuthResponse(
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=request.full_name,
                role="owner",
                workspace_id=workspace_id,
            ),
            workspace_id=workspace_id,
            message="Account created successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login")
async def login(
    request: LoginRequest,
    response: Response,
):
    """
    Authenticate user and set auth cookie.
    """
    try:
        supabase = await get_async_supabase()

        # Authenticate with Supabase
        auth_response = await supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })

        if not auth_response.user or not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        user = auth_response.user

        # Get user's workspace
        user_record = await supabase.table("users").select(
            "workspace_id, role, full_name"
        ).eq("id", user.id).single().execute()

        workspace_id = user_record.data.get("workspace_id") if user_record.data else None
        role = user_record.data.get("role", "user") if user_record.data else "user"
        full_name = user_record.data.get("full_name") if user_record.data else None

        # Set auth cookie
        set_auth_cookie(response, auth_response.session.access_token)

        logger.info(f"User logged in: {user.email}")

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": full_name,
                "role": role,
                "workspace_id": workspace_id,
            },
            "message": "Login successful"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


@router.post("/logout")
async def logout(
    response: Response,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    """
    Log out user and clear auth cookie.
    """
    try:
        if current_user:
            supabase = await get_async_supabase()
            await supabase.auth.sign_out()
            logger.info(f"User logged out: {current_user.email}")

        clear_auth_cookie(response)

        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Logout error: {e}")
        # Still clear the cookie even if Supabase call fails
        clear_auth_cookie(response)
        return {"message": "Logged out"}


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get current user's profile.
    """
    try:
        supabase = await get_async_supabase()

        # Get full user profile
        user_result = await supabase.table("users").select(
            "*, workspaces(name)"
        ).eq("id", current_user.id).single().execute()

        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )

        user_data = user_result.data

        # Get subscription info (may not exist for new users)
        subscription_status = None
        plan_type = None

        if current_user.workspace_id:
            try:
                sub_result = await supabase.table("subscriptions").select(
                    "status, plan"
                ).eq("workspace_id", current_user.workspace_id).maybe_single().execute()

                if sub_result.data:
                    subscription_status = sub_result.data.get("status")
                    plan_type = sub_result.data.get("plan")
            except Exception:
                # No subscription exists yet - this is fine for new users
                pass

        return UserProfile(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data.get("full_name"),
            avatar_url=user_data.get("avatar_url"),
            workspace_id=user_data["workspace_id"],
            role=user_data.get("role", "user"),
            subscription_status=subscription_status,
            plan_type=plan_type,
            created_at=user_data["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.patch("/me")
async def update_profile(
    request: UpdateProfileRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Update current user's profile.
    """
    try:
        supabase = await get_async_supabase()

        update_data = {}
        if request.full_name is not None:
            update_data["full_name"] = request.full_name
        if request.avatar_url is not None:
            update_data["avatar_url"] = request.avatar_url

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        result = await supabase.table("users").update(
            update_data
        ).eq("id", current_user.id).execute()

        logger.info(f"Profile updated: {current_user.email}")

        return {"message": "Profile updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
):
    """
    Send password reset email.
    """
    try:
        supabase = await get_async_supabase()

        await supabase.auth.reset_password_email(request.email)

        # Always return success to avoid email enumeration
        return {"message": "If an account exists with this email, you will receive a password reset link"}

    except Exception as e:
        logger.error(f"Password reset error: {e}")
        # Still return success for security
        return {"message": "If an account exists with this email, you will receive a password reset link"}


@router.get("/google/url")
async def get_google_auth_url():
    """
    Get Google OAuth URL for login.
    """
    try:
        supabase = await get_async_supabase()

        # Get OAuth URL from Supabase
        redirect_url = f"{settings.CORS_ORIGINS.split(',')[0]}/auth/callback"

        response = await supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_url,
            }
        })

        return {"url": response.url}

    except Exception as e:
        logger.error(f"Google auth URL error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Google auth URL"
        )


@router.post("/google/callback")
async def google_callback(
    response: Response,
    access_token: str,
    refresh_token: Optional[str] = None,
):
    """
    Handle Google OAuth callback.
    Exchange tokens and set auth cookie.
    """
    try:
        supabase = await get_async_supabase()

        # Set session with tokens
        session_response = await supabase.auth.set_session(access_token, refresh_token or "")

        if not session_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OAuth token"
            )

        user = session_response.user

        # Check if user record exists
        user_result = await supabase.table("users").select(
            "workspace_id, role"
        ).eq("id", user.id).single().execute()

        workspace_id = None
        role = "user"

        if not user_result.data:
            # Create workspace and user record for new OAuth user
            full_name = user.user_metadata.get("full_name") or user.user_metadata.get("name")

            workspace_result = await supabase.table("workspaces").insert({
                "name": f"{full_name or user.email}'s Workspace",
            }).execute()

            workspace_id = workspace_result.data[0]["id"]
            role = "owner"

            await supabase.table("users").insert({
                "id": user.id,
                "email": user.email,
                "full_name": full_name,
                "avatar_url": user.user_metadata.get("avatar_url"),
                "workspace_id": workspace_id,
                "role": "owner",
            }).execute()

            logger.info(f"New OAuth user created: {user.email}")
        else:
            workspace_id = user_result.data.get("workspace_id")
            role = user_result.data.get("role", "user")

        # Set auth cookie
        if session_response.session:
            set_auth_cookie(response, session_response.session.access_token)

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.user_metadata.get("full_name"),
                "role": role,
                "workspace_id": workspace_id,
            },
            "message": "Google login successful"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed"
        )
