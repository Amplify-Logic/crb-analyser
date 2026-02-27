"""
Drop-in replacement for Anthropic() client that routes LLM calls through the Claude Code CLI.

Uses the Claude Max subscription (separate billing) instead of Anthropic API credits.
Duck-types the Anthropic SDK interface: client.messages.create() returns .content[0].text and .usage.*.

Usage:
    from src.config.claude_cli_client import ClaudeCodeClient
    client = ClaudeCodeClient()
    response = client.messages.create(model="claude-opus-4-6", max_tokens=4096, messages=[...])
    print(response.content[0].text)
"""

import json
import os
import shutil
import subprocess
import structlog
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = structlog.get_logger(__name__)

# Map Anthropic SDK model IDs to Claude CLI --model flag values
MODEL_MAP = {
    "claude-opus-4-6": "opus",
    "claude-opus-4-5-20251101": "opus",
    "claude-sonnet-4-5-20250929": "sonnet",
    "claude-sonnet-4-6": "sonnet",
    "claude-haiku-4-5-20251001": "haiku",
}


@dataclass
class CLITextBlock:
    """Mimics anthropic.types.TextBlock."""
    text: str
    type: str = "text"


@dataclass
class CLIUsage:
    """Mimics anthropic.types.Usage with estimated token counts."""
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class CLIResponse:
    """Mimics anthropic.types.Message returned by client.messages.create()."""
    content: List[CLITextBlock] = field(default_factory=list)
    usage: CLIUsage = field(default_factory=CLIUsage)
    model: str = ""
    id: str = "cli-response"
    type: str = "message"
    role: str = "assistant"
    stop_reason: str = "end_turn"


class CLIMessages:
    """Mimics client.messages with a create() method that calls the Claude CLI."""

    TIMEOUT_SECONDS = 900  # 15 min — large prompts (45K+ chars) need more time

    def create(
        self,
        model: str,
        max_tokens: int,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> CLIResponse:
        """
        Call Claude CLI subprocess, mirroring Anthropic().messages.create().

        Pipes the prompt via stdin to handle large prompts (avoids shell arg limits).
        """
        cli_model = MODEL_MAP.get(model, "sonnet")

        # Build the prompt from messages
        prompt_parts = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                # Handle structured content blocks
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block["text"])
                    elif isinstance(block, str):
                        text_parts.append(block)
                content = "\n".join(text_parts)
            prompt_parts.append(content)

        prompt = "\n\n".join(prompt_parts)

        # Build CLI command
        cmd = [
            "claude",
            "-p",
            "--model", cli_model,
            "--output-format", "json",
            "--no-session-persistence",
        ]

        # Add system prompt via flag
        if system:
            # Truncate very long system prompts for the flag (CLI has arg limits)
            if len(system) > 50000:
                # Prepend to user message instead
                prompt = f"<system>\n{system}\n</system>\n\n{prompt}"
            else:
                cmd.extend(["--system-prompt", system])

        logger.info(
            "dev_mode_cli_call",
            model=cli_model,
            prompt_length=len(prompt),
            max_tokens=max_tokens,
        )

        try:
            # Clean env for CLI subprocess:
            # - CLAUDECODE: avoid "nested session" error when spawned by Claude Code
            # - ANTHROPIC_API_KEY: force CLI to use Max subscription instead of API credits
            env = os.environ.copy()
            env.pop("CLAUDECODE", None)
            env.pop("ANTHROPIC_API_KEY", None)

            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_SECONDS,
                env=env,
            )

            if result.returncode != 0:
                stderr = result.stderr.strip()
                stdout = result.stdout.strip()
                logger.error(
                    "cli_call_failed",
                    returncode=result.returncode,
                    stderr=stderr[:500],
                    stdout_preview=stdout[:500],
                )
                # CLI returns JSON on stdout even with non-zero exit code
                if stdout:
                    try:
                        parsed = json.loads(stdout)
                        error_msg = parsed.get("result", "")
                        if parsed.get("is_error"):
                            raise RuntimeError(f"Claude CLI error: {error_msg}")
                        if error_msg and not parsed.get("is_error"):
                            # CLI returned a valid result despite non-zero exit
                            logger.warning("cli_nonzero_but_has_result", returncode=result.returncode)
                            input_tokens = len(prompt) // 4
                            output_tokens = len(error_msg) // 4
                            return CLIResponse(
                                content=[CLITextBlock(text=error_msg)],
                                usage=CLIUsage(input_tokens=input_tokens, output_tokens=output_tokens),
                                model=model,
                            )
                    except json.JSONDecodeError:
                        pass
                raise RuntimeError(f"Claude CLI failed (exit {result.returncode}): {stderr[:200] or stdout[:200]}")

            output = result.stdout.strip()

            # Parse JSON output
            try:
                parsed = json.loads(output)
            except json.JSONDecodeError:
                # CLI returned plain text instead of JSON — use as-is
                parsed = {"result": output}

            # Extract result text
            if parsed.get("is_error"):
                raise RuntimeError(f"Claude CLI error: {parsed.get('result', 'unknown error')}")

            result_text = parsed.get("result", output)
            cost_usd = parsed.get("cost_usd", 0)
            duration_ms = parsed.get("duration_ms", 0)

            # Estimate token counts from text lengths (rough: ~4 chars per token)
            input_tokens = len(prompt) // 4
            output_tokens = len(result_text) // 4

            logger.info(
                "dev_mode_cli_response",
                model=cli_model,
                output_length=len(result_text),
                cost_usd=cost_usd,
                duration_ms=duration_ms,
                estimated_input_tokens=input_tokens,
                estimated_output_tokens=output_tokens,
            )

            return CLIResponse(
                content=[CLITextBlock(text=result_text)],
                usage=CLIUsage(input_tokens=input_tokens, output_tokens=output_tokens),
                model=model,
            )

        except subprocess.TimeoutExpired:
            logger.error("cli_call_timeout", timeout=self.TIMEOUT_SECONDS)
            raise RuntimeError(f"Claude CLI timed out after {self.TIMEOUT_SECONDS}s")


class ClaudeCodeClient:
    """
    Drop-in replacement for Anthropic() that routes calls through Claude Code CLI.

    Uses the Claude Max subscription instead of API credits.
    """

    def __init__(self) -> None:
        # Validate that claude CLI is available
        if not shutil.which("claude"):
            raise RuntimeError(
                "Claude Code CLI not found on PATH. "
                "Install it: https://docs.anthropic.com/en/docs/claude-code"
            )
        self.messages = CLIMessages()
        logger.info("dev_mode_client_initialized", cli_path=shutil.which("claude"))
