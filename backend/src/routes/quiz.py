"""
Quiz Routes

Public routes for quiz sessions with save/resume functionality.
No authentication required - uses email for session lookup.

Includes research integration for dynamic question customization.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr

from src.config.supabase_client import get_async_supabase
from src.config.questionnaire import (
    get_questionnaire,
    get_total_questions,
    get_section_count,
)
from src.agents.pre_research_agent import PreResearchAgent, start_company_research
from src.models.research import StartResearchRequest, DynamicQuestionnaire
from src.services.teaser_service import generate_teaser_report
from src.services.email import send_teaser_report_email
from src.services.brevo_service import (
    get_brevo_service,
    QuizCompleterContact,
)
from src.models.quiz_confidence import (
    ConfidenceState,
    ConfidenceCategory,
    AdaptiveQuestion,
    create_initial_confidence_from_research,
    update_confidence_from_analysis,
    CONFIDENCE_THRESHOLDS,
)
from src.services.quiz_engine import (
    AnswerAnalyzer,
    QuestionGenerator,
    IndustryQuestionBank,
    get_available_industries,
)
from src.models.research import CompanyProfile
from src.services.software_research_service import (
    research_session_stack,
    software_research_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create a new quiz session."""
    email: EmailStr
    tier: str = "quick"  # 'quick' or 'full'
    industry: Optional[str] = None


class CreateSessionResponse(BaseModel):
    """Response after creating a quiz session."""
    session_id: str
    email: str
    tier: str
    status: str
    created_at: str


class ExistingStackItem(BaseModel):
    """A software tool in the user's existing stack."""
    slug: str  # Vendor slug or custom identifier
    source: str  # "selected" or "free_text"
    name: Optional[str] = None  # Display name (required for free_text)


class QuizProgressUpdate(BaseModel):
    """Partial progress update for a quiz session."""
    current_section: Optional[int] = None
    current_question: Optional[int] = None
    answers: Optional[Dict[str, Any]] = None
    email: Optional[EmailStr] = None  # For capturing real email after quiz preview
    industry: Optional[str] = None  # For market data collection
    existing_stack: Optional[List[ExistingStackItem]] = None  # User's current software


class QuizProgressResponse(BaseModel):
    """Response with quiz progress info."""
    success: bool
    session_id: str
    completion_percent: int
    current_section: int
    current_question: int
    answers_count: int


class SessionResponse(BaseModel):
    """Full session data response."""
    id: str
    email: str
    tier: str
    status: str
    current_section: int
    current_question: int
    answers: Dict[str, Any]
    completion_percent: int
    created_at: str
    updated_at: str
    existing_stack: Optional[List[Dict[str, Any]]] = None


class ResumeResponse(BaseModel):
    """Response for resume lookup."""
    has_progress: bool
    session: Optional[SessionResponse] = None


class QuestionnaireResponse(BaseModel):
    """Questionnaire structure response."""
    sections: List[Dict[str, Any]]
    total_questions: int
    total_sections: int


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_completion(
    answers: Dict[str, Any],
    total_questions: int,
    tier: str = "quick"
) -> int:
    """Calculate completion percentage based on answered questions."""
    if total_questions == 0:
        return 0

    answered = len([k for k, v in answers.items() if v is not None and v != ""])
    return min(100, int((answered / total_questions) * 100))


# ============================================================================
# Routes
# ============================================================================

@router.post("/sessions", response_model=CreateSessionResponse)
async def create_quiz_session(request: CreateSessionRequest):
    """
    Create a new quiz session.

    Creates a session that can be saved incrementally and resumed later.
    """
    try:
        supabase = await get_async_supabase()

        # Check if there's already an in-progress session for this email
        existing = await supabase.table("quiz_sessions").select("id, status").eq(
            "email", request.email
        ).eq("status", "in_progress").order(
            "created_at", desc=True
        ).limit(1).execute()

        if existing.data:
            # Return existing session ID
            logger.info(f"Returning existing session for {request.email}")
            session = existing.data[0]
            full_session = await supabase.table("quiz_sessions").select("*").eq(
                "id", session["id"]
            ).single().execute()

            return CreateSessionResponse(
                session_id=session["id"],
                email=request.email,
                tier=full_session.data.get("tier", request.tier),
                status="in_progress",
                created_at=full_session.data.get("created_at", datetime.utcnow().isoformat()),
            )

        # Create new session
        session_data = {
            "email": request.email,
            "tier": request.tier,
            "status": "in_progress",
            "current_section": 0,
            "current_question": 0,
            "answers": {},
            "results": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        if request.industry:
            session_data["answers"]["industry"] = request.industry

        result = await supabase.table("quiz_sessions").insert(session_data).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session"
            )

        session = result.data[0]
        logger.info(f"Created quiz session {session['id']} for {request.email}")

        return CreateSessionResponse(
            session_id=session["id"],
            email=session["email"],
            tier=session["tier"],
            status=session["status"],
            created_at=session["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create quiz session"
        )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_quiz_session(session_id: str):
    """
    Get a quiz session with current progress.
    """
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data
        answers = session.get("answers", {})
        industry = answers.get("industry")
        total_questions = get_total_questions(industry)

        return SessionResponse(
            id=session["id"],
            email=session["email"],
            tier=session["tier"],
            status=session["status"],
            current_section=session.get("current_section", 0),
            current_question=session.get("current_question", 0),
            answers=answers,
            completion_percent=calculate_completion(answers, total_questions, session["tier"]),
            created_at=session["created_at"],
            updated_at=session.get("updated_at", session["created_at"]),
            existing_stack=session.get("existing_stack"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get quiz session"
        )


@router.patch("/sessions/{session_id}", response_model=QuizProgressResponse)
async def save_quiz_progress(session_id: str, progress: QuizProgressUpdate):
    """
    Save partial quiz progress.

    Called on every answer to enable resume functionality.
    Merges new answers with existing ones.
    """
    try:
        supabase = await get_async_supabase()

        # Get existing session
        existing = await supabase.table("quiz_sessions").select("*").eq(
            "id", session_id
        ).single().execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = existing.data

        # Can only update in_progress sessions
        if session["status"] not in ["in_progress", "pending_payment"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update session with status: {session['status']}"
            )

        # Merge answers
        existing_answers = session.get("answers", {})
        if progress.answers:
            existing_answers.update(progress.answers)

        # Build update data
        update_data = {
            "answers": existing_answers,
            "updated_at": datetime.utcnow().isoformat(),
        }

        if progress.current_section is not None:
            update_data["current_section"] = progress.current_section

        if progress.current_question is not None:
            update_data["current_question"] = progress.current_question

        # Update email if provided (for lead capture after quiz preview)
        if progress.email is not None:
            update_data["email"] = progress.email
            logger.info(f"Captured email for session {session_id}: {progress.email}")

        # Update industry if provided (for market data)
        if progress.industry is not None:
            # Store in answers under special key for tracking
            existing_answers["_detected_industry"] = progress.industry
            update_data["answers"] = existing_answers

        # Update existing_stack if provided (for Connect vs Replace)
        if progress.existing_stack is not None:
            update_data["existing_stack"] = [
                item.model_dump() for item in progress.existing_stack
            ]
            logger.info(f"Updated existing_stack for session {session_id}: {len(progress.existing_stack)} tools")

        # Update session
        result = await supabase.table("quiz_sessions").update(
            update_data
        ).eq("id", session_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save progress"
            )

        updated = result.data[0]
        industry = existing_answers.get("industry")
        total_questions = get_total_questions(industry)

        logger.info(f"Progress saved for session {session_id}: {len(existing_answers)} answers")

        return QuizProgressResponse(
            success=True,
            session_id=session_id,
            completion_percent=calculate_completion(existing_answers, total_questions),
            current_section=updated.get("current_section", 0),
            current_question=updated.get("current_question", 0),
            answers_count=len(existing_answers),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save progress error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save quiz progress"
        )


@router.post("/sessions/{session_id}/complete")
async def complete_quiz_session(session_id: str):
    """
    Mark a quiz session as complete.

    Validates that required questions are answered, then marks
    the session as ready for checkout.
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

        if session["status"] not in ["in_progress"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session already in status: {session['status']}"
            )

        answers = session.get("answers", {})
        industry = answers.get("industry")

        # Validate required questions
        sections = get_questionnaire(industry)
        missing_required = []

        for section in sections:
            for question in section.get("questions", []):
                q_id = question["id"]
                if question.get("required", False):
                    value = answers.get(q_id)
                    if value is None or value == "" or (isinstance(value, list) and len(value) == 0):
                        missing_required.append(q_id)

        if missing_required:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Missing required answers",
                    "missing": missing_required[:10],  # Return first 10
                    "total_missing": len(missing_required),
                }
            )

        # Calculate preliminary results
        results = _calculate_preliminary_results(answers, industry)

        # Research unknown software in existing_stack (Phase 2B)
        existing_stack = session.get("existing_stack", [])
        researched_stack = None
        if existing_stack:
            # Check if any items are free_text (unknown software)
            has_free_text = any(
                item.get("source") == "free_text" for item in existing_stack
            )
            if has_free_text:
                logger.info(
                    f"Researching unknown software for session {session_id}"
                )
                try:
                    researched_items = await research_session_stack(
                        existing_stack, cache_results=True
                    )
                    # Convert to dicts for storage
                    researched_stack = [
                        item.model_dump() for item in researched_items
                    ]
                    logger.info(
                        f"Research complete for {len(researched_items)} stack items"
                    )
                except Exception as e:
                    logger.error(f"Stack research failed: {e}")
                    # Continue without research - don't block completion

        # Build update data
        update_data = {
            "status": "pending_payment",
            "results": results,
            "completed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        if researched_stack:
            update_data["existing_stack"] = researched_stack

        # Update session
        await supabase.table("quiz_sessions").update(
            update_data
        ).eq("id", session_id).execute()

        logger.info(f"Quiz session {session_id} marked complete, ready for payment")

        return {
            "success": True,
            "session_id": session_id,
            "status": "pending_payment",
            "results": results,
            "existing_stack_researched": researched_stack is not None,
            "message": "Quiz complete. Proceed to checkout.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete quiz session"
        )


@router.get("/sessions/resume", response_model=ResumeResponse)
async def resume_quiz_session(email: str = Query(..., description="Email to look up")):
    """
    Find an in-progress quiz session for an email.

    Allows users to resume where they left off.
    """
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("quiz_sessions").select("*").eq(
            "email", email
        ).in_("status", ["in_progress", "pending_payment"]).order(
            "updated_at", desc=True
        ).limit(1).execute()

        if not result.data:
            return ResumeResponse(has_progress=False)

        session = result.data[0]
        answers = session.get("answers", {})
        industry = answers.get("industry")
        total_questions = get_total_questions(industry)

        return ResumeResponse(
            has_progress=True,
            session=SessionResponse(
                id=session["id"],
                email=session["email"],
                tier=session["tier"],
                status=session["status"],
                current_section=session.get("current_section", 0),
                current_question=session.get("current_question", 0),
                answers=answers,
                completion_percent=calculate_completion(answers, total_questions),
                created_at=session["created_at"],
                updated_at=session.get("updated_at", session["created_at"]),
                existing_stack=session.get("existing_stack"),
            )
        )

    except Exception as e:
        logger.error(f"Resume lookup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to look up session"
        )


@router.get("/questions/{industry}", response_model=QuestionnaireResponse)
async def get_industry_questions(industry: str):
    """
    Get industry-specific questionnaire.

    Returns the questionnaire structure with questions tailored
    to the specified industry.
    """
    try:
        sections = get_questionnaire(industry)

        return QuestionnaireResponse(
            sections=sections,
            total_questions=get_total_questions(industry),
            total_sections=get_section_count(industry),
        )

    except Exception as e:
        logger.error(f"Get questions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get questionnaire"
        )


@router.get("/software-options")
async def get_software_options(industry: Optional[str] = Query(None, description="Industry slug")):
    """
    Get software options for the existing stack question.

    Returns industry-specific software plus cross-industry tools,
    grouped by category for easy UI display.
    """
    from src.config.existing_stack import (
        get_software_options_grouped,
        get_all_categories,
    )

    grouped = get_software_options_grouped(industry)
    categories = get_all_categories(industry)

    return {
        "industry": industry,
        "categories": categories,
        "options_by_category": grouped,
        "total_options": sum(len(opts) for opts in grouped.values()),
    }


class ResearchSoftwareRequest(BaseModel):
    """Request to research unknown software."""
    name: str
    context: Optional[str] = None  # e.g., industry, software type


@router.post("/research-software")
async def research_software(request: ResearchSoftwareRequest):
    """
    Research unknown software API capabilities.

    Use this to research software not in our vendor database.
    Returns estimated API openness score (1-5) and integration details.
    """
    try:
        result = await software_research_service.research_unknown_software(
            name=request.name,
            context=request.context,
            check_cache=True,
        )

        if not result.found:
            return {
                "success": False,
                "name": result.name,
                "error": result.error,
            }

        capabilities = result.capabilities
        return {
            "success": True,
            "name": result.name,
            "cached": result.cached,
            "capabilities": {
                "api_score": capabilities.estimated_api_score,
                "has_api": capabilities.has_api,
                "has_webhooks": capabilities.has_webhooks,
                "has_zapier": capabilities.has_zapier,
                "has_make": capabilities.has_make,
                "has_oauth": capabilities.has_oauth,
                "reasoning": capabilities.reasoning,
                "confidence": capabilities.confidence,
                "source_urls": capabilities.source_urls,
            },
        }

    except Exception as e:
        logger.error(f"Research software error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to research software: {str(e)}"
        )


@router.post("/sessions/{session_id}/research-stack")
async def research_session_existing_stack(session_id: str):
    """
    Research all free_text software in a session's existing stack.

    Useful for re-running research if it failed during quiz completion,
    or for running research before report generation.
    """
    try:
        supabase = await get_async_supabase()

        # Get session
        result = await supabase.table("quiz_sessions").select(
            "id, existing_stack"
        ).eq("id", session_id).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        existing_stack = result.data.get("existing_stack", [])
        if not existing_stack:
            return {
                "success": True,
                "session_id": session_id,
                "researched_count": 0,
                "message": "No existing stack to research",
            }

        # Research the stack
        researched_items = await research_session_stack(
            existing_stack, cache_results=True
        )

        # Update session with researched stack
        await supabase.table("quiz_sessions").update({
            "existing_stack": [item.model_dump() for item in researched_items],
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", session_id).execute()

        # Count researched items
        researched_count = sum(
            1 for item in researched_items
            if item.researched and item.api_score is not None
        )

        logger.info(
            f"Researched {researched_count} stack items for session {session_id}"
        )

        return {
            "success": True,
            "session_id": session_id,
            "researched_count": researched_count,
            "total_items": len(researched_items),
            "items": [item.model_dump() for item in researched_items],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Research stack error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to research existing stack"
        )


# ============================================================================
# Helper Functions
# ============================================================================

def _calculate_preliminary_results(answers: Dict[str, Any], industry: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate preliminary results from quiz answers.

    These are shown before payment and used to personalize the checkout.
    """
    # Extract key metrics from answers
    company_size = answers.get("company_size", "1-10")
    current_tools = answers.get("current_tools", [])
    pain_points = answers.get("pain_points", [])
    budget_range = answers.get("ai_budget", "5000-15000")

    # Simple AI readiness scoring based on answers
    readiness_factors = []

    # Factor 1: Company size (larger = more ready)
    size_scores = {
        "1-10": 40,
        "11-50": 55,
        "51-200": 70,
        "201-1000": 80,
        "1000+": 85,
    }
    readiness_factors.append(size_scores.get(company_size, 50))

    # Factor 2: Current tool usage
    tool_score = min(90, 40 + len(current_tools) * 10)
    readiness_factors.append(tool_score)

    # Factor 3: Pain points identified (more = more opportunity)
    pain_score = min(85, 30 + len(pain_points) * 8)
    readiness_factors.append(pain_score)

    # Factor 4: Budget available
    budget_scores = {
        "0-2000": 30,
        "2000-5000": 45,
        "5000-15000": 60,
        "15000-50000": 75,
        "50000+": 90,
    }
    readiness_factors.append(budget_scores.get(budget_range, 50))

    # Average the factors
    ai_readiness_score = int(sum(readiness_factors) / len(readiness_factors))

    # Count opportunities based on pain points
    opportunity_count = max(3, len(pain_points) + 2)

    # Estimate value potential based on company size and pain points
    base_values = {
        "1-10": 15000,
        "11-50": 35000,
        "51-200": 75000,
        "201-1000": 150000,
        "1000+": 300000,
    }
    base_value = base_values.get(company_size, 25000)
    value_multiplier = 1 + (len(pain_points) * 0.15)

    return {
        "ai_readiness_score": ai_readiness_score,
        "opportunity_count": opportunity_count,
        "value_potential": {
            "min": int(base_value * value_multiplier * 0.7),
            "max": int(base_value * value_multiplier * 1.3),
        },
        "industry": industry or answers.get("industry", "general"),
        "calculated_at": datetime.utcnow().isoformat(),
    }


# ============================================================================
# Research Integration Routes
# ============================================================================

class StartResearchSessionRequest(BaseModel):
    """Request to start research for a quiz session."""
    company_name: Optional[str] = None
    website_url: str


@router.post("/sessions/{session_id}/research")
async def start_session_research(session_id: str, request: StartResearchSessionRequest):
    """
    Start company research for a quiz session.

    Called when user enters their company website.
    Research runs in background while user continues quiz.
    Returns a research_id to track progress.
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

        # Extract company name from website if not provided
        company_name = request.company_name
        if not company_name:
            # Parse from URL
            from urllib.parse import urlparse
            parsed = urlparse(request.website_url)
            domain = parsed.netloc or parsed.path
            company_name = domain.replace("www.", "").split(".")[0].title()

        # Create research record
        import uuid
        research_id = str(uuid.uuid4())

        # Update session with research info
        await supabase.table("quiz_sessions").update({
            "research_id": research_id,
            "research_status": "pending",
            "company_website": request.website_url,
            "company_name": company_name,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", session_id).execute()

        logger.info(f"Started research {research_id} for session {session_id}")

        return {
            "success": True,
            "research_id": research_id,
            "session_id": session_id,
            "company_name": company_name,
            "website_url": request.website_url,
            "status": "pending",
            "message": "Research started. Use the stream endpoint to track progress.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start research error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start research"
        )


@router.get("/sessions/{session_id}/research/stream")
async def stream_research_progress(session_id: str):
    """
    Stream research progress via Server-Sent Events.

    Frontend connects to this endpoint after starting research
    to receive real-time updates.
    """
    try:
        supabase = await get_async_supabase()

        # Get session with research info
        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data
        company_name = session.get("company_name")
        website_url = session.get("company_website")

        if not company_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No company information for research"
            )

        async def research_generator():
            """Generate SSE events from research agent."""
            try:
                async for event in start_company_research(company_name, website_url):
                    yield event

                # Update session with research complete status
                await supabase.table("quiz_sessions").update({
                    "research_status": "complete",
                    "updated_at": datetime.utcnow().isoformat(),
                }).eq("id", session_id).execute()

            except Exception as e:
                logger.error(f"Research stream error: {e}")
                yield f"data: {{'status': 'failed', 'error': '{str(e)}'}}\n\n"

        return StreamingResponse(
            research_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Research stream error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stream research"
        )


@router.get("/sessions/{session_id}/research/status")
async def get_research_status(session_id: str):
    """
    Get current research status for a session.

    Returns the research profile if complete.
    """
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data

        return {
            "session_id": session_id,
            "research_id": session.get("research_id"),
            "status": session.get("research_status", "not_started"),
            "company_name": session.get("company_name"),
            "company_website": session.get("company_website"),
            "company_profile": session.get("company_profile"),
            "dynamic_questionnaire": session.get("dynamic_questionnaire"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get research status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get research status"
        )


@router.post("/sessions/{session_id}/research/save")
async def save_research_results(session_id: str, results: Dict[str, Any]):
    """
    Save research results to the session.

    Called by frontend after research stream completes.
    Stores company profile and generated questionnaire.
    """
    try:
        supabase = await get_async_supabase()

        # Get session
        existing = await supabase.table("quiz_sessions").select("id").eq(
            "id", session_id
        ).single().execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Extract results
        company_profile = results.get("company_profile")
        questionnaire = results.get("questionnaire")

        update_data = {
            "research_status": "complete",
            "updated_at": datetime.utcnow().isoformat(),
        }

        if company_profile:
            update_data["company_profile"] = company_profile

        if questionnaire:
            update_data["dynamic_questionnaire"] = questionnaire

        await supabase.table("quiz_sessions").update(update_data).eq(
            "id", session_id
        ).execute()

        logger.info(f"Saved research results for session {session_id}")

        return {
            "success": True,
            "session_id": session_id,
            "has_profile": company_profile is not None,
            "has_questionnaire": questionnaire is not None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save research results error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save research results"
        )


@router.get("/sessions/{session_id}/dynamic-questions")
async def get_dynamic_questions(session_id: str):
    """
    Get dynamic questions based on research.

    Returns customized questionnaire if research is complete,
    or falls back to standard questions.
    """
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data
        research_status = session.get("research_status")
        dynamic_questionnaire = session.get("dynamic_questionnaire")

        if research_status == "complete" and dynamic_questionnaire:
            # Return dynamic questions
            return {
                "type": "dynamic",
                "research_complete": True,
                "company_name": session.get("company_name"),
                "research_summary": dynamic_questionnaire.get("research_summary"),
                "confirmed_facts": dynamic_questionnaire.get("confirmed_facts", []),
                "questions": dynamic_questionnaire.get("questions", []),
                "sections": dynamic_questionnaire.get("sections", []),
                "total_questions": dynamic_questionnaire.get("total_questions", 0),
                "estimated_time_minutes": dynamic_questionnaire.get("estimated_time_minutes", 10),
            }

        # Fall back to standard questions
        industry = session.get("answers", {}).get("industry", "general")
        standard_sections = get_questionnaire(industry)

        return {
            "type": "standard",
            "research_complete": False,
            "research_status": research_status,
            "sections": standard_sections,
            "total_questions": get_total_questions(industry),
            "total_sections": get_section_count(industry),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get dynamic questions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dynamic questions"
        )


# ============================================================================
# Teaser Report Routes
# ============================================================================

class TeaserEmailRequest(BaseModel):
    """Request with email for teaser report."""
    email: Optional[EmailStr] = None


class DevPreviewRequest(BaseModel):
    """Request for dev-mode preview generation."""
    company_profile: Dict[str, Any]
    quiz_answers: Optional[Dict[str, Any]] = {}
    interview_messages: Optional[List[Dict[str, str]]] = []


@router.post("/dev/preview")
async def generate_dev_preview(request_data: DevPreviewRequest):
    """
    DEV ONLY: Generate preview without needing a real session.

    Accepts company profile and answers directly.
    """
    try:
        interview_data = {"messages": request_data.interview_messages or []}

        # Generate preview using insights-first teaser (no AI generation)
        teaser = await generate_teaser_report(
            request_data.company_profile,
            request_data.quiz_answers or {},
            interview_data
        )

        # Return new insights-first format directly
        # PreviewReport.tsx expects: ai_readiness, diagnostics, opportunity_areas, next_steps
        logger.info(f"Generated DEV preview for {teaser.get('company_name', 'unknown')}")
        return teaser

    except Exception as e:
        logger.error(f"Generate DEV preview error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )


@router.post("/sessions/{session_id}/preview")
async def generate_session_preview(
    session_id: str,
    request_data: Optional[dict] = None
):
    """
    Generate preview/micro report after 5-min interview.

    Uses company profile + interview answers to create a teaser.
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
        interview_data = session.get("interview_data", {})

        # Merge interview data if provided in request
        if request_data:
            if request_data.get("company_profile"):
                company_profile = {**company_profile, **request_data["company_profile"]}
            if request_data.get("interview_answers"):
                interview_data["answers"] = request_data["interview_answers"]
            if request_data.get("interview_messages"):
                interview_data["messages"] = request_data["interview_messages"]

        # Generate preview using insights-first teaser (no AI generation)
        teaser = await generate_teaser_report(company_profile, answers, interview_data)

        # Return new insights-first format directly
        # PreviewReport.tsx expects: ai_readiness, diagnostics, opportunity_areas, next_steps
        logger.info(f"Generated preview for session {session_id}")
        return teaser

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate preview error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate preview"
        )


@router.post("/sessions/{session_id}/teaser")
async def generate_session_teaser(
    session_id: str,
    email_data: Optional[TeaserEmailRequest] = None
):
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
        interview_data = session.get("interview_data", {})

        # Generate teaser (AI-powered with Haiku 4.5)
        teaser = await generate_teaser_report(company_profile, answers, interview_data)

        # Update email if provided
        update_data = {
            "teaser_report": teaser,
            "updated_at": datetime.utcnow().isoformat(),
        }

        email_sent = False
        brevo_added = False
        if email_data and email_data.email:
            real_email = email_data.email
            update_data["email"] = real_email

            # Send email
            try:
                success = await send_teaser_report_email(
                    to_email=real_email,
                    company_name=teaser.get("company_name", "Your Company"),
                    score=teaser["ai_readiness_score"],
                    findings=teaser["revealed_findings"],
                    session_id=session_id
                )
                if success:
                    update_data["teaser_sent_at"] = datetime.utcnow().isoformat()
                    email_sent = True
            except Exception as e:
                logger.error(f"Failed to send teaser email: {e}")

            # Add to Brevo for nurture sequence
            try:
                brevo = get_brevo_service()
                if brevo.is_configured:
                    score = teaser.get("ai_readiness_score", 50)
                    # Determine readiness level
                    if score >= 70:
                        readiness_level = "High"
                    elif score >= 40:
                        readiness_level = "Medium"
                    else:
                        readiness_level = "Low"

                    contact = QuizCompleterContact(
                        email=real_email,
                        first_name=company_profile.get("basics", {}).get("name", {}).get("value", "").split()[0] if company_profile.get("basics", {}).get("name", {}).get("value") else "there",
                        company_name=teaser.get("company_name", "Your Company"),
                        industry=teaser.get("industry", answers.get("industry", "general")),
                        quiz_score=score,
                        ai_readiness_level=readiness_level,
                        report_id=session_id,
                        signup_source="organic",  # TODO: track source from UTM params
                    )
                    await brevo.add_quiz_completer(contact)
                    brevo_added = True
                    logger.info(f"Added {real_email} to Brevo nurture list")
            except Exception as e:
                logger.error(f"Failed to add contact to Brevo: {e}")

        await supabase.table("quiz_sessions").update(update_data).eq(
            "id", session_id
        ).execute()

        logger.info(f"Generated teaser for session {session_id}")

        return {
            "success": True,
            "teaser": teaser,
            "email_sent": email_sent,
            "added_to_nurture": brevo_added,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate teaser error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate teaser report"
        )


# ============================================================================
# DEV: Test Report Generation
# ============================================================================

class DevTestReportRequest(BaseModel):
    """Request for dev-mode full report generation."""
    company_profile: Dict[str, Any]
    quiz_answers: Optional[Dict[str, Any]] = {}
    interview_messages: Optional[List[Dict[str, str]]] = []
    confidence_scores: Optional[Dict[str, Any]] = None
    tier: str = "quick"
    model_strategy: Optional[str] = None  # e.g., "anthropic_quick", "gemini_primary", "hybrid"


@router.post("/dev/generate-test-report")
async def generate_test_report(request_data: DevTestReportRequest):
    """
    DEV ONLY: Generate a full report for testing without payment.

    Creates a quiz session with test data and triggers report generation.
    Returns the report ID so you can view it in the report viewer.
    """
    import uuid
    from src.services.report_service import generate_report_streaming

    try:
        supabase = await get_async_supabase()

        # Extract company info from profile
        basics = request_data.company_profile.get("basics", {})
        industry_data = request_data.company_profile.get("industry", {})

        company_name = basics.get("name", {}).get("value", "Test Company")
        website = basics.get("website", {}).get("value", "test-company.com")
        industry = industry_data.get("primary_industry", {}).get("value", "professional-services")

        # Create a test session - only use columns that exist in the schema
        session_id = str(uuid.uuid4())

        # Combine interview messages into answers for storage
        answers = request_data.quiz_answers or {}
        if request_data.interview_messages:
            answers["interview_responses"] = request_data.interview_messages

        # Ensure industry is in answers (report generator expects it there)
        if "industry" not in answers and industry:
            answers["industry"] = industry

        # Add company size from profile
        size_data = request_data.company_profile.get("size", {})
        if "company_size" not in answers:
            answers["company_size"] = size_data.get("employee_range", {}).get("value", "11-50")
        if "employee_count" not in answers:
            answers["employee_count"] = size_data.get("employee_count", {}).get("value", 25)

        # Build interview_data structure with messages and confidence scores
        interview_data = {
            "messages": request_data.interview_messages or [],
            "confidence": request_data.confidence_scores or {},
        }

        session_data = {
            "id": session_id,
            "email": "dev-test@crb-analyser.local",
            "tier": request_data.tier,
            "status": "paid",  # Mark as paid to bypass payment check
            "current_section": 0,
            "current_question": 0,
            "answers": answers,
            "company_name": company_name,
            "company_website": website,
            "company_profile": request_data.company_profile,
            "interview_data": interview_data,
        }

        # Insert the test session
        await supabase.table("quiz_sessions").insert(session_data).execute()

        logger.info(f"Created test session {session_id} for {company_name} (industry={industry})")

        # Generate the report (this will create the report in the database)
        report_id = None
        generation_error = None
        last_progress = None

        async for event in generate_report_streaming(session_id, request_data.tier):
            # Parse the SSE event to extract data
            if event.startswith("data: "):
                try:
                    data = json.loads(event[6:].strip())
                    last_progress = data

                    # Check for completion with report_id
                    if data.get("report_id"):
                        report_id = data["report_id"]

                    # Check for errors
                    if data.get("phase") == "error":
                        generation_error = data.get("error", "Unknown error during report generation")
                        logger.error(f"Report generation error: {generation_error}")

                    # Log progress
                    if data.get("progress"):
                        logger.debug(f"Report progress: {data.get('step')} ({data.get('progress')}%)")

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse SSE event: {e}")

        # If there was an error, raise it
        if generation_error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {generation_error}"
            )

        # Get the report ID from the session if not found in events
        if not report_id:
            session_result = await supabase.table("quiz_sessions").select("report_id").eq(
                "id", session_id
            ).single().execute()
            report_id = session_result.data.get("report_id") if session_result.data else None

        if not report_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Report generation completed but report_id not found"
            )

        logger.info(f"Generated test report {report_id} for session {session_id}")

        return {
            "success": True,
            "session_id": session_id,
            "report_id": report_id,
            "company_name": company_name,
            "industry": industry,
            "view_url": f"/report/{report_id}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate test report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate test report: {str(e)}"
        )


@router.post("/dev/generate-test-report/stream")
async def generate_test_report_stream(request_data: DevTestReportRequest):
    """
    DEV ONLY: Generate a full report with streaming progress updates.

    Creates a quiz session and streams SSE events for real-time progress.
    Frontend should use EventSource to consume this endpoint.
    """
    import uuid
    from src.services.report_service import generate_report_streaming

    async def event_generator():
        """Generate SSE events for report generation progress."""
        try:
            supabase = await get_async_supabase()

            # Extract company info from profile
            basics = request_data.company_profile.get("basics", {})
            industry_data = request_data.company_profile.get("industry", {})

            company_name = basics.get("name", {}).get("value", "Test Company")
            website = basics.get("website", {}).get("value", "test-company.com")
            industry = industry_data.get("primary_industry", {}).get("value", "professional-services")

            # Yield initial event
            yield f"data: {json.dumps({'phase': 'init', 'step': 'Creating session...', 'progress': 5, 'company_name': company_name})}\n\n"

            # Create a test session
            session_id = str(uuid.uuid4())

            # Combine interview messages into answers for storage
            answers = request_data.quiz_answers or {}
            if request_data.interview_messages:
                answers["interview_responses"] = request_data.interview_messages

            if "industry" not in answers and industry:
                answers["industry"] = industry

            size_data = request_data.company_profile.get("size", {})
            if "company_size" not in answers:
                answers["company_size"] = size_data.get("employee_range", {}).get("value", "11-50")
            if "employee_count" not in answers:
                answers["employee_count"] = size_data.get("employee_count", {}).get("value", 25)

            interview_data = {
                "messages": request_data.interview_messages or [],
                "confidence": request_data.confidence_scores or {},
            }

            session_data = {
                "id": session_id,
                "email": "dev-test@crb-analyser.local",
                "tier": request_data.tier,
                "status": "paid",
                "current_section": 0,
                "current_question": 0,
                "answers": answers,
                "company_name": company_name,
                "company_website": website,
                "company_profile": request_data.company_profile,
                "interview_data": interview_data,
            }

            await supabase.table("quiz_sessions").insert(session_data).execute()
            logger.info(f"[STREAM] Created test session {session_id} for {company_name}")

            # Log model strategy for debugging
            strategy_info = request_data.model_strategy or "default"
            yield f"data: {json.dumps({'phase': 'init', 'step': f'Session created (strategy: {strategy_info})', 'progress': 10, 'session_id': session_id, 'model_strategy': strategy_info})}\n\n"

            # Stream the actual report generation events
            report_id = None
            async for event in generate_report_streaming(
                session_id,
                request_data.tier,
                model_strategy=request_data.model_strategy
            ):
                # Forward the event directly
                yield event

                # Parse to check for completion
                if event.startswith("data: "):
                    try:
                        data = json.loads(event[6:].strip())
                        if data.get("report_id"):
                            report_id = data["report_id"]
                    except json.JSONDecodeError:
                        pass

            # Final completion event with navigation info
            if report_id:
                yield f"data: {json.dumps({'phase': 'done', 'step': 'Report ready!', 'progress': 100, 'report_id': report_id, 'view_url': f'/report/{report_id}'})}\n\n"
            else:
                yield f"data: {json.dumps({'phase': 'error', 'step': 'Report ID not found', 'progress': 0, 'error': 'Report generation completed but report_id not found'})}\n\n"

        except Exception as e:
            logger.error(f"[STREAM] Error in report generation: {e}", exc_info=True)
            yield f"data: {json.dumps({'phase': 'error', 'step': 'Generation failed', 'progress': 0, 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/dev/session-debug/{session_id}")
async def get_session_debug_data(session_id: str):
    """
    DEV ONLY: Get full session data including all inputs used for report generation.

    Returns:
    - Quiz answers
    - Company profile (research scrape data)
    - Interview messages
    - Knowledge base data that would be loaded for this industry
    """
    from src.knowledge import (
        get_industry_context,
        get_relevant_opportunities,
        get_vendor_recommendations,
        get_benchmarks_for_metrics,
    )

    try:
        supabase = await get_async_supabase()

        # Get full session data
        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data
        answers = session.get("answers", {})
        industry = answers.get("industry", "general")

        # Load knowledge base data for this industry
        kb_context = get_industry_context(industry)
        kb_opportunities = get_relevant_opportunities(industry)
        kb_vendors = get_vendor_recommendations(industry)
        kb_benchmarks = get_benchmarks_for_metrics(industry)

        return {
            "session_id": session_id,
            "input_data": {
                "company_name": session.get("company_name"),
                "company_website": session.get("company_website"),
                "company_profile": session.get("company_profile"),
                "quiz_answers": answers,
                "interview_data": session.get("interview_data"),
                "interview_messages": answers.get("interview_responses", []),
            },
            "knowledge_base": {
                "industry": industry,
                "is_supported": kb_context.get("is_supported", False),
                "industry_context": kb_context,
                "opportunities": kb_opportunities,
                "opportunities_count": len(kb_opportunities) if kb_opportunities else 0,
                "vendors": kb_vendors,
                "vendors_count": len(kb_vendors) if kb_vendors else 0,
                "benchmarks": kb_benchmarks,
                "benchmark_categories": list(kb_benchmarks.keys()) if kb_benchmarks else [],
            },
            "session_meta": {
                "tier": session.get("tier"),
                "status": session.get("status"),
                "report_id": session.get("report_id"),
                "created_at": session.get("created_at"),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session debug data error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session debug data: {str(e)}"
        )


# ============================================================================
# Adaptive Quiz Models
# ============================================================================

class AdaptiveStartRequest(BaseModel):
    """Request to start an adaptive quiz session."""
    session_id: str


class AdaptiveStartResponse(BaseModel):
    """Response after starting adaptive quiz."""
    session_id: str
    question: Dict[str, Any]
    confidence: Dict[str, Any]
    company_name: Optional[str] = None
    industry: Optional[str] = None


class AdaptiveAnswerRequest(BaseModel):
    """Request to submit an answer and get next question."""
    session_id: str
    question_id: str
    answer: str
    answer_type: str = "voice"  # voice, text, select, number


class AdaptiveAnswerResponse(BaseModel):
    """Response after submitting answer."""
    complete: bool
    question: Optional[Dict[str, Any]] = None
    confidence: Dict[str, Any]
    analysis_hint: Optional[Dict[str, Any]] = None
    redirect: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None


class AdaptiveStateResponse(BaseModel):
    """Current state of adaptive quiz."""
    session_id: str
    confidence: Dict[str, Any]
    questions_asked: int
    is_complete: bool
    answers: List[Dict[str, Any]]


# ============================================================================
# Adaptive Quiz Routes
# ============================================================================

# In-memory storage for active quiz generators (in production, use Redis)
_active_generators: Dict[str, QuestionGenerator] = {}


@router.post("/adaptive/start", response_model=AdaptiveStartResponse)
async def start_adaptive_quiz(request: AdaptiveStartRequest):
    """
    Start an adaptive quiz session.

    Initializes confidence state from research findings and generates
    the first personalized question.
    """
    try:
        supabase = await get_async_supabase()

        # Get existing session
        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", request.session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data
        company_profile_data = session.get("company_profile", {})
        answers = session.get("answers", {})
        industry = answers.get("industry", "general")

        # Convert to CompanyProfile model
        try:
            company_profile = CompanyProfile(**company_profile_data) if company_profile_data else None
        except Exception as e:
            logger.warning(f"Failed to parse company profile: {e}")
            company_profile = None

        # Create minimal profile if none exists
        if company_profile is None:
            from src.models.research import CompanyBasics, ResearchedField
            company_name = session.get("company_name") or answers.get("company_name") or "Unknown Company"
            company_profile = CompanyProfile(
                basics=CompanyBasics(
                    name=ResearchedField(value=company_name),
                    website=session.get("website"),
                    description=ResearchedField(value=answers.get("business_description", "")),
                )
            )

        # Initialize confidence from research
        confidence_state = create_initial_confidence_from_research(
            company_profile_data,
            research_quality_score=50  # Default mid-quality
        )

        # Create question generator
        generator = QuestionGenerator(company_profile, industry)
        _active_generators[request.session_id] = generator

        # Try to get an industry question first, then fall back to AI generation
        first_question = generator.get_next_industry_question(confidence_state)
        if not first_question:
            first_question = await generator.generate_next_question(confidence_state)

        # Update session with adaptive mode
        await supabase.table("quiz_sessions").update({
            "quiz_mode": "adaptive",
            "confidence_state": confidence_state.model_dump(mode='json'),
            "adaptive_answers": [],
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        logger.info(f"Started adaptive quiz for session {request.session_id}")

        return AdaptiveStartResponse(
            session_id=request.session_id,
            question=first_question.model_dump(),
            confidence=confidence_state.get_progress_summary(),
            company_name=session.get("company_name"),
            industry=industry,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start adaptive quiz error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start adaptive quiz: {str(e)}"
        )


@router.post("/adaptive/answer", response_model=AdaptiveAnswerResponse)
async def submit_adaptive_answer(request: AdaptiveAnswerRequest):
    """
    Submit an answer and get the next question.

    Analyzes the answer, updates confidence scores, and either:
    - Returns next question if thresholds not met
    - Returns completion response if all thresholds met
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
        company_profile_data = session.get("company_profile", {})
        answers = session.get("answers", {})
        industry = answers.get("industry", "general")

        # Load or create confidence state
        confidence_data = session.get("confidence_state", {})
        if confidence_data:
            confidence_state = ConfidenceState(**confidence_data)
        else:
            confidence_state = create_initial_confidence_from_research(company_profile_data)

        # Convert to CompanyProfile model
        try:
            company_profile = CompanyProfile(**company_profile_data) if company_profile_data else None
        except Exception:
            company_profile = None

        # Create minimal profile if none exists
        if company_profile is None:
            from src.models.research import CompanyBasics, ResearchedField
            company_name = session.get("company_name") or answers.get("company_name") or "Unknown Company"
            company_profile = CompanyProfile(
                basics=CompanyBasics(
                    name=ResearchedField(value=company_name),
                    website=session.get("website"),
                    description=ResearchedField(value=answers.get("business_description", "")),
                )
            )

        # Get or create question generator
        generator = _active_generators.get(request.session_id)
        if not generator:
            generator = QuestionGenerator(company_profile, industry)
            _active_generators[request.session_id] = generator

        # Create the question object from the request
        current_question = AdaptiveQuestion(
            id=request.question_id,
            question="",  # We don't need the full question for analysis
            target_categories=[],  # Will be extracted from question bank if available
            question_type=request.answer_type,
            input_type=request.answer_type,
        )

        # Try to get question details from question bank
        bank_question = generator.question_bank.get_question_by_id(request.question_id)
        if bank_question:
            target_cats = []
            for cat_str in bank_question.get("target_categories", []):
                try:
                    target_cats.append(ConfidenceCategory(cat_str))
                except ValueError:
                    pass
            current_question = AdaptiveQuestion(
                id=request.question_id,
                question=bank_question.get("question", ""),
                target_categories=target_cats,
                question_type=bank_question.get("question_type", "voice"),
                input_type=bank_question.get("input_type", "voice"),
                options=bank_question.get("options"),
            )

        # Analyze the answer
        analyzer = AnswerAnalyzer()
        analysis = await analyzer.analyze(
            request.answer,
            current_question,
            company_profile
        )

        # Update confidence state
        confidence_state = update_confidence_from_analysis(confidence_state, analysis)

        # Store the answer
        adaptive_answers = session.get("adaptive_answers", []) or []
        adaptive_answers.append({
            "question_id": request.question_id,
            "question": current_question.question,
            "answer": request.answer,
            "answer_type": request.answer_type,
            "analysis": analysis.model_dump(mode='json'),
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Check for completion
        if confidence_state.ready_for_teaser:
            # Mark quiz as complete
            await supabase.table("quiz_sessions").update({
                "confidence_state": confidence_state.model_dump(mode='json'),
                "adaptive_answers": adaptive_answers,
                "quiz_completed_at": datetime.utcnow().isoformat(),
                "status": "pending_payment",
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", request.session_id).execute()

            # Cleanup generator
            _active_generators.pop(request.session_id, None)

            logger.info(f"Adaptive quiz complete for session {request.session_id}")

            return AdaptiveAnswerResponse(
                complete=True,
                confidence=confidence_state.get_progress_summary(),
                redirect=f"/quiz/preview?session_id={request.session_id}",
                summary=confidence_state.to_teaser_summary(),
            )

        # Generate next question
        # First try industry question (with deep dive check), then AI generation
        next_question = generator.get_next_industry_question(
            confidence_state,
            last_question_id=request.question_id,
            last_answer_value=request.answer,
        )
        if not next_question:
            next_question = await generator.generate_next_question(
                confidence_state,
                last_answer=request.answer,
                last_analysis=analysis,
            )

        # Update session
        await supabase.table("quiz_sessions").update({
            "confidence_state": confidence_state.model_dump(mode='json'),
            "adaptive_answers": adaptive_answers,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        return AdaptiveAnswerResponse(
            complete=False,
            question=next_question.model_dump(),
            confidence=confidence_state.get_progress_summary(),
            analysis_hint={
                "detected_signals": analysis.detected_signals,
                "is_deep_dive": next_question.is_deep_dive,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit adaptive answer error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process answer: {str(e)}"
        )


@router.get("/adaptive/state/{session_id}", response_model=AdaptiveStateResponse)
async def get_adaptive_state(session_id: str):
    """
    Get current state of an adaptive quiz.

    Returns confidence scores, questions asked, and collected answers.
    """
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("quiz_sessions").select("*").eq(
            "id", session_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = result.data
        confidence_data = session.get("confidence_state", {})
        adaptive_answers = session.get("adaptive_answers", []) or []

        if confidence_data:
            confidence_state = ConfidenceState(**confidence_data)
            confidence_summary = confidence_state.get_progress_summary()
        else:
            confidence_summary = {
                "scores": {},
                "thresholds": {cat.value: thresh for cat, thresh in CONFIDENCE_THRESHOLDS.items()},
                "gaps": [],
                "ready_for_teaser": False,
                "questions_asked": 0,
            }

        return AdaptiveStateResponse(
            session_id=session_id,
            confidence=confidence_summary,
            questions_asked=len(adaptive_answers),
            is_complete=session.get("quiz_completed_at") is not None,
            answers=adaptive_answers,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get adaptive state error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get adaptive quiz state"
        )


@router.get("/adaptive/industries")
async def list_available_industries():
    """
    List industries with available question banks.

    Returns list of industry slugs that have specialized questions.
    """
    return {
        "industries": get_available_industries(),
        "total": len(get_available_industries()),
    }


@router.get("/adaptive/questions/{industry}")
async def get_industry_question_bank(industry: str):
    """
    Get the question bank for an industry.

    Returns all predefined questions, deep dives, and woven confirmations.
    """
    bank = IndustryQuestionBank.load(industry)

    return {
        "industry": bank.industry,
        "display_name": bank.display_name,
        "questions": bank.questions,
        "questions_count": len(bank.questions),
        "deep_dive_templates": bank.deep_dive_templates,
        "woven_confirmation_templates": bank.woven_confirmation_templates,
    }
