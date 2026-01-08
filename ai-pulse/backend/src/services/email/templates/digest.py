"""
Digest Email Template
"""

from typing import List
from src.scoring.rules import ScoredArticle


def render_digest_html(
    articles: List[ScoredArticle],
    summaries: dict[str, str],
    digest_id: str,
    user_id: str,
    base_url: str = "https://aipulse.dev",
) -> str:
    """Render HTML digest email."""

    articles_html = ""
    for i, scored in enumerate(articles, 1):
        article = scored.article
        summary = summaries.get(article.external_id, article.description or "")

        thumbnail_html = ""
        if article.thumbnail_url:
            thumbnail_html = f'''
            <img src="{article.thumbnail_url}" alt=""
                 style="width: 100%; max-width: 120px; border-radius: 8px; margin-right: 15px;">
            '''

        source_badge = scored.source.source_type.value.upper()

        articles_html += f'''
        <tr>
            <td style="padding: 20px 0; border-bottom: 1px solid #2a2a2a;">
                <table cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                        <td style="vertical-align: top; width: 120px;">
                            {thumbnail_html}
                        </td>
                        <td style="vertical-align: top; padding-left: 15px;">
                            <span style="display: inline-block; background: #7c3aed; color: white;
                                         font-size: 10px; padding: 2px 6px; border-radius: 4px;
                                         margin-bottom: 8px;">
                                {source_badge}
                            </span>
                            <h3 style="margin: 0 0 8px 0; font-size: 16px;">
                                <a href="{article.url}" style="color: #f5f5f5; text-decoration: none;">
                                    {article.title}
                                </a>
                            </h3>
                            <p style="margin: 0; color: #a0a0a0; font-size: 14px; line-height: 1.5;">
                                {summary[:200]}...
                            </p>
                            <p style="margin: 8px 0 0 0; color: #666; font-size: 12px;">
                                {scored.source.name}
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        '''

    tracking_pixel = f'{base_url}/api/track/open?d={digest_id}&u={user_id}'

    return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Pulse Daily Digest</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <table cellpadding="0" cellspacing="0" width="100%" style="background-color: #0a0a0a;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px;">
                    <!-- Header -->
                    <tr>
                        <td style="padding-bottom: 30px; border-bottom: 1px solid #2a2a2a;">
                            <h1 style="margin: 0; font-size: 28px; color: #f5f5f5;">
                                <span style="color: #7c3aed;">AI</span> Pulse
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #666; font-size: 14px;">
                                Your daily AI digest
                            </p>
                        </td>
                    </tr>

                    <!-- Stats Bar -->
                    <tr>
                        <td style="padding: 20px 0;">
                            <table cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td style="text-align: center; color: #a0a0a0; font-size: 12px;">
                                        <strong style="color: #7c3aed; font-size: 18px;">{len(articles)}</strong><br>
                                        Top Picks
                                    </td>
                                    <td style="text-align: center; color: #a0a0a0; font-size: 12px;">
                                        <strong style="color: #7c3aed; font-size: 18px;">50+</strong><br>
                                        Sources Checked
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Articles -->
                    <tr>
                        <td>
                            <table cellpadding="0" cellspacing="0" width="100%">
                                {articles_html}
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 0; text-align: center; color: #666; font-size: 12px;">
                            <p style="margin: 0;">
                                <a href="{base_url}/dashboard" style="color: #7c3aed;">View Dashboard</a> |
                                <a href="{base_url}/settings" style="color: #7c3aed;">Preferences</a> |
                                <a href="{base_url}/unsubscribe?u={user_id}" style="color: #666;">Unsubscribe</a>
                            </p>
                            <p style="margin: 15px 0 0 0;">
                                AI Pulse - Skip the noise, get the signal.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    <img src="{tracking_pixel}" width="1" height="1" alt="">
</body>
</html>
'''


def render_digest_text(
    articles: List[ScoredArticle],
    summaries: dict[str, str],
) -> str:
    """Render plain text digest email."""

    lines = [
        "AI PULSE - Daily Digest",
        "=" * 40,
        "",
    ]

    for i, scored in enumerate(articles, 1):
        article = scored.article
        summary = summaries.get(article.external_id, article.description or "")

        lines.extend([
            f"{i}. {article.title}",
            f"   Source: {scored.source.name} ({scored.source.source_type.value})",
            f"   {summary[:150]}...",
            f"   {article.url}",
            "",
        ])

    lines.extend([
        "-" * 40,
        "AI Pulse - Skip the noise, get the signal.",
        "Manage preferences: https://aipulse.dev/settings",
    ])

    return "\n".join(lines)
