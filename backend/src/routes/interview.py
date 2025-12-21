"""
Interview Routes

Routes for the AI-powered interview experience after payment.
This provides a conversational interface to gather detailed business context.
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

logger = logging.getLogger(__name__)

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
) -> tuple[str, List[str], int, bool]:
    """
    Generate an AI-powered response using Claude.
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

    # Build company context
    company_info = ""
    if context.company_profile:
        basics = context.company_profile.get("basics", {})
        company_name = basics.get("name", {}).get("value", "the company")
        industry = context.company_profile.get("industry", {}).get("primary_industry", {}).get("value", "their industry")
        company_info = f"Company: {company_name}, Industry: {industry}"

    # Build conversation history
    messages = []
    for msg in previous_messages[-10:]:  # Last 10 messages for context
        messages.append({
            "role": msg.role if msg.role in ["user", "assistant"] else "user",
            "content": msg.content
        })
    messages.append({"role": "user", "content": user_message})

    # Topics we still need to cover
    all_topic_names = [t["name"] for t in INTERVIEW_TOPICS if t["id"] != "deep_dive"]
    uncovered = [t for t in all_topic_names if t not in topics_covered]

    # Use the centralized interview system prompt with session-specific context
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
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
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
        # Fallback to rule-based
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
    Uses Claude for natural conversation.
    """
    try:
        context = request.context or InterviewContext()
        previous_messages = context.previous_messages or []

        response, topics, progress, is_complete = await generate_ai_response(
            user_message=request.message,
            context=context,
            previous_messages=previous_messages,
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
    Mark the interview as complete and save all data.
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

        # Save interview data
        await supabase.table("quiz_sessions").update({
            "interview_completed": True,
            "interview_data": {
                "messages": request.messages,
                "topics_covered": request.topics_covered,
                "completed_at": datetime.utcnow().isoformat(),
            },
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", request.session_id).execute()

        logger.info(f"Interview completed for session {request.session_id}")

        return {
            "success": True,
            "message": "Interview saved successfully"
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
    voice: str = "aura-asteria-en"


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using Deepgram TTS.
    Returns audio as base64-encoded data.
    """
    import base64

    try:
        audio_data = await transcription_service.text_to_speech(
            request.text,
            request.voice
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
