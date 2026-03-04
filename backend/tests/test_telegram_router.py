"""Tests for Telegram intent router."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_router_classifies_crb_query():
    """Data queries about the business should route to 'query'."""
    from src.telegram.router import classify_intent

    with patch("src.telegram.router._call_classifier") as mock_llm:
        mock_llm.return_value = "query"
        result = await classify_intent("How many reports did we do this week?")
        assert result == "query"


@pytest.mark.asyncio
async def test_router_classifies_idea():
    """Idea-like messages should route to 'idea'."""
    from src.telegram.router import classify_intent

    with patch("src.telegram.router._call_classifier") as mock_llm:
        mock_llm.return_value = "idea"
        result = await classify_intent("What if we added a benchmarking tool for dental?")
        assert result == "idea"


@pytest.mark.asyncio
async def test_router_classifies_code_task():
    """Development tasks should route to 'code'."""
    from src.telegram.router import classify_intent

    with patch("src.telegram.router._call_classifier") as mock_llm:
        mock_llm.return_value = "code"
        result = await classify_intent("Add error handling to the quiz endpoint")
        assert result == "code"


@pytest.mark.asyncio
async def test_router_classifies_gtd():
    """Task management should route to 'gtd'."""
    from src.telegram.router import classify_intent

    with patch("src.telegram.router._call_classifier") as mock_llm:
        mock_llm.return_value = "gtd"
        result = await classify_intent("Remind me to call the accountant on Monday")
        assert result == "gtd"
