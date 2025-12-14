"""
Payment Routes

Stripe integration for CRB Analyser payments.
"""

import logging
import stripe
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from pydantic import BaseModel

from src.config.settings import settings
from src.config.supabase_client import get_async_supabase
from src.middleware.auth import require_workspace, CurrentUser

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter()


class CheckoutRequest(BaseModel):
    """Checkout session request."""
    audit_id: str
    tier: str = "professional"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class GuestCheckoutRequest(BaseModel):
    """Guest checkout request from quiz flow."""
    tier: str  # 'quick' or 'full'
    email: str
    quiz_answers: dict
    quiz_results: dict
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutResponse(BaseModel):
    """Checkout session response."""
    checkout_url: str
    session_id: str


@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Create a Stripe checkout session for an audit.
    """
    try:
        supabase = await get_async_supabase()

        # Verify audit exists and belongs to workspace
        audit_result = await supabase.table("audits").select(
            "id, title, tier, payment_status, clients(name)"
        ).eq("id", request.audit_id).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not audit_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        audit = audit_result.data

        # Check if already paid
        if audit["payment_status"] == "paid":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audit already paid"
            )

        # Get price
        price_mapping = {
            "professional": settings.PRICE_PROFESSIONAL_EARLY,  # Early bird
            "professional_standard": settings.PRICE_PROFESSIONAL,
        }
        price_amount = price_mapping.get(request.tier, settings.PRICE_PROFESSIONAL_EARLY)

        # Default URLs
        base_url = "http://localhost:5174"  # Would be from settings in production
        success_url = request.success_url or f"{base_url}/audit/{request.audit_id}/intake"
        cancel_url = request.cancel_url or f"{base_url}/new-audit"

        client_name = audit.get("clients", {}).get("name", "Client")

        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": f"CRB Audit - {client_name}",
                            "description": f"Professional Cost/Risk/Benefit Analysis for {client_name}",
                        },
                        "unit_amount": int(price_amount * 100),  # Convert to cents
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            customer_email=current_user.email,
            metadata={
                "audit_id": request.audit_id,
                "workspace_id": current_user.workspace_id,
                "user_id": current_user.id,
                "tier": request.tier,
            },
        )

        # Store session ID on audit
        await supabase.table("audits").update({
            "stripe_payment_id": session.id,
        }).eq("id", request.audit_id).execute()

        logger.info(f"Checkout session created: {session.id} for audit {request.audit_id}")

        return CheckoutResponse(
            checkout_url=session.url,
            session_id=session.id,
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment provider error: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/guest-checkout", response_model=CheckoutResponse)
async def create_guest_checkout(request: GuestCheckoutRequest):
    """
    Create a Stripe checkout session for guest users (from quiz flow).
    No authentication required - user creates account after payment.
    """
    try:
        supabase = await get_async_supabase()

        # Get pricing based on tier
        tier_config = {
            "quick": {
                "price": settings.PRICE_QUICK_REPORT,
                "name": "Quick Report",
                "description": "10-15 detailed findings with ROI calculations and vendor recommendations",
            },
            "full": {
                "price": settings.PRICE_FULL_ANALYSIS,
                "name": "Full Analysis",
                "description": "Complete CRB analysis with vendor comparisons, implementation roadmap, and 30-min consultation",
            },
        }

        tier_info = tier_config.get(request.tier)
        if not tier_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tier: {request.tier}"
            )

        # Store quiz data for later retrieval
        quiz_data = {
            "email": request.email,
            "tier": request.tier,
            "answers": request.quiz_answers,
            "results": request.quiz_results,
            "status": "pending_payment",
            "created_at": datetime.utcnow().isoformat(),
        }

        # Insert into quiz_sessions table (temporary storage)
        quiz_result = await supabase.table("quiz_sessions").insert(quiz_data).execute()
        quiz_session_id = quiz_result.data[0]["id"]

        # Default URLs
        base_url = settings.CORS_ORIGINS.split(",")[0]  # First CORS origin
        success_url = request.success_url or f"{base_url}/checkout/success"
        cancel_url = request.cancel_url or f"{base_url}/quiz"

        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": f"CRB Analyser - {tier_info['name']}",
                            "description": tier_info["description"],
                        },
                        "unit_amount": int(tier_info["price"] * 100),  # Convert to cents
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            customer_email=request.email,
            metadata={
                "quiz_session_id": quiz_session_id,
                "tier": request.tier,
                "type": "guest_checkout",
            },
        )

        # Update quiz session with Stripe session ID
        await supabase.table("quiz_sessions").update({
            "stripe_session_id": session.id,
        }).eq("id", quiz_session_id).execute()

        logger.info(f"Guest checkout session created: {session.id} for quiz {quiz_session_id}")

        return CheckoutResponse(
            checkout_url=session.url,
            session_id=session.id,
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment provider error: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Guest checkout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
):
    """
    Handle Stripe webhooks.
    """
    try:
        payload = await request.body()

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload,
                stripe_signature,
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Handle specific events
        if event["type"] == "checkout.session.completed":
            await handle_checkout_completed(event["data"]["object"])
        elif event["type"] == "payment_intent.succeeded":
            logger.info(f"Payment succeeded: {event['data']['object']['id']}")
        elif event["type"] == "payment_intent.payment_failed":
            await handle_payment_failed(event["data"]["object"])

        return {"received": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


async def handle_checkout_completed(session: dict):
    """Handle successful checkout."""
    supabase = await get_async_supabase()
    metadata = session.get("metadata", {})

    # Check if this is a guest checkout
    if metadata.get("type") == "guest_checkout":
        await handle_guest_checkout_completed(session)
        return

    # Handle regular audit checkout
    audit_id = metadata.get("audit_id")
    if not audit_id:
        logger.error("No audit_id in session metadata")
        return

    try:
        # Update audit payment status
        await supabase.table("audits").update({
            "payment_status": "paid",
            "price_paid": session.get("amount_total", 0) / 100,
            "stripe_payment_id": session.get("payment_intent"),
        }).eq("id", audit_id).execute()

        # Log activity
        await supabase.table("audit_activity_log").insert({
            "audit_id": audit_id,
            "action": "payment_completed",
            "details": {
                "amount": session.get("amount_total", 0) / 100,
                "currency": session.get("currency", "eur"),
                "session_id": session.get("id"),
            },
        }).execute()

        logger.info(f"Payment completed for audit {audit_id}")

    except Exception as e:
        logger.error(f"Handle checkout error: {e}")


async def handle_guest_checkout_completed(session: dict):
    """Handle successful guest checkout from quiz flow."""
    supabase = await get_async_supabase()
    metadata = session.get("metadata", {})
    quiz_session_id = metadata.get("quiz_session_id")

    if not quiz_session_id:
        logger.error("No quiz_session_id in session metadata")
        return

    try:
        # Update quiz session status
        await supabase.table("quiz_sessions").update({
            "status": "paid",
            "payment_completed_at": datetime.utcnow().isoformat(),
            "stripe_payment_id": session.get("payment_intent"),
            "amount_paid": session.get("amount_total", 0) / 100,
        }).eq("id", quiz_session_id).execute()

        logger.info(f"Guest checkout completed for quiz session {quiz_session_id}")

        # TODO: Send email with report access link
        # TODO: Trigger report generation

    except Exception as e:
        logger.error(f"Handle guest checkout error: {e}")


async def handle_payment_failed(payment_intent: dict):
    """Handle failed payment."""
    logger.warning(f"Payment failed: {payment_intent.get('id')}")

    # Could notify user, update audit status, etc.


@router.get("/status/{audit_id}")
async def get_payment_status(
    audit_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get payment status for an audit.
    """
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("audits").select(
            "payment_status, price_paid, stripe_payment_id, tier"
        ).eq("id", audit_id).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        return {
            "audit_id": audit_id,
            "payment_status": result.data["payment_status"],
            "price_paid": result.data.get("price_paid"),
            "tier": result.data["tier"],
            "requires_payment": result.data["tier"] == "professional" and result.data["payment_status"] != "paid",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get payment status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment status"
        )


@router.post("/verify-session/{session_id}")
async def verify_session(
    session_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Verify a Stripe checkout session after redirect.
    """
    try:
        # Retrieve session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == "paid":
            # Double-check audit is updated
            audit_id = session.metadata.get("audit_id")
            if audit_id:
                supabase = await get_async_supabase()
                await supabase.table("audits").update({
                    "payment_status": "paid",
                }).eq("id", audit_id).execute()

            return {
                "verified": True,
                "payment_status": "paid",
                "audit_id": audit_id,
            }
        else:
            return {
                "verified": False,
                "payment_status": session.payment_status,
            }

    except stripe.error.StripeError as e:
        logger.error(f"Verify session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session"
        )
