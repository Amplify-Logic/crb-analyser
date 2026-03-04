"""Tests for Telegram bot core setup."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_is_admin_allows_correct_chat_id():
    """Only the configured admin chat ID should be allowed."""
    with patch("src.telegram.bot.settings") as mock_settings:
        mock_settings.TELEGRAM_ADMIN_CHAT_ID = "12345"
        from src.telegram.bot import is_admin
        assert is_admin(12345) is True
        assert is_admin(99999) is False


@pytest.mark.asyncio
async def test_is_admin_rejects_when_no_chat_id_configured():
    """If no admin chat ID is set, reject everyone."""
    with patch("src.telegram.bot.settings") as mock_settings:
        mock_settings.TELEGRAM_ADMIN_CHAT_ID = None
        from src.telegram.bot import is_admin
        assert is_admin(12345) is False
