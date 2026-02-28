"""
Scheduler Service

Background job scheduler for periodic tasks like follow-up emails, storage cleanup,
pipeline reporting, re-engagement, and operational monitoring.
Uses APScheduler for in-process scheduling.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def send_follow_up_emails():
    """
    Send follow-up emails to users who received reports 7 days ago.
    Runs daily at 10 AM.
    """
    logger.info("Starting follow-up email job")

    try:
        from src.config.supabase_client import get_async_supabase
        from src.services.email import send_follow_up_email

        supabase = await get_async_supabase()

        # Find reports completed 7 days ago that haven't received follow-up
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        eight_days_ago = datetime.utcnow() - timedelta(days=8)

        # Query reports completed between 7-8 days ago without follow-up
        result = await supabase.table("reports").select(
            "id, quiz_session_id, executive_summary"
        ).gte(
            "generation_completed_at", eight_days_ago.isoformat()
        ).lte(
            "generation_completed_at", seven_days_ago.isoformat()
        ).is_(
            "follow_up_sent_at", "null"
        ).eq(
            "status", "completed"
        ).execute()

        if not result.data:
            logger.info("No reports need follow-up emails")
            return

        sent_count = 0
        for report in result.data:
            try:
                # Get email from quiz session
                quiz_result = await supabase.table("quiz_sessions").select(
                    "email"
                ).eq("id", report["quiz_session_id"]).single().execute()

                if not quiz_result.data or not quiz_result.data.get("email"):
                    continue

                email = quiz_result.data["email"]
                executive_summary = report.get("executive_summary", {})
                top_opportunities = executive_summary.get("top_opportunities", [])
                top_opportunity = top_opportunities[0] if top_opportunities else None

                # Send follow-up email
                success = await send_follow_up_email(
                    to_email=email,
                    report_id=report["id"],
                    days_since=7,
                    top_opportunity=top_opportunity,
                )

                if success:
                    # Mark follow-up as sent
                    await supabase.table("reports").update({
                        "follow_up_sent_at": datetime.utcnow().isoformat()
                    }).eq("id", report["id"]).execute()
                    sent_count += 1
                    logger.info(f"Follow-up sent for report {report['id']}")

            except Exception as e:
                logger.error(f"Failed to send follow-up for report {report['id']}: {e}")
                continue

        logger.info(f"Follow-up email job completed. Sent {sent_count} emails.")

        try:
            from src.telegram.notifications import notify_scheduler_job
            await notify_scheduler_job(
                "Follow-up Emails",
                success=True,
                details=f"Sent {sent_count} follow-up emails",
            )
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Follow-up email job failed: {e}")


async def cleanup_old_pdfs():
    """
    Clean up PDFs older than 30 days from storage.
    Runs daily at 3 AM.
    """
    logger.info("Starting storage cleanup job")

    try:
        from src.services.storage_service import get_storage_service

        service = get_storage_service()
        deleted_count = await service.cleanup_old_files(days_old=30)

        logger.info(f"Storage cleanup completed. Deleted {deleted_count} files.")

        try:
            from src.telegram.notifications import notify_scheduler_job
            await notify_scheduler_job(
                "Storage Cleanup",
                success=True,
                details=f"Deleted {deleted_count} files",
            )
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Storage cleanup job failed: {e}")


async def refresh_vendor_pricing():
    """
    Refresh vendor pricing from vendor websites.
    Runs weekly on Sundays at 2 AM.

    This ensures our vendor pricing data stays current.
    """
    logger.info("Starting vendor pricing refresh job")

    try:
        from src.services.vendor_refresh_service import vendor_refresh_service

        # Refresh vendors that haven't been updated in 7+ days
        results = await vendor_refresh_service.refresh_all_vendors(
            older_than_days=7,
            limit=50,  # Limit per run to avoid overloading
        )

        success_count = sum(1 for r in results if r.get("success"))
        changed_count = sum(1 for r in results if r.get("changed"))

        logger.info(
            f"Vendor refresh completed: {success_count}/{len(results)} successful, "
            f"{changed_count} pricing changes detected"
        )

        try:
            from src.telegram.notifications import notify_scheduler_job
            await notify_scheduler_job(
                "Vendor Refresh",
                success=True,
                details=f"{success_count}/{len(results)} successful, {changed_count} changes",
            )
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Vendor pricing refresh job failed: {e}")


async def cleanup_expired_quiz_sessions():
    """
    Clean up quiz sessions that expired without payment.
    Runs daily at 4 AM.
    """
    logger.info("Starting expired quiz session cleanup")

    try:
        from src.config.supabase_client import get_async_supabase

        supabase = await get_async_supabase()

        # Delete quiz sessions older than 7 days that were never paid
        cutoff = datetime.utcnow() - timedelta(days=7)

        result = await supabase.table("quiz_sessions").delete().lt(
            "created_at", cutoff.isoformat()
        ).in_(
            "status", ["pending_payment", "expired"]
        ).execute()

        deleted_count = len(result.data) if result.data else 0
        logger.info(f"Expired quiz cleanup completed. Deleted {deleted_count} sessions.")

        try:
            from src.telegram.notifications import notify_scheduler_job
            await notify_scheduler_job(
                "Quiz Cleanup",
                success=True,
                details=f"Deleted {deleted_count} expired sessions",
            )
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Expired quiz cleanup failed: {e}")


async def send_morning_briefing():
    """
    Send morning briefing digest via Telegram.
    Runs daily at 7 AM UTC.
    """
    logger.info("Starting morning briefing job")

    try:
        from src.telegram.handlers.crb_commands import generate_briefing
        from src.telegram.notifications import notify_admin

        briefing = await generate_briefing()
        await notify_admin(briefing)

        logger.info("Morning briefing sent successfully")

    except Exception as e:
        logger.error(f"Morning briefing failed: {e}")


# =============================================================================
# PHASE A — REVENUE JOBS
# =============================================================================


async def generate_pipeline_report() -> None:
    """
    Weekly pipeline digest: leads, conversions, revenue, industry breakdown.
    Runs Monday 7:30 UTC.
    """
    logger.info("Starting weekly pipeline report job")

    try:
        from src.config.supabase_client import get_async_supabase
        from src.telegram.notifications import notify_admin

        supabase = await get_async_supabase()
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=7)
        prev_week_start = now - timedelta(days=14)

        # Current week: quiz sessions
        sessions_result = await supabase.table("quiz_sessions").select(
            "id, status, industry, tier, created_at"
        ).gte("created_at", week_start.isoformat()).execute()

        sessions = sessions_result.data or []
        total_leads = len(sessions)
        completions = [s for s in sessions if s.get("status") == "completed"]
        conversion_count = len(completions)
        conversion_rate = (
            round(conversion_count / total_leads * 100, 1) if total_leads else 0
        )

        # Industry breakdown
        industry_counts: dict[str, int] = {}
        for s in sessions:
            ind = s.get("industry") or "unknown"
            industry_counts[ind] = industry_counts.get(ind, 0) + 1

        # Revenue from completed sessions by tier
        quick_count = sum(1 for s in completions if s.get("tier") == "quick")
        full_count = sum(1 for s in completions if s.get("tier") == "full")
        quick_revenue = quick_count * 95
        full_revenue = full_count * 895
        total_revenue = quick_revenue + full_revenue

        # Reports stats
        reports_result = await supabase.table("reports").select(
            "id, status"
        ).gte("created_at", week_start.isoformat()).execute()
        reports = reports_result.data or []
        reports_completed = sum(1 for r in reports if r.get("status") == "completed")
        reports_failed = sum(1 for r in reports if r.get("status") == "failed")

        # Previous week for delta
        prev_sessions_result = await supabase.table("quiz_sessions").select(
            "id"
        ).gte(
            "created_at", prev_week_start.isoformat()
        ).lt(
            "created_at", week_start.isoformat()
        ).execute()
        prev_leads = len(prev_sessions_result.data or [])
        delta = total_leads - prev_leads
        delta_str = f"+{delta}" if delta >= 0 else str(delta)

        # Format industry lines
        industry_lines = ""
        for ind, count in sorted(
            industry_counts.items(), key=lambda x: x[1], reverse=True
        ):
            industry_lines += f"  {ind}: {count}\n"

        # Top industry
        top_industry = max(industry_counts, key=industry_counts.get) if industry_counts else "n/a"
        top_pct = (
            round(industry_counts.get(top_industry, 0) / max(total_leads, 1) * 100)
            if industry_counts
            else 0
        )

        date_range = f"{week_start.strftime('%b %d')}-{now.strftime('%d')}"
        msg = (
            f"*Weekly Pipeline — {date_range}*\n\n"
            f"Leads: {total_leads} ({delta_str} vs last week)\n"
            f"{industry_lines}"
            f"Conversions: {conversion_count} ({conversion_rate}% rate)\n"
            f"Revenue: EUR {total_revenue:,}\n"
            f"  Quick tier: {quick_count} x EUR 95 = EUR {quick_revenue:,}\n"
            f"  Full tier: {full_count} x EUR 895 = EUR {full_revenue:,}\n"
            f"Reports: {len(reports)} generated, {reports_completed} completed, {reports_failed} failed\n\n"
            f"Top industry: {top_industry} ({top_pct}% of leads)"
        )

        await notify_admin(msg)
        logger.info("Weekly pipeline report sent")

    except Exception as e:
        logger.error(f"Weekly pipeline report failed: {e}")
        try:
            from src.telegram.notifications import notify_scheduler_job
            await notify_scheduler_job("Pipeline Report", success=False, details=str(e))
        except Exception:
            pass


async def send_quiz_reengagement() -> None:
    """
    Re-engage users who abandoned quiz at payment step.
    First nudge at 24-48h, second at 72-96h.
    Runs daily at 11:00 UTC.
    """
    logger.info("Starting quiz re-engagement job")

    try:
        from src.config.supabase_client import get_async_supabase
        from src.services.brevo_service import send_reengagement_email
        from src.telegram.notifications import notify_admin

        supabase = await get_async_supabase()
        now = datetime.now(timezone.utc)

        # First nudge window: 24-48h ago, no prior nudge
        first_start = now - timedelta(hours=48)
        first_end = now - timedelta(hours=24)

        first_result = await supabase.table("quiz_sessions").select(
            "id, email, industry, company_name"
        ).eq(
            "status", "pending_payment"
        ).gte(
            "created_at", first_start.isoformat()
        ).lte(
            "created_at", first_end.isoformat()
        ).is_(
            "last_nudge_at", "null"
        ).execute()

        first_candidates = first_result.data or []

        # Second nudge window: 72-96h ago, nudge_count == 1
        second_start = now - timedelta(hours=96)
        second_end = now - timedelta(hours=72)

        second_result = await supabase.table("quiz_sessions").select(
            "id, email, industry, company_name"
        ).eq(
            "status", "pending_payment"
        ).gte(
            "created_at", second_start.isoformat()
        ).lte(
            "created_at", second_end.isoformat()
        ).eq(
            "nudge_count", 1
        ).execute()

        second_candidates = second_result.data or []

        first_sent = 0
        for session in first_candidates:
            email = session.get("email")
            if not email:
                continue
            try:
                # Skip if email already has a completed session
                completed_check = await supabase.table("quiz_sessions").select(
                    "id"
                ).eq("email", email).eq("status", "completed").limit(1).execute()
                if completed_check.data:
                    continue

                await send_reengagement_email(
                    to_email=email,
                    company_name=session.get("company_name", ""),
                    nudge_number=1,
                )

                await supabase.table("quiz_sessions").update({
                    "nudge_count": 1,
                    "last_nudge_at": now.isoformat(),
                }).eq("id", session["id"]).execute()
                first_sent += 1
            except Exception as e:
                logger.error(f"First nudge failed for {session['id']}: {e}")

        second_sent = 0
        for session in second_candidates:
            email = session.get("email")
            if not email:
                continue
            try:
                completed_check = await supabase.table("quiz_sessions").select(
                    "id"
                ).eq("email", email).eq("status", "completed").limit(1).execute()
                if completed_check.data:
                    continue

                await send_reengagement_email(
                    to_email=email,
                    company_name=session.get("company_name", ""),
                    nudge_number=2,
                )

                await supabase.table("quiz_sessions").update({
                    "nudge_count": 2,
                    "last_nudge_at": now.isoformat(),
                }).eq("id", session["id"]).execute()
                second_sent += 1
            except Exception as e:
                logger.error(f"Second nudge failed for {session['id']}: {e}")

        msg = (
            f"*Quiz Re-engagement — {now.strftime('%b %d')}*\n\n"
            f"First nudge (24h): {first_sent} sent\n"
            f"Second nudge (72h): {second_sent} sent"
        )
        await notify_admin(msg)
        logger.info(f"Re-engagement done: {first_sent} first, {second_sent} second")

    except Exception as e:
        logger.error(f"Quiz re-engagement job failed: {e}")
        try:
            from src.telegram.notifications import notify_scheduler_job
            await notify_scheduler_job("Re-engagement", success=False, details=str(e))
        except Exception:
            pass


async def scan_upsell_candidates() -> None:
    """
    Find quick-tier customers with high readiness who could upgrade to full.
    Runs Wednesday 8:00 UTC.
    """
    logger.info("Starting upsell scanner job")

    try:
        from src.config.supabase_client import get_async_supabase
        from src.telegram.notifications import notify_admin

        supabase = await get_async_supabase()

        # Get completed quick-tier sessions
        quick_result = await supabase.table("quiz_sessions").select(
            "id, email, company_name, industry"
        ).eq("tier", "quick").eq("status", "completed").execute()

        quick_sessions = quick_result.data or []
        if not quick_sessions:
            logger.info("No quick-tier completions to scan")
            return

        # Collect emails that already have full-tier
        full_result = await supabase.table("quiz_sessions").select(
            "email"
        ).eq("tier", "full").eq("status", "completed").execute()
        full_emails = {s["email"] for s in (full_result.data or []) if s.get("email")}

        candidates: list[dict[str, Any]] = []
        for session in quick_sessions:
            email = session.get("email")
            if not email or email in full_emails:
                continue

            # Get report for readiness score
            report_result = await supabase.table("reports").select(
                "results, status"
            ).eq("quiz_session_id", session["id"]).eq("status", "completed").limit(1).execute()

            if not report_result.data:
                continue

            results = report_result.data[0].get("results") or {}
            readiness = results.get("ai_readiness_score") or results.get("readiness_score", 0)

            if readiness >= 7:
                candidates.append({
                    "company": session.get("company_name", "Unknown"),
                    "industry": session.get("industry", "unknown"),
                    "readiness": readiness,
                    "email": email,
                })

        if not candidates:
            logger.info("No upsell candidates found")
            return

        # Format message
        iso_week = datetime.now(timezone.utc).isocalendar()[1]
        lines = [f"*Upsell Candidates — Week {iso_week}*\n"]
        lines.append(f"{len(candidates)} quick-tier customers with high readiness:\n")

        for i, c in enumerate(candidates[:10], 1):  # Cap at 10 for Telegram limit
            lines.append(
                f"{i}. {c['company']} ({c['industry']}) — Readiness: {c['readiness']}/10\n"
                f"   Email: {c['email']}"
            )

        await notify_admin("\n".join(lines))
        logger.info(f"Upsell scanner found {len(candidates)} candidates")

    except Exception as e:
        logger.error(f"Upsell scanner failed: {e}")
        try:
            from src.telegram.notifications import notify_scheduler_job
            await notify_scheduler_job("Upsell Scanner", success=False, details=str(e))
        except Exception:
            pass


# =============================================================================
# PHASE B — OPS JOBS
# =============================================================================


async def track_api_costs_daily() -> None:
    """
    Daily API cost estimation from structured logs.
    Runs daily at 23:00 UTC.
    """
    logger.info("Starting daily API cost tracker")

    try:
        from src.telegram.notifications import notify_admin

        # Cost-per-1K-token estimates (EUR, as of Feb 2026)
        PRICING: dict[str, dict[str, float]] = {
            "haiku": {"input": 0.00025, "output": 0.00125},
            "sonnet": {"input": 0.003, "output": 0.015},
            "opus": {"input": 0.015, "output": 0.075},
        }

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        costs: dict[str, float] = {}
        call_counts: dict[str, int] = {}

        # Try to read from Redis usage tracking
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.REDIS_URL)

            for model_tier in PRICING:
                key = f"api_usage:{today}:{model_tier}"
                data = await r.get(key)
                if data:
                    usage = json.loads(data)
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    calls = usage.get("calls", 0)

                    cost = (
                        (input_tokens / 1000) * PRICING[model_tier]["input"]
                        + (output_tokens / 1000) * PRICING[model_tier]["output"]
                    )
                    costs[model_tier] = round(cost, 2)
                    call_counts[model_tier] = calls

            await r.aclose()
        except Exception as e:
            logger.warning(f"Redis cost tracking unavailable: {e}")

        total_cost = sum(costs.values())
        threshold = 10.0

        # Build message
        cost_lines = []
        for tier, cost in sorted(costs.items(), key=lambda x: x[1], reverse=True):
            calls = call_counts.get(tier, 0)
            cost_lines.append(f"  {tier}: {calls} calls — EUR {cost:.2f}")

        alert = " (OVER THRESHOLD)" if total_cost > threshold else ""
        msg = (
            f"*API Costs — {today}*{alert}\n\n"
            f"Daily spend: EUR {total_cost:.2f} (threshold: EUR {threshold:.0f})\n"
        )
        if cost_lines:
            msg += "  Anthropic:\n" + "\n".join(cost_lines)
        else:
            msg += "  No usage data tracked today (Redis tracking not active)"

        if total_cost > threshold:
            await notify_admin(msg)
        else:
            # Store silently, only push weekly
            logger.info(f"Daily API cost: EUR {total_cost:.2f}")

        # Store daily total in Redis for weekly aggregation
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.REDIS_URL)
            await r.setex(
                f"api_cost_daily:{today}",
                60 * 60 * 24 * 10,  # 10 day TTL
                json.dumps({"total": total_cost, "breakdown": costs, "calls": call_counts}),
            )
            await r.aclose()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"API cost tracker failed: {e}")


async def send_api_cost_weekly_summary() -> None:
    """
    Weekly API cost trend summary.
    Runs Monday 7:15 UTC.
    """
    logger.info("Starting weekly API cost summary")

    try:
        from src.telegram.notifications import notify_admin

        daily_costs: list[tuple[str, float]] = []

        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.REDIS_URL)

            for days_ago in range(7):
                date = (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%d")
                data = await r.get(f"api_cost_daily:{date}")
                if data:
                    parsed = json.loads(data)
                    daily_costs.append((date, parsed.get("total", 0)))

            await r.aclose()
        except Exception as e:
            logger.warning(f"Could not read weekly cost data: {e}")

        if not daily_costs:
            logger.info("No cost data for weekly summary")
            return

        total_week = sum(c for _, c in daily_costs)
        avg_daily = total_week / len(daily_costs) if daily_costs else 0
        trend = " -> ".join(f"EUR {c:.2f}" for _, c in reversed(daily_costs))

        msg = (
            f"*API Cost Summary — Weekly*\n\n"
            f"Total: EUR {total_week:.2f}\n"
            f"Avg daily: EUR {avg_daily:.2f}\n"
            f"7-day trend: {trend}"
        )
        await notify_admin(msg)
        logger.info(f"Weekly API cost summary sent: EUR {total_week:.2f}")

    except Exception as e:
        logger.error(f"Weekly API cost summary failed: {e}")


async def send_error_digest() -> None:
    """
    Daily error digest from structured logs.
    Runs daily at 22:00 UTC.
    """
    logger.info("Starting error digest job")

    try:
        from src.telegram.notifications import notify_admin

        errors: dict[str, int] = {}
        warnings: dict[str, int] = {}

        # Read from Redis error buffer if available
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.REDIS_URL)

            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            error_key = f"errors:{today}"
            warning_key = f"warnings:{today}"

            error_entries = await r.lrange(error_key, 0, -1)
            for entry in error_entries:
                msg_text = entry.decode("utf-8") if isinstance(entry, bytes) else str(entry)
                # Strip variable parts for deduplication
                pattern = _normalize_error_pattern(msg_text)
                errors[pattern] = errors.get(pattern, 0) + 1

            warning_entries = await r.lrange(warning_key, 0, -1)
            for entry in warning_entries:
                msg_text = entry.decode("utf-8") if isinstance(entry, bytes) else str(entry)
                pattern = _normalize_error_pattern(msg_text)
                warnings[pattern] = warnings.get(pattern, 0) + 1

            await r.aclose()
        except Exception as e:
            logger.warning(f"Redis error buffer unavailable: {e}")

        total_errors = sum(errors.values())
        total_warnings = sum(warnings.values())

        if total_errors == 0 and total_warnings == 0:
            today = datetime.now(timezone.utc).strftime("%b %d")
            await notify_admin(f"*Error Digest — {today}*\n\nClean day — no errors or warnings")
            logger.info("Error digest: clean day")
            return

        today = datetime.now(timezone.utc).strftime("%b %d")
        lines = [f"*Error Digest — {today}*\n"]
        lines.append(f"Total: {total_errors} errors, {total_warnings} warnings\n")

        if errors:
            lines.append("Top errors:")
            for pattern, count in sorted(errors.items(), key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"  {count}x {pattern}")

        if warnings:
            lines.append("\nTop warnings:")
            for pattern, count in sorted(warnings.items(), key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"  {count}x {pattern}")

        await notify_admin("\n".join(lines))
        logger.info(f"Error digest sent: {total_errors} errors, {total_warnings} warnings")

    except Exception as e:
        logger.error(f"Error digest failed: {e}")


def _normalize_error_pattern(msg: str) -> str:
    """Strip variable parts (UUIDs, timestamps, IDs) for deduplication."""
    import re
    # Replace UUIDs
    msg = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '<UUID>', msg)
    # Replace long hex strings
    msg = re.sub(r'[0-9a-f]{24,}', '<ID>', msg)
    # Replace ISO timestamps
    msg = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[.\d]*Z?', '<TS>', msg)
    # Truncate to reasonable length
    return msg[:200]


# =============================================================================
# PHASE C — DATA QUALITY JOBS
# =============================================================================


async def audit_knowledge_freshness() -> None:
    """
    Audit knowledge base file freshness and alert on stale data.
    Runs Monday 3:00 UTC.
    """
    logger.info("Starting KB freshness audit job")

    try:
        from src.cli.auto_refresh import cmd_kb_audit
        from src.telegram.notifications import notify_admin

        # cmd_kb_audit expects an args object but only uses output format
        class _FakeArgs:
            output = "json"

        result = cmd_kb_audit(_FakeArgs())
        summary = result.get("summary", {})
        stale = summary.get("stale", 0)
        aging = summary.get("aging", 0)
        health = result.get("health", "unknown")

        # Only alert if there are stale files
        if stale == 0 and aging == 0:
            logger.info(f"KB audit: healthy ({summary.get('total_files', 0)} files, all fresh)")
            return

        lines = [f"*KB Freshness Audit — {datetime.now(timezone.utc).strftime('%b %d')}*\n"]
        lines.append(f"Health: {health.upper()}")
        lines.append(f"Fresh (≤7d): {summary.get('fresh', 0)}")
        lines.append(f"Current (≤30d): {summary.get('current', 0)}")
        lines.append(f"Aging (≤90d): {aging}")
        lines.append(f"Stale (>90d): {stale}")

        # List stale files
        for industry, types in result.get("industries", {}).items():
            stale_types = [
                f"{t} ({info.get('days_old', '?')}d)"
                for t, info in types.items()
                if isinstance(info, dict) and info.get("freshness") in ("stale", "aging")
            ]
            if stale_types:
                lines.append(f"  {industry}: {', '.join(stale_types)}")

        await notify_admin("\n".join(lines))
        logger.info(f"KB audit alert sent: {stale} stale, {aging} aging")

    except Exception as e:
        logger.error(f"KB freshness audit failed: {e}")


async def run_db_consistency_audit() -> None:
    """
    Run database consistency checks and alert on issues.
    Runs Sunday 5:00 UTC.
    """
    logger.info("Starting DB consistency audit job")

    try:
        from src.cli.db_audit import run_audit
        from src.telegram.notifications import notify_admin

        result = await run_audit(fix=False)
        summary = result.get("summary", {})
        health = result.get("health", "unknown")

        tables_audited = summary.get("tables_audited", 0)
        tables_clean = summary.get("tables_clean", 0)
        tables_dirty = summary.get("tables_dirty", 0)
        invalid_rows = summary.get("total_invalid_rows", 0)

        if tables_dirty == 0:
            logger.info(f"DB audit: clean ({tables_audited} tables, 0 issues)")
            return

        today = datetime.now(timezone.utc).strftime("%b %d")
        lines = [f"*DB Audit — {today}*\n"]
        lines.append(f"Health: {health.upper()}")
        lines.append(f"Tables: {tables_audited} checked, {tables_clean} clean, {tables_dirty} with issues")
        lines.append(f"Invalid rows: {invalid_rows}")

        # Include issue details if available
        issues = result.get("issues", [])
        for issue in issues[:5]:
            lines.append(f"  - {issue.get('table', '?')}: {issue.get('description', '?')}")

        if tables_dirty > 0:
            lines.append("\nRun: make db-audit-fix")

        await notify_admin("\n".join(lines))
        logger.info(f"DB audit alert sent: {tables_dirty} dirty tables, {invalid_rows} invalid rows")

    except Exception as e:
        logger.error(f"DB consistency audit failed: {e}")


# =============================================================================
# PHASE D — GROWTH INTEL JOBS
# =============================================================================


async def generate_industry_heatmap() -> None:
    """
    30-day industry performance heatmap with trends.
    Runs Monday 7:45 UTC.
    """
    logger.info("Starting industry heatmap job")

    try:
        from src.config.supabase_client import get_async_supabase
        from src.telegram.notifications import notify_admin

        supabase = await get_async_supabase()
        now = datetime.now(timezone.utc)
        current_start = now - timedelta(days=30)
        prev_start = now - timedelta(days=60)

        # Current 30-day window
        current_result = await supabase.table("quiz_sessions").select(
            "id, industry, status, tier"
        ).gte("created_at", current_start.isoformat()).execute()

        current_sessions = current_result.data or []

        # Previous 30-day window
        prev_result = await supabase.table("quiz_sessions").select(
            "id, industry, status"
        ).gte(
            "created_at", prev_start.isoformat()
        ).lt(
            "created_at", current_start.isoformat()
        ).execute()

        prev_sessions = prev_result.data or []

        # Aggregate by industry
        def _aggregate(sessions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
            by_industry: dict[str, dict[str, Any]] = {}
            for s in sessions:
                ind = s.get("industry") or "unknown"
                if ind not in by_industry:
                    by_industry[ind] = {"leads": 0, "completed": 0}
                by_industry[ind]["leads"] += 1
                if s.get("status") == "completed":
                    by_industry[ind]["completed"] += 1
            return by_industry

        current_agg = _aggregate(current_sessions)
        prev_agg = _aggregate(prev_sessions)

        if not current_agg:
            logger.info("No sessions for heatmap")
            return

        # Build table
        lines = ["*Industry Heatmap — 30 Day View*\n"]
        lines.append("```")
        lines.append(f"{'Industry':<18} {'Leads':>5} {'Conv%':>6} {'Trend':>8}")

        hottest = ("", 0)
        best_converting = ("", 0.0)
        fastest_growing = ("", -999)

        for ind in sorted(current_agg, key=lambda x: current_agg[x]["leads"], reverse=True):
            data = current_agg[ind]
            leads = data["leads"]
            completed = data["completed"]
            conv_rate = round(completed / leads * 100) if leads else 0

            prev_leads = prev_agg.get(ind, {}).get("leads", 0)
            if prev_leads == 0 and leads > 0:
                trend_str = "NEW"
                trend_pct = 100
            elif prev_leads > 0:
                trend_pct = round((leads - prev_leads) / prev_leads * 100)
                if trend_pct > 5:
                    trend_str = f"↑ +{trend_pct}%"
                elif trend_pct < -5:
                    trend_str = f"↓ {trend_pct}%"
                else:
                    trend_str = "→ flat"
            else:
                trend_pct = 0
                trend_str = "→ flat"

            lines.append(f"{ind:<18} {leads:>5} {conv_rate:>5}% {trend_str:>8}")

            if leads > hottest[1]:
                hottest = (ind, leads)
            if conv_rate > best_converting[1]:
                best_converting = (ind, conv_rate)
            if trend_pct > fastest_growing[1]:
                fastest_growing = (ind, trend_pct)

        lines.append("```")
        lines.append(f"\nHottest: {hottest[0]} (volume)")
        lines.append(f"Best converting: {best_converting[0]} ({best_converting[1]:.0f}%)")
        lines.append(f"Fastest growing: {fastest_growing[0]} (+{fastest_growing[1]}%)")

        await notify_admin("\n".join(lines))
        logger.info("Industry heatmap sent")

    except Exception as e:
        logger.error(f"Industry heatmap failed: {e}")


async def detect_case_study_candidates() -> None:
    """
    Find high-quality report recipients who are ideal case study candidates.
    Runs Friday 9:00 UTC.
    """
    logger.info("Starting case study candidate detector")

    try:
        from src.config.supabase_client import get_async_supabase
        from src.telegram.notifications import notify_admin

        supabase = await get_async_supabase()
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)

        # Get reports completed this week
        reports_result = await supabase.table("reports").select(
            "id, quiz_session_id, results, quality_score"
        ).eq(
            "status", "completed"
        ).gte(
            "created_at", week_ago.isoformat()
        ).execute()

        reports = reports_result.data or []
        candidates: list[dict[str, Any]] = []

        for report in reports:
            results = report.get("results") or {}
            quality = report.get("quality_score") or results.get("quality_score", 0)
            readiness = results.get("ai_readiness_score") or results.get("readiness_score", 0)

            if quality < 8 or readiness < 7:
                continue

            # Get session info
            session_result = await supabase.table("quiz_sessions").select(
                "company_name, email, industry"
            ).eq("id", report["quiz_session_id"]).limit(1).execute()

            if not session_result.data:
                continue

            session = session_result.data[0]
            company = session.get("company_name")
            if not company:
                continue

            crb_score = results.get("crb_score", results.get("net_score", 0))

            candidates.append({
                "company": company,
                "industry": session.get("industry", "unknown"),
                "quality": quality,
                "readiness": readiness,
                "crb_score": crb_score,
                "email": session.get("email", ""),
            })

        if not candidates:
            logger.info("No case study candidates this week")
            return

        iso_week = datetime.now(timezone.utc).isocalendar()[1]
        lines = [f"*Case Study Candidates — Week {iso_week}*\n"]
        lines.append(f"{len(candidates)} new candidate(s) this week:\n")

        for c in candidates[:5]:
            lines.append(
                f"*{c['company']}* ({c['industry']})\n"
                f"  Report quality: {c['quality']}/10\n"
                f"  AI readiness: {c['readiness']}/10\n"
                f"  CRB score: {c['crb_score']}\n"
                f"  Contact: {c['email']}"
            )

        await notify_admin("\n".join(lines))
        logger.info(f"Case study detector found {len(candidates)} candidates")

    except Exception as e:
        logger.error(f"Case study detector failed: {e}")


# =============================================================================
# PHASE E — LONG-TERM JOBS
# =============================================================================


async def check_trend_freshness() -> None:
    """
    Monthly check on industry trend data freshness.
    Runs 1st of month at 2:00 UTC.
    """
    logger.info("Starting trend freshness check")

    try:
        from src.telegram.notifications import notify_admin

        trends_path = Path(__file__).parent.parent / "knowledge" / "insights" / "curated" / "trends.json"
        if not trends_path.exists():
            logger.warning("Trends file not found")
            return

        with open(trends_path) as f:
            data = json.load(f)

        insights = data.get("insights", [])
        now = datetime.now(timezone.utc)
        fresh = 0
        aging = 0
        stale_entries: list[dict[str, Any]] = []

        for insight in insights:
            # Check supporting_data dates
            dates = []
            for sd in insight.get("supporting_data", []):
                d = sd.get("date", "")
                if d:
                    dates.append(str(d))

            # Use last_updated from top level as fallback
            last_updated = data.get("last_updated", "")
            if last_updated:
                try:
                    if len(str(last_updated)) <= 10:
                        updated_dt = datetime.strptime(str(last_updated), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    else:
                        updated_dt = datetime.fromisoformat(str(last_updated).replace("Z", "+00:00"))
                    days_old = (now - updated_dt).days
                    if days_old <= 30:
                        fresh += 1
                    elif days_old <= 60:
                        aging += 1
                    else:
                        stale_entries.append({
                            "title": insight.get("title", "Unknown"),
                            "days_old": days_old,
                        })
                except (ValueError, TypeError):
                    aging += 1
            else:
                aging += 1

        month = now.strftime("%B %Y")
        lines = [f"*Trend Refresh — {month}*\n"]
        lines.append(f"Current trends: {len(insights)} entries")
        lines.append(f"  Fresh (<30d): {fresh}")
        lines.append(f"  Aging (30-60d): {aging}")
        lines.append(f"  Stale (>60d): {len(stale_entries)}")

        for entry in stale_entries:
            lines.append(f"    - \"{entry['title']}\" — {entry['days_old']} days old")

        if stale_entries:
            lines.append("\nAction: Refresh stale trends in knowledge base")

        await notify_admin("\n".join(lines))
        logger.info(f"Trend freshness: {fresh} fresh, {aging} aging, {len(stale_entries)} stale")

    except Exception as e:
        logger.error(f"Trend freshness check failed: {e}")


async def scan_vendor_coverage() -> None:
    """
    Scan vendor categories for coverage gaps and staleness.
    Runs Wednesday 3:00 UTC.
    """
    logger.info("Starting vendor coverage scan")

    try:
        from src.config.supabase_client import get_async_supabase
        from src.telegram.notifications import notify_admin

        supabase = await get_async_supabase()

        # Get vendor counts by category from Supabase
        vendors_result = await supabase.table("vendors").select(
            "id, category, slug, last_verified_at"
        ).execute()

        vendors = vendors_result.data or []

        # Count by category
        by_category: dict[str, list[dict[str, Any]]] = {}
        for v in vendors:
            cat = v.get("category") or "uncategorized"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(v)

        total_vendors = len(vendors)
        low_coverage: list[tuple[str, int]] = []
        stale_vendors: list[dict[str, Any]] = []

        now = datetime.now(timezone.utc)
        for cat, cat_vendors in by_category.items():
            if len(cat_vendors) < 5:
                low_coverage.append((cat, len(cat_vendors)))

            for v in cat_vendors:
                last_verified = v.get("last_verified_at")
                if last_verified:
                    try:
                        verified_dt = datetime.fromisoformat(
                            str(last_verified).replace("Z", "+00:00")
                        )
                        if (now - verified_dt).days > 90:
                            stale_vendors.append({
                                "slug": v.get("slug", "?"),
                                "last_verified": last_verified,
                            })
                    except (ValueError, TypeError):
                        pass

        if not low_coverage and not stale_vendors:
            logger.info(f"Vendor coverage healthy: {len(by_category)} categories, {total_vendors} vendors")
            return

        iso_week = now.isocalendar()[1]
        lines = [f"*Vendor Coverage — Week {iso_week}*\n"]
        lines.append(f"Categories: {len(by_category)}")
        lines.append(f"Total vendors: {total_vendors}")

        if low_coverage:
            lines.append("\nLow coverage categories:")
            for cat, count in sorted(low_coverage, key=lambda x: x[1]):
                lines.append(f"  {cat}: {count} vendors (target: 5+)")

        if stale_vendors:
            lines.append(f"\nStale vendors (>90d unverified): {len(stale_vendors)}")
            for v in stale_vendors[:5]:
                lines.append(f"  {v['slug']} — last verified {v['last_verified']}")

        await notify_admin("\n".join(lines))
        logger.info(f"Vendor coverage: {len(low_coverage)} low, {len(stale_vendors)} stale")

    except Exception as e:
        logger.error(f"Vendor coverage scan failed: {e}")


# =============================================================================
# SCHEDULER SETUP
# =============================================================================


def setup_scheduler():
    """
    Set up all scheduled jobs.
    Call this during application startup.
    """
    scheduler = get_scheduler()

    # Follow-up emails - daily at 10 AM UTC
    scheduler.add_job(
        send_follow_up_emails,
        CronTrigger(hour=10, minute=0),
        id="follow_up_emails",
        name="Send 7-day follow-up emails",
        replace_existing=True,
    )

    # Storage cleanup - daily at 3 AM UTC
    scheduler.add_job(
        cleanup_old_pdfs,
        CronTrigger(hour=3, minute=0),
        id="storage_cleanup",
        name="Clean up old PDFs",
        replace_existing=True,
    )

    # Expired quiz cleanup - daily at 4 AM UTC
    scheduler.add_job(
        cleanup_expired_quiz_sessions,
        CronTrigger(hour=4, minute=0),
        id="quiz_cleanup",
        name="Clean up expired quiz sessions",
        replace_existing=True,
    )

    # Vendor pricing refresh - weekly on Sundays at 2 AM UTC
    scheduler.add_job(
        refresh_vendor_pricing,
        CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="vendor_refresh",
        name="Refresh vendor pricing from websites",
        replace_existing=True,
    )

    # Morning briefing - daily at 7 AM UTC
    scheduler.add_job(
        send_morning_briefing,
        CronTrigger(hour=7, minute=0),
        id="morning_briefing",
        name="Send morning briefing via Telegram",
        replace_existing=True,
    )

    # --- Phase A: Revenue ---

    # Weekly pipeline report - Monday 7:30 UTC
    scheduler.add_job(
        generate_pipeline_report,
        CronTrigger(day_of_week="mon", hour=7, minute=30),
        id="pipeline_report",
        name="Weekly pipeline report",
        replace_existing=True,
    )

    # Quiz re-engagement - daily 11:00 UTC
    scheduler.add_job(
        send_quiz_reengagement,
        CronTrigger(hour=11, minute=0),
        id="quiz_reengagement",
        name="Abandoned quiz re-engagement emails",
        replace_existing=True,
    )

    # Upsell scanner - Wednesday 8:00 UTC
    scheduler.add_job(
        scan_upsell_candidates,
        CronTrigger(day_of_week="wed", hour=8, minute=0),
        id="upsell_scanner",
        name="Scan quick-tier customers for upsell",
        replace_existing=True,
    )

    # --- Phase B: Ops ---

    # KB freshness audit - Monday 3:00 UTC
    scheduler.add_job(
        audit_knowledge_freshness,
        CronTrigger(day_of_week="mon", hour=3, minute=0),
        id="kb_freshness_audit",
        name="Knowledge base freshness audit",
        replace_existing=True,
    )

    # API cost tracker - daily 23:00 UTC
    scheduler.add_job(
        track_api_costs_daily,
        CronTrigger(hour=23, minute=0),
        id="api_cost_daily",
        name="Daily API cost tracking",
        replace_existing=True,
    )

    # API cost weekly summary - Monday 7:15 UTC
    scheduler.add_job(
        send_api_cost_weekly_summary,
        CronTrigger(day_of_week="mon", hour=7, minute=15),
        id="api_cost_weekly",
        name="Weekly API cost summary",
        replace_existing=True,
    )

    # Error digest - daily 22:00 UTC
    scheduler.add_job(
        send_error_digest,
        CronTrigger(hour=22, minute=0),
        id="error_digest",
        name="Daily error digest",
        replace_existing=True,
    )

    # --- Phase C: Data Quality ---

    # DB consistency audit - Sunday 5:00 UTC
    scheduler.add_job(
        run_db_consistency_audit,
        CronTrigger(day_of_week="sun", hour=5, minute=0),
        id="db_consistency_audit",
        name="Database consistency audit",
        replace_existing=True,
    )

    # --- Phase D: Growth Intel ---

    # Industry heatmap - Monday 7:45 UTC
    scheduler.add_job(
        generate_industry_heatmap,
        CronTrigger(day_of_week="mon", hour=7, minute=45),
        id="industry_heatmap",
        name="30-day industry heatmap",
        replace_existing=True,
    )

    # Case study candidates - Friday 9:00 UTC
    scheduler.add_job(
        detect_case_study_candidates,
        CronTrigger(day_of_week="fri", hour=9, minute=0),
        id="case_study_detector",
        name="Detect case study candidates",
        replace_existing=True,
    )

    # --- Phase E: Long-term ---

    # Trend freshness - monthly 1st at 2:00 UTC
    scheduler.add_job(
        check_trend_freshness,
        CronTrigger(day=1, hour=2, minute=0),
        id="trend_freshness",
        name="Monthly industry trend freshness check",
        replace_existing=True,
    )

    # Vendor coverage scan - Wednesday 3:00 UTC
    scheduler.add_job(
        scan_vendor_coverage,
        CronTrigger(day_of_week="wed", hour=3, minute=0),
        id="vendor_coverage",
        name="Weekly vendor coverage gap scan",
        replace_existing=True,
    )

    logger.info("Scheduler configured with 17 jobs")
    return scheduler


def start_scheduler():
    """Start the scheduler if not already running."""
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")
        _scheduler = None


# =============================================================================
# MANUAL TRIGGER FUNCTIONS (testing/admin)
# =============================================================================


async def trigger_follow_up_emails() -> None:
    """Manually trigger follow-up email job."""
    await send_follow_up_emails()


async def trigger_storage_cleanup() -> None:
    """Manually trigger storage cleanup job."""
    await cleanup_old_pdfs()


async def trigger_quiz_cleanup() -> None:
    """Manually trigger quiz session cleanup job."""
    await cleanup_expired_quiz_sessions()


async def trigger_vendor_refresh() -> None:
    """Manually trigger vendor pricing refresh job."""
    await refresh_vendor_pricing()


async def trigger_pipeline_report() -> None:
    """Manually trigger weekly pipeline report."""
    await generate_pipeline_report()


async def trigger_quiz_reengagement() -> None:
    """Manually trigger quiz re-engagement emails."""
    await send_quiz_reengagement()


async def trigger_upsell_scanner() -> None:
    """Manually trigger upsell candidate scan."""
    await scan_upsell_candidates()


async def trigger_api_cost_daily() -> None:
    """Manually trigger daily API cost tracking."""
    await track_api_costs_daily()


async def trigger_api_cost_weekly() -> None:
    """Manually trigger weekly API cost summary."""
    await send_api_cost_weekly_summary()


async def trigger_error_digest() -> None:
    """Manually trigger error digest."""
    await send_error_digest()


async def trigger_kb_audit() -> None:
    """Manually trigger KB freshness audit."""
    await audit_knowledge_freshness()


async def trigger_db_audit() -> None:
    """Manually trigger DB consistency audit."""
    await run_db_consistency_audit()


async def trigger_industry_heatmap() -> None:
    """Manually trigger industry heatmap."""
    await generate_industry_heatmap()


async def trigger_case_study_detector() -> None:
    """Manually trigger case study candidate detection."""
    await detect_case_study_candidates()


async def trigger_trend_freshness() -> None:
    """Manually trigger trend freshness check."""
    await check_trend_freshness()


async def trigger_vendor_coverage() -> None:
    """Manually trigger vendor coverage scan."""
    await scan_vendor_coverage()
