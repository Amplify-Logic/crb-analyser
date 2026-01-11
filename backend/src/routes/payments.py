"""
Payment Routes

Stripe integration for CRB Analyser payments.
"""

import asyncio
import logging
import secrets
import string
import stripe
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header, BackgroundTasks
from pydantic import BaseModel

from src.config.settings import settings
from src.config.supabase_client import get_async_supabase
from src.middleware.auth import require_workspace, CurrentUser
from src.services.report_service import generate_report_for_quiz, get_report
from src.services.email import send_report_ready_email, send_payment_confirmation_email, send_welcome_email
from src.services.brevo_service import get_brevo_service

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


# ============================================================================
# Account Creation from Quiz Session
# ============================================================================

async def create_user_from_quiz_session(
    supabase,
    session: Dict[str, Any],
    tier_purchased: str
) -> Dict[str, Any]:
    """
    Create user account from quiz session after payment.

    Uses manual rollback to clean up partial records on failure.

    Returns: {user_id, workspace_id, audit_id, password}
    """
    email = session["email"]
    company_name = session.get("company_name", "My Company")

    # Track created resources for cleanup on failure
    created_user_id: Optional[str] = None
    created_workspace_id: Optional[str] = None
    created_client_id: Optional[str] = None
    created_audit_id: Optional[str] = None

    async def cleanup_on_failure():
        """Clean up partially created resources."""
        try:
            if created_audit_id:
                await supabase.table("interview_responses").delete().eq(
                    "audit_id", created_audit_id
                ).execute()
                await supabase.table("audits").delete().eq(
                    "id", created_audit_id
                ).execute()
            if created_client_id:
                await supabase.table("clients").delete().eq(
                    "id", created_client_id
                ).execute()
            if created_user_id:
                await supabase.table("users").delete().eq(
                    "id", created_user_id
                ).execute()
            if created_workspace_id:
                await supabase.table("workspaces").delete().eq(
                    "id", created_workspace_id
                ).execute()
            if created_user_id:
                try:
                    await supabase.auth.admin.delete_user(created_user_id)
                except Exception:
                    pass  # Auth deletion may fail, that's ok
            logger.warning(f"Cleaned up partial account creation for {email}")
        except Exception as cleanup_err:
            logger.error(f"Cleanup failed for {email}: {cleanup_err}")

    try:
        # Generate random password
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))

        # Create user in Supabase Auth
        auth_response = await supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,  # Auto-confirm since they paid
            "user_metadata": {
                "full_name": company_name,
                "source": "quiz_payment"
            }
        })

        if not auth_response.user:
            raise Exception("Failed to create user account")

        user = auth_response.user
        created_user_id = user.id

        # Create workspace
        workspace_result = await supabase.table("workspaces").insert({
            "name": f"{company_name} Workspace",
        }).execute()

        created_workspace_id = workspace_result.data[0]["id"]

        # Link user to workspace
        await supabase.table("users").insert({
            "id": user.id,
            "email": email,
            "full_name": company_name,
            "workspace_id": created_workspace_id,
            "role": "admin",
        }).execute()

        # Create client
        industry = session.get("company_profile", {}).get("industry", {}).get("primary_industry", {}).get("value", "general")
        client_result = await supabase.table("clients").insert({
            "workspace_id": created_workspace_id,
            "name": company_name,
            "industry": industry,
            "website": session.get("company_website"),
        }).execute()

        created_client_id = client_result.data[0]["id"]

        # Determine if strategy call is included
        strategy_call_included = tier_purchased in ["report_plus_call", "human", "full"]

        # Create audit
        audit_result = await supabase.table("audits").insert({
            "workspace_id": created_workspace_id,
            "client_id": created_client_id,
            "title": f"{company_name} - CRB Audit",
            "tier": tier_purchased,
            "status": "pending",
            "workshop_status": "pending",
            "strategy_call_included": strategy_call_included,
        }).execute()

        created_audit_id = audit_result.data[0]["id"]

        # Create interview_responses record
        await supabase.table("interview_responses").insert({
            "audit_id": created_audit_id,
            "user_id": user.id,
            "status": "not_started",
        }).execute()

        logger.info(f"Created account for {email}: user={user.id}, workspace={created_workspace_id}, audit={created_audit_id}")

        return {
            "user_id": user.id,
            "workspace_id": created_workspace_id,
            "client_id": created_client_id,
            "audit_id": created_audit_id,
            "password": password,
        }

    except Exception as e:
        logger.error(f"Account creation failed for {email}: {e}")
        await cleanup_on_failure()
        raise


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
            "ai": {
                "price": 147,
                "name": "CRB Report",
                "description": "15-20 AI opportunities analyzed with honest verdicts, vendor pricing, ROI calculations, and implementation roadmap",
            },
            "human": {
                "price": 497,
                "name": "CRB Report + Strategy Call",
                "description": "Complete CRB report plus 60-minute strategy call with expert and live Q&A on your specific situation",
            },
            # Legacy tiers (keep for backwards compatibility)
            "quick": {
                "price": 147,
                "name": "CRB Report",
                "description": "15-20 AI opportunities analyzed with honest verdicts, vendor pricing, ROI calculations, and implementation roadmap",
            },
            "full": {
                "price": 497,
                "name": "CRB Report + Strategy Call",
                "description": "Complete CRB report plus 60-minute strategy call with expert and live Q&A on your specific situation",
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
    background_tasks: BackgroundTasks,
    stripe_signature: str = Header(None, alias="stripe-signature"),
):
    """
    Handle Stripe webhooks.
    Returns quickly and processes report generation in background.
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
            await handle_checkout_completed(event["data"]["object"], background_tasks)
        elif event["type"] == "checkout.session.expired":
            await handle_checkout_expired(event["data"]["object"])
        elif event["type"] == "charge.refunded":
            await handle_charge_refunded(event["data"]["object"])
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


async def handle_checkout_completed(session: dict, background_tasks: BackgroundTasks):
    """Handle successful checkout with idempotency."""
    supabase = await get_async_supabase()
    metadata = session.get("metadata", {})

    # Check if this is a guest checkout
    if metadata.get("type") == "guest_checkout":
        await handle_guest_checkout_completed(session, background_tasks)
        return

    # Handle regular audit checkout
    audit_id = metadata.get("audit_id")
    if not audit_id:
        logger.error("No audit_id in session metadata")
        return

    try:
        # Idempotency check - skip if already processed
        existing = await supabase.table("audits").select("payment_status").eq(
            "id", audit_id
        ).single().execute()

        if existing.data and existing.data.get("payment_status") == "paid":
            logger.info(f"Payment already processed for audit {audit_id}, skipping")
            return

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


async def _generate_report_background(quiz_session_id: str, tier: str, email: Optional[str]):
    """
    Background task for report generation and notification.
    Runs after webhook returns to avoid Stripe timeout.
    """
    try:
        logger.info(f"Background: Starting report generation for quiz session {quiz_session_id}")
        report_id = await generate_report_for_quiz(quiz_session_id, tier)

        if report_id:
            logger.info(f"Background: Report generated: {report_id}")

            # Get report summary for email
            report = await get_report(report_id)
            if report and email:
                executive_summary = report.get("executive_summary", {})

                # Generate PDF for attachment
                pdf_bytes = None
                try:
                    from src.services.pdf_generator import generate_pdf_from_report_data
                    pdf_buffer = await generate_pdf_from_report_data(report)
                    pdf_bytes = pdf_buffer.read()

                    # Also cache PDF in storage
                    from src.services.storage_service import upload_report_pdf
                    await upload_report_pdf(report_id, pdf_bytes)
                    logger.info(f"Background: PDF generated and cached for report {report_id}")
                except Exception as pdf_err:
                    logger.warning(f"Background: Failed to generate PDF for email: {pdf_err}")

                await send_report_ready_email(
                    to_email=email,
                    report_id=report_id,
                    ai_readiness_score=executive_summary.get("ai_readiness_score", 0),
                    top_opportunities=executive_summary.get("top_opportunities", []),
                    pdf_bytes=pdf_bytes,
                )
        else:
            logger.error(f"Background: Failed to generate report for quiz session {quiz_session_id}")
            # Send failure email
            if email:
                from src.services.email import send_report_failed_email
                await send_report_failed_email(email)

    except Exception as e:
        logger.error(f"Background report generation error: {e}", exc_info=True)


async def handle_guest_checkout_completed(session: dict, background_tasks: BackgroundTasks):
    """Handle successful guest checkout from quiz flow with idempotency and account creation."""
    supabase = await get_async_supabase()
    metadata = session.get("metadata", {})
    quiz_session_id = metadata.get("quiz_session_id")
    tier = metadata.get("tier", "quick")

    if not quiz_session_id:
        logger.error("No quiz_session_id in session metadata")
        return

    try:
        # Idempotency check - skip if already processed (check for user_id as indicator)
        existing = await supabase.table("quiz_sessions").select("*").eq(
            "id", quiz_session_id
        ).single().execute()

        if not existing.data:
            logger.error(f"Quiz session not found: {quiz_session_id}")
            return

        quiz_data = existing.data

        if quiz_data.get("user_id"):
            logger.info(f"Payment already processed for quiz {quiz_session_id}, skipping")
            return

        if quiz_data.get("status") in ["paid", "generating", "completed"]:
            logger.info(f"Payment already processed for quiz {quiz_session_id}, skipping")
            return

        email = quiz_data.get("email")
        company_name = quiz_data.get("company_name", "My Company")
        amount = session.get("amount_total", 0) / 100

        # Create user account from quiz session
        logger.info(f"Creating account for quiz session {quiz_session_id}")
        try:
            account_data = await create_user_from_quiz_session(supabase, quiz_data, tier)

            # Update quiz session with links
            await supabase.table("quiz_sessions").update({
                "user_id": account_data["user_id"],
                "workspace_id": account_data["workspace_id"],
                "audit_id": account_data["audit_id"],
                "tier_purchased": tier,
                "status": "paid",
                "stripe_payment_id": session.get("payment_intent"),
                "amount_paid": amount,
                "payment_completed_at": datetime.utcnow().isoformat(),
            }).eq("id", quiz_session_id).execute()

            logger.info(f"Account created for quiz session {quiz_session_id}: user={account_data['user_id']}")

            # Update Brevo to mark as paid customer (stops upsell sequence)
            try:
                brevo = get_brevo_service()
                if brevo.is_configured and email:
                    await brevo.mark_as_paid_customer(email)
                    logger.info(f"Marked {email} as paid customer in Brevo")
            except Exception as brevo_err:
                logger.warning(f"Failed to update Brevo paid status: {brevo_err}")

            # Send welcome email with credentials
            if email:
                strategy_call_included = tier in ["report_plus_call", "human", "full"]
                await send_welcome_email(
                    to_email=email,
                    company_name=company_name,
                    password=account_data["password"],
                    audit_id=account_data["audit_id"],
                    has_strategy_call=strategy_call_included
                )

        except Exception as account_err:
            logger.error(f"Failed to create account for quiz {quiz_session_id}: {account_err}")
            # Still update quiz session status even if account creation fails
            await supabase.table("quiz_sessions").update({
                "status": "paid",
                "payment_completed_at": datetime.utcnow().isoformat(),
                "stripe_payment_id": session.get("payment_intent"),
                "amount_paid": amount,
            }).eq("id", quiz_session_id).execute()

            # Send payment confirmation email as fallback
            if email:
                await send_payment_confirmation_email(email, tier, amount)

        # Update status to generating and schedule background report generation
        await supabase.table("quiz_sessions").update({
            "status": "generating",
        }).eq("id", quiz_session_id).execute()

        # Schedule report generation in background (returns immediately to Stripe)
        logger.info(f"Scheduling background report generation for quiz session {quiz_session_id}")
        background_tasks.add_task(_generate_report_background, quiz_session_id, tier, email)

    except Exception as e:
        logger.error(f"Handle guest checkout error: {e}", exc_info=True)


async def handle_payment_failed(payment_intent: dict):
    """Handle failed payment."""
    logger.warning(f"Payment failed: {payment_intent.get('id')}")
    # Could notify user, update audit status, etc.


async def handle_checkout_expired(session: dict):
    """Handle expired checkout session."""
    supabase = await get_async_supabase()
    metadata = session.get("metadata", {})

    logger.info(f"Checkout session expired: {session.get('id')}")

    # Handle guest checkout expiration
    if metadata.get("type") == "guest_checkout":
        quiz_session_id = metadata.get("quiz_session_id")
        if quiz_session_id:
            try:
                await supabase.table("quiz_sessions").update({
                    "status": "expired",
                }).eq("id", quiz_session_id).execute()
                logger.info(f"Quiz session {quiz_session_id} marked as expired")
            except Exception as e:
                logger.error(f"Failed to update expired quiz session: {e}")
        return

    # Handle regular audit checkout expiration
    audit_id = metadata.get("audit_id")
    if audit_id:
        try:
            await supabase.table("audits").update({
                "payment_status": "expired",
            }).eq("id", audit_id).execute()

            await supabase.table("audit_activity_log").insert({
                "audit_id": audit_id,
                "action": "checkout_expired",
                "details": {"session_id": session.get("id")},
            }).execute()
            logger.info(f"Audit {audit_id} checkout marked as expired")
        except Exception as e:
            logger.error(f"Failed to update expired audit: {e}")


async def handle_charge_refunded(charge: dict):
    """Handle refunded charge."""
    supabase = await get_async_supabase()
    payment_intent_id = charge.get("payment_intent")
    refund_amount = charge.get("amount_refunded", 0) / 100

    logger.info(f"Charge refunded: {charge.get('id')}, amount: €{refund_amount}")

    if not payment_intent_id:
        logger.warning("No payment_intent in refunded charge")
        return

    try:
        # Find audit by stripe_payment_id
        audit_result = await supabase.table("audits").select("id").eq(
            "stripe_payment_id", payment_intent_id
        ).execute()

        if audit_result.data:
            audit_id = audit_result.data[0]["id"]
            await supabase.table("audits").update({
                "payment_status": "refunded",
                "refund_amount": refund_amount,
            }).eq("id", audit_id).execute()

            await supabase.table("audit_activity_log").insert({
                "audit_id": audit_id,
                "action": "payment_refunded",
                "details": {
                    "charge_id": charge.get("id"),
                    "amount": refund_amount,
                },
            }).execute()
            logger.info(f"Audit {audit_id} marked as refunded")
            return

        # Check quiz sessions
        quiz_result = await supabase.table("quiz_sessions").select("id, email").eq(
            "stripe_payment_id", payment_intent_id
        ).execute()

        if quiz_result.data:
            quiz_session_id = quiz_result.data[0]["id"]
            await supabase.table("quiz_sessions").update({
                "status": "refunded",
            }).eq("id", quiz_session_id).execute()
            logger.info(f"Quiz session {quiz_session_id} marked as refunded")

    except Exception as e:
        logger.error(f"Failed to handle refund: {e}")


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
