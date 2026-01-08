"""
Webhook Routes (Stripe)
"""

import logging
import stripe
from fastapi import APIRouter, Request, HTTPException, status

from src.config.settings import settings
from src.config.supabase_client import get_async_supabase
from src.config.observability import log_payment
from src.models.enums import SubscriptionStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.

    Processes subscription updates, payment success/failure.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook not configured"
        )

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info(f"Received Stripe webhook: {event_type}")

    supabase = await get_async_supabase()

    try:
        if event_type == "checkout.session.completed":
            await handle_checkout_completed(supabase, data)

        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(supabase, data)

        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(supabase, data)

        elif event_type == "invoice.payment_succeeded":
            await handle_payment_succeeded(supabase, data)

        elif event_type == "invoice.payment_failed":
            await handle_payment_failed(supabase, data)

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        # Don't raise - return 200 so Stripe doesn't retry
        return {"status": "error", "message": str(e)}

    return {"status": "success"}


async def handle_checkout_completed(supabase, session):
    """Handle successful checkout."""
    user_id = session.get("metadata", {}).get("user_id")
    subscription_id = session.get("subscription")
    customer_id = session.get("customer")

    if not user_id:
        logger.error("No user_id in checkout session metadata")
        return

    # Update user with subscription info
    await supabase.table("users").update({
        "subscription_status": SubscriptionStatus.ACTIVE.value,
        "subscription_id": subscription_id,
        "stripe_customer_id": customer_id,
    }).eq("id", user_id).execute()

    # Log payment
    amount = session.get("amount_total", 0)
    currency = session.get("currency", "usd").upper()
    plan = session.get("metadata", {}).get("plan", "monthly")

    log_payment(
        user_id=user_id,
        amount_cents=amount,
        currency=currency,
        plan=plan,
        success=True,
        stripe_session_id=session.get("id"),
    )

    logger.info(f"User {user_id} subscribed successfully")


async def handle_subscription_updated(supabase, subscription):
    """Handle subscription status changes."""
    customer_id = subscription.get("customer")
    status = subscription.get("status")

    # Map Stripe status to our status
    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "past_due": SubscriptionStatus.PAST_DUE,
        "canceled": SubscriptionStatus.CANCELED,
        "unpaid": SubscriptionStatus.INACTIVE,
        "trialing": SubscriptionStatus.TRIALING,
    }

    our_status = status_map.get(status, SubscriptionStatus.INACTIVE)

    # Update user
    await supabase.table("users").update({
        "subscription_status": our_status.value,
    }).eq("stripe_customer_id", customer_id).execute()

    logger.info(f"Subscription updated for customer {customer_id}: {our_status.value}")


async def handle_subscription_deleted(supabase, subscription):
    """Handle subscription cancellation."""
    customer_id = subscription.get("customer")

    await supabase.table("users").update({
        "subscription_status": SubscriptionStatus.CANCELED.value,
        "subscription_id": None,
    }).eq("stripe_customer_id", customer_id).execute()

    logger.info(f"Subscription canceled for customer {customer_id}")


async def handle_payment_succeeded(supabase, invoice):
    """Handle successful payment."""
    customer_id = invoice.get("customer")
    amount = invoice.get("amount_paid", 0)
    currency = invoice.get("currency", "usd").upper()

    # Ensure subscription is active
    await supabase.table("users").update({
        "subscription_status": SubscriptionStatus.ACTIVE.value,
    }).eq("stripe_customer_id", customer_id).execute()

    # Get user ID for logging
    user_result = await supabase.table("users").select("id").eq(
        "stripe_customer_id", customer_id
    ).single().execute()

    if user_result.data:
        log_payment(
            user_id=user_result.data["id"],
            amount_cents=amount,
            currency=currency,
            plan="subscription",
            success=True,
        )

    logger.info(f"Payment succeeded for customer {customer_id}")


async def handle_payment_failed(supabase, invoice):
    """Handle failed payment."""
    customer_id = invoice.get("customer")
    amount = invoice.get("amount_due", 0)
    currency = invoice.get("currency", "usd").upper()

    # Mark as past due
    await supabase.table("users").update({
        "subscription_status": SubscriptionStatus.PAST_DUE.value,
    }).eq("stripe_customer_id", customer_id).execute()

    # Get user ID for logging
    user_result = await supabase.table("users").select("id").eq(
        "stripe_customer_id", customer_id
    ).single().execute()

    if user_result.data:
        log_payment(
            user_id=user_result.data["id"],
            amount_cents=amount,
            currency=currency,
            plan="subscription",
            success=False,
            error="Payment failed",
        )

    logger.warning(f"Payment failed for customer {customer_id}")
