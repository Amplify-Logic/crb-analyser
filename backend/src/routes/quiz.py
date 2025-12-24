"""
Quiz Routes

Public routes for quiz sessions with save/resume functionality.
No authentication required - uses email for session lookup.

Includes research integration for dynamic question customization.
"""

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


class QuizProgressUpdate(BaseModel):
    """Partial progress update for a quiz session."""
    current_section: Optional[int] = None
    current_question: Optional[int] = None
    answers: Optional[Dict[str, Any]] = None
    email: Optional[EmailStr] = None  # For capturing real email after quiz preview
    industry: Optional[str] = None  # For market data collection


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

        # Update session
        await supabase.table("quiz_sessions").update({
            "status": "pending_payment",
            "results": results,
            "completed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", session_id).execute()

        logger.info(f"Quiz session {session_id} marked complete, ready for payment")

        return {
            "success": True,
            "session_id": session_id,
            "status": "pending_payment",
            "results": results,
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
