"""
Claude Code Bridge Handler

Bridges Telegram messages to Claude Code CLI subprocess.
Full agentic mode with streaming progress, background execution, and safety rails.
"""

import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from telegram import Update
from telegram.ext import ContextTypes

from src.telegram.bot import admin_guard

logger = logging.getLogger(__name__)

# Session tracking (simple in-memory for now)
_sessions: dict[str, dict] = {}

# Default timeout for Claude Code subprocess (15 minutes)
DEFAULT_TIMEOUT = 900
DEFAULT_MAX_TURNS = 25
MAX_CONCURRENT_TASKS = 3
MAX_TASKS_PER_HOUR = 10

# Patterns that indicate dangerous operations
BLOCKED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"rm\s+(-\w*)?r\w*f", re.IGNORECASE),  # rm -rf variants
    re.compile(r"git\s+push\s+--force", re.IGNORECASE),
    re.compile(r"git\s+push\s+-f\b", re.IGNORECASE),
    re.compile(r"drop\s+table", re.IGNORECASE),
    re.compile(r"drop\s+database", re.IGNORECASE),
    re.compile(r"--no-verify", re.IGNORECASE),
    re.compile(r"git\s+reset\s+--hard", re.IGNORECASE),
    re.compile(r"cat\s+\.env\b", re.IGNORECASE),
    re.compile(r"\.env\s.*secret", re.IGNORECASE),
    re.compile(r"truncate\s+table", re.IGNORECASE),
]


@dataclass
class SafetyResult:
    """Result of a safety check on a task description."""

    is_blocked: bool
    reason: str


def check_safety(task: str) -> SafetyResult:
    """Check if a task description contains dangerous patterns."""
    for pattern in BLOCKED_PATTERNS:
        if pattern.search(task):
            return SafetyResult(
                is_blocked=True,
                reason=f"Blocked — dangerous pattern detected: {pattern.pattern}",
            )
    return SafetyResult(is_blocked=False, reason="")


class RateLimiter:
    """Simple sliding-window rate limiter."""

    def __init__(self, max_per_hour: int = MAX_TASKS_PER_HOUR) -> None:
        self.max_per_hour = max_per_hour
        self._timestamps: list[float] = []

    def _prune(self) -> None:
        """Remove entries older than 1 hour."""
        cutoff = time.monotonic() - 3600
        self._timestamps = [t for t in self._timestamps if t > cutoff]

    def is_allowed(self) -> bool:
        """Check if another task is allowed within the rate limit."""
        self._prune()
        return len(self._timestamps) < self.max_per_hour

    def record(self) -> None:
        """Record a new task execution."""
        self._timestamps.append(time.monotonic())

    def remaining(self) -> int:
        """How many tasks can still be executed this hour."""
        self._prune()
        return max(0, self.max_per_hour - len(self._timestamps))


class SessionManager:
    """Track Claude Code session IDs per Telegram chat for conversation continuity."""

    def __init__(self) -> None:
        self._sessions: dict[int, str] = {}

    def get_session_id(self, chat_id: int) -> Optional[str]:
        """Get the active session ID for a chat, or None."""
        return self._sessions.get(chat_id)

    def save_session(self, chat_id: int, session_id: str) -> None:
        """Save a session ID for a chat."""
        self._sessions[chat_id] = session_id

    def clear_session(self, chat_id: int) -> None:
        """Clear the session for a chat (start fresh)."""
        self._sessions.pop(chat_id, None)


# Global instances
rate_limiter = RateLimiter()
session_manager = SessionManager()


class ProgressThrottle:
    """Throttle Telegram progress messages to avoid rate limits."""

    def __init__(self, min_interval_seconds: float = 5.0) -> None:
        self.min_interval = min_interval_seconds
        self._last_sent: float = 0.0

    def should_send(self, force: bool = False) -> bool:
        """Check if enough time has passed to send another update."""
        now = time.monotonic()
        if force or (now - self._last_sent) >= self.min_interval:
            self._last_sent = now
            return True
        return False


class TaskTracker:
    """Track background Claude Code tasks."""

    def __init__(self) -> None:
        self._tasks: dict[str, dict[str, Any]] = {}
        self._counter: int = 0
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    def create_task(self, description: str, chat_id: int) -> str:
        """Create a new task and return its ID."""
        self._counter += 1
        task_id = str(self._counter)
        self._tasks[task_id] = {
            "task_id": task_id,
            "description": description,
            "chat_id": chat_id,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "result": None,
            "error": None,
        }
        return task_id

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        """Get task info by ID."""
        return self._tasks.get(task_id)

    def complete_task(self, task_id: str, result: str) -> None:
        """Mark a task as completed."""
        if task_id in self._tasks:
            self._tasks[task_id]["status"] = "completed"
            self._tasks[task_id]["result"] = result
            self._tasks[task_id]["completed_at"] = datetime.now(
                timezone.utc
            ).isoformat()

    def fail_task(self, task_id: str, error: str) -> None:
        """Mark a task as failed."""
        if task_id in self._tasks:
            self._tasks[task_id]["status"] = "failed"
            self._tasks[task_id]["error"] = error

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task. Returns True if cancelled."""
        if task_id not in self._tasks:
            return False
        if self._tasks[task_id]["status"] != "running":
            return False
        self._tasks[task_id]["status"] = "cancelled"
        # Kill the subprocess if tracked
        process = self._processes.pop(task_id, None)
        if process:
            process.kill()
        return True

    def set_process(self, task_id: str, process: asyncio.subprocess.Process) -> None:
        """Associate a subprocess with a task for cancellation."""
        self._processes[task_id] = process

    def list_active(self) -> list[dict[str, Any]]:
        """List running tasks."""
        return [t for t in self._tasks.values() if t["status"] == "running"]

    def list_recent(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent tasks (all statuses)."""
        all_tasks = list(self._tasks.values())
        return all_tasks[-limit:]

    def active_count(self) -> int:
        """Count running tasks."""
        return len(self.list_active())


# Global task tracker
task_tracker = TaskTracker()


def parse_stream_event(event: dict[str, Any]) -> Optional[dict[str, str]]:
    """
    Parse a single stream-json event from Claude Code.

    Returns a dict with 'type', 'content'/'summary', or None to skip.
    """
    event_type = event.get("type")
    if not event_type:
        return None

    if event_type == "assistant":
        message = event.get("message")
        if not message:
            return None
        content_blocks = message.get("content", [])
        texts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
        full_text = " ".join(texts).strip()
        if not full_text:
            return None
        return {"type": "text", "content": full_text}

    if event_type == "tool_use":
        tool = event.get("tool", "unknown")
        tool_input = event.get("input", {})
        summary = _summarize_tool_use(tool, tool_input)
        return {"type": "tool_use", "tool": tool, "summary": summary}

    if event_type == "result":
        result_text = event.get("result", "")
        cost = event.get("cost_usd")
        duration_ms = event.get("duration_ms")
        content = str(result_text)
        if cost is not None:
            content += f"\n\nCost: ${cost:.4f}"
        if duration_ms is not None:
            duration_s = duration_ms / 1000
            content += f" | Duration: {duration_s:.1f}s"
        return {"type": "result", "content": content}

    return None


def _summarize_tool_use(tool: str, tool_input: dict[str, Any]) -> str:
    """Create a short summary of a tool use for Telegram display."""
    if tool == "Read":
        path = tool_input.get("file_path", "unknown")
        return f"Reading {Path(path).name}"
    if tool == "Edit":
        path = tool_input.get("file_path", "unknown")
        return f"Editing {Path(path).name}"
    if tool == "Write":
        path = tool_input.get("file_path", "unknown")
        return f"Writing {Path(path).name}"
    if tool == "Bash":
        command = tool_input.get("command", "")
        # Show first 60 chars of command
        short = command[:60] + ("..." if len(command) > 60 else "")
        return f"Running: {short}"
    if tool == "Glob":
        pattern = tool_input.get("pattern", "")
        return f"Searching: {pattern}"
    if tool == "Grep":
        pattern = tool_input.get("pattern", "")
        return f"Searching for: {pattern}"
    return f"Using {tool}"


def format_progress_line(parsed: dict[str, str]) -> str:
    """Format a single parsed event into a Telegram-friendly progress line."""
    if parsed["type"] == "tool_use":
        return f"→ {parsed['summary']}"
    if parsed["type"] == "text":
        content = parsed.get("content", "")
        if len(content) > 200:
            return content[:200] + "..."
        return content
    return ""


def format_task_summary(
    progress: list[dict[str, str]], result_text: str
) -> str:
    """
    Format a completed task's output into a Telegram-friendly summary.

    Extracts: files changed, commands run, and final result.
    """
    # Extract unique files that were modified (Edit/Write)
    files_changed: list[str] = []
    commands_run: list[str] = []
    for p in progress:
        tool = p.get("tool", "")
        summary = p.get("summary", "")
        if tool in ("Edit", "Write") and summary:
            # Extract filename from "Editing foo.py" / "Writing bar.py"
            parts = summary.split(" ", 1)
            if len(parts) > 1 and parts[1] not in files_changed:
                files_changed.append(parts[1])
        elif tool == "Bash" and summary:
            commands_run.append(summary)

    lines: list[str] = []

    if files_changed:
        lines.append("*Files changed:*")
        for f in files_changed[:10]:  # cap at 10
            lines.append(f"  • {f}")
        lines.append("")

    if commands_run:
        lines.append("*Commands:*")
        for c in commands_run[:5]:  # cap at 5
            lines.append(f"  • {c}")
        lines.append("")

    # Add the result — truncate for Telegram
    if result_text:
        truncated = result_text[:3000] if len(result_text) > 3000 else result_text
        lines.append(truncated)

    summary = "\n".join(lines)
    # Hard cap for Telegram
    if len(summary) > 4000:
        summary = summary[:3997] + "..."
    return summary


def build_claude_command(
    task: str, session_id: Optional[str] = None
) -> list[str]:
    """Build the Claude Code CLI command for agentic execution."""
    cmd = [
        "claude",
        "--output-format", "stream-json",
        "--max-turns", str(DEFAULT_MAX_TURNS),
        "--verbose",
    ]
    if session_id:
        cmd.extend(["--resume", session_id])
    cmd.append(task)
    return cmd


def build_subprocess_env() -> dict[str, str]:
    """Build environment for Claude Code subprocess, stripping CLAUDECODE."""
    return {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}


async def cmd_code_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /code_new <task> — start a fresh Claude Code session."""
    if not await admin_guard(update, context):
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0
    session_manager.clear_session(chat_id)
    await update.message.reply_text("Session cleared. Starting fresh.")

    # Delegate to cmd_code
    await cmd_code(update, context)


async def cmd_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /code <task> — send task to Claude Code in background."""
    if not await admin_guard(update, context):
        return

    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(
            "Claude Code Bridge (Agentic Mode)\n\n"
            "Usage: /code <task description>\n\n"
            "Examples:\n"
            "- /code add error handling to the quiz endpoint\n"
            "- /code run the test suite\n"
            "- /code what does report_service.py do?\n\n"
            "Commands:\n"
            "/tasks — list active/recent tasks\n"
            "/cancel <id> — cancel a running task",
        )
        return

    # Safety check
    safety = check_safety(text)
    if safety.is_blocked:
        await update.message.reply_text(f"Blocked: {safety.reason}")
        return

    # Rate limit check
    if not rate_limiter.is_allowed():
        await update.message.reply_text(
            "Rate limit reached. Max 10 tasks per hour. Try again later."
        )
        return

    # Check concurrent task limit
    if task_tracker.active_count() >= MAX_CONCURRENT_TASKS:
        await update.message.reply_text(
            f"Too many active tasks ({MAX_CONCURRENT_TASKS} max). "
            "Use /tasks to see running tasks or /cancel <id> to stop one."
        )
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0
    rate_limiter.record()
    task_id = task_tracker.create_task(text, chat_id=chat_id)

    # Check for existing session to resume
    existing_session = session_manager.get_session_id(chat_id)
    session_note = " (continuing session)" if existing_session else ""

    await update.message.reply_text(
        f"Started task #{task_id}{session_note}. I'll update you as I go.\n\n{text}"
    )

    # Launch in background — don't block the bot
    asyncio.create_task(
        _run_background_task(update, task_id, text, session_id=existing_session),
        name=f"claude-code-{task_id}",
    )


async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /tasks — list active and recent Claude Code tasks."""
    if not await admin_guard(update, context):
        return

    active = task_tracker.list_active()
    recent = task_tracker.list_recent(limit=5)

    lines: list[str] = []

    if active:
        lines.append("*Active Tasks:*")
        for t in active:
            lines.append(f"  #{t['task_id']} — {t['description'][:60]}")
    else:
        lines.append("No active tasks.")

    completed = [t for t in recent if t["status"] != "running"]
    if completed:
        lines.append("\n*Recent:*")
        for t in completed:
            status = t["status"]
            lines.append(f"  #{t['task_id']} [{status}] — {t['description'][:60]}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cancel <id> — cancel a running Claude Code task."""
    if not await admin_guard(update, context):
        return

    if not context.args:
        await update.message.reply_text("Usage: /cancel <task_id>")
        return

    task_id = context.args[0]
    if task_tracker.cancel_task(task_id):
        await update.message.reply_text(f"Task #{task_id} cancelled.")
    else:
        await update.message.reply_text(
            f"Task #{task_id} not found or already finished."
        )


async def cmd_undo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /undo — revert the last git commit."""
    if not await admin_guard(update, context):
        return

    try:
        process = await asyncio.create_subprocess_exec(
            "git", "log", "--oneline", "-1",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        last_commit = stdout.decode().strip()

        if not last_commit:
            await update.message.reply_text("No commits found to undo.")
            return

        await update.message.reply_text(
            f"Reverting last commit:\n`{last_commit}`",
            parse_mode="Markdown",
        )

        process = await asyncio.create_subprocess_exec(
            "git", "revert", "--no-edit", "HEAD",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            await update.message.reply_text("Reverted successfully.")
        else:
            error = stderr.decode().strip()
            await update.message.reply_text(f"Revert failed:\n{error[:1000]}")

    except Exception as e:
        logger.error(f"Undo command failed: {e}")
        await update.message.reply_text(f"Undo failed: {e}")


async def _run_background_task(
    update: Update,
    task_id: str,
    task: str,
    session_id: Optional[str] = None,
) -> None:
    """Run a Claude Code task in the background with error handling."""
    try:
        await _run_claude_code_streaming(
            update, task, task_id=task_id, session_id=session_id,
        )
    except FileNotFoundError:
        task_tracker.fail_task(task_id, error="Claude Code CLI not found")
        await update.message.reply_text(
            "Claude Code CLI not found. Install with: "
            "`npm install -g @anthropic-ai/claude-code`",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Claude Code task #{task_id} error: {e}")
        task_tracker.fail_task(task_id, error=str(e))
        await update.message.reply_text(f"Task #{task_id} failed: {e}")


async def _run_claude_code_streaming(
    update: Update,
    task: str,
    timeout: int = DEFAULT_TIMEOUT,
    task_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    """
    Run Claude Code in full agentic mode with streaming progress to Telegram.

    Reads stdout line-by-line, parses stream-json events, and sends
    throttled progress updates to the Telegram chat.
    """
    cmd = build_claude_command(task, session_id=session_id)
    env = build_subprocess_env()

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )

    # Track the process for cancellation
    if task_id:
        task_tracker.set_process(task_id, process)

    throttle = ProgressThrottle(min_interval_seconds=5.0)
    final_result: Optional[str] = None
    progress_messages: list[str] = []

    try:
        async def read_stream() -> None:
            nonlocal final_result
            assert process.stdout is not None
            async for line_bytes in process.stdout:
                line = line_bytes.decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                parsed = parse_stream_event(event)
                if parsed is None:
                    continue

                if parsed["type"] == "result":
                    final_result = parsed["content"]
                    await _send_telegram_update(
                        update, f"Task #{task_id} done.\n\n{final_result}"
                        if task_id else f"Done.\n\n{final_result}"
                    )
                elif parsed["type"] == "tool_use":
                    msg = f"→ {parsed['summary']}"
                    progress_messages.append(msg)
                    if throttle.should_send():
                        await _send_telegram_update(update, msg)
                elif parsed["type"] == "text":
                    content = parsed["content"]
                    if len(content) > 20 and throttle.should_send():
                        truncated = content[:500] + (
                            "..." if len(content) > 500 else ""
                        )
                        await _send_telegram_update(update, truncated)

        await asyncio.wait_for(read_stream(), timeout=timeout)

    except asyncio.TimeoutError:
        process.kill()
        if task_id:
            task_tracker.fail_task(task_id, error=f"Timed out after {timeout // 60}min")
        await update.message.reply_text(
            f"Claude Code timed out after {timeout // 60} minutes."
        )
        return

    # Wait for process to finish
    await process.wait()

    # Update task tracker
    if task_id:
        if final_result:
            task_tracker.complete_task(task_id, result=final_result)
        else:
            task_tracker.complete_task(task_id, result="Completed (no result event)")

    # If no result event was received, check stderr
    if final_result is None:
        stderr_output = ""
        if process.stderr:
            stderr_bytes = await process.stderr.read()
            stderr_output = stderr_bytes.decode("utf-8", errors="replace").strip()

        if stderr_output:
            await _send_telegram_update(
                update, f"Claude Code finished with errors:\n{stderr_output[:2000]}"
            )
        elif not progress_messages:
            await update.message.reply_text("No output from Claude Code.")


async def _send_telegram_update(update: Update, text: str) -> None:
    """Send a message to Telegram, respecting the 4096 char limit."""
    if len(text) > 4000:
        chunks = [text[i : i + 4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            await update.message.reply_text(chunk)
    else:
        await update.message.reply_text(text)
