# Email Services
"""
Email service for sending transactional emails via SendGrid.
"""

import logging
from typing import Optional

from src.config.settings import settings

logger = logging.getLogger(__name__)


async def send_report_ready_email(
    to_email: str,
    report_id: str,
    ai_readiness_score: int,
    top_opportunities: list = None,
) -> bool:
    """
    Send email notifying user their report is ready.

    Returns True if sent successfully.
    """
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid not configured, skipping email")
        return False

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        # Build report URL
        base_url = settings.CORS_ORIGINS.split(",")[0]
        report_url = f"{base_url}/report/{report_id}"

        # Build email content
        opportunities_html = ""
        if top_opportunities:
            opportunities_html = "<ul style='margin: 10px 0; padding-left: 20px;'>"
            for opp in top_opportunities[:3]:
                opportunities_html += f"<li style='margin: 5px 0;'><strong>{opp.get('title', 'Opportunity')}</strong> - {opp.get('value_potential', 'See report')}</li>"
            opportunities_html += "</ul>"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #6366f1; margin: 0;">CRB Analyser</h1>
                <p style="color: #666;">Your AI Readiness Report is Ready</p>
            </div>

            <div style="background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 30px; border-radius: 12px; text-align: center; margin: 20px 0;">
                <p style="margin: 0; font-size: 14px; opacity: 0.9;">Your AI Readiness Score</p>
                <p style="font-size: 48px; font-weight: bold; margin: 10px 0;">{ai_readiness_score}</p>
                <p style="margin: 0; font-size: 12px; opacity: 0.8;">out of 100</p>
            </div>

            {"<div style='background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 20px; margin: 20px 0;'><h3 style='color: #166534; margin: 0 0 10px 0;'>Top Opportunities</h3>" + opportunities_html + "</div>" if opportunities_html else ""}

            <div style="text-align: center; margin: 30px 0;">
                <a href="{report_url}" style="background: #6366f1; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                    View Your Full Report
                </a>
            </div>

            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0; color: #64748b; font-size: 14px;">
                    Your report includes:
                </p>
                <ul style="color: #64748b; font-size: 14px;">
                    <li>Detailed findings with cost/benefit analysis</li>
                    <li>Vendor recommendations with pricing</li>
                    <li>Implementation roadmap</li>
                    <li>ROI calculations</li>
                </ul>
            </div>

            <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
                <p>CRB Analyser - AI Implementation Insights for SMBs</p>
                <p>Questions? Reply to this email.</p>
            </div>
        </body>
        </html>
        """

        message = Mail(
            from_email=Email(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
            to_emails=To(to_email),
            subject=f"Your CRB Report is Ready - AI Readiness Score: {ai_readiness_score}",
            html_content=Content("text/html", html_content),
        )

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        logger.info(f"Report email sent to {to_email}, status: {response.status_code}")
        return response.status_code in [200, 201, 202]

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


async def send_payment_confirmation_email(
    to_email: str,
    tier: str,
    amount: float,
) -> bool:
    """
    Send payment confirmation email.
    """
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid not configured, skipping email")
        return False

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        tier_names = {
            "quick": "Quick Report",
            "full": "Full Analysis",
        }

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #6366f1; margin: 0;">CRB Analyser</h1>
                <p style="color: #666;">Payment Confirmation</p>
            </div>

            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h2 style="color: #166534; margin: 0 0 10px 0;">Thank you for your purchase!</h2>
                <p style="color: #166534; margin: 0;">
                    You've purchased: <strong>{tier_names.get(tier, tier)}</strong><br>
                    Amount: <strong>€{amount:.2f}</strong>
                </p>
            </div>

            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin: 0 0 10px 0; color: #334155;">What's Next?</h3>
                <p style="color: #64748b; margin: 0;">
                    We're generating your personalized CRB analysis report. This typically takes 2-5 minutes.
                    You'll receive another email when your report is ready.
                </p>
            </div>

            <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
                <p>CRB Analyser - AI Implementation Insights for SMBs</p>
                <p>Questions? Reply to this email.</p>
            </div>
        </body>
        </html>
        """

        message = Mail(
            from_email=Email(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
            to_emails=To(to_email),
            subject=f"Payment Confirmed - Your CRB Report is Being Generated",
            html_content=Content("text/html", html_content),
        )

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        logger.info(f"Payment confirmation sent to {to_email}, status: {response.status_code}")
        return response.status_code in [200, 201, 202]

    except Exception as e:
        logger.error(f"Failed to send payment confirmation: {e}")
        return False
