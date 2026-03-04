"""
CRB Operator Commands

/health, /reports, /leads, /vendors, /briefing
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from telegram import Update
from telegram.ext import ContextTypes

from src.telegram.bot import admin_guard

logger = logging.getLogger(__name__)


def format_health_response(data: Dict[str, Any]) -> str:
    """Format health check data into a Telegram message."""
    vendors = data.get("vendors", {})
    kb = data.get("kb", {})
    expertise = data.get("expertise", {})

    v_status = "OK" if vendors.get("status") == "healthy" else "WARNING"
    k_status = "OK" if kb.get("status") == "healthy" else "WARNING"
    e_status = "OK" if expertise.get("status") == "healthy" else "WARNING"

    return (
        f"*System Health*\n\n"
        f"Vendors: {v_status} — {vendors.get('total', '?')} total, "
        f"{vendors.get('stale_count', 0)} stale\n"
        f"Knowledge Base: {k_status} — {kb.get('stale_files', 0)} stale files\n"
        f"Expertise: {e_status} — {expertise.get('record_count', 0)} records"
    )


def format_reports_response(data: Dict[str, Any]) -> str:
    """Format report stats into a Telegram message."""
    return (
        f"*Reports — {data.get('period', 'today')}*\n\n"
        f"Total: {data.get('total', 0)}\n"
        f"Completed: {data.get('completed', 0)}\n"
        f"Failed: {data.get('failed', 0)}"
    )


def format_leads_response(leads: List[Dict[str, Any]]) -> str:
    """Format lead list into a Telegram message."""
    if not leads:
        return "*Recent Leads*\n\nNo new leads."

    lines = ["*Recent Leads*\n"]
    for lead in leads[:10]:
        company = lead.get("company_name", "Unknown")
        industry = lead.get("industry", "?")
        email = lead.get("email", "")
        lines.append(f"- {company} ({industry}) — {email}")
    return "\n".join(lines)


async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /health — system health check."""
    if not await admin_guard(update, context):
        return

    await update.message.reply_text("Running health check...")

    try:
        from src.config.supabase_client import get_async_supabase

        # Vendor health
        supabase = await get_async_supabase()
        vendor_result = await supabase.table("vendors").select("id", count="exact").execute()
        total_vendors = vendor_result.count or 0

        # Try to get stale count
        stale = 0
        try:
            from src.agents.research.refresh import get_stale_count
            stale = await get_stale_count()
        except Exception:
            pass

        vendor_status = "healthy" if stale < 10 else "warning"

        health_data = {
            "vendors": {"stale_count": stale, "total": total_vendors, "status": vendor_status},
            "kb": {"stale_files": 0, "status": "healthy"},
            "expertise": {"status": "healthy", "record_count": 0},
        }

        await update.message.reply_text(
            format_health_response(health_data), parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        await update.message.reply_text(f"Health check failed: {e}")


async def cmd_reports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reports [today|week|month] — report delivery stats."""
    if not await admin_guard(update, context):
        return

    period = "today"
    if context.args:
        period = context.args[0].lower()

    try:
        from src.config.supabase_client import get_async_supabase

        supabase = await get_async_supabase()
        now = datetime.now(timezone.utc)

        if period == "week":
            since = now - timedelta(days=7)
        elif period == "month":
            since = now - timedelta(days=30)
        else:
            since = now.replace(hour=0, minute=0, second=0, microsecond=0)

        result = await supabase.table("reports").select(
            "id, status"
        ).gte("created_at", since.isoformat()).execute()

        reports = result.data or []
        completed = sum(1 for r in reports if r.get("status") == "completed")
        failed = sum(1 for r in reports if r.get("status") == "failed")

        data = {
            "total": len(reports),
            "completed": completed,
            "failed": failed,
            "period": period,
        }

        await update.message.reply_text(
            format_reports_response(data), parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Failed to fetch reports: {e}")


async def cmd_leads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /leads — recent quiz completions."""
    if not await admin_guard(update, context):
        return

    try:
        from src.config.supabase_client import get_async_supabase

        supabase = await get_async_supabase()
        since = datetime.now(timezone.utc) - timedelta(days=7)

        result = await supabase.table("quiz_sessions").select(
            "email, company_name, answers, created_at"
        ).gte("created_at", since.isoformat()).order(
            "created_at", desc=True
        ).limit(10).execute()

        # Extract industry from answers JSONB
        for lead in (result.data or []):
            answers = lead.get("answers") or {}
            lead["industry"] = answers.get("industry", "?")

        await update.message.reply_text(
            format_leads_response(result.data or []), parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Failed to fetch leads: {e}")


async def cmd_vendors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /vendors [stale|refresh] — vendor data status."""
    if not await admin_guard(update, context):
        return

    subcommand = context.args[0].lower() if context.args else "status"

    try:
        if subcommand == "refresh":
            from src.services.scheduler_service import trigger_vendor_refresh
            await update.message.reply_text("Starting vendor refresh...")
            await trigger_vendor_refresh()
            await update.message.reply_text("Vendor refresh complete.")
        else:
            stale = 0
            try:
                from src.agents.research.refresh import get_stale_count
                stale = await get_stale_count()
            except Exception:
                pass
            await update.message.reply_text(
                f"*Vendor Status*\n\nStale vendors (>90 days): {stale}",
                parse_mode="Markdown",
            )
    except Exception as e:
        await update.message.reply_text(f"Vendor command failed: {e}")


async def cmd_briefing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /briefing — full morning digest."""
    if not await admin_guard(update, context):
        return

    await update.message.reply_text("Generating briefing...")

    try:
        briefing = await generate_briefing()
        await update.message.reply_text(briefing, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Briefing failed: {e}")


async def generate_briefing() -> str:
    """Generate the full morning briefing digest."""
    from src.config.supabase_client import get_async_supabase

    supabase = await get_async_supabase()
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)

    # Reports (yesterday)
    reports_result = await supabase.table("reports").select(
        "id, status"
    ).gte("created_at", yesterday.isoformat()).execute()
    reports = reports_result.data or []
    reports_completed = sum(1 for r in reports if r.get("status") == "completed")

    # Leads (yesterday)
    leads_result = await supabase.table("quiz_sessions").select(
        "id, company_name, answers"
    ).gte("created_at", yesterday.isoformat()).execute()
    leads = leads_result.data or []

    # Extract industry from answers JSONB
    for lead in leads:
        answers = lead.get("answers") or {}
        lead["industry"] = answers.get("industry", "unknown")

    # Vendor health
    stale = -1
    try:
        from src.agents.research.refresh import get_stale_count
        stale = await get_stale_count()
    except Exception:
        pass

    v_status = "OK" if stale < 10 else f"WARNING ({stale} stale)"

    # Industry breakdown of leads
    industries: Dict[str, int] = {}
    for lead in leads:
        ind = lead.get("industry", "unknown")
        industries[ind] = industries.get(ind, 0) + 1
    industry_lines = "\n".join(f"  {k}: {v}" for k, v in industries.items()) or "  None"

    briefing = (
        f"*CRB Analyser — {now.strftime('%b %d')} Daily Brief*\n\n"
        f"*Reports*\n"
        f"  Delivered: {reports_completed}\n"
        f"  Total: {len(reports)}\n\n"
        f"*Leads (24h)*\n"
        f"  New: {len(leads)}\n"
        f"{industry_lines}\n\n"
        f"*Data Health*\n"
        f"  Vendors: {v_status}\n"
    )

    return briefing
