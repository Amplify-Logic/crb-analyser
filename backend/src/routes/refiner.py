"""
Refiner Routes

API endpoints for report refiner conversations.
"""

import structlog
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.services.report_service import get_report as get_report_by_id
from src.services.refiner_service import RefinerService

logger = structlog.get_logger(__name__)

router = APIRouter()


class SendMessageRequest(BaseModel):
    content: str


class SendMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None


@router.post("/{report_id}/conversations")
async def create_conversation(report_id: str):
    """Start a new conversation for a report."""
    report = await get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    service = RefinerService(report_id=report_id)
    conversation = await service.create_conversation(report_id)

    # Generate starter prompts from report data
    starter_prompts = service.generate_starter_prompts(report)

    return {
        "id": conversation["id"],
        "report_id": report_id,
        "status": conversation["status"],
        "starter_prompts": starter_prompts,
    }


@router.get("/{report_id}/conversations")
async def list_conversations(report_id: str):
    """List all conversations for a report."""
    report = await get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    service = RefinerService(report_id=report_id)
    conversations = await service.get_conversations(report_id)
    return {"conversations": conversations}


@router.get("/{report_id}/conversations/{conversation_id}/messages")
async def get_messages(report_id: str, conversation_id: str):
    """Get message history for a conversation."""
    service = RefinerService(report_id=report_id)
    messages = await service.get_messages(conversation_id)
    return {"messages": messages}


@router.post("/{report_id}/conversations/{conversation_id}/messages")
async def send_message(
    report_id: str,
    conversation_id: str,
    request: SendMessageRequest,
):
    """Send a message and get an AI response."""
    report = await get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    service = RefinerService(report_id=report_id)

    # Get conversation history
    history = await service.get_messages(conversation_id)
    history_for_llm = [{"role": m["role"], "content": m["content"]} for m in history]

    # Save user message
    await service.save_message(conversation_id, "user", request.content)

    # Get AI response
    try:
        result = await service.send_message(report, history_for_llm, request.content)
    except Exception as e:
        logger.error("refiner_send_failed", error=str(e), report_id=report_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate response",
        )

    # Save assistant message
    saved = await service.save_message(
        conversation_id,
        "assistant",
        result["content"],
        model_used=result.get("model_used"),
        tokens_used=result.get("tokens_used"),
    )

    return {
        "id": saved["id"],
        "role": "assistant",
        "content": result["content"],
        "model_used": result.get("model_used"),
        "tokens_used": result.get("tokens_used"),
    }
