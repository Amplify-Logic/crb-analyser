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
    pdf_bytes: bytes = None,
) -> bool:
    """
    Send email notifying user their report is ready.

    Args:
        to_email: Recipient email address
        report_id: Report ID for generating view link
        ai_readiness_score: The AI readiness score to display
        top_opportunities: List of top opportunities to highlight
        pdf_bytes: Optional PDF content to attach

    Returns True if sent successfully.
    """
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid not configured, skipping email")
        return False

    try:
        import base64
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition

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

        # Attach PDF if provided
        if pdf_bytes:
            try:
                encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                attachment = Attachment(
                    FileContent(encoded_pdf),
                    FileName(f"CRB-Report-{report_id[:8]}.pdf"),
                    FileType("application/pdf"),
                    Disposition("attachment"),
                )
                message.attachment = attachment
                logger.info(f"PDF attached to email for report {report_id}")
            except Exception as attach_err:
                logger.warning(f"Failed to attach PDF: {attach_err}")
                # Continue without attachment

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


async def send_report_failed_email(
    to_email: str,
    error_message: str = None,
) -> bool:
    """
    Send email notifying user that report generation failed.

    Returns True if sent successfully.
    """
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid not configured, skipping email")
        return False

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #6366f1; margin: 0;">CRB Analyser</h1>
                <p style="color: #666;">Report Generation Issue</p>
            </div>

            <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h2 style="color: #dc2626; margin: 0 0 10px 0;">We encountered an issue</h2>
                <p style="color: #7f1d1d; margin: 0;">
                    Unfortunately, we weren't able to generate your CRB analysis report.
                    Our team has been notified and is looking into this.
                </p>
            </div>

            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin: 0 0 10px 0; color: #334155;">What happens next?</h3>
                <ul style="color: #64748b; margin: 0; padding-left: 20px;">
                    <li>Our team will investigate the issue</li>
                    <li>We'll regenerate your report within 24 hours</li>
                    <li>You'll receive an email when it's ready</li>
                    <li>If we can't resolve it, we'll issue a full refund</li>
                </ul>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <p style="color: #64748b;">
                    Questions? Reply to this email and we'll help you right away.
                </p>
            </div>

            <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
                <p>CRB Analyser - AI Implementation Insights for SMBs</p>
            </div>
        </body>
        </html>
        """

        message = Mail(
            from_email=Email(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
            to_emails=To(to_email),
            subject="Issue with Your CRB Report - We're On It",
            html_content=Content("text/html", html_content),
        )

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        logger.info(f"Report failed email sent to {to_email}, status: {response.status_code}")
        return response.status_code in [200, 201, 202]

    except Exception as e:
        logger.error(f"Failed to send report failed email: {e}")
        return False


async def send_teaser_report_email(
    to_email: str,
    company_name: str,
    score: int,
    findings: list,
    session_id: str
) -> bool:
    """Send teaser report via email."""
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid not configured, skipping email")
        return False

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        # Build findings HTML
        findings_html = ""
        for i, finding in enumerate(findings, 1):
            roi_html = ""
            if finding.get("roi_estimate"):
                roi_html = f'<p style="margin: 10px 0 0 0; color: #22c55e; font-weight: bold;">Potential ROI: €{finding["roi_estimate"]["min"]:,} - €{finding["roi_estimate"]["max"]:,}</p>'
            findings_html += f"""
            <div style="margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: #1a1a1a;">Finding {i}: {finding['title']}</h3>
                <p style="margin: 0; color: #4a4a4a;">{finding.get('summary', '')}</p>
                {roi_html}
            </div>
            """

        # Build frontend URL
        base_url = settings.CORS_ORIGINS.split(",")[0]

        html_content = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #1a1a1a;">Your AI Readiness Report</h1>

            <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; margin: 20px 0;">
                <p style="color: white; margin: 0; font-size: 18px;">AI Readiness Score</p>
                <p style="color: white; margin: 10px 0; font-size: 48px; font-weight: bold;">{score}/100</p>
            </div>

            <h2 style="color: #1a1a1a;">Your Top Findings</h2>
            {findings_html}

            <div style="text-align: center; margin: 30px 0;">
                <p style="color: #666; margin-bottom: 15px;">Unlock your complete report with 15-20 detailed findings and implementation roadmap.</p>
                <a href="{base_url}/quiz?session={session_id}#pricing"
                   style="display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">
                    Get Full Report
                </a>
            </div>

            <p style="color: #999; font-size: 12px; text-align: center;">
                CRB Analyser - AI-Powered Business Audits
            </p>
        </body>
        </html>
        """

        message = Mail(
            from_email=Email(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
            to_emails=To(to_email),
            subject=f"Your AI Readiness Score: {score}/100 - {company_name}",
            html_content=Content("text/html", html_content),
        )

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        logger.info(f"Teaser email sent to {to_email}, status: {response.status_code}")
        return response.status_code in [200, 201, 202]

    except Exception as e:
        logger.error(f"Failed to send teaser email: {e}")
        return False


async def send_welcome_email(
    to_email: str,
    company_name: str,
    password: str,
    audit_id: str,
    has_strategy_call: bool = False
) -> bool:
    """Send welcome email with login credentials."""
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid not configured, skipping email")
        return False

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        # Build frontend URL
        base_url = settings.CORS_ORIGINS.split(",")[0]

        call_section = ""
        if has_strategy_call:
            call_section = """
            <div style="margin: 20px 0; padding: 15px; background: #fef3c7; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0; color: #92400e;">Strategy Call Included</h3>
                <p style="margin: 0; color: #78350f;">After your workshop is complete and report is ready, you'll receive a link to book your 60-minute strategy call with our founders.</p>
            </div>
            """

        html_content = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #1a1a1a;">Welcome, {company_name}!</h1>

            <p style="color: #4a4a4a; font-size: 16px;">
                Thank you for your purchase. Your account has been created and you can now access your personalized AI audit dashboard.
            </p>

            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin: 0 0 15px 0; color: #1a1a1a;">Your Login Credentials</h3>
                <p style="margin: 5px 0;"><strong>Email:</strong> {to_email}</p>
                <p style="margin: 5px 0;"><strong>Temporary Password:</strong> <code style="background: #e5e7eb; padding: 2px 8px; border-radius: 4px;">{password}</code></p>
                <p style="margin: 15px 0 0 0; font-size: 14px; color: #666;">We recommend changing your password after first login.</p>
            </div>

            {call_section}

            <h2 style="color: #1a1a1a;">Next Steps</h2>
            <ol style="color: #4a4a4a;">
                <li style="margin-bottom: 10px;"><strong>Complete your workshop</strong> - 90 minutes of questions to give us deep insight into your business</li>
                <li style="margin-bottom: 10px;"><strong>We review</strong> - Our experts review your report within 24-48 hours</li>
                <li style="margin-bottom: 10px;"><strong>Get your report</strong> - Full interactive report with 15-20 findings</li>
            </ol>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{base_url}/login"
                   style="display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">
                    Start Your Workshop
                </a>
            </div>

            <p style="color: #999; font-size: 12px; text-align: center;">
                Questions? Reply to this email and we'll help you out.
            </p>
        </body>
        </html>
        """

        message = Mail(
            from_email=Email(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
            to_emails=To(to_email),
            subject="Welcome to CRB Analyser - Your Account is Ready",
            html_content=Content("text/html", html_content),
        )

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        logger.info(f"Welcome email sent to {to_email}, status: {response.status_code}")
        return response.status_code in [200, 201, 202]

    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
        return False


async def send_follow_up_email(
    to_email: str,
    report_id: str,
    days_since: int = 7,
    top_opportunity: dict = None,
) -> bool:
    """
    Send follow-up email X days after report delivery.

    Args:
        to_email: Recipient email address
        report_id: Report ID for generating view link
        days_since: Number of days since report delivery
        top_opportunity: The top opportunity from the report

    Returns True if sent successfully.
    """
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid not configured, skipping email")
        return False

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        # Build URLs
        base_url = settings.CORS_ORIGINS.split(",")[0]
        report_url = f"{base_url}/report/{report_id}"
        booking_url = "https://calendly.com/crb-analyser/implementation-call"

        # Build opportunity section
        opportunity_html = ""
        if top_opportunity:
            opportunity_html = f"""
            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h3 style="color: #166534; margin: 0 0 10px 0;">Your Top Opportunity</h3>
                <p style="margin: 0; color: #166534;">
                    <strong>{top_opportunity.get('title', 'See your report')}</strong><br>
                    Potential value: {top_opportunity.get('value_potential', 'See report for details')}
                </p>
            </div>
            """

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #6366f1; margin: 0;">CRB Analyser</h1>
                <p style="color: #666;">How's Your AI Implementation Going?</p>
            </div>

            <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0; color: #334155;">
                    Hi there,
                </p>
                <p style="color: #64748b;">
                    It's been {days_since} days since you received your CRB Analysis Report.
                    We wanted to check in and see how things are going with your AI implementation journey.
                </p>
            </div>

            {opportunity_html}

            <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin: 0 0 10px 0;">Need Help Getting Started?</h3>
                <p style="color: #1e40af; margin: 0 0 15px 0;">
                    Many businesses find it helpful to discuss their report with an expert.
                    Book a free 30-minute implementation call to:
                </p>
                <ul style="color: #1e40af; margin: 0 0 15px 0;">
                    <li>Review your top opportunities</li>
                    <li>Get vendor recommendations</li>
                    <li>Plan your implementation roadmap</li>
                </ul>
                <div style="text-align: center;">
                    <a href="{booking_url}" style="background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                        Book Implementation Call
                    </a>
                </div>
            </div>

            <div style="text-align: center; margin: 20px 0;">
                <a href="{report_url}" style="color: #6366f1; text-decoration: underline;">
                    View Your Report Again
                </a>
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
            subject="How's Your AI Implementation Going?",
            html_content=Content("text/html", html_content),
        )

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        logger.info(f"Follow-up email sent to {to_email}, status: {response.status_code}")
        return response.status_code in [200, 201, 202]

    except Exception as e:
        logger.error(f"Failed to send follow-up email: {e}")
        return False
