"""
Intake Routes

Routes for managing intake questionnaire responses.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from src.config.supabase_client import get_async_supabase
from src.services.transcription_service import transcription_service
from src.config.questionnaire import (
    get_questionnaire,
    get_total_questions,
    get_section_count,
    QUESTIONNAIRE_SECTIONS,
)
from src.middleware.auth import require_workspace, CurrentUser
from src.models.intake import (
    IntakeResponse,
    IntakeUpdate,
    IntakeComplete,
    IntakeWithAudit,
    QuestionnaireResponse,
    IntakeValidationResult,
    IntakeValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/questionnaire", response_model=QuestionnaireResponse)
async def get_questionnaire_structure(
    industry: Optional[str] = None,
):
    """
    Get the questionnaire structure.

    Optionally include industry-specific questions.
    """
    sections = get_questionnaire(industry)

    return QuestionnaireResponse(
        sections=sections,
        total_questions=get_total_questions(industry),
        total_sections=get_section_count(industry),
    )


@router.get("/{audit_id}", response_model=IntakeWithAudit)
async def get_intake(
    audit_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get intake responses for an audit.
    """
    try:
        supabase = await get_async_supabase()

        # Get audit with client info (verifies workspace ownership)
        audit_result = await supabase.table("audits").select(
            "id, title, status, workspace_id, clients(name, industry)"
        ).eq("id", audit_id).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not audit_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        audit = audit_result.data
        client_info = audit.pop("clients", None)

        # Get intake responses
        intake_result = await supabase.table("intake_responses").select("*").eq(
            "audit_id", audit_id
        ).single().execute()

        if not intake_result.data:
            # Create empty intake if doesn't exist
            intake_result = await supabase.table("intake_responses").insert({
                "audit_id": audit_id,
                "is_complete": False,
                "current_section": 1,
                "responses": {},
            }).execute()

        intake_data = intake_result.data
        if isinstance(intake_data, list):
            intake_data = intake_data[0]

        return IntakeWithAudit(
            **intake_data,
            audit_title=audit.get("title"),
            audit_status=audit.get("status"),
            client_name=client_info.get("name") if client_info else None,
            client_industry=client_info.get("industry") if client_info else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get intake error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get intake responses"
        )


@router.patch("/{audit_id}", response_model=IntakeResponse)
async def update_intake(
    audit_id: str,
    request: IntakeUpdate,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Update/save intake responses.

    Supports saving progress - user can leave and resume later.
    """
    try:
        supabase = await get_async_supabase()

        # Verify audit belongs to workspace
        audit_check = await supabase.table("audits").select("id, status").eq(
            "id", audit_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not audit_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        # Can only update intake if audit is in intake status
        if audit_check.data["status"] not in ["intake", "pending"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify intake after submission"
            )

        # Get existing intake
        existing = await supabase.table("intake_responses").select("*").eq(
            "audit_id", audit_id
        ).single().execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intake not found"
            )

        # Merge responses (preserve existing, update new)
        existing_responses = existing.data.get("responses", {})
        if request.responses:
            existing_responses.update(request.responses)

        update_data = {
            "responses": existing_responses,
            "updated_at": datetime.utcnow().isoformat(),
        }

        if request.current_section is not None:
            update_data["current_section"] = request.current_section

        result = await supabase.table("intake_responses").update(
            update_data
        ).eq("audit_id", audit_id).execute()

        logger.info(f"Intake updated: {audit_id} by {current_user.email}")

        return IntakeResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update intake error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update intake"
        )


@router.post("/{audit_id}/validate", response_model=IntakeValidationResult)
async def validate_intake(
    audit_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Validate intake responses before completion.

    Checks all required questions are answered.
    """
    try:
        supabase = await get_async_supabase()

        # Get audit with client for industry-specific validation
        audit_result = await supabase.table("audits").select(
            "id, clients(industry)"
        ).eq("id", audit_id).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not audit_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        client_info = audit_result.data.get("clients", {})
        industry = client_info.get("industry") if client_info else None

        # Get intake responses
        intake_result = await supabase.table("intake_responses").select("*").eq(
            "audit_id", audit_id
        ).single().execute()

        if not intake_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intake not found"
            )

        responses = intake_result.data.get("responses", {})

        # Validate against questionnaire
        errors = []
        missing_required = []
        sections = get_questionnaire(industry)

        for section in sections:
            for question in section["questions"]:
                q_id = question["id"]
                is_required = question.get("required", False)

                if is_required:
                    value = responses.get(q_id)
                    if value is None or value == "" or (isinstance(value, list) and len(value) == 0):
                        missing_required.append(q_id)
                        errors.append(IntakeValidationError(
                            question_id=q_id,
                            message=f"Required question not answered: {question['question'][:50]}..."
                        ))

        return IntakeValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            missing_required=missing_required,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validate intake error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate intake"
        )


@router.post("/{audit_id}/complete", response_model=IntakeResponse)
async def complete_intake(
    audit_id: str,
    request: IntakeComplete,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Mark intake as complete and submit for analysis.

    Validates all required questions, saves final responses,
    and updates audit status to processing.
    """
    try:
        supabase = await get_async_supabase()

        # Get audit
        audit_result = await supabase.table("audits").select(
            "id, status, tier, payment_status, clients(industry)"
        ).eq("id", audit_id).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not audit_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit not found"
            )

        audit = audit_result.data

        # Can only complete intake if in intake status
        if audit["status"] != "intake":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Intake already completed"
            )

        # Check payment status for professional tier
        if audit["tier"] == "professional" and audit["payment_status"] != "paid":
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Payment required before completing intake"
            )

        # Validate responses
        client_info = audit.get("clients", {})
        industry = client_info.get("industry") if client_info else None
        sections = get_questionnaire(industry)

        missing_required = []
        for section in sections:
            for question in section["questions"]:
                q_id = question["id"]
                is_required = question.get("required", False)

                if is_required:
                    value = request.responses.get(q_id)
                    if value is None or value == "" or (isinstance(value, list) and len(value) == 0):
                        missing_required.append(q_id)

        if missing_required:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required answers: {', '.join(missing_required)}"
            )

        # Update intake
        now = datetime.utcnow().isoformat()
        intake_result = await supabase.table("intake_responses").update({
            "responses": request.responses,
            "is_complete": True,
            "completed_at": now,
            "current_section": get_section_count(industry),
            "updated_at": now,
        }).eq("audit_id", audit_id).execute()

        # Update audit status to processing
        await supabase.table("audits").update({
            "status": "processing",
            "current_phase": "discovery",
            "started_at": now,
            "updated_at": now,
        }).eq("id", audit_id).execute()

        # Log activity
        await supabase.table("audit_activity_log").insert({
            "audit_id": audit_id,
            "action": "intake_completed",
            "details": {"responses_count": len(request.responses)},
            "performed_by": current_user.id,
        }).execute()

        logger.info(f"Intake completed: {audit_id} by {current_user.email}")

        return IntakeResponse(**intake_result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete intake error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete intake"
        )


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Transcribe audio to text using Deepgram.

    Accepts audio file (webm, mp3, wav, etc.) and returns transcribed text.
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

        logger.info(f"Audio transcribed for user {current_user.email}: {len(text)} chars")

        return {
            "text": text,
            "confidence": confidence,
        }

    except HTTPException:
        raise
    except ValueError as e:
        # Deepgram API key not configured
        logger.error(f"Transcription config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transcription service not configured"
        )
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcribe audio"
        )
