"""
Assumption Validation Routes

This module provides a conversational interface for validating assumptions
before final report generation. Claude asks targeted questions to:

1. Validate high-sensitivity assumptions
2. Gather missing information
3. Correct any incorrect assumptions
4. Ensure analysis is grounded in verified data

This is the "quality gate" between analysis and final report.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import anthropic

from src.config.supabase_client import get_async_supabase
from src.config.settings import settings
from src.config.system_prompt import FOUNDATIONAL_LOGIC
from src.models.assumptions import (
    Assumption,
    AssumptionLog,
    AssumptionStatus,
    AssumptionCategory,
    AssumptionSource,
    STANDARD_ASSUMPTIONS,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Models
# =============================================================================

class ValidationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None


class ValidationContext(BaseModel):
    """Context for the validation session."""
    report_id: str
    quiz_session_id: str
    assumptions: List[Dict[str, Any]] = Field(default_factory=list)
    validated_assumptions: List[str] = Field(default_factory=list)  # IDs of validated
    corrected_values: Dict[str, Any] = Field(default_factory=dict)  # assumption_id -> new value
    messages: List[ValidationMessage] = Field(default_factory=list)
    questions_asked: int = 0
    is_complete: bool = False


class StartValidationRequest(BaseModel):
    quiz_session_id: str
    preliminary_findings: Optional[List[Dict[str, Any]]] = None


class ValidationRespondRequest(BaseModel):
    session_id: str
    message: str
    context: Optional[ValidationContext] = None


class ValidationCompleteRequest(BaseModel):
    session_id: str


# =============================================================================
# System Prompt for Validation
# =============================================================================

VALIDATION_SYSTEM_PROMPT = f"""{FOUNDATIONAL_LOGIC}

═══════════════════════════════════════════════════════════════════════════════
ASSUMPTION VALIDATION SESSION
═══════════════════════════════════════════════════════════════════════════════

You are conducting an assumption validation session before generating a final
CRB analysis report. Your goal is to ensure all assumptions are verified with
the business owner so the final report is grounded in REAL data, not estimates.

YOUR OBJECTIVES:
1. Validate high-sensitivity assumptions first (these affect ROI calculations)
2. Gather specific numbers where we used defaults
3. Correct any assumptions the user identifies as wrong
4. Fill in any gaps in our understanding

CONVERSATION STYLE:
- Be direct and efficient - the user wants to finish and get their report
- Explain WHY you need each piece of information
- Accept approximate answers ("about 5 hours" is fine)
- Group related questions when possible
- Thank them for corrections - it makes the report more accurate

QUESTION PRIORITIES:
1. Financial assumptions (hourly rates, budgets, costs)
2. Time-based assumptions (hours spent on tasks, timelines)
3. Technical assumptions (current tools, integrations)
4. Process assumptions (how they do things now)

WHEN TO CONCLUDE:
- After validating all high-sensitivity assumptions
- When user indicates they want to proceed
- After ~5-8 exchanges maximum

WHAT NOT TO DO:
- Don't make recommendations (that comes in the report)
- Don't overwhelm with too many questions at once
- Don't challenge their answers - accept what they tell you
- Don't ask about things that don't affect the analysis
"""


# =============================================================================
# Routes
# =============================================================================

@router.post("/start")
async def start_validation_session(request: StartValidationRequest):
    """
    Start a new assumption validation session.

    This analyzes the preliminary findings and identifies assumptions
    that need validation before generating the final report.
    """
    supabase = await get_async_supabase()

    # Get the quiz session
    quiz_result = await supabase.table("quiz_sessions").select("*").eq(
        "id", request.quiz_session_id
    ).single().execute()

    if not quiz_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz session not found"
        )

    quiz_data = quiz_result.data

    # Extract assumptions from preliminary analysis
    assumptions = extract_assumptions_from_quiz(quiz_data, request.preliminary_findings)

    # Create validation session
    session_id = str(uuid.uuid4())

    # Generate opening message from Claude
    opening_message = await generate_opening_message(quiz_data, assumptions)

    # Store session
    validation_session = {
        "id": session_id,
        "quiz_session_id": request.quiz_session_id,
        "status": "in_progress",
        "assumptions": [a.model_dump() for a in assumptions],
        "validated_assumptions": [],
        "corrected_values": {},
        "messages": [
            {"role": "assistant", "content": opening_message, "timestamp": datetime.utcnow().isoformat()}
        ],
        "questions_asked": 1,
        "created_at": datetime.utcnow().isoformat(),
    }

    await supabase.table("validation_sessions").insert(validation_session).execute()

    # Update quiz session
    await supabase.table("quiz_sessions").update({
        "validation_session_id": session_id,
        "status": "validating_assumptions"
    }).eq("id", request.quiz_session_id).execute()

    return {
        "session_id": session_id,
        "message": opening_message,
        "assumptions_to_validate": len([a for a in assumptions if a.sensitivity == "high"]),
        "total_assumptions": len(assumptions)
    }


@router.post("/respond")
async def respond_to_validation(request: ValidationRespondRequest):
    """
    Process user response and continue the validation conversation.
    """
    supabase = await get_async_supabase()

    # Get validation session
    session_result = await supabase.table("validation_sessions").select("*").eq(
        "id", request.session_id
    ).single().execute()

    if not session_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validation session not found"
        )

    session = session_result.data

    if session.get("status") == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation session already completed"
        )

    # Get quiz data for context
    quiz_result = await supabase.table("quiz_sessions").select("*").eq(
        "id", session["quiz_session_id"]
    ).single().execute()

    quiz_data = quiz_result.data or {}

    # Build conversation history
    messages = session.get("messages", [])
    messages.append({
        "role": "user",
        "content": request.message,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Parse assumptions
    assumptions = [Assumption(**a) for a in session.get("assumptions", [])]
    validated = session.get("validated_assumptions", [])
    corrected = session.get("corrected_values", {})
    questions_asked = session.get("questions_asked", 0) + 1

    # Generate response
    response_data = await generate_validation_response(
        user_message=request.message,
        messages=messages,
        assumptions=assumptions,
        validated=validated,
        corrected=corrected,
        quiz_data=quiz_data,
        questions_asked=questions_asked
    )

    ai_response = response_data["response"]
    new_validated = response_data["newly_validated"]
    new_corrections = response_data["corrections"]
    should_complete = response_data["should_complete"]

    # Update validated and corrected
    validated.extend(new_validated)
    corrected.update(new_corrections)

    # Add assistant message
    messages.append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Update session
    update_data = {
        "messages": messages,
        "validated_assumptions": validated,
        "corrected_values": corrected,
        "questions_asked": questions_asked,
        "updated_at": datetime.utcnow().isoformat()
    }

    if should_complete:
        update_data["status"] = "completed"
        update_data["completed_at"] = datetime.utcnow().isoformat()

    await supabase.table("validation_sessions").update(update_data).eq(
        "id", request.session_id
    ).execute()

    # Calculate progress
    high_sensitivity = [a for a in assumptions if a.sensitivity == "high"]
    validated_high = [a for a in high_sensitivity if a.id in validated]
    progress = int((len(validated_high) / max(len(high_sensitivity), 1)) * 100)

    return {
        "message": ai_response,
        "is_complete": should_complete,
        "progress": progress,
        "validated_count": len(validated),
        "corrections_count": len(corrected),
        "questions_asked": questions_asked
    }


@router.post("/complete")
async def complete_validation(request: ValidationCompleteRequest):
    """
    Mark validation as complete and proceed to report generation.
    """
    supabase = await get_async_supabase()

    # Get validation session
    session_result = await supabase.table("validation_sessions").select("*").eq(
        "id", request.session_id
    ).single().execute()

    if not session_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validation session not found"
        )

    session = session_result.data

    # Update session status
    await supabase.table("validation_sessions").update({
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat()
    }).eq("id", request.session_id).execute()

    # Update quiz session status
    await supabase.table("quiz_sessions").update({
        "status": "ready_for_report",
        "validated_assumptions": session.get("validated_assumptions", []),
        "corrected_values": session.get("corrected_values", {})
    }).eq("id", session["quiz_session_id"]).execute()

    return {
        "status": "completed",
        "quiz_session_id": session["quiz_session_id"],
        "validated_count": len(session.get("validated_assumptions", [])),
        "corrections_count": len(session.get("corrected_values", {})),
        "ready_for_report": True
    }


@router.get("/{session_id}")
async def get_validation_session(session_id: str):
    """Get the current state of a validation session."""
    supabase = await get_async_supabase()

    result = await supabase.table("validation_sessions").select("*").eq(
        "id", session_id
    ).single().execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validation session not found"
        )

    return result.data


# =============================================================================
# Helper Functions
# =============================================================================

def extract_assumptions_from_quiz(
    quiz_data: Dict[str, Any],
    preliminary_findings: Optional[List[Dict[str, Any]]] = None
) -> List[Assumption]:
    """
    Extract assumptions that need validation from quiz data and findings.
    """
    assumptions = []
    answers = quiz_data.get("answers", {})

    # Standard assumptions that always need validation

    # 1. Hourly rate
    hourly_rate = answers.get("hourly_rate")
    if not hourly_rate:
        assumptions.append(Assumption(
            id="assum-hourly-rate",
            category=AssumptionCategory.FINANCIAL,
            status=AssumptionStatus.PENDING_VALIDATION,
            statement="We're using €50/hour as the hourly labor cost",
            reason="This is used to calculate the value of time saved",
            source=AssumptionSource.DEFAULT_VALUE,
            sensitivity="high",
            validation_question="What's the approximate hourly cost of your team's time (including overhead, benefits, etc.)? A rough estimate is fine.",
            if_wrong="All time-savings calculations would change proportionally",
            impacts=["all-findings"]
        ))

    # 2. Team size
    employee_count = answers.get("employee_count") or answers.get("team_size")
    if not employee_count:
        assumptions.append(Assumption(
            id="assum-team-size",
            category=AssumptionCategory.HUMAN,
            status=AssumptionStatus.PENDING_VALIDATION,
            statement="Team size is unclear - we're estimating based on context",
            reason="Affects which solutions are appropriate and cost calculations",
            source=AssumptionSource.ANALYST_INFERENCE,
            sensitivity="high",
            validation_question="How many people are on your team (full-time equivalent)?",
            if_wrong="Pricing tier recommendations and capacity estimates would be affected",
            impacts=["all-recommendations"]
        ))

    # 3. Hours spent on repetitive tasks
    manual_hours = answers.get("manual_hours") or answers.get("hours_on_repetitive")
    if not manual_hours:
        assumptions.append(Assumption(
            id="assum-manual-hours",
            category=AssumptionCategory.OPERATIONAL,
            status=AssumptionStatus.PENDING_VALIDATION,
            statement="We're estimating 10-15 hours/week on repetitive tasks",
            reason="This is the primary basis for efficiency savings calculations",
            source=AssumptionSource.INDUSTRY_BENCHMARK,
            source_detail="Typical for SMBs in this industry",
            sensitivity="high",
            validation_question="Roughly how many hours per week does your team spend on repetitive, manual tasks that feel like they could be automated?",
            if_wrong="ROI projections could be significantly off",
            impacts=["efficiency-findings", "automation-recommendations"]
        ))

    # 4. Current tech spend
    tech_budget = answers.get("monthly_tech_spend") or answers.get("software_budget")
    if not tech_budget:
        assumptions.append(Assumption(
            id="assum-tech-budget",
            category=AssumptionCategory.FINANCIAL,
            status=AssumptionStatus.PENDING_VALIDATION,
            statement="Current monthly software/tech spend is unclear",
            reason="Helps us recommend appropriately priced solutions",
            source=AssumptionSource.ANALYST_INFERENCE,
            sensitivity="medium",
            validation_question="Roughly how much do you currently spend per month on software and tools?",
            if_wrong="We might recommend solutions outside your budget comfort zone",
            impacts=["pricing-recommendations"]
        ))

    # 5. Revenue/business size (for ROI context)
    revenue = answers.get("annual_revenue") or answers.get("monthly_revenue")
    if not revenue:
        assumptions.append(Assumption(
            id="assum-revenue",
            category=AssumptionCategory.FINANCIAL,
            status=AssumptionStatus.PENDING_VALIDATION,
            statement="We don't have a clear picture of business revenue",
            reason="Important for sizing recommendations appropriately",
            source=AssumptionSource.ANALYST_INFERENCE,
            sensitivity="medium",
            validation_question="What's your approximate annual revenue range? (Even a rough bracket helps - e.g., €100K-500K, €500K-1M, €1M+)",
            if_wrong="Investment recommendations might not be proportional to your business",
            impacts=["investment-sizing"]
        ))

    # 6. Implementation timeline expectations
    timeline = answers.get("timeline") or answers.get("urgency")
    if not timeline:
        assumptions.append(Assumption(
            id="assum-timeline",
            category=AssumptionCategory.TIMELINE,
            status=AssumptionStatus.PENDING_VALIDATION,
            statement="We're assuming a 3-6 month implementation horizon",
            reason="Affects which solutions are realistic to recommend",
            source=AssumptionSource.DEFAULT_VALUE,
            sensitivity="medium",
            validation_question="What's your ideal timeline for implementing improvements? Are you looking for quick wins (weeks) or willing to invest in longer projects (months)?",
            if_wrong="We might recommend solutions that don't fit your timeline",
            impacts=["timeline-recommendations"]
        ))

    # Add assumptions from preliminary findings if provided
    if preliminary_findings:
        for finding in preliminary_findings:
            if finding.get("assumptions"):
                for assumption_data in finding["assumptions"]:
                    if isinstance(assumption_data, dict):
                        try:
                            assumptions.append(Assumption(**assumption_data))
                        except Exception:
                            pass

    return assumptions


async def generate_opening_message(
    quiz_data: Dict[str, Any],
    assumptions: List[Assumption]
) -> str:
    """Generate the opening message for the validation session."""

    company_name = quiz_data.get("answers", {}).get("company_name", "your business")
    high_sensitivity = [a for a in assumptions if a.sensitivity == "high"]

    # Count what we need to validate
    count = len(high_sensitivity)

    if count == 0:
        return f"""Thanks for completing the questionnaire! I have a good understanding of {company_name}.

Before I generate your final report, I just want to quickly confirm a couple of things to make sure the numbers are accurate.

First question: What's the approximate hourly cost of your team's time, including overhead? A rough estimate like "about €40-50/hour" is perfectly fine."""

    # Pick the first high-sensitivity assumption to ask about
    first_assumption = high_sensitivity[0]

    return f"""Thanks for completing the questionnaire! Before I generate your final CRB analysis report, I need to verify a few key assumptions to make sure the numbers are accurate for {company_name}.

I have about {count} important questions - this should only take 2-3 minutes.

Let's start: {first_assumption.validation_question}"""


async def generate_validation_response(
    user_message: str,
    messages: List[Dict[str, Any]],
    assumptions: List[Assumption],
    validated: List[str],
    corrected: Dict[str, Any],
    quiz_data: Dict[str, Any],
    questions_asked: int
) -> Dict[str, Any]:
    """
    Generate Claude's response in the validation conversation.

    Returns dict with:
    - response: The AI message
    - newly_validated: List of assumption IDs validated in this exchange
    - corrections: Dict of corrections made
    - should_complete: Whether validation should end
    """

    # Find unvalidated high-sensitivity assumptions
    unvalidated_high = [
        a for a in assumptions
        if a.sensitivity == "high" and a.id not in validated
    ]

    unvalidated_medium = [
        a for a in assumptions
        if a.sensitivity == "medium" and a.id not in validated
    ]

    # Build context for Claude
    company_name = quiz_data.get("answers", {}).get("company_name", "the business")

    assumption_context = "\n".join([
        f"- {a.id}: {a.statement} (sensitivity: {a.sensitivity})"
        for a in assumptions
    ])

    validated_context = f"Already validated: {', '.join(validated)}" if validated else "No assumptions validated yet"

    remaining_high = len(unvalidated_high)
    remaining_medium = len(unvalidated_medium)

    context_prompt = f"""
CURRENT VALIDATION STATE:
- Company: {company_name}
- Questions asked so far: {questions_asked}
- Remaining high-sensitivity assumptions: {remaining_high}
- Remaining medium-sensitivity assumptions: {remaining_medium}
- {validated_context}
- Corrections made: {json.dumps(corrected) if corrected else "None"}

ALL ASSUMPTIONS TO VALIDATE:
{assumption_context}

INSTRUCTIONS:
1. Parse what the user said and identify if it validates/corrects any assumptions
2. Thank them briefly for the info
3. If there are more high-sensitivity assumptions, ask the next one
4. If all high-sensitivity are done, ask if they want to validate medium ones or proceed
5. If user says "done" or "proceed" or similar, wrap up

After {8} total questions, suggest wrapping up unless they want to continue.

Respond naturally - you're having a conversation, not interrogating them.
"""

    # Build messages for Claude
    claude_messages = []
    for msg in messages[-10:]:  # Last 10 messages
        claude_messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            system=VALIDATION_SYSTEM_PROMPT + context_prompt,
            messages=claude_messages
        )
        ai_response = response.content[0].text

    except Exception as e:
        logger.error(f"Claude API error in validation: {e}")
        # Fallback response
        if unvalidated_high:
            next_q = unvalidated_high[0]
            ai_response = f"Thanks for that. Next question: {next_q.validation_question}"
        else:
            ai_response = "Thanks! I think I have what I need. Ready to generate your report?"

    # Determine what was validated (simple heuristic - in production would be more sophisticated)
    newly_validated = []
    corrections = {}

    # Check if user provided numerical info that matches an assumption
    user_lower = user_message.lower()

    # Look for hour mentions
    if any(word in user_lower for word in ["hour", "€", "$", "euro", "dollar", "weekly", "monthly"]):
        # Try to find which assumption this validates
        for a in unvalidated_high + unvalidated_medium:
            if "hourly" in a.statement.lower() and ("hour" in user_lower or "€" in user_lower):
                newly_validated.append(a.id)
                # Extract value if possible (simplified)
                import re
                numbers = re.findall(r'[\d,]+(?:\.\d+)?', user_message)
                if numbers:
                    corrections[a.id] = numbers[0]
                break
            elif "team" in a.statement.lower() and any(w in user_lower for w in ["people", "team", "employees", "person"]):
                newly_validated.append(a.id)
                numbers = re.findall(r'\d+', user_message)
                if numbers:
                    corrections[a.id] = numbers[0]
                break
            elif "hours" in a.validation_question.lower() and "hour" in user_lower:
                newly_validated.append(a.id)
                numbers = re.findall(r'\d+', user_message)
                if numbers:
                    corrections[a.id] = numbers[0]
                break

    # Check for completion signals
    should_complete = False
    completion_signals = ["done", "proceed", "continue", "that's all", "let's go", "generate", "ready", "finish"]
    if any(signal in user_lower for signal in completion_signals):
        should_complete = True

    # Also complete if we've asked enough questions and covered high-sensitivity
    if questions_asked >= 8 and remaining_high <= 1:
        should_complete = True

    # Or if all high-sensitivity validated
    if remaining_high == 0 and remaining_medium == 0:
        should_complete = True

    return {
        "response": ai_response,
        "newly_validated": newly_validated,
        "corrections": corrections,
        "should_complete": should_complete
    }
