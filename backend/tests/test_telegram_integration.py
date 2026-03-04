"""Integration tests for the full Telegram bot flow."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_bot_admin_auth():
    """Bot should authenticate admin correctly."""
    with patch("src.telegram.bot.settings") as mock_settings:
        mock_settings.TELEGRAM_BOT_TOKEN = "test-token"
        mock_settings.TELEGRAM_ADMIN_CHAT_ID = "12345"

        from src.telegram.bot import is_admin
        assert is_admin(12345) is True
        assert is_admin(99999) is False


@pytest.mark.asyncio
async def test_gtd_store_full_workflow(tmp_path):
    """Full GTD workflow: capture -> organize -> review."""
    from src.telegram.gtd_store import GTDStore

    store = GTDStore(tmp_path)

    # 1. Capture
    store.capture("Buy birthday gift for mom")
    store.capture("Research new CI/CD pipeline")
    store.capture("Call accountant about Q1")
    assert len(store.get_inbox()) == 3

    # 2. Organize (move from inbox to appropriate lists)
    store.add_next_action("Buy birthday gift for mom", context="errands")
    store.add_project("CI/CD Pipeline Upgrade", next_action="Research GitHub Actions vs CircleCI")
    store.add_next_action("Call accountant about Q1", context="calls")

    # 3. Clear inbox items
    store.clear_inbox_item("Buy birthday gift")
    store.clear_inbox_item("Research new CI/CD")
    store.clear_inbox_item("Call accountant")
    assert len(store.get_inbox()) == 0

    # 4. Review
    errands = store.get_next_actions(context="errands")
    calls = store.get_next_actions(context="calls")
    projects = store.get_projects()

    assert len(errands) == 1
    assert len(calls) == 1
    assert len(projects) == 1

    # 5. Complete an action
    store.complete_action("Buy birthday gift for mom")
    errands = store.get_next_actions(context="errands")
    assert errands[0]["done"] is True

    # 6. Review summary
    summary = store.get_review_summary()
    assert "Next Actions" in summary
    assert "Projects" in summary
