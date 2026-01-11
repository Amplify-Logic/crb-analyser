"""
Prompt Safety Utilities

Sanitization functions to prevent prompt injection attacks
when including user input in LLM prompts.
"""

import re


def sanitize_user_input(text: str) -> str:
    """
    Sanitize user input before including in LLM prompts.

    Removes or neutralizes common prompt injection patterns
    and limits input length to prevent context stuffing.

    Args:
        text: Raw user input

    Returns:
        Sanitized text safe for prompt inclusion
    """
    if not text:
        return ""

    # Remove potential injection patterns
    dangerous_patterns = [
        r'ignore\s+(all\s+)?previous\s+instructions',
        r'ignore\s+(all\s+)?above',
        r'disregard\s+(all\s+)?previous',
        r'forget\s+(all\s+)?previous',
        r'system\s*prompt',
        r'you\s+are\s+now',
        r'new\s+instructions',
        r'</?(system|user|assistant)>',
        r'<\|im_start\|>',
        r'<\|im_end\|>',
        r'\[INST\]',
        r'\[/INST\]',
    ]

    sanitized = text
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '[FILTERED]', sanitized, flags=re.IGNORECASE)

    # Escape XML-like tags that could be interpreted as message boundaries
    sanitized = re.sub(r'<([^>]+)>', r'&lt;\1&gt;', sanitized)

    # Limit length to prevent context stuffing
    max_length = 5000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "...[truncated]"

    return sanitized
