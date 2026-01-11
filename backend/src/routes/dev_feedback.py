"""
Dev Feedback Routes

Dev/admin-only routes for:
1. Viewing full report context (quiz, research, interview data)
2. Submitting feedback that feeds into the expertise system

Part of the Signal Loop (SIL) - learning from every analysis.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from src.config.supabase_client import get_async_supabase
from src.config.settings import settings
from src.models.feedback import ReportFeedback, ReportContext
from src.expertise import get_self_improve_service

logger = logging.getLogger(__name__)

router = APIRouter()


def is_dev_mode() -> bool:
    """Check if we're in development mode."""
    return settings.APP_ENV in ("development", "dev", "local") or settings.DEBUG


# ============================================================================
# Context Endpoint - View inputs that went into report
# ============================================================================

@router.get("/reports/{report_id}/context")
async def get_report_context(
    report_id: str,
    dev: bool = Query(False, description="Dev mode flag"),
):
    """
    Get the full context that went into generating a report.

    Returns quiz answers, company profile, interview data, research data, etc.
    Dev/admin only.
    """
    if not is_dev_mode() and not dev:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Context view only available in dev mode"
        )

    # Handle sample report - return mock context for demo
    if report_id == "sample":
        return ReportContext(
            session_id="sample-session",
            email=None,
            company_name="TechFlow Solutions",
            quiz_answers={
                "industry": "b2b_saas",
                "team_size": "11-50",
                "main_pain_points": ["manual_processes", "scaling_support"],
            },
            company_profile={"name": "TechFlow Solutions", "industry": "B2B SaaS"},
            interview_data={},
            interview_transcript=[],
            research_data={},
            industry_knowledge={},
            vendors_considered=[],
            generation_started_at=None,
            generation_completed_at=None,
            confidence_scores={},
            tokens_used={},
            generation_trace={},
        ).model_dump()

    try:
        supabase = await get_async_supabase()

        # Get report with token_usage and generation_trace
        report_result = await supabase.table("reports").select(
            "id, quiz_session_id, tier, status, "
            "generation_started_at, generation_completed_at, "
            "assumption_log, token_usage, generation_trace"
        ).eq("id", report_id).single().execute()

        if not report_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        report = report_result.data
        session_id = report.get("quiz_session_id")

        # Get session data
        session_result = await supabase.table("quiz_sessions").select("*").eq(
            "id", session_id
        ).single().execute()

        session = session_result.data or {}
        answers = session.get("answers", {}) or {}

        # Extract interview transcript - check both locations
        # 1. interview_data.messages (standard location)
        # 2. answers.interview_responses (dev test reports store here)
        interview_data = session.get("interview_data", {}) or {}
        transcript = interview_data.get("messages", [])

        # If no transcript in interview_data, check answers.interview_responses
        if not transcript:
            interview_responses = answers.get("interview_responses", [])
            if interview_responses:
                # Convert string responses to message format
                if isinstance(interview_responses, list):
                    if interview_responses and isinstance(interview_responses[0], str):
                        # List of strings - convert to messages
                        transcript = [{"role": "user", "content": msg} for msg in interview_responses]
                    elif interview_responses and isinstance(interview_responses[0], dict):
                        # Already in message format
                        transcript = interview_responses

        # Get research data if stored separately
        research_data = session.get("research_data", {}) or {}

        # If no research_data, use company_profile as research context
        if not research_data and session.get("company_profile"):
            research_data = {
                "company_profile": session.get("company_profile"),
                "source": "pre_research_scrape",
            }

        # Extract semantic retrieval from assumption_log
        assumption_log = report.get("assumption_log", {}) or {}
        semantic_retrieval = assumption_log.get("semantic_retrieval", {})
        industry_knowledge = {}
        if semantic_retrieval:
            industry_knowledge = {
                "query": semantic_retrieval.get("query", ""),
                "total_results": semantic_retrieval.get("total_results", 0),
                "search_time_ms": semantic_retrieval.get("search_time_ms", 0),
                "opportunities_retrieved": semantic_retrieval.get("opportunities_retrieved", 0),
                "vendors_retrieved": semantic_retrieval.get("vendors_retrieved", 0),
                "case_studies_retrieved": semantic_retrieval.get("case_studies_retrieved", 0),
            }

        # Get token usage
        token_usage = report.get("token_usage", {}) or {}

        # Get generation trace
        generation_trace = report.get("generation_trace", {}) or {}

        # Build context response
        context = ReportContext(
            session_id=session_id,
            email=session.get("email"),
            company_name=session.get("company_name"),
            quiz_answers=answers,
            company_profile=session.get("company_profile", {}) or {},
            interview_data=interview_data,
            interview_transcript=transcript,
            research_data=research_data,
            industry_knowledge=industry_knowledge,
            vendors_considered=[],  # Would need to extract from report
            generation_started_at=report.get("generation_started_at"),
            generation_completed_at=report.get("generation_completed_at"),
            confidence_scores=interview_data.get("confidence", {}) or {},
            tokens_used=token_usage.get("summary", {}),
            generation_trace=generation_trace,
        )

        return context.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load report context"
        )


# ============================================================================
# Feedback Endpoints
# ============================================================================

@router.post("/feedback")
async def submit_feedback(feedback: ReportFeedback):
    """
    Submit feedback on a report.

    This data feeds into the expertise system to improve future analyses.
    """
    if not is_dev_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Feedback submission only available in dev mode"
        )

    try:
        supabase = await get_async_supabase()

        # Verify report exists
        report_result = await supabase.table("reports").select(
            "id, quiz_session_id"
        ).eq("id", feedback.report_id).single().execute()

        if not report_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        # Store feedback in reports table
        await supabase.table("reports").update({
            "dev_feedback": feedback.to_dict(),
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", feedback.report_id).execute()

        # Also store in a dedicated feedback table for aggregation
        # (Create this table if needed via migration)
        try:
            await supabase.table("report_feedback").insert({
                "report_id": feedback.report_id,
                "session_id": feedback.session_id,
                "feedback_data": feedback.to_dict(),
                "overall_quality": feedback.overall_quality,
                "accuracy_score": feedback.accuracy_score,
                "actionability_score": feedback.actionability_score,
                "relevance_score": feedback.relevance_score,
                "created_at": datetime.utcnow().isoformat(),
            }).execute()
        except Exception as e:
            # Table might not exist yet - that's okay
            logger.warning(f"Could not store in report_feedback table: {e}")

        logger.info(
            f"Feedback submitted for report {feedback.report_id}: "
            f"quality={feedback.overall_quality}/10"
        )

        # Trigger expertise system update (Signal Loop)
        expertise_updates = None
        try:
            # Get industry from session
            session_result = await supabase.table("quiz_sessions").select(
                "answers"
            ).eq("id", report["quiz_session_id"]).single().execute()

            if session_result.data:
                answers = session_result.data.get("answers", {})
                industry = answers.get("industry", "general")

                # Learn from feedback
                service = get_self_improve_service()
                expertise_updates = await service.learn_from_feedback(
                    report_id=feedback.report_id,
                    industry=industry,
                    feedback=feedback.to_dict(),
                )
                logger.info(f"Expertise updated from feedback: {expertise_updates}")
        except Exception as e:
            logger.warning(f"Failed to update expertise from feedback: {e}")

        return {
            "success": True,
            "report_id": feedback.report_id,
            "message": "Feedback submitted successfully",
            "scores": {
                "overall_quality": feedback.overall_quality,
                "accuracy": feedback.accuracy_score,
                "actionability": feedback.actionability_score,
                "relevance": feedback.relevance_score,
            },
            "expertise_updates": expertise_updates,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )


@router.get("/feedback/{report_id}")
async def get_feedback(report_id: str):
    """
    Get existing feedback for a report.
    """
    if not is_dev_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Feedback view only available in dev mode"
        )

    try:
        supabase = await get_async_supabase()

        result = await supabase.table("reports").select(
            "id, dev_feedback"
        ).eq("id", report_id).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        return {
            "report_id": report_id,
            "feedback": result.data.get("dev_feedback"),
            "has_feedback": result.data.get("dev_feedback") is not None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load feedback"
        )


@router.get("/feedback/stats")
async def get_feedback_stats():
    """
    Get aggregate feedback statistics.
    Useful for tracking overall report quality over time.
    """
    if not is_dev_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Stats only available in dev mode"
        )

    try:
        supabase = await get_async_supabase()

        # Get all reports with feedback
        result = await supabase.table("reports").select(
            "id, dev_feedback, created_at"
        ).not_.is_("dev_feedback", "null").execute()

        if not result.data:
            return {
                "total_reviewed": 0,
                "average_scores": None,
                "recent_feedback": [],
            }

        feedbacks = [r["dev_feedback"] for r in result.data if r.get("dev_feedback")]

        if not feedbacks:
            return {
                "total_reviewed": 0,
                "average_scores": None,
                "recent_feedback": [],
            }

        # Calculate averages
        avg_quality = sum(f.get("overall_quality", 5) for f in feedbacks) / len(feedbacks)
        avg_accuracy = sum(f.get("accuracy_score", 5) for f in feedbacks) / len(feedbacks)
        avg_actionability = sum(f.get("actionability_score", 5) for f in feedbacks) / len(feedbacks)
        avg_relevance = sum(f.get("relevance_score", 5) for f in feedbacks) / len(feedbacks)

        return {
            "total_reviewed": len(feedbacks),
            "average_scores": {
                "overall_quality": round(avg_quality, 1),
                "accuracy": round(avg_accuracy, 1),
                "actionability": round(avg_actionability, 1),
                "relevance": round(avg_relevance, 1),
            },
            "recent_feedback": [
                {
                    "report_id": r["id"],
                    "quality": r["dev_feedback"].get("overall_quality"),
                    "submitted_at": r["dev_feedback"].get("submitted_at"),
                }
                for r in result.data[:10]
            ],
        }

    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load feedback stats"
        )
