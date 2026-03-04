"""Tests for Telegram notification service."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_notify_sends_message_to_admin():
    """Notification should send to configured admin chat ID."""
    mock_bot = AsyncMock()
    mock_app = MagicMock()
    mock_app.bot = mock_bot

    with patch("src.telegram.bot.get_bot_application", return_value=mock_app):
        with patch("src.telegram.notifications.settings") as mock_settings:
            mock_settings.TELEGRAM_ADMIN_CHAT_ID = "12345"

            from src.telegram.notifications import notify_admin
            await notify_admin("Test message")

            mock_bot.send_message.assert_called_once_with(
                chat_id="12345",
                text="Test message",
                parse_mode="Markdown",
            )


@pytest.mark.asyncio
async def test_notify_skips_when_no_bot():
    """Should silently skip when bot is not configured."""
    with patch("src.telegram.bot.get_bot_application", return_value=None):
        from src.telegram.notifications import notify_admin
        # Should not raise
        await notify_admin("Test message")


@pytest.mark.asyncio
async def test_notify_payment_formats_correctly():
    """Payment notification should include amount and company."""
    mock_bot = AsyncMock()
    mock_app = MagicMock()
    mock_app.bot = mock_bot

    with patch("src.telegram.bot.get_bot_application", return_value=mock_app):
        with patch("src.telegram.notifications.settings") as mock_settings:
            mock_settings.TELEGRAM_ADMIN_CHAT_ID = "12345"

            from src.telegram.notifications import notify_payment
            await notify_payment(
                amount=147,
                currency="EUR",
                company="Bonbon Dental",
                email="test@bonbon.com",
            )

            call_text = mock_bot.send_message.call_args[1]["text"]
            assert "147" in call_text
            assert "Bonbon Dental" in call_text
