"""Tests for GTD task management."""
import pytest
from pathlib import Path


@pytest.fixture
def gtd_dir(tmp_path):
    """Create a temporary GTD directory."""
    return tmp_path


@pytest.mark.asyncio
async def test_capture_adds_to_inbox(gtd_dir):
    """Capturing an item should add it to inbox.md."""
    from src.telegram.gtd_store import GTDStore

    store = GTDStore(gtd_dir)
    store.capture("Call the accountant about Q1 taxes")

    inbox = (gtd_dir / "inbox.md").read_text()
    assert "Call the accountant about Q1 taxes" in inbox


@pytest.mark.asyncio
async def test_capture_multiple_items(gtd_dir):
    """Multiple captures should all appear in inbox."""
    from src.telegram.gtd_store import GTDStore

    store = GTDStore(gtd_dir)
    store.capture("Buy groceries")
    store.capture("Email client proposal")

    inbox = (gtd_dir / "inbox.md").read_text()
    assert "Buy groceries" in inbox
    assert "Email client proposal" in inbox


@pytest.mark.asyncio
async def test_add_next_action(gtd_dir):
    """Adding a next action should file it under the right context."""
    from src.telegram.gtd_store import GTDStore

    store = GTDStore(gtd_dir)
    store.add_next_action("Call dentist", context="calls")

    actions = store.get_next_actions()
    assert any("Call dentist" in a["text"] for a in actions)


@pytest.mark.asyncio
async def test_add_project(gtd_dir):
    """Adding a project should create it in projects.md."""
    from src.telegram.gtd_store import GTDStore

    store = GTDStore(gtd_dir)
    store.add_project("Launch Telegram bot", next_action="Set up bot token")

    projects = store.get_projects()
    assert any("Launch Telegram bot" in p["name"] for p in projects)


@pytest.mark.asyncio
async def test_get_next_actions_by_context(gtd_dir):
    """Should filter next actions by context."""
    from src.telegram.gtd_store import GTDStore

    store = GTDStore(gtd_dir)
    store.add_next_action("Call dentist", context="calls")
    store.add_next_action("Buy milk", context="errands")
    store.add_next_action("Call accountant", context="calls")

    calls = store.get_next_actions(context="calls")
    assert len(calls) == 2
    assert all("Call" in a["text"] for a in calls)
