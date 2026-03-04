# backend/src/routes/workshop.py
"""
Workshop Routes

API endpoints for the personalized 90-minute workshop experience.
Handles all three phases: Confirmation, Deep-Dive, and Synthesis.

Phases:
1. Confirmation - Verify research findings and prioritize pain points
2. Deep-Dive - Adaptive questioning per pain point with milestone summaries
3. Synthesis - Final questions and transition to report generation
"""

import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.middleware.security import endpoint_limiter
from src.config.supabase_client import get_async_supabase
from src.config.settings import settings
from src.skills import get_skill, SkillContext
from src.knowledge import normalize_industry
from src.models.workshop import (
    WorkshopPhase,
    WorkshopData,
    DetectedSignals,
    WorkshopConfidence,
    DepthDimensions,
)

import anthropic

logger = logging.getLogger(__name__)

router = APIRouter()

# Global client for skills
_anthropic_client: Optional[anthropic.Anthropic] = None


def get_anthropic_client() -> anthropic.Anthropic:
    """Get or create the Anthropic client."""
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _anthropic_client


# =============================================================================
# Request/Response Models
# =============================================================================

class WorkshopStartRequest(BaseModel):
    """Request to start workshop."""
    session_id: str


class ConfirmationCard(BaseModel):
    """A card shown in Phase 1 confirmation."""
    category: str
    title: str
    items: List[str]
    source_count: int
    editable: bool = True


class WorkshopStartResponse(BaseModel):
    """Response from workshop start."""
    session_id: str
    company_name: str
    confirmation_cards: List[ConfirmationCard]
    detected_signals: Dict[str, Any]
    pain_points: List[Dict[str, str]]


class WorkshopConfirmRequest(BaseModel):
    """Request to save confirmation phase."""
    session_id: str
    ratings: Dict[str, str]  # category -> "accurate" | "inaccurate" | "edited"
    corrections: Optional[List[Dict[str, str]]] = None
    priority_order: Optional[List[str]] = None


class WorkshopRespondRequest(BaseModel):
    """Request to get next workshop response."""
    session_id: str
    message: str
    current_pain_point: str


class WorkshopRespondResponse(BaseModel):
    """Response with next question."""
    response: str
    confidence_update: Dict[str, Any]
    should_show_milestone: bool
    estimated_remaining: str
    suggestions: List[str] = []


class MilestoneRequest(BaseModel):
    """Request to generate milestone summary."""
    session_id: str
    pain_point_id: str


class MilestoneFeedbackRequest(BaseModel):
    """Request to save milestone feedback."""
    session_id: str
    pain_point_id: str
    feedback: str  # "looks_good" | "needs_edit"
    notes: Optional[str] = None


class WorkshopCompleteRequest(BaseModel):
    """Request to complete workshop."""
    session_id: str
    final_answers: Dict[str, Any]


# =============================================================================
# Helpers
# =============================================================================


def _get_stage_suggestions(stage: str, pain_label: str = "") -> List[str]:
    """Return 2-3 contextual quick-reply suggestions matching the current question's stage."""
    stage_suggestions: Dict[str, List[str]] = {
        "current_state": [
            "It's mostly manual — someone handles it each time",
            "We have a tool but still do a lot by hand",
            "Multiple people are involved and it's messy",
        ],
        "failed_attempts": [
            "We haven't really tried to change this yet",
            "We tested a solution but it didn't stick",
            "We explored options but nothing was the right fit",
        ],
        "cost_impact": [
            "It takes several hours every week",
            "The biggest cost is errors and rework",
            "It's hard to measure but it definitely slows us down",
        ],
        "ideal_state": [
            "I'd want it fully automated end-to-end",
            "Just faster and more reliable than today",
            "Better visibility so we know what's happening",
        ],
        "stakeholders": [
            "I make this call myself",
            "My team and I decide together",
            "Leadership needs to approve any changes",
        ],
    }
    return stage_suggestions.get(stage, [])[:3]


# =============================================================================
# Dev Routes
# =============================================================================


@router.post("/dev/create-test-session")
async def create_test_workshop_session(industry: str = "ecommerce"):
    """DEV ONLY: Create a paid test session ready for workshop testing."""
    import uuid

    if settings.APP_ENV not in ("development", "dev", "local"):
        raise HTTPException(status_code=403, detail="Dev-only endpoint")

    # Industry test data (mirrors frontend devTestData.ts)
    test_data: Dict[str, Dict[str, Any]] = {
        "dental": {
            "company_name": "Nordic Dental Group",
            "website": "https://nordicdental.example.com",
            "profile": {
                "basics": {"name": {"value": "Nordic Dental Group"}, "industry": {"value": "dental"}},
                "size": {"employee_range": {"value": "21-50"}, "employee_count": {"value": 35}},
            },
            "answers": {
                "industry": "dental",
                "company_size": "21-50",
                "employee_count": 35,
                "current_tools": ["crm", "scheduling", "communication"],
                "biggest_challenge": "Patients ghost us after consultations",
                "pain_points": ["patient no-shows", "insurance verification", "treatment follow-up"],
                "automation_experience": "basic",
                "ai_budget": "10000-25000",
            },
        },
        "ecommerce": {
            "company_name": "Verde Sustainable Fashion",
            "website": "https://verde.example.com",
            "profile": {
                "basics": {"name": {"value": "Verde Sustainable Fashion"}, "industry": {"value": "ecommerce"}},
                "size": {"employee_range": {"value": "11-25"}, "employee_count": {"value": 16}},
            },
            "answers": {
                "industry": "ecommerce",
                "company_size": "11-25",
                "employee_count": 16,
                "current_tools": ["crm", "email_marketing", "helpdesk", "analytics"],
                "biggest_challenge": "Cart abandonment at 72%",
                "pain_points": ["cart abandonment", "support overwhelm", "inventory forecasting", "returns"],
                "automation_experience": "intermediate",
                "ai_budget": "10000-25000",
            },
        },
    }

    data = test_data.get(industry, test_data["ecommerce"])
    session_id = str(uuid.uuid4())

    session_data = {
        "id": session_id,
        "email": "dev-workshop-test@crb-analyser.local",
        "tier": "full",
        "status": "paid",
        "current_section": 0,
        "current_question": 0,
        "answers": data["answers"],
        "company_name": data["company_name"],
        "company_website": data["website"],
        "company_profile": data["profile"],
        "interview_data": {"messages": [], "confidence": {}},
    }

    supabase = await get_async_supabase()
    await supabase.table("quiz_sessions").insert(session_data).execute()

    logger.info(f"DEV: Created workshop test session {session_id} ({data['company_name']})")

    return {
        "session_id": session_id,
        "company_name": data["company_name"],
        "industry": industry,
        "workshop_url": f"/workshop?session_id={session_id}",
    }


# =============================================================================
# Routes
# =============================================================================

@router.post("/start", response_model=WorkshopStartResponse)
async def start_workshop(request: WorkshopStartRequest):
    """
    Start the workshop for a paid session.

    Loads quiz data and company profile, builds confirmation cards,
    detects adaptive signals, and initializes workshop state.
    """
    try:
        supabase = await get_async_supabase()

        # Get session
        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", request.session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data

        # Verify session is paid and ready for workshop
        workshop_valid_statuses = [
            "paid", "workshop_started", "workshop_complete",
            "workshop_confirmation", "workshop_deepdive", "workshop",
        ]
        if session.get("status") not in workshop_valid_statuses:
            logger.warning(
                f"Workshop start called with invalid session status={session.get('status')} "
                f"for session_id={request.session_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Session not ready for workshop. Status: {session.get('status')}"
            )

        company_profile = session.get("company_profile", {})
        answers = session.get("answers", {})

        # Extract company name
        basics = company_profile.get("basics", {})
        company_name = basics.get("name", {}).get("value", session.get("company_name", "Your Company"))

        # Build confirmation cards from quiz + research data
        confirmation_cards = _build_confirmation_cards(company_profile, answers)

        # Detect adaptive signals
        client = get_anthropic_client()
        signal_skill = get_skill("adaptive-signal-detector", client=client)

        industry = answers.get("industry", "professional-services")
        normalized_industry = normalize_industry(industry)

        signal_context = SkillContext(
            industry=normalized_industry,
            metadata={
                "role": answers.get("role") or basics.get("contact_role", {}).get("value"),
                "company_size": answers.get("company_size"),
                "budget_answer": answers.get("ai_budget"),
                "quiz_answers": answers,
                "company_profile": company_profile,
            }
        )

        signal_result = await signal_skill.run(signal_context)
        detected_signals = signal_result.data if signal_result.success else {}

        # Build pain points list
        pain_points = _extract_pain_points(answers, company_profile)

        # Initialize workshop data
        workshop_data = WorkshopData(
            phase=WorkshopPhase.CONFIRMATION,
            detected_signals=DetectedSignals(
                technical=detected_signals.get("technical", False),
                budget_ready=detected_signals.get("budget_ready", False),
                decision_maker=detected_signals.get("decision_maker", False),
            ),
        )

        # Update session
        await supabase.table("quiz_sessions").update({
            "workshop_phase": "confirmation",
            "workshop_data": workshop_data.to_dict(),
            "workshop_started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        logger.info(f"Workshop started for session {request.session_id}")

        return WorkshopStartResponse(
            session_id=request.session_id,
            company_name=company_name,
            confirmation_cards=confirmation_cards,
            detected_signals=detected_signals,
            pain_points=pain_points,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workshop start error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start workshop"
        )


@router.post("/confirm")
async def save_confirmation(request: WorkshopConfirmRequest):
    """
    Save Phase 1 confirmation ratings and move to deep-dive.
    """
    try:
        supabase = await get_async_supabase()

        # Get session
        result = await supabase.table("quiz_sessions").select(
            "workshop_data, answers, status"
        ).eq("id", request.session_id).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Verify session has been paid for
        workshop_valid_statuses = [
            "paid", "workshop_started", "workshop_complete",
            "workshop_confirmation", "workshop_deepdive", "workshop",
        ]
        if result.data.get("status") not in workshop_valid_statuses:
            logger.warning(
                f"Workshop confirm called with invalid session status={result.data.get('status')} "
                f"for session_id={request.session_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session must be paid before accessing workshop"
            )

        workshop_data = result.data.get("workshop_data", {})
        answers = result.data.get("answers", {})

        # Update confirmation data
        workshop_data["confirmation"] = {
            "ratings": request.ratings,
            "corrections": request.corrections or [],
            "priority_order": request.priority_order or [],
            "completed_at": datetime.utcnow().isoformat(),
        }
        workshop_data["phase"] = "deepdive"

        # Determine deep-dive order
        pain_points = _extract_pain_points(answers, {})
        if request.priority_order:
            # Use user's priority
            deep_dive_order = request.priority_order
        else:
            # Default order from quiz pain points
            deep_dive_order = [pp["id"] for pp in pain_points[:4]]

        workshop_data["deep_dive_order"] = deep_dive_order
        workshop_data["pain_point_labels"] = {pp["id"]: pp["label"] for pp in pain_points}
        workshop_data["current_deep_dive_index"] = 0
        workshop_data["deep_dives"] = []

        # Update session
        await supabase.table("quiz_sessions").update({
            "workshop_phase": "deepdive",
            "workshop_data": workshop_data,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        return {
            "success": True,
            "phase": "deepdive",
            "deep_dive_order": deep_dive_order,
            "first_pain_point": deep_dive_order[0] if deep_dive_order else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save confirmation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save confirmation"
        )


@router.post("/respond", response_model=WorkshopRespondResponse)
async def workshop_respond(request: WorkshopRespondRequest, raw_request: Request):
    """
    Process user message and return adaptive response.
    """
    # Rate limit: 10 requests per minute (LLM-calling endpoint)
    await endpoint_limiter.check(raw_request, "workshop_respond", limit=10, window=60)

    try:
        supabase = await get_async_supabase()

        # Get session
        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", request.session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data

        # Verify session has been paid for
        workshop_valid_statuses = [
            "paid", "workshop_started", "workshop_complete",
            "workshop_confirmation", "workshop_deepdive", "workshop",
        ]
        if session.get("status") not in workshop_valid_statuses:
            logger.warning(
                f"Workshop respond called with invalid session status={session.get('status')} "
                f"for session_id={request.session_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session must be paid before accessing workshop"
            )

        workshop_data = session.get("workshop_data", {})
        answers = session.get("answers", {})
        company_profile = session.get("company_profile", {})

        # Get current deep-dive state
        deep_dives = workshop_data.get("deep_dives", [])

        # Find or create current deep-dive
        current_dd = None
        for dd in deep_dives:
            if dd.get("pain_point_id") == request.current_pain_point:
                current_dd = dd
                break

        if not current_dd:
            current_dd = {
                "pain_point_id": request.current_pain_point,
                "pain_point_label": _get_pain_point_label(request.current_pain_point),
                "started_at": datetime.utcnow().isoformat(),
                "transcript": [],
                "conversation_stage": "current_state",
            }
            deep_dives.append(current_dd)

        # Add user message to transcript
        current_dd["transcript"].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Generate response using workshop question skill
        client = get_anthropic_client()
        question_skill = get_skill("workshop-question", client=client)

        industry = answers.get("industry", "professional-services")
        company_name = company_profile.get("basics", {}).get("name", {}).get("value", "your company")

        # Get data gaps and user notes if in followup stage
        current_stage = current_dd.get("conversation_stage", "current_state")
        data_gaps = []
        user_notes = None

        if current_stage == "followup":
            # Find the milestone for this pain point to get data gaps
            milestones = workshop_data.get("milestones", [])
            for milestone in milestones:
                if milestone.get("pain_point_id") == request.current_pain_point:
                    data_gaps = milestone.get("data_gaps", [])
                    user_notes = milestone.get("user_notes")
                    break

            # Track followup count for determining when to complete
            followup_count = current_dd.get("followup_count", 0) + 1
            current_dd["followup_count"] = followup_count

        skill_context = SkillContext(
            industry=normalize_industry(industry),
            metadata={
                "phase": "deepdive",
                "current_pain_point": request.current_pain_point,
                "pain_point_label": current_dd["pain_point_label"],
                "conversation_stage": current_stage,
                "signals": workshop_data.get("detected_signals", {}),
                "previous_messages": current_dd["transcript"][-10:],
                "company_name": company_name,
                "data_gaps": data_gaps,
                "user_notes": user_notes,
                "followup_count": current_dd.get("followup_count", 0),
            }
        )

        question_result = await question_skill.run(skill_context)

        if not question_result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response"
            )

        response_text = question_result.data["question"]
        next_stage = question_result.data["next_stage"]

        # Add assistant message to transcript
        current_dd["transcript"].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Update conversation stage
        current_dd["conversation_stage"] = next_stage

        # Check if we should show milestone
        should_show_milestone = next_stage == "complete"

        # Calculate confidence update — show current stage (what was just asked)
        message_count = len(current_dd["transcript"])
        confidence_update = {
            "current_pain_point": request.current_pain_point,
            "messages": message_count,
            "stage": current_stage,
            "estimated_completeness": min(100, (message_count / 10) * 100),
        }

        # Calculate remaining time
        total_pain_points = len(workshop_data.get("deep_dive_order", []))
        completed_dds = sum(1 for dd in deep_dives if dd.get("finding"))
        remaining = total_pain_points - completed_dds
        estimated_remaining = f"{remaining * 15}-{remaining * 20} min"

        # Save updated workshop data
        workshop_data["deep_dives"] = deep_dives
        await supabase.table("quiz_sessions").update({
            "workshop_data": workshop_data,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        # Generate quick-reply suggestions matching the question just asked
        suggestions = _get_stage_suggestions(current_stage, current_dd["pain_point_label"]) if not should_show_milestone else []

        return WorkshopRespondResponse(
            response=response_text,
            confidence_update=confidence_update,
            should_show_milestone=should_show_milestone,
            estimated_remaining=estimated_remaining,
            suggestions=suggestions,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workshop respond error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.post("/respond/stream")
async def workshop_respond_stream(request: WorkshopRespondRequest, raw_request: Request):
    """Stream the workshop AI response token by token via SSE."""
    from src.config.model_routing import get_model_for_task

    await endpoint_limiter.check(raw_request, "workshop_respond_stream", limit=10, window=60)

    # --- identical session setup as /respond ---
    supabase = await get_async_supabase()
    result = await supabase.table("quiz_sessions").select("*").eq(
        "id", request.session_id
    ).single().execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    session = result.data
    workshop_valid_statuses = [
        "paid", "workshop_started", "workshop_complete",
        "workshop_confirmation", "workshop_deepdive", "workshop",
    ]
    if session.get("status") not in workshop_valid_statuses:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session must be paid")

    workshop_data = session.get("workshop_data", {})
    answers = session.get("answers", {})
    company_profile = session.get("company_profile", {})
    deep_dives = workshop_data.get("deep_dives", [])

    current_dd = None
    for dd in deep_dives:
        if dd.get("pain_point_id") == request.current_pain_point:
            current_dd = dd
            break

    if not current_dd:
        current_dd = {
            "pain_point_id": request.current_pain_point,
            "pain_point_label": _get_pain_point_label(request.current_pain_point),
            "started_at": datetime.utcnow().isoformat(),
            "transcript": [],
            "conversation_stage": "current_state",
        }
        deep_dives.append(current_dd)

    current_dd["transcript"].append({
        "role": "user",
        "content": request.message,
        "timestamp": datetime.utcnow().isoformat(),
    })

    client = get_anthropic_client()
    question_skill = get_skill("workshop-question", client=client)
    industry = answers.get("industry", "professional-services")
    company_name = company_profile.get("basics", {}).get("name", {}).get("value", "your company")
    current_stage = current_dd.get("conversation_stage", "current_state")

    data_gaps: List[str] = []
    user_notes: Optional[str] = None
    if current_stage == "followup":
        for milestone in workshop_data.get("milestones", []):
            if milestone.get("pain_point_id") == request.current_pain_point:
                data_gaps = milestone.get("data_gaps", [])
                user_notes = milestone.get("user_notes")
                break
        followup_count = current_dd.get("followup_count", 0) + 1
        current_dd["followup_count"] = followup_count

    # Build prompt and system message using the skill's internal methods
    prompt_text = question_skill._build_prompt(
        pain_label=current_dd["pain_point_label"],
        stage=current_stage,
        signals=workshop_data.get("detected_signals", {}),
        previous=current_dd["transcript"][-10:],
        company_name=company_name,
        industry=normalize_industry(industry),
        data_gaps=data_gaps,
        user_notes=user_notes,
    )
    system_text = question_skill._get_system_prompt(
        signals=workshop_data.get("detected_signals", {}),
        company_name=company_name,
        industry=normalize_industry(industry),
    )

    # Determine next stage (same logic as skill)
    from src.skills.workshop.question_skill import CONVERSATION_STAGES, FOLLOWUP_STAGE
    if current_stage == FOLLOWUP_STAGE:
        fc = current_dd.get("followup_count", 0)
        next_stage = "complete" if fc >= 2 else FOLLOWUP_STAGE
    elif current_stage in CONVERSATION_STAGES:
        idx = CONVERSATION_STAGES.index(current_stage)
        next_stage = CONVERSATION_STAGES[idx + 1] if idx < len(CONVERSATION_STAGES) - 1 else "complete"
    else:
        next_stage = "complete"

    should_show_milestone = next_stage == "complete"
    message_count = len(current_dd["transcript"])
    confidence_update = {
        "current_pain_point": request.current_pain_point,
        "messages": message_count,
        "stage": current_stage,
        "estimated_completeness": min(100, (message_count / 10) * 100),
    }
    total_pain_points = len(workshop_data.get("deep_dive_order", []))
    completed_dds = sum(1 for dd2 in deep_dives if dd2.get("finding"))
    remaining = total_pain_points - completed_dds
    estimated_remaining = f"{remaining * 15}-{remaining * 20} min"
    suggestions = _get_stage_suggestions(current_stage, current_dd["pain_point_label"]) if not should_show_milestone else []

    async def event_generator() -> AsyncGenerator[str, None]:
        accumulated = ""
        try:
            with client.messages.stream(
                model=get_model_for_task("classify_finding"),
                max_tokens=500,
                system=system_text,
                messages=[{"role": "user", "content": prompt_text}],
            ) as stream:
                for text in stream.text_stream:
                    accumulated += text
                    yield f"data: {json.dumps({'type': 'token', 'content': text})}\n\n"
        except Exception as e:
            logger.error("streaming_error", error=str(e))
            if not accumulated:
                accumulated = "Thank you for sharing that. Can you tell me more?"
                yield f"data: {json.dumps({'type': 'token', 'content': accumulated})}\n\n"

        # Clean up response
        response_text = accumulated.strip().strip('"').strip("'")

        # Save to transcript
        current_dd["transcript"].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.utcnow().isoformat(),
        })
        current_dd["conversation_stage"] = next_stage
        workshop_data["deep_dives"] = deep_dives

        await supabase.table("quiz_sessions").update({
            "workshop_data": workshop_data,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        # Send completion metadata
        yield f"data: {json.dumps({'type': 'complete', 'suggestions': suggestions, 'confidence_update': confidence_update, 'should_show_milestone': should_show_milestone, 'estimated_remaining': estimated_remaining})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/milestone")
async def generate_milestone(request: MilestoneRequest):
    """
    Generate milestone summary after deep-dive.
    """
    try:
        supabase = await get_async_supabase()

        # Get session
        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", request.session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data

        # Verify session has been paid for
        workshop_valid_statuses = [
            "paid", "workshop_started", "workshop_complete",
            "workshop_confirmation", "workshop_deepdive", "workshop",
        ]
        if session.get("status") not in workshop_valid_statuses:
            logger.warning(
                f"Workshop milestone called with invalid session status={session.get('status')} "
                f"for session_id={request.session_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session must be paid before accessing workshop"
            )

        workshop_data = session.get("workshop_data", {})
        answers = session.get("answers", {})
        company_profile = session.get("company_profile", {})

        # Find the deep-dive
        deep_dives = workshop_data.get("deep_dives", [])
        current_dd = None
        for dd in deep_dives:
            if dd.get("pain_point_id") == request.pain_point_id:
                current_dd = dd
                break

        if not current_dd:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deep-dive not found"
            )

        # Generate milestone using skill
        client = get_anthropic_client()
        milestone_skill = get_skill("milestone-synthesis", client=client)

        industry = answers.get("industry", "professional-services")
        company_name = company_profile.get("basics", {}).get("name", {}).get("value", "the company")

        # Extract tools mentioned in conversation
        tools_mentioned = []
        for msg in current_dd.get("transcript", []):
            content = msg.get("content", "").lower()
            for tool in ["hubspot", "salesforce", "slack", "excel", "google", "zapier", "notion", "asana", "monday"]:
                if tool in content and tool.capitalize() not in tools_mentioned:
                    tools_mentioned.append(tool.capitalize())

        skill_context = SkillContext(
            industry=normalize_industry(industry),
            metadata={
                "pain_point_id": request.pain_point_id,
                "pain_point_label": current_dd.get("pain_point_label", "This challenge"),
                "transcript": current_dd.get("transcript", []),
                "company_name": company_name,
                "tools_mentioned": tools_mentioned,
            }
        )

        milestone_result = await milestone_skill.run(skill_context)

        if not milestone_result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate milestone"
            )

        milestone_data = milestone_result.data

        # Save milestone
        milestones = workshop_data.get("milestones", [])
        milestones.append({
            "pain_point_id": request.pain_point_id,
            "finding": milestone_data.get("finding", {}),
            "roi": milestone_data.get("roi", {}),
            "vendors": milestone_data.get("vendors", []),
            "confidence": milestone_data.get("confidence", 0),
            "shown_at": datetime.utcnow().isoformat(),
        })

        # Mark deep-dive as having a finding
        current_dd["finding"] = milestone_data.get("finding", {})
        current_dd["completed_at"] = datetime.utcnow().isoformat()

        workshop_data["milestones"] = milestones
        workshop_data["deep_dives"] = deep_dives

        await supabase.table("quiz_sessions").update({
            "workshop_data": workshop_data,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        return milestone_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate milestone error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate milestone"
        )


@router.post("/milestone/feedback")
async def save_milestone_feedback(request: MilestoneFeedbackRequest, raw_request: Request):
    """
    Save user feedback on a milestone.

    If feedback is "needs_edit", enables re-entry to the conversation
    with targeted follow-up questions based on data gaps.
    """
    # Rate limit: 10 requests per minute (may trigger LLM for follow-up generation)
    await endpoint_limiter.check(raw_request, "workshop_milestone_feedback", limit=10, window=60)

    try:
        supabase = await get_async_supabase()

        result = await supabase.table("quiz_sessions").select(
            "workshop_data, answers, status"
        ).eq("id", request.session_id).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Verify session has been paid for
        workshop_valid_statuses = [
            "paid", "workshop_started", "workshop_complete",
            "workshop_confirmation", "workshop_deepdive", "workshop",
        ]
        if result.data.get("status") not in workshop_valid_statuses:
            logger.warning(
                f"Workshop milestone feedback called with invalid session status={result.data.get('status')} "
                f"for session_id={request.session_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session must be paid before accessing workshop"
            )

        workshop_data = result.data.get("workshop_data", {})
        answers = result.data.get("answers", {})
        milestones = workshop_data.get("milestones", [])
        deep_dives = workshop_data.get("deep_dives", [])

        # Find the milestone and deep-dive
        target_milestone = None
        target_dd = None
        for milestone in milestones:
            if milestone.get("pain_point_id") == request.pain_point_id:
                milestone["user_feedback"] = request.feedback
                milestone["user_notes"] = request.notes
                target_milestone = milestone
                break

        for dd in deep_dives:
            if dd.get("pain_point_id") == request.pain_point_id:
                target_dd = dd
                break

        workshop_data["milestones"] = milestones

        # If user wants to edit, enable re-entry
        followup_questions = []
        can_continue = False

        if request.feedback == "needs_edit" and target_milestone:
            can_continue = True

            # Generate follow-up questions based on data gaps and user notes
            followup_questions = _generate_followup_questions(
                milestone=target_milestone,
                user_notes=request.notes,
                deep_dive=target_dd,
            )

            # Reset the deep-dive stage for continuation
            if target_dd:
                target_dd["conversation_stage"] = "followup"
                target_dd["completed_at"] = None  # Mark as not completed
                # Add a system note about re-entry
                target_dd["transcript"].append({
                    "role": "system",
                    "content": f"User requested adjustments: {request.notes or 'No specific notes'}",
                    "timestamp": datetime.utcnow().isoformat(),
                })

            workshop_data["deep_dives"] = deep_dives

        await supabase.table("quiz_sessions").update({
            "workshop_data": workshop_data,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        return {
            "success": True,
            "can_continue": can_continue,
            "followup_questions": followup_questions,
            "pain_point_id": request.pain_point_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save milestone feedback error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save feedback"
        )


@router.get("/preview/{session_id}")
async def get_report_preview(session_id: str):
    """Build a preview of what the report will contain based on workshop data."""
    try:
        supabase = await get_async_supabase()
        result = await supabase.table("quiz_sessions").select(
            "workshop_data, workshop_confidence, company_profile"
        ).eq("id", session_id).single().execute()

        if not result.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        session = result.data
        workshop_data = session.get("workshop_data", {})
        milestones = workshop_data.get("milestones", [])
        confidence = session.get("workshop_confidence", {})
        company_profile = session.get("company_profile", {})

        company_name = company_profile.get("basics", {}).get("name", {}).get("value", "Your Company")

        # Calculate combined savings
        total_savings = sum(
            m.get("roi", {}).get("potential_savings", 0)
            for m in milestones
        )

        # Build findings summary
        findings = []
        max_savings = max(
            (m.get("roi", {}).get("potential_savings", 0) for m in milestones),
            default=0,
        )
        for m in milestones:
            finding = m.get("finding", {})
            roi = m.get("roi", {})

            # Classify badge
            badge = "strategic"
            hours = roi.get("hours_per_week", 0)
            savings_pct = roi.get("savings_percentage", 0)
            savings = roi.get("potential_savings", 0)
            if hours < 5 and savings_pct > 70:
                badge = "quick_win"
            elif savings == max_savings and max_savings > 0:
                badge = "high_roi"

            findings.append({
                "title": finding.get("title", "Untitled"),
                "savings": savings,
                "badge": badge,
                "severity": finding.get("pain_severity", "medium"),
                "vendors": m.get("vendors", [])[:2],
            })

        # Report sections with confidence
        overall_conf = confidence.get("overall", 60) if isinstance(confidence, dict) else 60
        topics = confidence.get("topics", {}) if isinstance(confidence, dict) else {}
        sections = [
            {"name": "Executive Summary", "confidence": min(overall_conf, 95)},
            {"name": "Current State Analysis", "confidence": topics.get("current_challenges", {}).get("coverage", 60)},
            {"name": "AI Opportunities", "confidence": topics.get("business_goals", {}).get("coverage", 60), "finding_count": len(findings)},
            {"name": "Vendor Recommendations", "confidence": topics.get("technology", {}).get("coverage", 50)},
            {"name": "Implementation Roadmap", "confidence": topics.get("budget_timeline", {}).get("coverage", 50)},
            {"name": "ROI Projections", "confidence": overall_conf},
        ]

        return {
            "company_name": company_name,
            "total_savings": total_savings,
            "findings": findings,
            "sections": sections,
            "duration_minutes": workshop_data.get("duration_minutes"),
            "pain_points_analyzed": len(milestones),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_report_preview_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build report preview"
        )


@router.get("/deepdive/{session_id}/{pain_point_index}")
async def get_deepdive_state(session_id: str, pain_point_index: int):
    """Return existing conversation state for a deep-dive if it exists."""
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("quiz_sessions").select(
            "workshop_data"
        ).eq("id", session_id).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        workshop_data = result.data.get("workshop_data", {})
        deep_dives = workshop_data.get("deep_dives", [])

        for dd in deep_dives:
            if dd.get("pain_point_index") == pain_point_index:
                return {
                    "exists": True,
                    "transcript": dd.get("transcript", []),
                    "conversation_stage": dd.get("conversation_stage", "current_state"),
                    "confidence": dd.get("confidence"),
                }
        return {"exists": False}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_deepdive_state_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get deep-dive state"
        )


@router.get("/state/{session_id}")
async def get_workshop_state(session_id: str):
    """
    Get current workshop state for session recovery.
    """
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("quiz_sessions").select(
            "workshop_phase, workshop_data, workshop_confidence, company_profile, answers, status"
        ).eq("id", session_id).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Verify session has been paid for
        workshop_valid_statuses = [
            "paid", "workshop_started", "workshop_complete",
            "workshop_confirmation", "workshop_deepdive", "workshop",
        ]
        if result.data.get("status") not in workshop_valid_statuses:
            logger.warning(
                f"Workshop state called with invalid session status={result.data.get('status')} "
                f"for session_id={session_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session must be paid before accessing workshop"
            )

        session = result.data
        workshop_data = session.get("workshop_data", {})
        company_profile = session.get("company_profile", {})

        company_name = company_profile.get("basics", {}).get("name", {}).get("value", "Your Company")

        return {
            "session_id": session_id,
            "company_name": company_name,
            "phase": session.get("workshop_phase", "confirmation"),
            "workshop_data": workshop_data,
            "confidence": session.get("workshop_confidence", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get workshop state error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workshop state"
        )


@router.post("/complete")
async def complete_workshop(request: WorkshopCompleteRequest):
    """
    Complete the workshop and trigger report generation.

    Enforces confidence gate - workshop must have sufficient data quality.
    """
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", request.session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data

        # Verify session has been paid for
        workshop_valid_statuses = [
            "paid", "workshop_started", "workshop_complete",
            "workshop_confirmation", "workshop_deepdive", "workshop",
        ]
        if session.get("status") not in workshop_valid_statuses:
            logger.warning(
                f"Workshop complete called with invalid session status={session.get('status')} "
                f"for session_id={request.session_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session must be paid before accessing workshop"
            )

        workshop_data = session.get("workshop_data") or {}

        # Enforce confidence gate
        confidence = _build_workshop_confidence(workshop_data)
        if not confidence.is_ready_for_report():
            gaps = _identify_data_gaps(workshop_data, confidence)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INSUFFICIENT_DATA",
                    "message": "Workshop needs more information before generating report",
                    "gaps": gaps,
                    "confidence_level": confidence.level,
                    "confidence_score": confidence.overall_score,
                }
            )

        # Calculate duration
        started_at = workshop_data.get("started_at")
        if started_at:
            try:
                start_time = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                duration = int((datetime.utcnow() - start_time.replace(tzinfo=None)).total_seconds() / 60)
            except Exception:
                duration = 0
        else:
            duration = 0

        # Update workshop data
        workshop_data["phase"] = "complete"
        workshop_data["final_answers"] = request.final_answers
        workshop_data["completed_at"] = datetime.utcnow().isoformat()
        workshop_data["duration_minutes"] = duration

        # Calculate total savings
        total_savings = sum(
            m.get("roi", {}).get("potential_savings", 0)
            for m in workshop_data.get("milestones", [])
        )

        # Update session
        await supabase.table("quiz_sessions").update({
            "workshop_phase": "complete",
            "workshop_data": workshop_data,
            "workshop_completed_at": datetime.utcnow().isoformat(),
            "status": "generating",
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        logger.info(f"Workshop completed for session {request.session_id} in {duration} minutes")

        return {
            "success": True,
            "session_id": request.session_id,
            "summary": {
                "duration_minutes": duration,
                "pain_points_analyzed": len(workshop_data.get("deep_dives", [])),
                "total_savings": total_savings,
                "milestones_generated": len(workshop_data.get("milestones", [])),
            },
            "next_step": f"/api/reports/stream/{request.session_id}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete workshop error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete workshop"
        )


# =============================================================================
# Helper Functions
# =============================================================================

def _build_confirmation_cards(
    company_profile: Dict[str, Any],
    answers: Dict[str, Any],
) -> List[ConfirmationCard]:
    """Build confirmation cards from quiz and research data."""
    cards = []

    # Business card
    basics = company_profile.get("basics", {})
    industry_data = company_profile.get("industry", {})
    size_data = company_profile.get("size", {})

    business_items = []
    if basics.get("name", {}).get("value"):
        business_items.append(basics["name"]["value"])
    if industry_data.get("primary_industry", {}).get("value"):
        business_items.append(f"Industry: {industry_data['primary_industry']['value']}")
    if size_data.get("employee_range", {}).get("value"):
        business_items.append(f"Team size: {size_data['employee_range']['value']}")
    if basics.get("description", {}).get("value"):
        desc = basics["description"]["value"][:100]
        business_items.append(desc)

    if business_items:
        cards.append(ConfirmationCard(
            category="business",
            title="Your Business",
            items=business_items,
            source_count=len([i for i in business_items if i]),
        ))

    # Pain points card
    pain_points = answers.get("pain_points", [])
    if isinstance(pain_points, list) and pain_points:
        cards.append(ConfirmationCard(
            category="pain_points",
            title="Pain Points You Mentioned",
            items=pain_points[:5],
            source_count=len(pain_points),
        ))

    # Tools card
    tools = answers.get("current_tools", [])
    tech = company_profile.get("technology", {})
    if isinstance(tools, list):
        all_tools = tools.copy()
    else:
        all_tools = []

    if tech.get("tools_detected", {}).get("value"):
        detected = tech["tools_detected"]["value"]
        if isinstance(detected, list):
            all_tools.extend([t for t in detected if t not in all_tools])

    if all_tools:
        cards.append(ConfirmationCard(
            category="tools",
            title="Your Current Tools",
            items=all_tools[:8],
            source_count=len(all_tools),
        ))

    # Goals card
    goals = []
    if answers.get("main_goal"):
        goals.append(answers["main_goal"])
    if answers.get("success_metrics"):
        if isinstance(answers["success_metrics"], list):
            goals.extend(answers["success_metrics"])
        else:
            goals.append(answers["success_metrics"])

    if goals:
        cards.append(ConfirmationCard(
            category="goals",
            title="What Success Looks Like",
            items=goals[:4],
            source_count=len(goals),
        ))

    return cards


def _extract_pain_points(
    answers: Dict[str, Any],
    company_profile: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Extract pain points as structured list."""
    pain_points = []

    raw_pains = answers.get("pain_points", [])
    if isinstance(raw_pains, list):
        for i, pain in enumerate(raw_pains[:5]):
            pain_points.append({
                "id": f"pain_{i}",
                "label": pain if isinstance(pain, str) else str(pain),
                "source": "quiz",
            })

    return pain_points


def _get_pain_point_label(pain_point_id: str) -> str:
    """Get human-readable label for pain point ID."""
    # Map common IDs to labels
    labels = {
        "reporting": "Client Reporting",
        "lead_followup": "Lead Follow-up",
        "proposals": "Proposal Generation",
        "scheduling": "Scheduling & Coordination",
        "data_entry": "Data Entry",
        "customer_support": "Customer Support",
        "invoicing": "Invoicing & Billing",
        "onboarding": "Client Onboarding",
    }

    # Handle pain_X format
    if pain_point_id.startswith("pain_"):
        return pain_point_id.replace("pain_", "Pain Point ").replace("_", " ").title()

    return labels.get(pain_point_id, pain_point_id.replace("_", " ").title())


def _generate_followup_questions(
    milestone: Dict[str, Any],
    user_notes: Optional[str],
    deep_dive: Optional[Dict[str, Any]],
) -> List[str]:
    """
    Generate targeted follow-up questions based on data gaps and user feedback.

    These questions help gather missing information to improve the finding accuracy.
    """
    questions = []

    # Get data gaps from milestone
    data_gaps = milestone.get("data_gaps", [])
    roi = milestone.get("roi", {})
    finding = milestone.get("finding", {})

    # If user provided specific notes, prioritize addressing those
    if user_notes:
        notes_lower = user_notes.lower()

        if any(word in notes_lower for word in ["number", "amount", "cost", "hour", "time"]):
            questions.append(
                "Can you give me more specific numbers? For example, how many hours "
                "per week does this task take, or what's the approximate cost involved?"
            )

        if any(word in notes_lower for word in ["wrong", "incorrect", "not right", "different"]):
            questions.append(
                "I'd like to make sure I understand correctly. Can you walk me through "
                "exactly how this process works in your business?"
            )

        if any(word in notes_lower for word in ["miss", "forgot", "also", "more"]):
            questions.append(
                "What else should I know about this challenge that we haven't covered yet?"
            )

    # Address data gaps from milestone synthesis
    for gap in data_gaps[:2]:  # Limit to top 2 gaps
        gap_lower = gap.lower()

        if "hour" in gap_lower or "time" in gap_lower:
            questions.append(
                "How much time does your team spend on this each week? "
                "Even a rough estimate helps."
            )
        elif "cost" in gap_lower or "budget" in gap_lower:
            questions.append(
                "Do you have a sense of what this is costing you currently? "
                "This could be in direct costs or lost productivity."
            )
        elif "stakeholder" in gap_lower or "team" in gap_lower:
            questions.append(
                "Who else on your team is affected by this issue? "
                "Are there other stakeholders we should consider?"
            )
        elif "tool" in gap_lower or "software" in gap_lower:
            questions.append(
                "What tools or systems are you currently using for this? "
                "And are there any you've tried that didn't work?"
            )
        else:
            # Generic gap question
            questions.append(f"Could you tell me more about: {gap}?")

    # If ROI data is weak, ask for specifics
    if roi.get("hours_per_week", 0) == 0 or roi.get("confidence", 1.0) < 0.5:
        if not any("time" in q.lower() or "hour" in q.lower() for q in questions):
            questions.append(
                "To calculate potential savings accurately, I need to understand: "
                "roughly how many hours per week does your team spend on this?"
            )

    # If pain severity is unclear
    if finding.get("pain_severity") == "low" and not questions:
        questions.append(
            "This seems like it might not be a major pain point. "
            "Is this actually causing significant problems, or is it more of a minor annoyance?"
        )

    # Fallback generic questions if no specific ones generated
    if not questions:
        questions = [
            "What specifically would you like me to adjust about this finding?",
            "Is there anything about your current process I misunderstood?",
        ]

    # Limit to 3 questions max
    return questions[:3]


def _build_workshop_confidence(workshop_data: Dict[str, Any]) -> WorkshopConfidence:
    """
    Build WorkshopConfidence from workshop data.

    Calculates confidence based on:
    - Number of deep-dives completed
    - Milestones generated
    - Data quality from conversations
    """
    confidence = WorkshopConfidence()

    milestones = workshop_data.get("milestones", [])
    deep_dives = workshop_data.get("deep_dives", [])

    # Count pain points with sufficient data
    pain_points_extracted = len([
        dd for dd in deep_dives
        if dd.get("finding") or len(dd.get("transcript", [])) >= 4
    ])

    # Count quantifiable impacts from milestones
    quantifiable_impacts = len([
        m for m in milestones
        if m.get("roi", {}).get("potential_savings", 0) > 0
    ])

    # Set quality indicators
    confidence.quality_indicators = {
        "pain_points_extracted": pain_points_extracted,
        "quantifiable_impacts": quantifiable_impacts,
        "milestones_generated": len(milestones),
        "deep_dives_completed": len([dd for dd in deep_dives if dd.get("completed_at")]),
    }

    # Build topic confidence from deep-dive coverage
    # Map deep-dives to topic areas
    if deep_dives:
        # Current challenges topic
        challenges_score = min(100, len(deep_dives) * 25)
        confidence.topics["current_challenges"] = {"coverage": challenges_score}

        # Business goals (from milestones with ROI)
        goals_score = min(100, quantifiable_impacts * 30)
        confidence.topics["business_goals"] = {"coverage": goals_score}

        # Team operations (from transcript length)
        total_messages = sum(len(dd.get("transcript", [])) for dd in deep_dives)
        ops_score = min(100, total_messages * 5)
        confidence.topics["team_operations"] = {"coverage": ops_score}

        # Technology (from tools mentioned)
        tools_mentioned = set()
        for dd in deep_dives:
            for msg in dd.get("transcript", []):
                content = msg.get("content", "").lower()
                for tool in ["hubspot", "salesforce", "slack", "excel", "zapier", "notion"]:
                    if tool in content:
                        tools_mentioned.add(tool)
        tech_score = min(100, len(tools_mentioned) * 20)
        confidence.topics["technology"] = {"coverage": tech_score}

        # Budget/timeline (from final answers or milestone feedback)
        budget_score = 40 if workshop_data.get("final_answers") else 0
        confidence.topics["budget_timeline"] = {"coverage": budget_score}

    # Calculate depth dimensions
    confidence.depth_dimensions = DepthDimensions(
        integration_depth=0.5 if len(milestones) >= 2 else 0.2,
        cost_quantification=0.8 if quantifiable_impacts >= 2 else 0.3,
        stakeholder_mapping=0.5 if (workshop_data.get("final_answers") or {}).get("stakeholders") else 0.1,
        implementation_readiness=0.4 if len(milestones) >= 1 else 0.0,
    )

    # Recalculate overall score
    confidence.calculate_overall()

    return confidence


def _identify_data_gaps(
    workshop_data: Dict[str, Any],
    confidence: WorkshopConfidence,
) -> List[str]:
    """
    Identify specific data gaps that need to be addressed.

    Returns actionable messages for the user.
    """
    gaps = []

    milestones = workshop_data.get("milestones", [])
    deep_dives = workshop_data.get("deep_dives", [])

    # Check minimum requirements
    if not deep_dives:
        gaps.append("No pain points have been discussed yet")
    elif len([dd for dd in deep_dives if dd.get("finding")]) == 0:
        gaps.append("Complete at least one pain point discussion to generate a finding")

    if not milestones:
        gaps.append("No milestone summaries have been generated")

    # Check for specific topic gaps
    challenges_conf = confidence.calculate_topic_confidence("current_challenges")
    if challenges_conf < 0.5:
        gaps.append("Need more detail about current challenges and pain points")

    goals_conf = confidence.calculate_topic_confidence("business_goals")
    if goals_conf < 0.4:
        gaps.append("Need to understand business goals and success metrics")

    # Check for quantifiable data
    has_numbers = any(
        m.get("roi", {}).get("hours_per_week", 0) > 0
        for m in milestones
    )
    if not has_numbers and milestones:
        gaps.append("Need specific numbers (hours spent, costs) for ROI calculation")

    # Check milestone feedback
    needs_edit_count = sum(
        1 for m in milestones
        if m.get("user_feedback") == "needs_edit"
    )
    if needs_edit_count > 0:
        gaps.append(f"{needs_edit_count} finding(s) marked as needing adjustments")

    # Collect data gaps from milestones
    for milestone in milestones:
        milestone_gaps = milestone.get("data_gaps", [])
        for gap in milestone_gaps[:2]:  # Limit per milestone
            if gap and gap not in gaps:
                gaps.append(gap)

    return gaps[:5]  # Return top 5 gaps
