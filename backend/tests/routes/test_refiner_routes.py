"""Tests for refiner API routes."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


class TestRefinerRoutes:
    """Test refiner conversation endpoints."""

    @pytest.fixture
    def mock_report(self):
        return {
            "id": "report-123",
            "status": "released",
            "quiz_session_id": "quiz-456",
            "executive_summary": {"ai_readiness_score": 55},
            "findings": [{"id": "f-001", "title": "Test Finding", "customer_value_score": 8}],
            "recommendations": [{"id": "rec-001", "title": "Test Rec", "roi_percentage": 150}],
            "value_summary": {},
            "company_name": "Test Co",
        }

    @pytest.mark.asyncio
    async def test_create_conversation_returns_id(self, mock_report):
        """Creating a conversation should return conversation ID."""
        from src.routes.refiner import router
        from fastapi import FastAPI
        from httpx import AsyncClient, ASGITransport

        app = FastAPI()
        app.include_router(router, prefix="/api/reports")

        with patch("src.routes.refiner.get_report_by_id", return_value=mock_report), \
             patch("src.routes.refiner.RefinerService") as MockService:

            mock_service = MockService.return_value
            mock_service.create_conversation = AsyncMock(return_value={
                "id": "conv-789",
                "report_id": "report-123",
                "status": "active",
            })
            mock_service.generate_starter_prompts = MagicMock(return_value=[
                "Why was this scored highest?",
                "Break down the value?",
                "What should I do first?",
            ])

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/api/reports/report-123/conversations")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "conv-789"
            assert len(data["starter_prompts"]) == 3

    @pytest.mark.asyncio
    async def test_send_message_returns_response(self, mock_report):
        """Sending a message should return assistant response."""
        from src.routes.refiner import router
        from fastapi import FastAPI
        from httpx import AsyncClient, ASGITransport

        app = FastAPI()
        app.include_router(router, prefix="/api/reports")

        with patch("src.routes.refiner.get_report_by_id", return_value=mock_report), \
             patch("src.routes.refiner.RefinerService") as MockService:

            mock_service = MockService.return_value
            mock_service.get_messages = AsyncMock(return_value=[])
            mock_service.save_message = AsyncMock(return_value={"id": "msg-1"})
            mock_service.send_message = AsyncMock(return_value={
                "content": "Based on your report...",
                "model_used": "claude-sonnet-4-6",
                "tokens_used": 500,
            })

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/reports/report-123/conversations/conv-789/messages",
                    json={"content": "Why Gorgias?"},
                )

            assert response.status_code == 200
            data = response.json()
            assert "Based on your report" in data["content"]
            assert data["model_used"] == "claude-sonnet-4-6"
