"""
Interview Routes

Routes for the AI-powered interview experience after payment.
This provides a conversational interface to gather detailed business context.

Skills Integration:
- FollowUpQuestionSkill: Generates adaptive follow-up questions
- PainExtractionSkill: Extracts structured pain points from transcript
- InterviewConfidenceSkill: Calculates readiness for report generation

Confidence Framework:
- Tracks topic coverage, depth, specificity, actionability per topic
- Calculates overall readiness score with quality multipliers
- Determines when interview is ready for report generation
- Triggers automatic report generation when thresholds met
"""

import logging
from typing import Optional, List
from datetime import datetime
import json

from fastapi import APIRouter, HTTPException, status, UploadFile, File
from pydantic import BaseModel
import anthropic

from src.config.supabase_client import get_async_supabase
from src.config.settings import settings
from src.config.system_prompt import get_interview_system_prompt, FOUNDATIONAL_LOGIC
from src.services.transcription_service import transcription_service
from src.skills import get_skill, SkillContext
from src.expertise import get_expertise_store
from src.knowledge import normalize_industry
from src.models.interview_confidence import (
    ReadinessLevel,
    ReportStatus,
)

logger = logging.getLogger(__name__)

# Global client for skills (lazy initialized)
_anthropic_client: Optional[anthropic.Anthropic] = None


def get_anthropic_client() -> anthropic.Anthropic:
    """Get or create the Anthropic client."""
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _anthropic_client

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class MessageContext(BaseModel):
    role: str
    content: str


class InterviewContext(BaseModel):
    company_profile: Optional[dict] = None
    previous_messages: Optional[List[MessageContext]] = None
    question_count: int = 0
    topics_covered: Optional[List[str]] = None


class InterviewRespondRequest(BaseModel):
    session_id: str
    message: str
    context: Optional[InterviewContext] = None


class InterviewCompleteRequest(BaseModel):
    session_id: str
    messages: List[dict]
    topics_covered: List[str]


# ============================================================================
# Interview Topics and Questions
# ============================================================================

INTERVIEW_TOPICS = [
    {
        "id": "current_challenges",
        "name": "Current Challenges",
        "questions": [
            "What's the biggest operational challenge you're facing right now?",
            "How much time does your team spend on repetitive tasks?",
            "What processes cause the most frustration for your team?",
        ]
    },
    {
        "id": "business_goals",
        "name": "Business Goals",
        "questions": [
            "What are your main growth objectives for the next 12 months?",
            "If you could automate one thing in your business, what would it be?",
            "What would 'success' look like for an AI implementation?",
        ]
    },
    {
        "id": "team_operations",
        "name": "Team & Operations",
        "questions": [
            "Can you walk me through a typical day for your team?",
            "Where do bottlenecks usually occur in your workflow?",
            "How does information flow between team members and departments?",
        ]
    },
    {
        "id": "technology",
        "name": "Technology & Tools",
        "questions": [
            "What software tools does your team use daily?",
            "Are there integrations between your tools that don't work well?",
            "Have you tried any AI tools before? What was that experience like?",
        ]
    },
    {
        "id": "budget_timeline",
        "name": "Budget & Timeline",
        "questions": [
            "What budget range are you considering for AI solutions?",
            "How quickly would you like to see improvements?",
            "Do you have internal resources for implementation, or would you need support?",
        ]
    },
    {
        "id": "deep_dive",
        "name": "Deep Dive",
        "questions": [
            "Tell me more about that specific challenge...",
            "What have you tried so far to address this?",
            "How does this impact your bottom line?",
        ]
    },
]


def get_next_question(context: InterviewContext) -> tuple[str, List[str], int]:
    """
    Determine the next question based on interview progress.
    Returns: (next_question, updated_topics, progress_percentage)
    """
    topics_covered = context.topics_covered or ["introduction"]
    question_count = context.question_count

    # Calculate which topics we've covered
    covered_ids = set()
    for topic in topics_covered:
        for t in INTERVIEW_TOPICS:
            if topic.lower() in t["name"].lower() or topic.lower() in t["id"]:
                covered_ids.add(t["id"])

    # Find next uncovered topic
    next_topic = None
    for topic in INTERVIEW_TOPICS:
        if topic["id"] not in covered_ids and topic["id"] != "deep_dive":
            next_topic = topic
            break

    # Calculate progress
    total_expected_questions = len(INTERVIEW_TOPICS) * 2  # ~2 questions per topic
    progress = min(95, int((question_count / total_expected_questions) * 100))

    if not next_topic:
        # All topics covered, do a summary
        return (
            "We've covered a lot of ground! Is there anything else you'd like to add about your situation before we wrap up?",
            list(set(topics_covered + ["summary"])),
            95
        )

    # Get a question from this topic
    q_index = question_count % len(next_topic["questions"])
    question = next_topic["questions"][q_index]

    return (
        question,
        list(set(topics_covered + [next_topic["name"]])),
        progress
    )


async def generate_ai_response(
    user_message: str,
    context: InterviewContext,
    previous_messages: List[MessageContext],
    industry: str = "general",
) -> tuple[str, List[str], int, bool]:
    """
    Generate an AI-powered response using FollowUpQuestionSkill.

    Uses the skills framework for adaptive follow-up questions.
    Falls back to legacy Claude-based method if skill fails.

    Returns: (response, updated_topics, progress, is_complete)
    """
    topics_covered = context.topics_covered or ["introduction"]
    question_count = context.question_count

    # Check for completion signals
    completion_signals = ["that's all", "nothing else", "i'm done", "that's it", "wrap up", "finish"]
    if any(signal in user_message.lower() for signal in completion_signals):
        return (
            "Thank you so much for sharing all this valuable information! This gives us a comprehensive picture of your business situation.\n\nClick 'Finish Interview' when you're ready, and we'll begin generating your personalized CRB report.",
            list(set(topics_covered + ["complete"])),
            100,
            True
        )

    # Try skill-based generation
    client = get_anthropic_client()
    skill = get_skill("followup-question", client=client)

    if skill:
        try:
            # Get expertise for the industry
            expertise_store = get_expertise_store()
            normalized_industry = normalize_industry(industry)
            expertise = expertise_store.get_expertise(normalized_industry)

            skill_context = SkillContext(
                industry=normalized_industry,
                expertise=expertise,
                metadata={
                    "user_message": user_message,
                    "previous_messages": [
                        {"role": m.role, "content": m.content}
                        for m in previous_messages[-10:]
                    ],
                    "topics_covered": topics_covered,
                    "question_count": question_count,
                }
            )

            result = await skill.run(skill_context)

            if result.success:
                data = result.data
                # Build response with the generated question
                response = data["question"]

                # Update topics
                new_topics = list(set(topics_covered + data.get("topics_touched", [])))

                # Calculate progress
                total_expected = 12
                progress = min(95, int((question_count / total_expected) * 100))

                is_complete = data.get("is_completion_candidate", False)

                logger.info(
                    f"FollowUp skill: type={data['question_type']}, "
                    f"progress={progress}%, expertise_applied={result.expertise_applied}"
                )
                return (response, new_topics, progress, is_complete)

        except Exception as e:
            logger.warning(f"FollowUpQuestionSkill failed, using legacy: {e}")

    # Fall back to legacy Claude-based response
    return await generate_ai_response_legacy(user_message, context, previous_messages)


async def generate_ai_response_legacy(
    user_message: str,
    context: InterviewContext,
    previous_messages: List[MessageContext],
) -> tuple[str, List[str], int, bool]:
    """
    Generate an AI-powered response using Claude (legacy method).
    Returns: (response, updated_topics, progress, is_complete)
    """
    topics_covered = context.topics_covered or ["introduction"]
    question_count = context.question_count

    # Build company context
    company_info = ""
    if context.company_profile:
        basics = context.company_profile.get("basics", {})
        company_name = basics.get("name", {}).get("value", "the company")
        industry = context.company_profile.get("industry", {}).get("primary_industry", {}).get("value", "their industry")
        company_info = f"Company: {company_name}, Industry: {industry}"

    # Build conversation history
    messages = []
    for msg in previous_messages[-10:]:
        messages.append({
            "role": msg.role if msg.role in ["user", "assistant"] else "user",
            "content": msg.content
        })
    messages.append({"role": "user", "content": user_message})

    # Topics we still need to cover
    all_topic_names = [t["name"] for t in INTERVIEW_TOPICS if t["id"] != "deep_dive"]
    uncovered = [t for t in all_topic_names if t not in topics_covered]

    # Use the centralized interview system prompt
    interview_base = get_interview_system_prompt()

    system_prompt = f"""{interview_base}

═══════════════════════════════════════════════════════════════════════════════
CURRENT SESSION CONTEXT
═══════════════════════════════════════════════════════════════════════════════

{company_info}

Topics already covered: {', '.join(topics_covered)}
Topics still to explore: {', '.join(uncovered) if uncovered else 'All main topics covered'}
Questions asked so far: {question_count}

═══════════════════════════════════════════════════════════════════════════════
RESPONSE GUIDELINES
═══════════════════════════════════════════════════════════════════════════════

1. Acknowledge what they shared (1-2 sentences, be specific to what they said)
2. Ask a follow-up OR transition to a new topic naturally
3. Keep responses conversational and warm, not robotic
4. Ask ONE question at a time
5. After covering all topics (~10-15 exchanges), guide toward wrapping up

Important:
- Be genuinely curious, not just checking boxes
- If they mention something interesting, dig deeper before moving on
- Use their words back to them to show you're listening
- Keep responses under 100 words total
- Do NOT make recommendations during the interview - just gather information"""

    try:
        client = get_anthropic_client()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=system_prompt,
            messages=messages
        )
        ai_response = response.content[0].text

        # Update topics based on conversation content
        new_topics = list(topics_covered)
        content_lower = (user_message + ai_response).lower()
        for topic in INTERVIEW_TOPICS:
            keywords = topic["name"].lower().split()
            if any(kw in content_lower for kw in keywords):
                if topic["name"] not in new_topics:
                    new_topics.append(topic["name"])

        # Calculate progress
        total_expected = len(INTERVIEW_TOPICS) * 2
        progress = min(95, int((question_count / total_expected) * 100))

        return (ai_response, new_topics, progress, False)

    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return generate_fallback_response(user_message, context)


def generate_fallback_response(
    user_message: str,
    context: InterviewContext,
) -> tuple[str, List[str], int, bool]:
    """Fallback to rule-based responses if Claude fails."""
    topics_covered = context.topics_covered or ["introduction"]
    question_count = context.question_count

    acknowledgments = [
        "I appreciate you sharing that.",
        "That's really helpful context.",
        "Thank you for explaining that.",
    ]
    ack = acknowledgments[question_count % len(acknowledgments)]
    next_q, updated_topics, progress = get_next_question(context)

    return (f"{ack}\n\n{next_q}", updated_topics, progress, False)


# ============================================================================
# Routes
# ============================================================================

@router.post("/respond")
async def interview_respond(request: InterviewRespondRequest):
    """
    Process a user message and return an AI response.
    Uses FollowUpQuestionSkill for adaptive conversations.
    """
    try:
        context = request.context or InterviewContext()
        previous_messages = context.previous_messages or []

        # Get industry from company profile
        industry = "general"
        if context.company_profile:
            industry = context.company_profile.get("industry", {}).get(
                "primary_industry", {}
            ).get("value", "general")

        response, topics, progress, is_complete = await generate_ai_response(
            user_message=request.message,
            context=context,
            previous_messages=previous_messages,
            industry=industry,
        )

        return {
            "response": response,
            "topics_covered": topics,
            "progress": progress,
            "is_complete": is_complete,
        }

    except Exception as e:
        logger.error(f"Interview respond error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.post("/complete")
async def interview_complete(request: InterviewCompleteRequest):
    """
    Mark the interview as complete, save data, and extract pain points.
    Uses PainExtractionSkill to analyze the conversation.
    """
    try:
        supabase = await get_async_supabase()

        # Get session
        session_result = await supabase.table("quiz_sessions").select("*").eq(
            "id", request.session_id
        ).single().execute()

        if not session_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = session_result.data

        # Get industry from session answers
        answers = session.get("answers", {})
        industry = answers.get("industry", "general")

        # Extract pain points using PainExtractionSkill
        pain_points_data = {}
        client = get_anthropic_client()
        skill = get_skill("pain-extraction", client=client)

        if skill and request.messages:
            try:
                expertise_store = get_expertise_store()
                normalized_industry = normalize_industry(industry)
                expertise = expertise_store.get_expertise(normalized_industry)

                skill_context = SkillContext(
                    industry=normalized_industry,
                    expertise=expertise,
                    metadata={
                        "transcript": request.messages,
                        "company_profile": answers.get("company_profile", {}),
                    }
                )

                result = await skill.run(skill_context)

                if result.success:
                    pain_points_data = result.data
                    logger.info(
                        f"Extracted {len(pain_points_data.get('pain_points', []))} pain points "
                        f"(confidence={pain_points_data.get('confidence_score', 0):.2f}, "
                        f"expertise_applied={result.expertise_applied})"
                    )

            except Exception as e:
                logger.warning(f"PainExtractionSkill failed: {e}")

        # Save interview data with extracted pain points
        await supabase.table("quiz_sessions").update({
            "interview_completed": True,
            "interview_data": {
                "messages": request.messages,
                "topics_covered": request.topics_covered,
                "completed_at": datetime.utcnow().isoformat(),
                "pain_points": pain_points_data,
            },
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        logger.info(f"Interview completed for session {request.session_id}")

        return {
            "success": True,
            "message": "Interview saved successfully",
            "pain_points_extracted": len(pain_points_data.get("pain_points", [])),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Interview complete error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save interview"
        )


@router.post("/transcribe")
async def transcribe_interview_audio(
    audio: UploadFile = File(...),
    session_id: Optional[str] = None,
):
    """
    Transcribe audio for interview (public endpoint for paid users).
    """
    try:
        # Validate file type
        allowed_types = [
            "audio/webm",
            "audio/mp3",
            "audio/mpeg",
            "audio/wav",
            "audio/ogg",
            "audio/m4a",
            "audio/mp4",
        ]
        content_type = audio.content_type or "audio/webm"
        if content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported audio format: {content_type}"
            )

        # Read audio data
        audio_data = await audio.read()

        if len(audio_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio file"
            )

        # Max 10MB
        if len(audio_data) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file too large (max 10MB)"
            )

        # Transcribe
        text, confidence = await transcription_service.transcribe_audio(
            audio_data, content_type
        )

        logger.info(f"Interview audio transcribed: {len(text)} chars")

        return {
            "text": text,
            "confidence": confidence,
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Transcription config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transcription service not configured"
        )
    except Exception as e:
        logger.error(f"Interview transcription error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcribe audio"
        )


class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None  # ElevenLabs voice ID (uses default if not provided)


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using ElevenLabs TTS.
    Returns audio as base64-encoded data.

    Popular voice IDs:
    - EXAVITQu4vr4xnSDxMaL: Sarah (conversational) - DEFAULT
    - 21m00Tcm4TlvDq8ikWAM: Rachel (calm, professional)
    - AZnzlk1XvdvUeBnXmlld: Domi (engaging, friendly)
    - MF3mGyEYCl7XYWbV9V6O: Elli (friendly, warm)
    - TxGEqnHWrfWFTfGW9XjX: Josh (deep, authoritative)
    """
    import base64

    try:
        audio_data = await transcription_service.text_to_speech(
            request.text,
            request.voice_id
        )

        # Return as base64 for easy frontend consumption
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        return {
            "audio": audio_base64,
            "format": "mp3",
            "text": request.text,
        }

    except ValueError as e:
        logger.error(f"TTS config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TTS service not configured"
        )
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate speech"
        )


# ============================================================================
# Confidence Framework Endpoints
# ============================================================================

class ConfidenceRequest(BaseModel):
    """Request to calculate interview confidence."""
    session_id: str
    messages: Optional[List[dict]] = None  # If not provided, loads from DB


class TriggerReportRequest(BaseModel):
    """Request to trigger report generation."""
    session_id: str
    force: bool = False  # Override confidence checks


@router.get("/confidence/{session_id}")
async def get_interview_confidence(session_id: str):
    """
    Calculate and return current interview confidence scores.

    This endpoint analyzes the interview transcript and returns:
    - Per-topic confidence scores (coverage, depth, specificity, actionability)
    - Quality indicators (pain points, quantified impacts, etc.)
    - Overall readiness score
    - Trigger decision (ready for report or needs more exploration)
    """
    try:
        supabase = await get_async_supabase()

        # Get session data
        session_result = await supabase.table("quiz_sessions").select("*").eq(
            "id", session_id
        ).single().execute()

        if not session_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = session_result.data
        interview_data = session.get("interview_data", {})
        messages = interview_data.get("messages", [])

        if not messages:
            return {
                "session_id": session_id,
                "has_messages": False,
                "readiness": {
                    "level": "insufficient",
                    "final_score": 0.0,
                    "is_ready_for_report": False,
                },
                "message": "No interview messages found. Start the interview to build confidence.",
            }

        # Get company profile and industry
        company_profile = session.get("company_profile", {})
        answers = session.get("answers", {})
        industry = answers.get("industry", "general")

        # Run confidence skill
        client = get_anthropic_client()
        skill = get_skill("interview-confidence", client=client)

        if not skill:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Confidence skill not available"
            )

        expertise_store = get_expertise_store()
        normalized_industry = normalize_industry(industry)
        expertise = expertise_store.get_expertise(normalized_industry)

        skill_context = SkillContext(
            industry=normalized_industry,
            expertise=expertise,
            metadata={
                "session_id": session_id,
                "messages": messages,
                "company_profile": company_profile,
            }
        )

        result = await skill.run(skill_context)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Confidence calculation failed: {result.error}"
            )

        # Store confidence data in session
        await supabase.table("quiz_sessions").update({
            "interview_data": {
                **interview_data,
                "confidence": result.data,
                "confidence_calculated_at": datetime.utcnow().isoformat(),
            },
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", session_id).execute()

        return {
            "session_id": session_id,
            "has_messages": True,
            "message_count": len(messages),
            **result.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Confidence calculation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate confidence"
        )


@router.post("/trigger-report")
async def trigger_report_generation(request: TriggerReportRequest):
    """
    Trigger report generation if interview is ready.

    This endpoint:
    1. Calculates current confidence (if not cached)
    2. Checks if readiness thresholds are met
    3. If ready (or force=True), triggers report generation
    4. Updates session status to 'generating'

    The actual report generation happens asynchronously.
    Use /api/reports/stream/{session_id} to monitor progress.
    """
    try:
        supabase = await get_async_supabase()

        # Get session data
        session_result = await supabase.table("quiz_sessions").select("*").eq(
            "id", request.session_id
        ).single().execute()

        if not session_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = session_result.data
        interview_data = session.get("interview_data", {})
        messages = interview_data.get("messages", [])

        if not messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No interview data available. Complete the interview first."
            )

        # Check if we have recent confidence data (within last 5 minutes)
        confidence_data = interview_data.get("confidence")
        confidence_timestamp = interview_data.get("confidence_calculated_at")

        should_recalculate = True
        if confidence_data and confidence_timestamp:
            calc_time = datetime.fromisoformat(confidence_timestamp.replace("Z", "+00:00"))
            age_seconds = (datetime.utcnow() - calc_time.replace(tzinfo=None)).total_seconds()
            should_recalculate = age_seconds > 300  # 5 minutes

        # Recalculate confidence if needed
        if should_recalculate:
            company_profile = session.get("company_profile", {})
            answers = session.get("answers", {})
            industry = answers.get("industry", "general")

            client = get_anthropic_client()
            skill = get_skill("interview-confidence", client=client)

            if skill:
                expertise_store = get_expertise_store()
                normalized_industry = normalize_industry(industry)
                expertise = expertise_store.get_expertise(normalized_industry)

                skill_context = SkillContext(
                    industry=normalized_industry,
                    expertise=expertise,
                    metadata={
                        "session_id": request.session_id,
                        "messages": messages,
                        "company_profile": company_profile,
                    }
                )

                result = await skill.run(skill_context)
                if result.success:
                    confidence_data = result.data

        # Check readiness
        overall_readiness = confidence_data.get("overall_readiness", {}) if confidence_data else {}
        is_ready = overall_readiness.get("is_ready_for_report", False)
        readiness_level = overall_readiness.get("level", "insufficient")

        if not is_ready and not request.force:
            return {
                "triggered": False,
                "reason": "Interview not ready for report generation",
                "readiness": {
                    "level": readiness_level,
                    "score": overall_readiness.get("final_score", 0),
                    "hard_gates": overall_readiness.get("hard_gates", {}),
                    "improvement_suggestions": overall_readiness.get("improvement_suggestions", []),
                },
                "message": "Continue the interview to improve confidence, or set force=true to proceed anyway.",
            }

        # Update session status to generating
        await supabase.table("quiz_sessions").update({
            "status": ReportStatus.GENERATING.value,
            "report_triggered_at": datetime.utcnow().isoformat(),
            "interview_data": {
                **interview_data,
                "confidence": confidence_data,
                "confidence_calculated_at": datetime.utcnow().isoformat(),
                "report_triggered": True,
                "forced": request.force,
            },
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        logger.info(
            f"Report generation triggered for session {request.session_id} "
            f"(readiness={readiness_level}, forced={request.force})"
        )

        return {
            "triggered": True,
            "session_id": request.session_id,
            "readiness": {
                "level": readiness_level,
                "score": overall_readiness.get("final_score", 0),
            },
            "forced": request.force,
            "next_step": f"Monitor progress at /api/reports/stream/{request.session_id}",
            "message": "Report generation has been triggered. It will be available for QA review within 2-5 minutes.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trigger report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger report generation"
        )


@router.get("/readiness-summary/{session_id}")
async def get_readiness_summary(session_id: str):
    """
    Get a quick summary of interview readiness without full recalculation.

    Useful for UI to show progress indicators.
    """
    try:
        supabase = await get_async_supabase()

        session_result = await supabase.table("quiz_sessions").select(
            "interview_data, status"
        ).eq("id", session_id).single().execute()

        if not session_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session = session_result.data
        interview_data = session.get("interview_data", {})
        messages = interview_data.get("messages", [])
        confidence = interview_data.get("confidence", {})
        overall = confidence.get("overall_readiness", {})

        return {
            "session_id": session_id,
            "status": session.get("status"),
            "message_count": len(messages),
            "topics_covered": interview_data.get("topics_covered", []),
            "readiness": {
                "level": overall.get("level", "insufficient"),
                "score": overall.get("final_score", 0),
                "is_ready": overall.get("is_ready_for_report", False),
            },
            "last_calculated": interview_data.get("confidence_calculated_at"),
            "suggestions": overall.get("improvement_suggestions", [])[:3],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get readiness summary"
        )
