# Anonymous Flow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make research + quiz fully anonymous, create accounts at payment, block logged-in users from new audits.

**Architecture:** The quiz flow already exists with research integration. We need to: (1) add missing DB columns, (2) add teaser report generation, (3) update payment webhook to create accounts, (4) add route protection.

**Tech Stack:** FastAPI, Supabase, React, Stripe

---

## Task 1: Database Migration - Quiz Sessions Columns

**Files:**
- Create: `backend/supabase/migrations/009_anonymous_flow.sql`

**Step 1: Create migration file**

```sql
-- Anonymous Flow Updates
-- Adds columns for research, teaser reports, and proper linking

-- Add research columns (some may already exist, use IF NOT EXISTS pattern)
DO $$
BEGIN
    -- Research data
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'company_name') THEN
        ALTER TABLE quiz_sessions ADD COLUMN company_name TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'company_website') THEN
        ALTER TABLE quiz_sessions ADD COLUMN company_website TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'company_profile') THEN
        ALTER TABLE quiz_sessions ADD COLUMN company_profile JSONB;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'research_id') THEN
        ALTER TABLE quiz_sessions ADD COLUMN research_id UUID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'research_status') THEN
        ALTER TABLE quiz_sessions ADD COLUMN research_status TEXT DEFAULT 'not_started';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'dynamic_questionnaire') THEN
        ALTER TABLE quiz_sessions ADD COLUMN dynamic_questionnaire JSONB;
    END IF;

    -- Teaser report
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'teaser_report') THEN
        ALTER TABLE quiz_sessions ADD COLUMN teaser_report JSONB;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'teaser_sent_at') THEN
        ALTER TABLE quiz_sessions ADD COLUMN teaser_sent_at TIMESTAMPTZ;
    END IF;

    -- Payment tier
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'tier_purchased') THEN
        ALTER TABLE quiz_sessions ADD COLUMN tier_purchased TEXT;
    END IF;

    -- Progress tracking
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'current_section') THEN
        ALTER TABLE quiz_sessions ADD COLUMN current_section INT DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'current_question') THEN
        ALTER TABLE quiz_sessions ADD COLUMN current_question INT DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'completed_at') THEN
        ALTER TABLE quiz_sessions ADD COLUMN completed_at TIMESTAMPTZ;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quiz_sessions' AND column_name = 'updated_at') THEN
        ALTER TABLE quiz_sessions ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- Add workshop columns to audits
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audits' AND column_name = 'workshop_status') THEN
        ALTER TABLE audits ADD COLUMN workshop_status TEXT DEFAULT 'pending';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audits' AND column_name = 'workshop_completed_at') THEN
        ALTER TABLE audits ADD COLUMN workshop_completed_at TIMESTAMPTZ;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audits' AND column_name = 'strategy_call_included') THEN
        ALTER TABLE audits ADD COLUMN strategy_call_included BOOLEAN DEFAULT FALSE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audits' AND column_name = 'strategy_call_scheduled_at') THEN
        ALTER TABLE audits ADD COLUMN strategy_call_scheduled_at TIMESTAMPTZ;
    END IF;
END $$;

-- Add review columns to reports
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'review_status') THEN
        ALTER TABLE reports ADD COLUMN review_status TEXT DEFAULT 'pending';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'reviewer_id') THEN
        ALTER TABLE reports ADD COLUMN reviewer_id UUID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'reviewer_notes') THEN
        ALTER TABLE reports ADD COLUMN reviewer_notes TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'reviewed_at') THEN
        ALTER TABLE reports ADD COLUMN reviewed_at TIMESTAMPTZ;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'reports' AND column_name = 'published_at') THEN
        ALTER TABLE reports ADD COLUMN published_at TIMESTAMPTZ;
    END IF;
END $$;

-- Create interview_responses table
CREATE TABLE IF NOT EXISTS interview_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID REFERENCES audits(id) NOT NULL,
    user_id UUID REFERENCES auth.users(id) NOT NULL,

    status TEXT DEFAULT 'not_started',
    current_section INT DEFAULT 0,
    current_question INT DEFAULT 0,
    estimated_time_remaining INT,

    responses JSONB DEFAULT '{}',
    recordings JSONB DEFAULT '[]',

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for interview_responses
ALTER TABLE interview_responses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own interview responses" ON interview_responses;
CREATE POLICY "Users can view own interview responses"
    ON interview_responses FOR SELECT
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can insert own interview responses" ON interview_responses;
CREATE POLICY "Users can insert own interview responses"
    ON interview_responses FOR INSERT
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can update own interview responses" ON interview_responses;
CREATE POLICY "Users can update own interview responses"
    ON interview_responses FOR UPDATE
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Service role full access interview_responses" ON interview_responses;
CREATE POLICY "Service role full access interview_responses"
    ON interview_responses FOR ALL
    USING (auth.role() = 'service_role');

-- Index for interview lookups
CREATE INDEX IF NOT EXISTS idx_interview_responses_audit ON interview_responses(audit_id);
CREATE INDEX IF NOT EXISTS idx_interview_responses_user ON interview_responses(user_id);
```

**Step 2: Apply migration**

Run: `cd backend && supabase db push` (or apply via Supabase dashboard)

**Step 3: Commit**

```bash
git add backend/supabase/migrations/009_anonymous_flow.sql
git commit -m "feat: add database columns for anonymous flow"
```

---

## Task 2: Teaser Report Generation Service

**Files:**
- Create: `backend/src/services/teaser_service.py`
- Modify: `backend/src/routes/quiz.py` (add endpoint)

**Step 1: Create teaser service**

```python
"""
Teaser Report Service

Generates the free teaser report with:
- AI Readiness Score
- 2 full findings (unblurred)
- Remaining findings (titles only, blurred)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_teaser_report(
    company_profile: Dict[str, Any],
    quiz_answers: Dict[str, Any],
    all_findings: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generate a teaser report from research and quiz data.

    Returns:
        Teaser report with score, 2 full findings, and blurred previews
    """
    # Calculate AI Readiness Score
    score_data = _calculate_ai_readiness_score(company_profile, quiz_answers)

    # Generate or use provided findings
    if all_findings:
        findings = all_findings
    else:
        findings = _generate_preliminary_findings(company_profile, quiz_answers)

    # Split into revealed and blurred
    revealed_findings = findings[:2]  # First 2 are full detail
    blurred_findings = [
        {
            "title": f["title"],
            "category": f.get("category", "opportunity"),
            "blurred": True
        }
        for f in findings[2:6]  # Next 4 are blurred previews
    ]

    return {
        "ai_readiness_score": score_data["score"],
        "score_breakdown": score_data["breakdown"],
        "score_interpretation": _get_score_interpretation(score_data["score"]),
        "revealed_findings": revealed_findings,
        "blurred_findings": blurred_findings,
        "total_findings_available": len(findings),
        "company_name": company_profile.get("basics", {}).get("name", {}).get("value", "Your Company"),
        "industry": company_profile.get("industry", {}).get("primary_industry", {}).get("value", "General"),
        "generated_at": datetime.utcnow().isoformat(),
    }


def _calculate_ai_readiness_score(
    company_profile: Dict[str, Any],
    quiz_answers: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate AI readiness score with breakdown."""
    breakdown = {}

    # Tech maturity (0-25 points)
    tech_stack = company_profile.get("tech_stack", {})
    tech_count = len(tech_stack.get("technologies_detected", []))
    tech_score = min(25, tech_count * 5)
    breakdown["tech_maturity"] = {
        "score": tech_score,
        "max": 25,
        "factors": ["Current tech stack", "Tool adoption"]
    }

    # Process clarity (0-25 points)
    pain_points = quiz_answers.get("pain_points", [])
    has_documented = quiz_answers.get("processes_documented", False)
    process_score = 10 if has_documented else 5
    process_score += min(15, len(pain_points) * 3)  # Identifying pain = clarity
    breakdown["process_clarity"] = {
        "score": process_score,
        "max": 25,
        "factors": ["Documented processes", "Identified pain points"]
    }

    # Data readiness (0-25 points)
    size = company_profile.get("size", {})
    employee_count = size.get("employee_count", {}).get("value", 10)
    if isinstance(employee_count, str):
        employee_count = 10
    data_score = min(25, 5 + (employee_count // 10) * 2)
    breakdown["data_readiness"] = {
        "score": data_score,
        "max": 25,
        "factors": ["Company size", "Data generation potential"]
    }

    # AI experience (0-25 points)
    current_tools = quiz_answers.get("current_tools", [])
    ai_experience = quiz_answers.get("ai_experience", "none")
    ai_score = 5
    if ai_experience == "experimenting":
        ai_score = 12
    elif ai_experience == "using":
        ai_score = 20
    elif ai_experience == "scaling":
        ai_score = 25
    ai_score += min(5, len(current_tools))
    ai_score = min(25, ai_score)
    breakdown["ai_experience"] = {
        "score": ai_score,
        "max": 25,
        "factors": ["Current AI usage", "Tool adoption"]
    }

    total_score = sum(b["score"] for b in breakdown.values())

    return {
        "score": total_score,
        "breakdown": breakdown
    }


def _get_score_interpretation(score: int) -> Dict[str, Any]:
    """Get interpretation text for score."""
    if score >= 80:
        return {
            "level": "Excellent",
            "summary": "Your organization is highly ready for AI implementation.",
            "recommendation": "Focus on strategic AI initiatives that drive competitive advantage."
        }
    elif score >= 60:
        return {
            "level": "Good",
            "summary": "You have a solid foundation for AI adoption.",
            "recommendation": "Address a few gaps to maximize AI ROI."
        }
    elif score >= 40:
        return {
            "level": "Developing",
            "summary": "There are opportunities to strengthen your AI readiness.",
            "recommendation": "Start with quick wins while building foundational capabilities."
        }
    else:
        return {
            "level": "Early Stage",
            "summary": "You're at the beginning of your AI journey.",
            "recommendation": "Focus on foundational improvements before major AI investments."
        }


def _generate_preliminary_findings(
    company_profile: Dict[str, Any],
    quiz_answers: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate preliminary findings from profile and answers."""
    findings = []

    # Finding 1: Based on pain points
    pain_points = quiz_answers.get("pain_points", [])
    if pain_points:
        findings.append({
            "title": f"Automation Opportunity: {pain_points[0]}",
            "category": "efficiency",
            "summary": f"Your team identified '{pain_points[0]}' as a key challenge. AI-powered automation could reduce time spent on this by 40-60%.",
            "impact": "high",
            "roi_estimate": {"min": 15000, "max": 45000, "currency": "EUR"},
        })

    # Finding 2: Based on company size
    size = company_profile.get("size", {})
    employee_range = size.get("employee_range", {}).get("value", "11-50")
    findings.append({
        "title": "Process Standardization Gap",
        "category": "operations",
        "summary": f"Companies with {employee_range} employees typically see 25% efficiency gains from standardizing workflows before AI implementation.",
        "impact": "medium",
        "roi_estimate": {"min": 8000, "max": 25000, "currency": "EUR"},
    })

    # Finding 3: Tech stack opportunity
    tech = company_profile.get("tech_stack", {})
    tech_list = [t.get("value", "") for t in tech.get("technologies_detected", [])]
    if tech_list:
        findings.append({
            "title": f"Integration Opportunity: {tech_list[0] if tech_list else 'Core Systems'}",
            "category": "technology",
            "summary": "Your current tech stack has integration opportunities that could reduce manual data entry.",
            "impact": "medium",
        })
    else:
        findings.append({
            "title": "Technology Assessment Needed",
            "category": "technology",
            "summary": "A detailed technology assessment would identify quick automation wins.",
            "impact": "medium",
        })

    # Add more generic findings for blurred section
    findings.extend([
        {"title": "Customer Communication Automation", "category": "customer"},
        {"title": "Data Analytics Enhancement", "category": "analytics"},
        {"title": "Workflow Bottleneck Identification", "category": "operations"},
        {"title": "Cost Reduction Opportunities", "category": "efficiency"},
    ])

    return findings
```

**Step 2: Add endpoint to quiz routes**

Add to `backend/src/routes/quiz.py` after the `complete_quiz_session` endpoint:

```python
from src.services.teaser_service import generate_teaser_report
from src.services.email import send_teaser_report_email


@router.post("/sessions/{session_id}/teaser")
async def generate_session_teaser(session_id: str, email_data: Optional[Dict[str, str]] = None):
    """
    Generate teaser report for completed quiz.

    Optionally captures email and sends the teaser.
    """
    try:
        supabase = await get_async_supabase()

        # Get session
        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data
        company_profile = session.get("company_profile", {})
        answers = session.get("answers", {})

        # Generate teaser
        teaser = generate_teaser_report(company_profile, answers)

        # Update email if provided
        update_data = {
            "teaser_report": teaser,
            "updated_at": datetime.utcnow().isoformat(),
        }

        if email_data and email_data.get("email"):
            real_email = email_data["email"]
            update_data["email"] = real_email

            # Send email
            try:
                await send_teaser_report_email(
                    to_email=real_email,
                    company_name=teaser.get("company_name", "Your Company"),
                    score=teaser["ai_readiness_score"],
                    findings=teaser["revealed_findings"],
                    session_id=session_id
                )
                update_data["teaser_sent_at"] = datetime.utcnow().isoformat()
            except Exception as e:
                logger.error(f"Failed to send teaser email: {e}")

        await supabase.table("quiz_sessions").update(update_data).eq(
            "id", session_id
        ).execute()

        logger.info(f"Generated teaser for session {session_id}")

        return {
            "success": True,
            "teaser": teaser,
            "email_sent": update_data.get("teaser_sent_at") is not None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate teaser error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate teaser report"
        )
```

**Step 3: Add teaser email function**

Add to `backend/src/services/email.py`:

```python
async def send_teaser_report_email(
    to_email: str,
    company_name: str,
    score: int,
    findings: List[Dict[str, Any]],
    session_id: str
) -> bool:
    """Send teaser report via email."""
    subject = f"Your AI Readiness Score: {score}/100 - {company_name}"

    findings_html = ""
    for i, finding in enumerate(findings, 1):
        findings_html += f"""
        <div style="margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
            <h3 style="margin: 0 0 10px 0; color: #1a1a1a;">Finding {i}: {finding['title']}</h3>
            <p style="margin: 0; color: #4a4a4a;">{finding.get('summary', '')}</p>
            {f'<p style="margin: 10px 0 0 0; color: #22c55e; font-weight: bold;">Potential ROI: €{finding["roi_estimate"]["min"]:,} - €{finding["roi_estimate"]["max"]:,}</p>' if finding.get('roi_estimate') else ''}
        </div>
        """

    html_content = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #1a1a1a;">Your AI Readiness Report</h1>

        <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; margin: 20px 0;">
            <p style="color: white; margin: 0; font-size: 18px;">AI Readiness Score</p>
            <p style="color: white; margin: 10px 0; font-size: 48px; font-weight: bold;">{score}/100</p>
        </div>

        <h2 style="color: #1a1a1a;">Your Top Findings</h2>
        {findings_html}

        <div style="text-align: center; margin: 30px 0;">
            <p style="color: #666; margin-bottom: 15px;">Unlock your complete report with 15-20 detailed findings and implementation roadmap.</p>
            <a href="{settings.FRONTEND_URL}/quiz?session={session_id}#pricing"
               style="display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">
                Get Full Report
            </a>
        </div>

        <p style="color: #999; font-size: 12px; text-align: center;">
            © CRB Analyser - AI-Powered Business Audits
        </p>
    </body>
    </html>
    """

    return await send_email(to_email, subject, html_content)
```

**Step 4: Commit**

```bash
git add backend/src/services/teaser_service.py backend/src/routes/quiz.py backend/src/services/email.py
git commit -m "feat: add teaser report generation with 2 revealed findings"
```

---

## Task 3: Update Payment Webhook for Account Creation

**Files:**
- Modify: `backend/src/routes/payments.py`

**Step 1: Add account creation function**

Add to `backend/src/routes/payments.py`:

```python
import secrets
import string
from src.services.email import send_welcome_email


async def create_user_from_quiz_session(
    supabase,
    session: Dict[str, Any],
    tier_purchased: str
) -> Dict[str, Any]:
    """
    Create user account from quiz session after payment.

    Returns: {user_id, workspace_id, audit_id, password}
    """
    email = session["email"]
    company_name = session.get("company_name", "My Company")

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

    # Create workspace
    workspace_result = await supabase.table("workspaces").insert({
        "name": f"{company_name} Workspace",
    }).execute()

    workspace_id = workspace_result.data[0]["id"]

    # Link user to workspace
    await supabase.table("users").insert({
        "id": user.id,
        "email": email,
        "full_name": company_name,
        "workspace_id": workspace_id,
        "role": "admin",
    }).execute()

    # Create client
    industry = session.get("company_profile", {}).get("industry", {}).get("primary_industry", {}).get("value", "general")
    client_result = await supabase.table("clients").insert({
        "workspace_id": workspace_id,
        "name": company_name,
        "industry": industry,
        "website": session.get("company_website"),
    }).execute()

    client_id = client_result.data[0]["id"]

    # Create audit
    audit_result = await supabase.table("audits").insert({
        "workspace_id": workspace_id,
        "client_id": client_id,
        "title": f"{company_name} - CRB Audit",
        "tier": tier_purchased,
        "status": "pending",
        "workshop_status": "pending",
        "strategy_call_included": tier_purchased == "report_plus_call",
    }).execute()

    audit_id = audit_result.data[0]["id"]

    # Create interview_responses record
    await supabase.table("interview_responses").insert({
        "audit_id": audit_id,
        "user_id": user.id,
        "status": "not_started",
    }).execute()

    return {
        "user_id": user.id,
        "workspace_id": workspace_id,
        "client_id": client_id,
        "audit_id": audit_id,
        "password": password,
    }
```

**Step 2: Update webhook handler**

Find the webhook handler in `payments.py` and update the quiz session handling:

```python
@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Handle Stripe webhook events."""
    try:
        payload = await request.body()

        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            await handle_checkout_completed(session, background_tasks)

        return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_checkout_completed(
    stripe_session: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Handle successful checkout."""
    supabase = await get_async_supabase()

    metadata = stripe_session.get("metadata", {})
    quiz_session_id = metadata.get("quiz_session_id")
    tier = metadata.get("tier", "report_only")

    if not quiz_session_id:
        logger.warning("No quiz_session_id in checkout metadata")
        return

    # Get quiz session
    result = await supabase.table("quiz_sessions").select("*").eq(
        "id", quiz_session_id
    ).single().execute()

    if not result.data:
        logger.error(f"Quiz session not found: {quiz_session_id}")
        return

    session = result.data

    # Check if already processed
    if session.get("user_id"):
        logger.info(f"Quiz session {quiz_session_id} already processed")
        return

    # Create user account
    try:
        account_data = await create_user_from_quiz_session(supabase, session, tier)

        # Update quiz session with links
        await supabase.table("quiz_sessions").update({
            "user_id": account_data["user_id"],
            "workspace_id": account_data["workspace_id"],
            "audit_id": account_data["audit_id"],
            "tier_purchased": tier,
            "status": "paid",
            "stripe_payment_id": stripe_session.get("payment_intent"),
            "amount_paid": stripe_session.get("amount_total", 0) / 100,
            "payment_completed_at": datetime.utcnow().isoformat(),
        }).eq("id", quiz_session_id).execute()

        # Send welcome email in background
        background_tasks.add_task(
            send_welcome_email,
            to_email=session["email"],
            company_name=session.get("company_name", "Your Company"),
            password=account_data["password"],
            audit_id=account_data["audit_id"],
            has_strategy_call=(tier == "report_plus_call")
        )

        logger.info(f"Created account for quiz session {quiz_session_id}")

    except Exception as e:
        logger.error(f"Failed to create account: {e}")
        raise
```

**Step 3: Add welcome email function**

Add to `backend/src/services/email.py`:

```python
async def send_welcome_email(
    to_email: str,
    company_name: str,
    password: str,
    audit_id: str,
    has_strategy_call: bool = False
) -> bool:
    """Send welcome email with login credentials."""
    subject = f"Welcome to CRB Analyser - Your Account is Ready"

    call_section = ""
    if has_strategy_call:
        call_section = """
        <div style="margin: 20px 0; padding: 15px; background: #fef3c7; border-radius: 8px;">
            <h3 style="margin: 0 0 10px 0; color: #92400e;">🎯 Strategy Call Included</h3>
            <p style="margin: 0; color: #78350f;">After your workshop is complete and report is ready, you'll receive a link to book your 60-minute strategy call with our founders.</p>
        </div>
        """

    html_content = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #1a1a1a;">Welcome, {company_name}!</h1>

        <p style="color: #4a4a4a; font-size: 16px;">
            Thank you for your purchase. Your account has been created and you can now access your personalized AI audit dashboard.
        </p>

        <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="margin: 0 0 15px 0; color: #1a1a1a;">Your Login Credentials</h3>
            <p style="margin: 5px 0;"><strong>Email:</strong> {to_email}</p>
            <p style="margin: 5px 0;"><strong>Temporary Password:</strong> <code style="background: #e5e7eb; padding: 2px 8px; border-radius: 4px;">{password}</code></p>
            <p style="margin: 15px 0 0 0; font-size: 14px; color: #666;">We recommend changing your password after first login.</p>
        </div>

        {call_section}

        <h2 style="color: #1a1a1a;">Next Steps</h2>
        <ol style="color: #4a4a4a;">
            <li style="margin-bottom: 10px;"><strong>Complete your workshop</strong> - 90 minutes of questions to give us deep insight into your business</li>
            <li style="margin-bottom: 10px;"><strong>We review</strong> - Our experts review your report within 24-48 hours</li>
            <li style="margin-bottom: 10px;"><strong>Get your report</strong> - Full interactive report with 15-20 findings</li>
        </ol>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{settings.FRONTEND_URL}/login"
               style="display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">
                Start Your Workshop
            </a>
        </div>

        <p style="color: #999; font-size: 12px; text-align: center;">
            Questions? Reply to this email and we'll help you out.
        </p>
    </body>
    </html>
    """

    return await send_email(to_email, subject, html_content)
```

**Step 4: Update checkout creation to include metadata**

Find the guest checkout endpoint and add quiz_session_id to metadata:

```python
@router.post("/guest-checkout", response_model=CheckoutResponse)
async def create_guest_checkout(request: GuestCheckoutRequest):
    """Create checkout for quiz flow (no auth required)."""
    try:
        # Determine price
        prices = {
            "report_only": 14700,  # €147
            "report_plus_call": 49700,  # €497
        }
        amount = prices.get(request.tier, 14700)

        # Get or create quiz session
        supabase = await get_async_supabase()

        session_result = await supabase.table("quiz_sessions").select("id").eq(
            "email", request.email
        ).order("created_at", desc=True).limit(1).execute()

        quiz_session_id = session_result.data[0]["id"] if session_result.data else None

        # Create Stripe checkout
        checkout = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": "CRB Analysis Report" if request.tier == "report_only" else "CRB Analysis + Strategy Call",
                        "description": "AI-powered business audit with actionable recommendations"
                    },
                    "unit_amount": amount,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=request.success_url or f"{settings.FRONTEND_URL}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=request.cancel_url or f"{settings.FRONTEND_URL}/quiz",
            customer_email=request.email,
            metadata={
                "quiz_session_id": quiz_session_id,
                "tier": request.tier,
            }
        )

        return CheckoutResponse(
            checkout_url=checkout.url,
            session_id=checkout.id
        )

    except Exception as e:
        logger.error(f"Guest checkout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 5: Commit**

```bash
git add backend/src/routes/payments.py backend/src/services/email.py
git commit -m "feat: create user account on payment with welcome email"
```

---

## Task 4: Route Protection for Logged-in Users

**Files:**
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/components/AnonymousRoute.tsx`

**Step 1: Create AnonymousRoute component**

```typescript
// frontend/src/components/AnonymousRoute.tsx
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

interface AnonymousRouteProps {
  children: React.ReactNode
}

/**
 * Route guard that redirects logged-in users to dashboard.
 * Used for quiz/research flow that should only be accessible to anonymous users.
 */
export default function AnonymousRoute({ children }: AnonymousRouteProps) {
  const { isAuthenticated, loading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!loading && isAuthenticated) {
      navigate('/dashboard', { replace: true })
    }
  }, [isAuthenticated, loading, navigate])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  // Only render children if NOT authenticated
  return !isAuthenticated ? <>{children}</> : null
}
```

**Step 2: Update App.tsx routes**

```typescript
// Add import at top
import AnonymousRoute from './components/AnonymousRoute'

// Update quiz route (around line 70-80)
<Route
  path="/quiz"
  element={
    <AnonymousRoute>
      <Quiz />
    </AnonymousRoute>
  }
/>

// Update new-audit route if it exists
<Route
  path="/new-audit"
  element={
    <AnonymousRoute>
      <NewAuditV2 />
    </AnonymousRoute>
  }
/>

// Also protect root if it leads to quiz
<Route
  path="/"
  element={<Landing />}  // Landing can check auth and show different CTAs
/>
```

**Step 3: Update Landing page CTA**

In `frontend/src/pages/Landing.tsx`, update the main CTA:

```typescript
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'

// Inside component:
const { isAuthenticated } = useAuth()
const navigate = useNavigate()

const handleGetStarted = () => {
  if (isAuthenticated) {
    navigate('/dashboard')
  } else {
    navigate('/quiz')
  }
}

// Update button:
<button onClick={handleGetStarted} className="...">
  {isAuthenticated ? 'Go to Dashboard' : 'Get Your Free AI Score'}
</button>
```

**Step 4: Commit**

```bash
git add frontend/src/components/AnonymousRoute.tsx frontend/src/App.tsx frontend/src/pages/Landing.tsx
git commit -m "feat: block logged-in users from starting new audits"
```

---

## Task 5: Update Frontend Quiz Flow

**Files:**
- Modify: `frontend/src/pages/Quiz.tsx`

**Step 1: Add email capture before teaser**

The Quiz.tsx already has `email_capture` phase. Update the phase flow:

```typescript
// Update phase type if needed
type QuizPhase = 'website' | 'researching' | 'findings' | 'questions' | 'email_capture' | 'teaser' | 'pricing'

// After questions complete, go to email_capture
const handleQuestionsComplete = () => {
  setPhase('email_capture')
}

// After email capture, generate and show teaser
const handleEmailSubmit = async () => {
  if (!userEmail || !sessionId) return

  setEmailSubmitting(true)
  try {
    const response = await fetch(`${API_BASE_URL}/api/quiz/sessions/${sessionId}/teaser`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: userEmail }),
    })

    if (response.ok) {
      const data = await response.json()
      setTeaserReport(data.teaser)
      setPhase('teaser')
    }
  } catch (error) {
    console.error('Teaser generation error:', error)
  } finally {
    setEmailSubmitting(false)
  }
}
```

**Step 2: Add teaser display phase**

```typescript
// Add state for teaser
const [teaserReport, setTeaserReport] = useState<any>(null)

// Add teaser phase render
{phase === 'teaser' && teaserReport && (
  <div className="max-w-2xl mx-auto">
    {/* Score display */}
    <div className="text-center mb-8">
      <h2 className="text-2xl font-bold mb-2">Your AI Readiness Score</h2>
      <div className="text-6xl font-bold text-primary-600">
        {teaserReport.ai_readiness_score}/100
      </div>
      <p className="text-gray-600 mt-2">{teaserReport.score_interpretation.summary}</p>
    </div>

    {/* Revealed findings */}
    <div className="space-y-4 mb-8">
      <h3 className="text-xl font-semibold">Your Top Findings</h3>
      {teaserReport.revealed_findings.map((finding: any, i: number) => (
        <div key={i} className="p-4 bg-white rounded-xl shadow-sm border">
          <h4 className="font-semibold text-lg">{finding.title}</h4>
          <p className="text-gray-600 mt-1">{finding.summary}</p>
          {finding.roi_estimate && (
            <p className="text-green-600 font-medium mt-2">
              Potential ROI: €{finding.roi_estimate.min.toLocaleString()} - €{finding.roi_estimate.max.toLocaleString()}
            </p>
          )}
        </div>
      ))}
    </div>

    {/* Blurred findings */}
    <div className="space-y-2 mb-8">
      <h3 className="text-lg font-semibold text-gray-500">More Findings Available</h3>
      {teaserReport.blurred_findings.map((finding: any, i: number) => (
        <div key={i} className="p-3 bg-gray-100 rounded-lg blur-sm">
          <p className="font-medium">{finding.title}</p>
        </div>
      ))}
    </div>

    {/* CTA */}
    <button
      onClick={() => setPhase('pricing')}
      className="w-full py-4 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition"
    >
      Unlock Full Report
    </button>
  </div>
)}
```

**Step 3: Add pricing phase**

```typescript
{phase === 'pricing' && (
  <div className="max-w-3xl mx-auto">
    <h2 className="text-2xl font-bold text-center mb-8">Choose Your Plan</h2>

    <div className="grid md:grid-cols-2 gap-6">
      {/* Report Only */}
      <div className="p-6 bg-white rounded-2xl shadow-sm border-2 border-gray-200">
        <h3 className="text-xl font-bold">Full Report</h3>
        <p className="text-3xl font-bold mt-2">€147</p>
        <ul className="mt-4 space-y-2 text-gray-600">
          <li>✓ 15-20 detailed findings</li>
          <li>✓ ROI calculations</li>
          <li>✓ Implementation roadmap</li>
          <li>✓ Vendor recommendations</li>
          <li>✓ Interactive web report</li>
          <li>✓ PDF export</li>
        </ul>
        <button
          onClick={() => handleCheckout('report_only')}
          className="w-full mt-6 py-3 bg-gray-900 text-white rounded-xl hover:bg-gray-800"
        >
          Get Report
        </button>
      </div>

      {/* Report + Call */}
      <div className="p-6 bg-white rounded-2xl shadow-sm border-2 border-primary-500 relative">
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary-500 text-white px-3 py-1 rounded-full text-sm">
          Recommended
        </div>
        <h3 className="text-xl font-bold">Report + Strategy Call</h3>
        <p className="text-3xl font-bold mt-2">€497</p>
        <ul className="mt-4 space-y-2 text-gray-600">
          <li>✓ Everything in Full Report</li>
          <li>✓ 60-min strategy call with founders</li>
          <li>✓ Personalized implementation plan</li>
          <li>✓ Q&A on your specific situation</li>
          <li>✓ Priority support</li>
        </ul>
        <button
          onClick={() => handleCheckout('report_plus_call')}
          className="w-full mt-6 py-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700"
        >
          Get Report + Call
        </button>
      </div>
    </div>
  </div>
)}
```

**Step 4: Add checkout handler**

```typescript
const handleCheckout = async (tier: 'report_only' | 'report_plus_call') => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/payments/guest-checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tier,
        email: userEmail,
        quiz_answers: answers,
        quiz_results: teaserReport,
      }),
    })

    if (response.ok) {
      const data = await response.json()
      window.location.href = data.checkout_url
    }
  } catch (error) {
    console.error('Checkout error:', error)
  }
}
```

**Step 5: Commit**

```bash
git add frontend/src/pages/Quiz.tsx
git commit -m "feat: add teaser display and pricing phases to quiz"
```

---

## Task 6: Checkout Success Page

**Files:**
- Create: `frontend/src/pages/CheckoutSuccess.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Create success page**

```typescript
// frontend/src/pages/CheckoutSuccess.tsx
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

export default function CheckoutSuccess() {
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(true)
  const sessionId = searchParams.get('session_id')

  useEffect(() => {
    // Brief delay to allow webhook to process
    const timer = setTimeout(() => setLoading(false), 2000)
    return () => clearTimeout(timer)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Setting up your account...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md mx-auto text-center p-8">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-4">Payment Successful!</h1>

        <p className="text-gray-600 mb-6">
          Thank you for your purchase. We've sent your login credentials to your email.
        </p>

        <div className="bg-blue-50 p-4 rounded-xl mb-6">
          <h3 className="font-semibold text-blue-900 mb-2">Next Steps</h3>
          <ol className="text-left text-blue-800 text-sm space-y-2">
            <li>1. Check your email for login credentials</li>
            <li>2. Log in and complete your 90-minute workshop</li>
            <li>3. Receive your full report within 24-48 hours</li>
          </ol>
        </div>

        <Link
          to="/login"
          className="inline-block w-full py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 transition"
        >
          Go to Login
        </Link>
      </div>
    </div>
  )
}
```

**Step 2: Add route in App.tsx**

```typescript
import CheckoutSuccess from './pages/CheckoutSuccess'

// Add route
<Route path="/checkout/success" element={<CheckoutSuccess />} />
```

**Step 3: Commit**

```bash
git add frontend/src/pages/CheckoutSuccess.tsx frontend/src/App.tsx
git commit -m "feat: add checkout success page"
```

---

## Summary

The implementation is now complete. The flow is:

1. ✅ **Anonymous user** visits `/quiz`
2. ✅ **Research agent** scrapes their website
3. ✅ **Dynamic quiz** fills knowledge gaps
4. ✅ **Email capture** before showing results
5. ✅ **Teaser report** with 2 full findings + blurred previews
6. ✅ **Pricing page** with €147 / €497 options
7. ✅ **Stripe checkout** processes payment
8. ✅ **Account created** automatically (webhook)
9. ✅ **Welcome email** sent with credentials
10. ✅ **Logged-in users** blocked from `/quiz` (redirected to dashboard)

**To test:**
1. Apply migration to database
2. Start backend: `cd backend && uvicorn src.main:app --reload --port 8383`
3. Start frontend: `cd frontend && npm run dev`
4. Visit `/quiz` as anonymous user
5. Complete flow through to checkout
6. Verify account created and email sent
7. Log in and verify redirect works
