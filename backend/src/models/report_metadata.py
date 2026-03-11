"""
Report Metadata Models — internal analytics capture.

Flat denormalized table optimized for aggregate queries (GROUP BY industry, AVG(score)).
Service-role only — not client-facing.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()

# USD→EUR conversion factor (approximate, good enough for internal cost tracking)
_USD_TO_EUR = Decimal("0.92")


class ReportMetadataCreate(BaseModel):
    """Input model used at insertion time."""

    report_id: str
    quiz_session_id: str

    # Company profile
    industry: Optional[str] = None
    company_name: Optional[str] = None
    employee_count: Optional[str] = None
    annual_revenue: Optional[str] = None
    tier: str

    # CRB scores
    ai_readiness_score: Optional[Decimal] = None
    customer_value_score: Optional[Decimal] = None
    business_health_score: Optional[Decimal] = None
    value_potential_min: Optional[Decimal] = None
    value_potential_max: Optional[Decimal] = None

    # Content counts
    findings_count: int = 0
    recommendations_count: int = 0
    playbooks_count: int = 0

    # Denormalized top-level data
    top_finding_categories: List[str] = Field(default_factory=list)
    recommended_vendor_names: List[str] = Field(default_factory=list)
    primary_goals: List[str] = Field(default_factory=list)

    # Generation performance
    generation_duration_seconds: Optional[Decimal] = None
    total_tokens: Optional[int] = None
    estimated_cost_eur: Optional[Decimal] = None
    validation_passed: Optional[bool] = None

    # Quiz context
    current_tools: List[str] = Field(default_factory=list)
    biggest_challenge: Optional[str] = None
    implementation_timeline: Optional[str] = None
    budget_comfort: Optional[str] = None

    @classmethod
    def from_report_context(
        cls,
        *,
        report_id: str,
        quiz_session_id: str,
        tier: str,
        context: Dict[str, Any],
        executive_summary: Dict[str, Any],
        findings: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        token_tracker: Any,
        generation_started_at: Optional[str],
        generation_completed_at: datetime,
    ) -> ReportMetadataCreate:
        """Extract all metadata fields from report generation artifacts."""
        answers: Dict[str, Any] = context.get("answers", {})

        # CRB scores from executive summary
        value_potential = executive_summary.get("total_value_potential", {})

        # Deduplicated finding categories
        categories: List[str] = list(dict.fromkeys(
            f.get("category", "")
            for f in findings
            if f.get("category")
        ))

        # Vendor names from recommendations
        vendor_names: List[str] = list(dict.fromkeys(
            r.get("vendor_name") or r.get("vendor", {}).get("name", "")
            for r in recommendations
            if r.get("vendor_name") or r.get("vendor", {}).get("name")
        ))

        # Generation duration
        duration: Optional[Decimal] = None
        if generation_started_at:
            try:
                started = datetime.fromisoformat(generation_started_at)
                delta = generation_completed_at - started
                duration = Decimal(str(round(delta.total_seconds(), 2)))
            except (ValueError, TypeError):
                pass

        # Token usage
        token_summary = token_tracker.get_summary()
        total_tokens = token_summary.get("total_tokens", 0)
        cost_usd = Decimal(str(token_summary.get("estimated_cost_usd", 0)))
        cost_eur = round(cost_usd * _USD_TO_EUR, 4)

        # Playbooks count — check findings for playbook data
        playbooks_count = sum(
            1 for f in findings if f.get("playbook") or f.get("implementation_playbook")
        )

        return cls(
            report_id=report_id,
            quiz_session_id=quiz_session_id,
            tier=tier,
            industry=answers.get("industry") or context.get("industry"),
            company_name=context.get("company_name"),
            employee_count=answers.get("employee_count"),
            annual_revenue=answers.get("annual_revenue"),
            ai_readiness_score=_to_decimal(executive_summary.get("ai_readiness_score")),
            customer_value_score=_to_decimal(executive_summary.get("customer_value_score")),
            business_health_score=_to_decimal(executive_summary.get("business_health_score")),
            value_potential_min=_to_decimal(value_potential.get("min")),
            value_potential_max=_to_decimal(value_potential.get("max")),
            findings_count=len(findings),
            recommendations_count=len(recommendations),
            playbooks_count=playbooks_count,
            top_finding_categories=categories,
            recommended_vendor_names=vendor_names,
            primary_goals=answers.get("primary_goals", []),
            generation_duration_seconds=duration,
            total_tokens=total_tokens,
            estimated_cost_eur=cost_eur,
            validation_passed=None,  # Set by caller if quality validation ran
            current_tools=answers.get("current_tools", []),
            biggest_challenge=answers.get("biggest_challenge"),
            implementation_timeline=answers.get("implementation_timeline"),
            budget_comfort=answers.get("budget_comfort"),
        )

    def to_db_row(self) -> Dict[str, Any]:
        """Convert to dict suitable for Supabase insert."""
        data = self.model_dump()
        # Convert Decimals to float for JSON serialization
        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = float(value)
        return data


class ReportMetadata(ReportMetadataCreate):
    """Full model including DB-generated fields."""

    id: str
    created_at: datetime


def _to_decimal(value: Any) -> Optional[Decimal]:
    """Safely convert a value to Decimal."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (ValueError, TypeError, ArithmeticError):
        return None


async def save_report_metadata(metadata: ReportMetadataCreate) -> None:
    """
    Persist report metadata to Supabase.

    Fire-and-forget: logs errors but never raises.
    """
    from src.config.supabase_client import get_async_supabase

    try:
        supabase = await get_async_supabase()
        await supabase.table("report_metadata").insert(
            metadata.to_db_row()
        ).execute()
        logger.info(
            "report_metadata_saved",
            report_id=metadata.report_id,
            industry=metadata.industry,
            tier=metadata.tier,
        )
    except Exception as e:
        logger.warning(
            "report_metadata_save_failed",
            error=str(e),
            report_id=metadata.report_id,
        )
