"""Tests for RefinerService context building."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.services.refiner_service import RefinerService


class TestBuildSystemPrompt:
    """Test system prompt construction from report data."""

    def test_includes_company_name(self):
        service = RefinerService(report_id="test-123")
        report_data = {
            "company_name": "Acme Store",
            "executive_summary": {"ai_readiness_score": 55},
            "findings": [],
            "recommendations": [],
        }
        prompt = service.build_system_prompt(report_data)
        assert "Acme Store" in prompt

    def test_includes_findings_summary(self):
        service = RefinerService(report_id="test-123")
        report_data = {
            "company_name": "Acme Store",
            "executive_summary": {"ai_readiness_score": 55},
            "findings": [
                {"id": "f-001", "title": "Customer Support Automation", "customer_value_score": 9},
                {"id": "f-002", "title": "Inventory Forecasting", "customer_value_score": 7},
            ],
            "recommendations": [],
        }
        prompt = service.build_system_prompt(report_data)
        assert "Customer Support Automation" in prompt
        assert "Inventory Forecasting" in prompt

    def test_includes_recommendations(self):
        service = RefinerService(report_id="test-123")
        report_data = {
            "company_name": "Acme Store",
            "executive_summary": {},
            "findings": [],
            "recommendations": [
                {"id": "rec-001", "title": "Implement Gorgias", "roi_percentage": 180},
            ],
        }
        prompt = service.build_system_prompt(report_data)
        assert "Gorgias" in prompt
        assert "180" in prompt

    def test_includes_behavioral_rules(self):
        service = RefinerService(report_id="test-123")
        report_data = {
            "company_name": "Test",
            "executive_summary": {},
            "findings": [],
            "recommendations": [],
        }
        prompt = service.build_system_prompt(report_data)
        assert "never apologize for the report" in prompt.lower() or "you authored this report" in prompt.lower()


class TestBuildMessages:
    """Test message history construction for Claude API."""

    def test_empty_history(self):
        service = RefinerService(report_id="test-123")
        messages = service.build_messages([], "Hello")
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"

    def test_includes_history(self):
        service = RefinerService(report_id="test-123")
        history = [
            {"role": "user", "content": "Why Gorgias?"},
            {"role": "assistant", "content": "Based on your support volume..."},
        ]
        messages = service.build_messages(history, "Tell me more")
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[2]["content"] == "Tell me more"


class TestGenerateStarterPrompts:
    """Test dynamic starter prompt generation."""

    def test_returns_three_prompts(self):
        service = RefinerService(report_id="test-123")
        report_data = {
            "findings": [
                {"id": "f-001", "title": "Customer Support Automation", "customer_value_score": 9},
            ],
            "recommendations": [
                {"id": "rec-001", "title": "Implement Gorgias", "roi_percentage": 180},
            ],
            "value_summary": {"total_value_min": 100000, "total_value_max": 200000},
            "executive_summary": {"ai_readiness_score": 55},
        }
        prompts = service.generate_starter_prompts(report_data)
        assert len(prompts) == 3
        assert all(isinstance(p, str) for p in prompts)
        assert all(p.endswith("?") for p in prompts)
