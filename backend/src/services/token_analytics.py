"""
Token Analytics Service

Provides analytics and cost tracking for AI API usage across reports.
Implements TICKET-008: Enhanced token tracking storage.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

from src.config.supabase_client import get_async_supabase
from src.config.model_routing import MODELS, TokenTracker

logger = logging.getLogger(__name__)


class TokenAnalyticsService:
    """
    Service for analyzing token usage and costs across reports.

    Features:
    - Aggregate usage by time period
    - Cost breakdown by model
    - Cost trends over time
    - Per-tier analysis
    """

    # Model pricing (same as TokenTracker for consistency)
    PRICING = {
        MODELS["haiku"]: {"input": 0.80, "output": 4.00, "name": "Haiku"},
        MODELS["sonnet"]: {"input": 3.00, "output": 15.00, "name": "Sonnet"},
        MODELS["opus"]: {"input": 15.00, "output": 75.00, "name": "Opus"},
    }

    @classmethod
    async def get_usage_summary(
        cls,
        days: int = 30,
        tier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get aggregate token usage summary for a time period.

        Args:
            days: Number of days to look back
            tier: Optional filter by report tier ("quick" or "full")
        """
        supabase = await get_async_supabase()

        # Calculate date range
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        # Query reports with token usage
        query = supabase.table("reports").select(
            "id, tier, token_usage, generation_completed_at"
        ).gte("generation_completed_at", start_date).eq("status", "completed")

        if tier:
            query = query.eq("tier", tier)

        result = await query.execute()
        reports = result.data or []

        # Aggregate metrics
        total_input = 0
        total_output = 0
        total_cost = 0.0
        by_model = defaultdict(lambda: {"input": 0, "output": 0, "cost": 0.0, "count": 0})
        by_task = defaultdict(lambda: {"input": 0, "output": 0, "count": 0})
        by_tier = defaultdict(lambda: {"input": 0, "output": 0, "cost": 0.0, "count": 0})

        for report in reports:
            token_usage = report.get("token_usage", {})
            if not token_usage:
                continue

            usage_list = token_usage.get("usage", [])
            summary = token_usage.get("summary", {})
            report_tier = report.get("tier", "quick")

            # Add to totals
            total_input += summary.get("total_input_tokens", 0)
            total_output += summary.get("total_output_tokens", 0)
            total_cost += summary.get("estimated_cost_usd", 0)

            # Aggregate by model
            by_model_data = summary.get("by_model", {})
            for model_id, model_data in by_model_data.items():
                by_model[model_id]["input"] += model_data.get("input", 0)
                by_model[model_id]["output"] += model_data.get("output", 0)
                by_model[model_id]["cost"] += model_data.get("estimated_cost_usd", 0)
                by_model[model_id]["count"] += 1

            # Aggregate by task
            for usage in usage_list:
                task = usage.get("task", "unknown")
                by_task[task]["input"] += usage.get("input_tokens", 0)
                by_task[task]["output"] += usage.get("output_tokens", 0)
                by_task[task]["count"] += 1

            # Aggregate by tier
            by_tier[report_tier]["input"] += summary.get("total_input_tokens", 0)
            by_tier[report_tier]["output"] += summary.get("total_output_tokens", 0)
            by_tier[report_tier]["cost"] += summary.get("estimated_cost_usd", 0)
            by_tier[report_tier]["count"] += 1

        # Calculate averages
        report_count = len(reports)
        avg_cost_per_report = total_cost / report_count if report_count > 0 else 0
        avg_tokens_per_report = (total_input + total_output) / report_count if report_count > 0 else 0

        return {
            "period": {
                "days": days,
                "start_date": start_date,
                "end_date": datetime.utcnow().isoformat(),
            },
            "totals": {
                "reports_generated": report_count,
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_tokens": total_input + total_output,
                "total_cost_usd": round(total_cost, 2),
            },
            "averages": {
                "cost_per_report_usd": round(avg_cost_per_report, 4),
                "tokens_per_report": int(avg_tokens_per_report),
            },
            "by_model": dict(by_model),
            "by_task": dict(by_task),
            "by_tier": dict(by_tier),
        }

    @classmethod
    async def get_cost_trend(
        cls,
        days: int = 30,
        granularity: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        Get cost trend over time.

        Args:
            days: Number of days to analyze
            granularity: "day" or "week"
        """
        supabase = await get_async_supabase()

        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        result = await supabase.table("reports").select(
            "token_usage, generation_completed_at"
        ).gte("generation_completed_at", start_date).eq("status", "completed").execute()

        reports = result.data or []

        # Group by date
        daily_costs = defaultdict(lambda: {"cost": 0.0, "tokens": 0, "reports": 0})

        for report in reports:
            token_usage = report.get("token_usage", {})
            completed_at = report.get("generation_completed_at")

            if not completed_at or not token_usage:
                continue

            # Parse date
            date_str = completed_at[:10]  # YYYY-MM-DD

            summary = token_usage.get("summary", {})
            daily_costs[date_str]["cost"] += summary.get("estimated_cost_usd", 0)
            daily_costs[date_str]["tokens"] += summary.get("total_tokens", 0)
            daily_costs[date_str]["reports"] += 1

        # Convert to sorted list
        trend = [
            {
                "date": date,
                "cost_usd": round(data["cost"], 4),
                "tokens": data["tokens"],
                "reports": data["reports"],
            }
            for date, data in sorted(daily_costs.items())
        ]

        # Aggregate by week if requested
        if granularity == "week":
            weekly_costs = defaultdict(lambda: {"cost": 0.0, "tokens": 0, "reports": 0})
            for item in trend:
                date = datetime.fromisoformat(item["date"])
                week_start = (date - timedelta(days=date.weekday())).strftime("%Y-%m-%d")
                weekly_costs[week_start]["cost"] += item["cost_usd"]
                weekly_costs[week_start]["tokens"] += item["tokens"]
                weekly_costs[week_start]["reports"] += item["reports"]

            trend = [
                {
                    "week_start": week,
                    "cost_usd": round(data["cost"], 4),
                    "tokens": data["tokens"],
                    "reports": data["reports"],
                }
                for week, data in sorted(weekly_costs.items())
            ]

        return trend

    @classmethod
    async def get_model_efficiency(cls, days: int = 30) -> Dict[str, Any]:
        """
        Analyze model efficiency - which models are being used for which tasks.

        Helps identify if model routing is working correctly.
        """
        supabase = await get_async_supabase()

        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        result = await supabase.table("reports").select(
            "tier, token_usage"
        ).gte("generation_completed_at", start_date).eq("status", "completed").execute()

        reports = result.data or []

        # Track task -> model usage
        task_model_usage = defaultdict(lambda: defaultdict(int))

        for report in reports:
            token_usage = report.get("token_usage", {})
            usage_list = token_usage.get("usage", [])

            for usage in usage_list:
                task = usage.get("task", "unknown")
                model = usage.get("model", "unknown")
                task_model_usage[task][model] += 1

        # Format output
        efficiency = {}
        for task, models in task_model_usage.items():
            efficiency[task] = {
                "models_used": dict(models),
                "primary_model": max(models, key=models.get) if models else "unknown",
                "total_calls": sum(models.values()),
            }

        # Check for misrouted calls (e.g., Opus for simple tasks)
        misrouted = []
        simple_tasks = ["parse_quiz_responses", "extract_industry", "validate_json"]
        for task in simple_tasks:
            if task in efficiency:
                for model, count in efficiency[task]["models_used"].items():
                    if "opus" in model.lower():
                        misrouted.append({
                            "task": task,
                            "model": model,
                            "count": count,
                            "issue": "Opus used for simple task - should use Haiku"
                        })

        return {
            "task_model_breakdown": efficiency,
            "potential_misrouted_calls": misrouted,
            "optimization_suggestions": cls._get_optimization_suggestions(efficiency),
        }

    @classmethod
    def _get_optimization_suggestions(cls, efficiency: Dict) -> List[str]:
        """Generate optimization suggestions based on usage patterns."""
        suggestions = []

        # Check for expensive model overuse
        opus_usage = sum(
            data.get("models_used", {}).get(MODELS["opus"], 0)
            for data in efficiency.values()
        )
        sonnet_usage = sum(
            data.get("models_used", {}).get(MODELS["sonnet"], 0)
            for data in efficiency.values()
        )
        haiku_usage = sum(
            data.get("models_used", {}).get(MODELS["haiku"], 0)
            for data in efficiency.values()
        )

        total = opus_usage + sonnet_usage + haiku_usage
        if total > 0:
            opus_pct = opus_usage / total * 100
            haiku_pct = haiku_usage / total * 100

            if opus_pct > 10:
                suggestions.append(
                    f"Opus usage is {opus_pct:.1f}% - consider moving more tasks to Sonnet"
                )

            if haiku_pct < 30:
                suggestions.append(
                    f"Haiku usage is only {haiku_pct:.1f}% - consider routing more simple tasks to Haiku"
                )

        return suggestions

    @classmethod
    async def get_report_cost_breakdown(cls, report_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed cost breakdown for a specific report."""
        supabase = await get_async_supabase()

        result = await supabase.table("reports").select(
            "id, tier, token_usage, generation_completed_at"
        ).eq("id", report_id).single().execute()

        if not result.data:
            return None

        report = result.data
        token_usage = report.get("token_usage", {})

        if not token_usage:
            return {
                "report_id": report_id,
                "message": "No token usage data available for this report"
            }

        # Format detailed breakdown
        usage_list = token_usage.get("usage", [])
        summary = token_usage.get("summary", {})

        task_costs = []
        for usage in usage_list:
            model = usage.get("model", "unknown")
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

            # Calculate cost
            pricing = cls.PRICING.get(model, {"input": 3.0, "output": 15.0, "name": "Unknown"})
            cost = (input_tokens / 1_000_000) * pricing["input"] + (output_tokens / 1_000_000) * pricing["output"]

            task_costs.append({
                "task": usage.get("task", "unknown"),
                "model": pricing.get("name", model),
                "model_id": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": round(cost, 6),
            })

        # Sort by cost (most expensive first)
        task_costs.sort(key=lambda x: x["cost_usd"], reverse=True)

        return {
            "report_id": report_id,
            "tier": report.get("tier"),
            "generated_at": report.get("generation_completed_at"),
            "summary": {
                "total_tokens": summary.get("total_tokens", 0),
                "total_cost_usd": summary.get("estimated_cost_usd", 0),
                "task_count": len(usage_list),
            },
            "task_breakdown": task_costs,
            "most_expensive_task": task_costs[0] if task_costs else None,
        }


# Convenience functions for common operations

async def get_monthly_cost_summary() -> Dict[str, Any]:
    """Get token usage summary for the last 30 days."""
    return await TokenAnalyticsService.get_usage_summary(days=30)


async def get_weekly_cost_trend() -> List[Dict[str, Any]]:
    """Get weekly cost trend for the last 30 days."""
    return await TokenAnalyticsService.get_cost_trend(days=30, granularity="week")


async def check_model_efficiency() -> Dict[str, Any]:
    """Check if model routing is optimized."""
    return await TokenAnalyticsService.get_model_efficiency(days=30)
