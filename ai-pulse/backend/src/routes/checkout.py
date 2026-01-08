"""
Checkout Routes (Stripe)
"""

import logging
import stripe
from fastapi import APIRouter, Depends, HTTPException, status

from src.config.settings import settings
from src.config.supabase_client import get_async_supabase
from src.middleware.auth import CurrentUser, get_current_user
from src.models.schemas import CheckoutRequest, CheckoutResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/checkout", tags=["checkout"])

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Create a Stripe checkout session.

    Supports monthly and annual plans in EUR and USD.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment system not configured"
        )

    # Get appropriate price ID
    is_annual = request.plan == "annual"
    price_id = settings.get_stripe_price(request.currency, is_annual)

    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Price not configured for {request.currency} {request.plan}"
        )

    try:
        supabase = await get_async_supabase()

        # Get or create Stripe customer
        user_record = await supabase.table("users").select(
            "stripe_customer_id"
        ).eq("id", current_user.id).single().execute()

        customer_id = user_record.data.get("stripe_customer_id") if user_record.data else None

        if not customer_id:
            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": current_user.id},
            )
            customer_id = customer.id

            # Save customer ID
            await supabase.table("users").update({
                "stripe_customer_id": customer_id,
                "currency": request.currency,
            }).eq("id", current_user.id).execute()

        # Create checkout session
        success_url = request.success_url or f"{settings.CORS_ORIGINS.split(',')[0]}/dashboard?checkout=success"
        cancel_url = request.cancel_url or f"{settings.CORS_ORIGINS.split(',')[0]}/pricing?checkout=canceled"

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": current_user.id,
                "plan": request.plan,
                "currency": request.currency,
            },
        )

        return CheckoutResponse(
            checkout_url=session.url,
            session_id=session.id,
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/portal")
async def create_billing_portal(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Create a Stripe billing portal session.

    Allows users to manage their subscription.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment system not configured"
        )

    try:
        supabase = await get_async_supabase()

        # Get Stripe customer ID
        user_record = await supabase.table("users").select(
            "stripe_customer_id"
        ).eq("id", current_user.id).single().execute()

        customer_id = user_record.data.get("stripe_customer_id") if user_record.data else None

        if not customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No billing account found"
            )

        # Create portal session
        return_url = f"{settings.CORS_ORIGINS.split(',')[0]}/dashboard"

        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )

        return {"portal_url": session.url}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
