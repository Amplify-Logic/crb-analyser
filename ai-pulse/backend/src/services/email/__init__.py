"""
Email Service

Supports Brevo (primary) and SendGrid (backup).
"""

import logging
from typing import Optional

from src.config.settings import settings

logger = logging.getLogger(__name__)


async def send_digest_email(
    to_email: str,
    to_name: Optional[str],
    subject: str,
    html_content: str,
    text_content: str,
) -> bool:
    """
    Send a digest email.

    Tries Brevo first, falls back to SendGrid.
    """
    if settings.BREVO_API_KEY:
        success = await _send_via_brevo(
            to_email, to_name, subject, html_content, text_content
        )
        if success:
            return True
        logger.warning("Brevo send failed, trying SendGrid")

    if settings.SENDGRID_API_KEY:
        return await _send_via_sendgrid(
            to_email, to_name, subject, html_content, text_content
        )

    logger.error("No email provider configured")
    return False


async def _send_via_brevo(
    to_email: str,
    to_name: Optional[str],
    subject: str,
    html_content: str,
    text_content: str,
) -> bool:
    """Send email via Brevo API."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "api-key": settings.BREVO_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "sender": {
                        "name": settings.FROM_NAME,
                        "email": settings.FROM_EMAIL,
                    },
                    "to": [{"email": to_email, "name": to_name or to_email}],
                    "subject": subject,
                    "htmlContent": html_content,
                    "textContent": text_content,
                }
            )
            response.raise_for_status()
            logger.info(f"Email sent via Brevo to {to_email}")
            return True

    except Exception as e:
        logger.error(f"Brevo send error: {e}")
        return False


async def _send_via_sendgrid(
    to_email: str,
    to_name: Optional[str],
    subject: str,
    html_content: str,
    text_content: str,
) -> bool:
    """Send email via SendGrid API."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "personalizations": [{
                        "to": [{"email": to_email, "name": to_name}],
                    }],
                    "from": {
                        "email": settings.FROM_EMAIL,
                        "name": settings.FROM_NAME,
                    },
                    "subject": subject,
                    "content": [
                        {"type": "text/plain", "value": text_content},
                        {"type": "text/html", "value": html_content},
                    ],
                }
            )
            response.raise_for_status()
            logger.info(f"Email sent via SendGrid to {to_email}")
            return True

    except Exception as e:
        logger.error(f"SendGrid send error: {e}")
        return False


async def send_welcome_email(to_email: str, to_name: Optional[str]) -> bool:
    """Send welcome email to new subscriber."""
    subject = "Welcome to AI Pulse!"

    html_content = f"""
    <html>
    <body style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #7c3aed;">Welcome to AI Pulse!</h1>
        <p>Hi{' ' + to_name if to_name else ''},</p>
        <p>Thanks for subscribing! You'll receive your daily AI digest at your preferred time.</p>
        <p><strong>What to expect:</strong></p>
        <ul>
            <li>Top 10 AI news items, curated daily</li>
            <li>Coverage of 50+ sources (YouTube, blogs, Reddit, Twitter)</li>
            <li>AI-generated summaries for quick reading</li>
        </ul>
        <p>Have questions? Just reply to this email.</p>
        <p>Best,<br>The AI Pulse Team</p>
    </body>
    </html>
    """

    text_content = f"""
Welcome to AI Pulse!

Hi{' ' + to_name if to_name else ''},

Thanks for subscribing! You'll receive your daily AI digest at your preferred time.

What to expect:
- Top 10 AI news items, curated daily
- Coverage of 50+ sources (YouTube, blogs, Reddit, Twitter)
- AI-generated summaries for quick reading

Have questions? Just reply to this email.

Best,
The AI Pulse Team
    """

    return await send_digest_email(to_email, to_name, subject, html_content, text_content)
