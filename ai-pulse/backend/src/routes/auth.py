"""
Authentication Routes
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Response, status

from src.config.supabase_client import get_async_supabase
from src.config.settings import settings
from src.middleware.auth import CurrentUser, get_current_user, COOKIE_NAME
from src.models.schemas import (
    LoginRequest,
    SignupRequest,
    AuthResponse,
    UserResponse,
    UserPreferences,
)
from src.models.enums import SubscriptionStatus, PreferredTime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def set_auth_cookie(response: Response, token: str) -> None:
    """Set HTTP-only auth cookie."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )


def clear_auth_cookie(response: Response) -> None:
    """Clear auth cookie."""
    response.delete_cookie(key=COOKIE_NAME)


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest, response: Response):
    """Create a new user account."""
    try:
        supabase = await get_async_supabase()

        # Create user in Supabase Auth
        auth_response = await supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )

        user_id = auth_response.user.id

        # Create user record in users table
        await supabase.table("users").insert({
            "id": user_id,
            "email": request.email,
            "name": request.name,
            "timezone": request.timezone,
            "preferred_time": request.preferred_time.value,
            "subscription_status": SubscriptionStatus.INACTIVE.value,
            "currency": "USD",
        }).execute()

        # Set auth cookie
        if auth_response.session:
            set_auth_cookie(response, auth_response.session.access_token)

        return AuthResponse(
            user=UserResponse(
                id=user_id,
                email=request.email,
                name=request.name,
                timezone=request.timezone,
                preferred_time=request.preferred_time,
                subscription_status=SubscriptionStatus.INACTIVE,
                currency="USD",
                created_at=auth_response.user.created_at,
            ),
            message="Account created successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account"
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, response: Response):
    """Login with email and password."""
    try:
        supabase = await get_async_supabase()

        auth_response = await supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })

        if not auth_response.user or not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Get user record
        user_record = await supabase.table("users").select("*").eq(
            "id", auth_response.user.id
        ).single().execute()

        if not user_record.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User record not found"
            )

        # Set auth cookie
        set_auth_cookie(response, auth_response.session.access_token)

        return AuthResponse(
            user=UserResponse(
                id=auth_response.user.id,
                email=auth_response.user.email,
                name=user_record.data.get("name"),
                timezone=user_record.data.get("timezone", "UTC"),
                preferred_time=PreferredTime(user_record.data.get("preferred_time", "lunch")),
                subscription_status=SubscriptionStatus(user_record.data.get("subscription_status", "inactive")),
                currency=user_record.data.get("currency", "USD"),
                created_at=auth_response.user.created_at,
            ),
            message="Login successful"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


@router.post("/logout")
async def logout(response: Response):
    """Logout and clear session."""
    clear_auth_cookie(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    """Get current user profile."""
    supabase = await get_async_supabase()

    user_record = await supabase.table("users").select("*").eq(
        "id", current_user.id
    ).single().execute()

    if not user_record.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=user_record.data.get("name"),
        timezone=user_record.data.get("timezone", "UTC"),
        preferred_time=PreferredTime(user_record.data.get("preferred_time", "lunch")),
        subscription_status=SubscriptionStatus(user_record.data.get("subscription_status", "inactive")),
        currency=user_record.data.get("currency", "USD"),
        created_at=user_record.data.get("created_at"),
    )


@router.patch("/me/preferences", response_model=UserResponse)
async def update_preferences(
    preferences: UserPreferences,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update user preferences."""
    supabase = await get_async_supabase()

    update_data = {}
    if preferences.timezone:
        update_data["timezone"] = preferences.timezone
    if preferences.preferred_time:
        update_data["preferred_time"] = preferences.preferred_time.value

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No preferences to update"
        )

    await supabase.table("users").update(update_data).eq(
        "id", current_user.id
    ).execute()

    # Return updated user
    return await get_me(current_user)
