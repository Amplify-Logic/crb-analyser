"""Tests for Claude Code bridge handler — streaming, task tracking, safety."""
import asyncio
import json
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


# --- Task 1: Stream JSON parsing ---


class TestStreamJsonParser:
    """Test parsing of Claude Code stream-json output."""

    def test_parse_assistant_text_event(self):
        """Assistant text events should extract the message content."""
        from src.telegram.handlers.claude_code_handler import parse_stream_event

        event = {
            "type": "assistant",
            "message": {
                "content": [{"type": "text", "text": "I'll fix the bug now."}]
            },
        }
        result = parse_stream_event(event)
        assert result is not None
        assert result["type"] == "text"
        assert "fix the bug" in result["content"]

    def test_parse_tool_use_event(self):
        """Tool use events should extract tool name and target."""
        from src.telegram.handlers.claude_code_handler import parse_stream_event

        event = {
            "type": "tool_use",
            "tool": "Read",
            "input": {"file_path": "/app/backend/src/routes/quiz.py"},
        }
        result = parse_stream_event(event)
        assert result is not None
        assert result["type"] == "tool_use"
        assert result["tool"] == "Read"
        assert "quiz.py" in result["summary"]

    def test_parse_tool_use_bash_event(self):
        """Bash tool use should show the command."""
        from src.telegram.handlers.claude_code_handler import parse_stream_event

        event = {
            "type": "tool_use",
            "tool": "Bash",
            "input": {"command": "pytest -v tests/"},
        }
        result = parse_stream_event(event)
        assert result is not None
        assert result["type"] == "tool_use"
        assert "pytest" in result["summary"]

    def test_parse_tool_use_edit_event(self):
        """Edit tool use should show the file being edited."""
        from src.telegram.handlers.claude_code_handler import parse_stream_event

        event = {
            "type": "tool_use",
            "tool": "Edit",
            "input": {"file_path": "/app/backend/src/main.py"},
        }
        result = parse_stream_event(event)
        assert result is not None
        assert "main.py" in result["summary"]

    def test_parse_result_event(self):
        """Result events should extract the final output."""
        from src.telegram.handlers.claude_code_handler import parse_stream_event

        event = {
            "type": "result",
            "result": "Fixed the validation bug. All 47 tests pass.",
            "cost_usd": 0.12,
            "duration_ms": 45000,
        }
        result = parse_stream_event(event)
        assert result is not None
        assert result["type"] == "result"
        assert "47 tests pass" in result["content"]

    def test_parse_unknown_event_returns_none(self):
        """Unknown event types should return None (skip)."""
        from src.telegram.handlers.claude_code_handler import parse_stream_event

        event = {"type": "system", "data": "something"}
        result = parse_stream_event(event)
        assert result is None

    def test_parse_malformed_event_returns_none(self):
        """Malformed events should return None, not crash."""
        from src.telegram.handlers.claude_code_handler import parse_stream_event

        result = parse_stream_event({})
        assert result is None

        result = parse_stream_event({"type": "assistant"})
        assert result is None


class TestProgressThrottling:
    """Test that Telegram updates are throttled to avoid rate limits."""

    def test_throttle_allows_first_message(self):
        """First message should always be allowed through."""
        from src.telegram.handlers.claude_code_handler import ProgressThrottle

        throttle = ProgressThrottle(min_interval_seconds=5)
        assert throttle.should_send() is True

    def test_throttle_blocks_rapid_messages(self):
        """Messages sent within the interval should be blocked."""
        from src.telegram.handlers.claude_code_handler import ProgressThrottle

        throttle = ProgressThrottle(min_interval_seconds=5)
        throttle.should_send()  # first — allowed
        assert throttle.should_send() is False  # too soon

    def test_throttle_allows_after_interval(self):
        """Messages after the interval has passed should be allowed."""
        from src.telegram.handlers.claude_code_handler import ProgressThrottle

        throttle = ProgressThrottle(min_interval_seconds=0)  # zero interval
        throttle.should_send()
        assert throttle.should_send() is True  # interval is 0, always passes

    def test_throttle_always_allows_result(self):
        """Result events should bypass throttling."""
        from src.telegram.handlers.claude_code_handler import ProgressThrottle

        throttle = ProgressThrottle(min_interval_seconds=999)
        throttle.should_send()  # first
        assert throttle.should_send(force=True) is True  # forced


class TestBuildCommand:
    """Test command construction for Claude Code subprocess."""

    def test_build_command_agentic_mode(self):
        """Command should use stream-json, no --print, higher max-turns."""
        from src.telegram.handlers.claude_code_handler import build_claude_command

        cmd = build_claude_command("fix the bug")
        assert "--print" not in cmd
        assert "--output-format" in cmd
        idx = cmd.index("--output-format")
        assert cmd[idx + 1] == "stream-json"
        assert "--max-turns" in cmd
        # Max turns should be >= 25
        turns_idx = cmd.index("--max-turns")
        assert int(cmd[turns_idx + 1]) >= 25

    def test_build_command_includes_task_prompt(self):
        """The task description should be the last argument."""
        from src.telegram.handlers.claude_code_handler import build_claude_command

        cmd = build_claude_command("add tests for quiz")
        assert cmd[-1] == "add tests for quiz"

    def test_build_command_strips_claudecode_env(self):
        """Subprocess env should not include CLAUDECODE."""
        from src.telegram.handlers.claude_code_handler import build_subprocess_env

        with patch.dict("os.environ", {"CLAUDECODE": "1", "HOME": "/tmp"}):
            env = build_subprocess_env()
            assert "CLAUDECODE" not in env
            assert "HOME" in env


# --- Task 3: Background execution with task tracking ---


class TestTaskTracker:
    """Test the background task tracking system."""

    def test_create_task_returns_id(self):
        """Creating a task should return a unique task ID."""
        from src.telegram.handlers.claude_code_handler import TaskTracker

        tracker = TaskTracker()
        task_id = tracker.create_task("fix the bug", chat_id=12345)
        assert task_id is not None
        assert isinstance(task_id, str)
        assert len(task_id) > 0

    def test_create_multiple_tasks_unique_ids(self):
        """Each task should get a unique ID."""
        from src.telegram.handlers.claude_code_handler import TaskTracker

        tracker = TaskTracker()
        id1 = tracker.create_task("task one", chat_id=12345)
        id2 = tracker.create_task("task two", chat_id=12345)
        assert id1 != id2

    def test_get_task_info(self):
        """Should retrieve task info by ID."""
        from src.telegram.handlers.claude_code_handler import TaskTracker

        tracker = TaskTracker()
        task_id = tracker.create_task("fix the bug", chat_id=12345)
        info = tracker.get_task(task_id)
        assert info is not None
        assert info["description"] == "fix the bug"
        assert info["chat_id"] == 12345
        assert info["status"] == "running"

    def test_get_nonexistent_task_returns_none(self):
        """Getting a non-existent task should return None."""
        from src.telegram.handlers.claude_code_handler import TaskTracker

        tracker = TaskTracker()
        assert tracker.get_task("nonexistent") is None

    def test_complete_task(self):
        """Marking a task complete should update its status."""
        from src.telegram.handlers.claude_code_handler import TaskTracker

        tracker = TaskTracker()
        task_id = tracker.create_task("fix it", chat_id=12345)
        tracker.complete_task(task_id, result="Done. 47 tests pass.")
        info = tracker.get_task(task_id)
        assert info["status"] == "completed"
        assert info["result"] == "Done. 47 tests pass."

    def test_fail_task(self):
        """Marking a task as failed should update its status."""
        from src.telegram.handlers.claude_code_handler import TaskTracker

        tracker = TaskTracker()
        task_id = tracker.create_task("fix it", chat_id=12345)
        tracker.fail_task(task_id, error="Timed out")
        info = tracker.get_task(task_id)
        assert info["status"] == "failed"
        assert info["error"] == "Timed out"

    def test_list_active_tasks(self):
        """Should list only running tasks."""
        from src.telegram.handlers.claude_code_handler import TaskTracker

        tracker = TaskTracker()
        id1 = tracker.create_task("task one", chat_id=12345)
        id2 = tracker.create_task("task two", chat_id=12345)
        tracker.complete_task(id1, result="done")
        active = tracker.list_active()
        assert len(active) == 1
        assert active[0]["task_id"] == id2

    def test_list_recent_tasks(self):
        """Should list recent tasks including completed ones."""
        from src.telegram.handlers.claude_code_handler import TaskTracker

        tracker = TaskTracker()
        id1 = tracker.create_task("task one", chat_id=12345)
        id2 = tracker.create_task("task two", chat_id=12345)
        tracker.complete_task(id1, result="done")
        recent = tracker.list_recent(limit=10)
        assert len(recent) == 2

    def test_cancel_task(self):
        """Cancelling a task should mark it as cancelled."""
        from src.telegram.handlers.claude_code_handler import TaskTracker

        tracker = TaskTracker()
        task_id = tracker.create_task("task one", chat_id=12345)
        tracker.cancel_task(task_id)
        info = tracker.get_task(task_id)
        assert info["status"] == "cancelled"

    def test_active_count(self):
        """Should count only running tasks."""
        from src.telegram.handlers.claude_code_handler import TaskTracker

        tracker = TaskTracker()
        tracker.create_task("one", chat_id=12345)
        tracker.create_task("two", chat_id=12345)
        assert tracker.active_count() == 2
        tracker.complete_task(tracker.list_active()[0]["task_id"], result="done")
        assert tracker.active_count() == 1


# --- Task 5: Smart output formatting ---


class TestOutputFormatter:
    """Test formatting Claude Code output for Telegram."""

    def test_format_task_summary_with_files_changed(self):
        """Summary should list files that were edited/written."""
        from src.telegram.handlers.claude_code_handler import format_task_summary

        progress = [
            {"type": "tool_use", "tool": "Read", "summary": "Reading quiz.py"},
            {"type": "tool_use", "tool": "Edit", "summary": "Editing quiz.py"},
            {"type": "tool_use", "tool": "Bash", "summary": "Running: pytest -v"},
            {"type": "tool_use", "tool": "Edit", "summary": "Editing main.py"},
        ]
        result_text = "Fixed the bug. All tests pass."
        summary = format_task_summary(progress, result_text)
        assert "quiz.py" in summary
        assert "main.py" in summary
        assert "Fixed the bug" in summary

    def test_format_task_summary_with_test_results(self):
        """Summary should highlight test results if present."""
        from src.telegram.handlers.claude_code_handler import format_task_summary

        progress = [
            {"type": "tool_use", "tool": "Bash", "summary": "Running: pytest -v tests/"},
        ]
        result_text = "All 47 tests passed."
        summary = format_task_summary(progress, result_text)
        assert "47 tests" in summary

    def test_format_task_summary_empty_progress(self):
        """Should handle empty progress gracefully."""
        from src.telegram.handlers.claude_code_handler import format_task_summary

        summary = format_task_summary([], "Done.")
        assert "Done." in summary

    def test_format_task_summary_truncates_long_result(self):
        """Long results should be truncated for Telegram."""
        from src.telegram.handlers.claude_code_handler import format_task_summary

        long_result = "x" * 5000
        summary = format_task_summary([], long_result)
        assert len(summary) <= 4000

    def test_format_progress_line_tool_use(self):
        """Tool use progress should format as arrow + summary."""
        from src.telegram.handlers.claude_code_handler import format_progress_line

        line = format_progress_line({"type": "tool_use", "tool": "Edit", "summary": "Editing quiz.py"})
        assert "Editing quiz.py" in line


# --- Task 7: Safety rails ---


class TestSafetyRails:
    """Test dangerous command detection and rate limiting."""

    def test_blocks_rm_rf(self):
        """Should detect rm -rf as dangerous."""
        from src.telegram.handlers.claude_code_handler import check_safety

        result = check_safety("rm -rf /")
        assert result.is_blocked
        assert "dangerous" in result.reason.lower() or "blocked" in result.reason.lower()

    def test_blocks_force_push(self):
        """Should detect git push --force as dangerous."""
        from src.telegram.handlers.claude_code_handler import check_safety

        result = check_safety("git push --force origin main")
        assert result.is_blocked

    def test_blocks_drop_table(self):
        """Should detect DROP TABLE as dangerous."""
        from src.telegram.handlers.claude_code_handler import check_safety

        result = check_safety("run DROP TABLE users")
        assert result.is_blocked

    def test_blocks_no_verify(self):
        """Should detect --no-verify as dangerous."""
        from src.telegram.handlers.claude_code_handler import check_safety

        result = check_safety("commit with --no-verify")
        assert result.is_blocked

    def test_allows_normal_task(self):
        """Normal tasks should pass safety check."""
        from src.telegram.handlers.claude_code_handler import check_safety

        result = check_safety("fix the quiz validation bug")
        assert not result.is_blocked

    def test_allows_test_commands(self):
        """Running tests should be allowed."""
        from src.telegram.handlers.claude_code_handler import check_safety

        result = check_safety("run pytest on the backend")
        assert not result.is_blocked

    def test_case_insensitive_detection(self):
        """Blocklist should be case-insensitive."""
        from src.telegram.handlers.claude_code_handler import check_safety

        result = check_safety("DROP table users")
        assert result.is_blocked

    def test_blocks_env_file_access(self):
        """Should block tasks that explicitly target .env files."""
        from src.telegram.handlers.claude_code_handler import check_safety

        result = check_safety("cat .env and show me the secrets")
        assert result.is_blocked


class TestRateLimiter:
    """Test rate limiting for Claude Code tasks."""

    def test_allows_first_task(self):
        """First task should always be allowed."""
        from src.telegram.handlers.claude_code_handler import RateLimiter

        limiter = RateLimiter(max_per_hour=10)
        assert limiter.is_allowed() is True

    def test_blocks_after_limit(self):
        """Should block after max tasks per hour."""
        from src.telegram.handlers.claude_code_handler import RateLimiter

        limiter = RateLimiter(max_per_hour=3)
        limiter.record()
        limiter.record()
        limiter.record()
        assert limiter.is_allowed() is False

    def test_allows_after_window_expires(self):
        """Should allow again once old entries expire."""
        from src.telegram.handlers.claude_code_handler import RateLimiter

        limiter = RateLimiter(max_per_hour=1)
        # Manually inject an old timestamp
        limiter._timestamps.append(time.monotonic() - 3700)
        assert limiter.is_allowed() is True

    def test_remaining_count(self):
        """Should report how many tasks remain."""
        from src.telegram.handlers.claude_code_handler import RateLimiter

        limiter = RateLimiter(max_per_hour=5)
        limiter.record()
        limiter.record()
        assert limiter.remaining() == 3


# --- Task 4: Session memory ---


class TestSessionManager:
    """Test session tracking for Claude Code conversations."""

    def test_get_session_returns_none_initially(self):
        """No session should exist for a new chat."""
        from src.telegram.handlers.claude_code_handler import SessionManager

        mgr = SessionManager()
        assert mgr.get_session_id(chat_id=12345) is None

    def test_save_and_retrieve_session(self):
        """Saving a session ID should make it retrievable."""
        from src.telegram.handlers.claude_code_handler import SessionManager

        mgr = SessionManager()
        mgr.save_session(chat_id=12345, session_id="sess-abc-123")
        assert mgr.get_session_id(chat_id=12345) == "sess-abc-123"

    def test_clear_session(self):
        """Clearing should remove the session for that chat."""
        from src.telegram.handlers.claude_code_handler import SessionManager

        mgr = SessionManager()
        mgr.save_session(chat_id=12345, session_id="sess-abc-123")
        mgr.clear_session(chat_id=12345)
        assert mgr.get_session_id(chat_id=12345) is None

    def test_separate_sessions_per_chat(self):
        """Different chats should have independent sessions."""
        from src.telegram.handlers.claude_code_handler import SessionManager

        mgr = SessionManager()
        mgr.save_session(chat_id=111, session_id="sess-aaa")
        mgr.save_session(chat_id=222, session_id="sess-bbb")
        assert mgr.get_session_id(chat_id=111) == "sess-aaa"
        assert mgr.get_session_id(chat_id=222) == "sess-bbb"

    def test_build_command_with_resume(self):
        """Command should include --resume when session ID is provided."""
        from src.telegram.handlers.claude_code_handler import build_claude_command

        cmd = build_claude_command("fix the bug", session_id="sess-abc-123")
        assert "--resume" in cmd
        idx = cmd.index("--resume")
        assert cmd[idx + 1] == "sess-abc-123"

    def test_build_command_without_resume(self):
        """Command should NOT include --resume when no session ID."""
        from src.telegram.handlers.claude_code_handler import build_claude_command

        cmd = build_claude_command("fix the bug")
        assert "--resume" not in cmd


# --- Task 6: Voice-to-code pipeline ---


class TestVoiceToCode:
    """Test that voice messages with code intent route to Claude Code."""

    @pytest.mark.asyncio
    async def test_code_intent_calls_bridge(self):
        """Voice text classified as 'code' should invoke the Claude Code bridge."""
        from src.telegram.handlers.message_handler import _handle_code

        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_chat = MagicMock()
        update.effective_chat.id = 12345

        # _handle_code should no longer be a stub
        with patch(
            "src.telegram.handlers.message_handler._launch_code_task",
        ) as mock_launch:
            mock_launch.return_value = None
            await _handle_code(update, "fix the quiz validation bug")
            mock_launch.assert_called_once()

    @pytest.mark.asyncio
    async def test_code_intent_passes_text_as_task(self):
        """The voice transcription text should become the code task description."""
        from src.telegram.handlers.message_handler import _handle_code

        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_chat = MagicMock()
        update.effective_chat.id = 12345

        with patch(
            "src.telegram.handlers.message_handler._launch_code_task",
        ) as mock_launch:
            mock_launch.return_value = None
            await _handle_code(update, "add error handling to the quiz endpoint")
            args = mock_launch.call_args
            assert "add error handling" in args[0][1]  # second positional arg = text
