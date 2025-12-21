"""
SelfImproveService - The learning engine for agent expertise.

After each analysis, this service:
1. Records what happened (tools used, findings, recommendations)
2. Updates expertise based on patterns observed
3. Distills insights that improve future analyses

This is what makes the CRB agent an "agent expert" rather than
a generic agent that forgets after each run.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from anthropic import Anthropic

from src.config.settings import settings
from .store import get_expertise_store, ExpertiseStore
from .schemas import (
    IndustryExpertise,
    VendorExpertise,
    ExecutionExpertise,
    AnalysisRecord,
    PainPointPattern,
    ProcessInsight,
    RecommendationPattern,
    VendorFit,
)

logger = logging.getLogger(__name__)


class SelfImproveService:
    """
    Learns from each analysis execution and updates expertise.

    The learning loop:
    1. Record the analysis (what was discovered, recommended, etc.)
    2. Update industry expertise (pain points, patterns, anti-patterns)
    3. Update vendor expertise (what works for which use cases)
    4. Update execution expertise (tool effectiveness, phase insights)
    """

    def __init__(self, store: Optional[ExpertiseStore] = None):
        self.store = store or get_expertise_store()
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def learn_from_analysis(
        self,
        audit_id: str,
        industry: str,
        company_size: str,
        context: Dict[str, Any],
        execution_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Main entry point: Learn from a completed analysis.

        Args:
            audit_id: The audit identifier
            industry: Industry of the analyzed company
            company_size: Size of the company
            context: The full context dict from CRB agent (findings, recommendations, etc.)
            execution_metrics: Metrics about the execution (tools used, tokens, etc.)

        Returns:
            Summary of what was learned
        """
        logger.info(f"Learning from analysis {audit_id} for {industry}")

        # Step 1: Create and save the analysis record
        record = self._create_analysis_record(
            audit_id, industry, company_size, context, execution_metrics
        )
        self.store.save_analysis_record(record)

        # Step 2: Update industry expertise
        industry_updates = self._update_industry_expertise(record)

        # Step 3: Update vendor expertise
        vendor_updates = self._update_vendor_expertise(record)

        # Step 4: Update execution expertise
        execution_updates = self._update_execution_expertise(record)

        # Step 5: Optional LLM reflection for deeper insights
        reflection = await self._reflect_on_analysis(record)

        return {
            "audit_id": audit_id,
            "industry": industry,
            "learned": {
                "industry_updates": industry_updates,
                "vendor_updates": vendor_updates,
                "execution_updates": execution_updates,
                "reflection": reflection,
            },
        }

    def _create_analysis_record(
        self,
        audit_id: str,
        industry: str,
        company_size: str,
        context: Dict[str, Any],
        execution_metrics: Dict[str, Any],
    ) -> AnalysisRecord:
        """Create a record of this analysis for learning."""

        # Extract pain points from findings
        pain_points = []
        for finding in context.get("findings", []):
            if finding.get("type") == "pain_point" or finding.get("category") == "issue":
                pain_points.append(finding.get("title", finding.get("name", "")))

        # Extract processes analyzed
        processes = []
        for finding in context.get("findings", []):
            if process := finding.get("process"):
                processes.append(process)

        # Extract recommendations with details
        recommendations = []
        for rec in context.get("recommendations", []):
            recommendations.append({
                "title": rec.get("title", ""),
                "type": rec.get("type", ""),
                "priority": rec.get("priority", ""),
                "vendors": rec.get("vendors", []),
                "roi": rec.get("roi", {}),
            })

        # Extract vendors recommended
        vendors = []
        for rec in context.get("recommendations", []):
            if rec_vendors := rec.get("vendors", []):
                vendors.extend([v.get("name", v) if isinstance(v, dict) else v for v in rec_vendors])

        return AnalysisRecord(
            audit_id=audit_id,
            industry=industry,
            company_size=company_size,
            pain_points_found=pain_points,
            processes_analyzed=list(set(processes)),
            recommendations_made=recommendations,
            vendors_recommended=list(set(vendors)),
            ai_readiness_score=context.get("ai_readiness_score", 50),
            total_potential_savings=context.get("total_potential_savings", 0),
            findings_count=len(context.get("findings", [])),
            tools_used=execution_metrics.get("tools_used", {}),
            token_usage=execution_metrics.get("token_usage", {}),
            phases_completed=execution_metrics.get("phases_completed", []),
            errors_encountered=execution_metrics.get("errors", []),
        )

    def _update_industry_expertise(self, record: AnalysisRecord) -> Dict[str, Any]:
        """Update industry expertise based on the analysis."""
        expertise = self.store.get_industry_expertise(record.industry)
        updates = {"pain_points": 0, "processes": 0, "patterns": 0}

        # Increment analysis count
        expertise.total_analyses += 1

        # Update pain points
        for pain_point in record.pain_points_found:
            if pain_point in expertise.pain_points:
                expertise.pain_points[pain_point].frequency += 1
                expertise.pain_points[pain_point].last_seen = datetime.utcnow()
            else:
                expertise.pain_points[pain_point] = PainPointPattern(
                    name=pain_point,
                    frequency=1,
                )
            updates["pain_points"] += 1

        # Update process insights
        for process in record.processes_analyzed:
            if process in expertise.processes:
                expertise.processes[process].automation_potential_observed.append(
                    record.ai_readiness_score
                )
            else:
                expertise.processes[process] = ProcessInsight(
                    process_name=process,
                    automation_potential_observed=[record.ai_readiness_score],
                )
            updates["processes"] += 1

        # Update average metrics (running average)
        n = expertise.total_analyses
        expertise.avg_ai_readiness = (
            (expertise.avg_ai_readiness * (n - 1) + record.ai_readiness_score) / n
        )
        expertise.avg_potential_savings = (
            (expertise.avg_potential_savings * (n - 1) + record.total_potential_savings) / n
        )

        # Update company size specific data
        size = record.company_size or "unknown"
        if size not in expertise.size_specific:
            expertise.size_specific[size] = {
                "count": 0,
                "avg_readiness": 0,
                "common_pain_points": [],
            }
        size_data = expertise.size_specific[size]
        size_data["count"] += 1
        size_data["avg_readiness"] = (
            (size_data["avg_readiness"] * (size_data["count"] - 1) + record.ai_readiness_score)
            / size_data["count"]
        )
        # Track pain points by size
        for pp in record.pain_points_found[:3]:  # Top 3
            if pp not in size_data["common_pain_points"]:
                size_data["common_pain_points"].append(pp)
                if len(size_data["common_pain_points"]) > 10:
                    size_data["common_pain_points"] = size_data["common_pain_points"][-10:]

        # Extract recommendation patterns
        for rec in record.recommendations_made:
            if rec.get("title"):
                pattern = RecommendationPattern(
                    pattern=f"For {record.company_size} {record.industry} companies",
                    recommendation=rec["title"],
                    context={
                        "company_size": record.company_size,
                        "ai_readiness": record.ai_readiness_score,
                    },
                )
                # Check if similar pattern exists
                similar = [p for p in expertise.effective_patterns if p.recommendation == rec["title"]]
                if similar:
                    similar[0].frequency += 1
                else:
                    expertise.effective_patterns.append(pattern)
                    updates["patterns"] += 1

        # Keep effective_patterns trimmed
        if len(expertise.effective_patterns) > 50:
            expertise.effective_patterns = sorted(
                expertise.effective_patterns,
                key=lambda p: p.frequency,
                reverse=True
            )[:50]

        self.store.save_industry_expertise(expertise)
        return updates

    def _update_vendor_expertise(self, record: AnalysisRecord) -> Dict[str, Any]:
        """Update vendor expertise based on recommendations."""
        expertise = self.store.get_vendor_expertise()
        updates = {"vendors_updated": 0}

        expertise.total_recommendations += len(record.vendors_recommended)

        for vendor_name in record.vendors_recommended:
            if vendor_name not in expertise.vendors:
                expertise.vendors[vendor_name] = VendorFit(vendor_name=vendor_name)

            vendor = expertise.vendors[vendor_name]
            vendor.recommendation_count += 1

            # Track company size fit
            if record.company_size and record.company_size not in vendor.company_size_fit:
                vendor.company_size_fit.append(record.company_size)

            updates["vendors_updated"] += 1

        self.store.save_vendor_expertise(expertise)
        return updates

    def _update_execution_expertise(self, record: AnalysisRecord) -> Dict[str, Any]:
        """Update execution expertise based on how the analysis ran."""
        expertise = self.store.get_execution_expertise()
        updates = {"tools_tracked": 0}

        expertise.total_executions += 1

        # Update tool success rates
        for tool_name, usage_count in record.tools_used.items():
            if tool_name not in expertise.tool_success_rates:
                expertise.tool_success_rates[tool_name] = 1.0  # Start optimistic

            # If tool was used without errors, it's successful
            had_errors = any(tool_name in err for err in record.errors_encountered)
            if had_errors:
                # Decay success rate
                current = expertise.tool_success_rates[tool_name]
                expertise.tool_success_rates[tool_name] = current * 0.9
            else:
                # Boost success rate (slowly)
                current = expertise.tool_success_rates[tool_name]
                expertise.tool_success_rates[tool_name] = min(1.0, current * 1.01)

            updates["tools_tracked"] += 1

        # Track failure patterns
        for error in record.errors_encountered:
            if error not in expertise.failure_patterns:
                expertise.failure_patterns.append(error)
                if len(expertise.failure_patterns) > 100:
                    expertise.failure_patterns = expertise.failure_patterns[-100:]

        self.store.save_execution_expertise(expertise)
        return updates

    async def _reflect_on_analysis(self, record: AnalysisRecord) -> Optional[str]:
        """
        Optional LLM reflection for deeper insights.

        This is additive - if it fails, we still have the rule-based updates.
        Uses a small model to minimize cost.
        """
        try:
            # Get current expertise for context
            expertise = self.store.get_industry_expertise(record.industry)

            prompt = f"""You are analyzing a completed CRB (Cost/Risk/Benefit) analysis to extract learnings.

ANALYSIS SUMMARY:
- Industry: {record.industry}
- Company Size: {record.company_size}
- AI Readiness Score: {record.ai_readiness_score}
- Pain Points Found: {', '.join(record.pain_points_found[:5]) if record.pain_points_found else 'None'}
- Recommendations Made: {len(record.recommendations_made)}
- Vendors Recommended: {', '.join(record.vendors_recommended[:5]) if record.vendors_recommended else 'None'}

CURRENT EXPERTISE (analyses so far: {expertise.total_analyses}):
- Common pain points: {list(expertise.pain_points.keys())[:5]}
- Confidence level: {expertise.confidence}

What is ONE key insight from this analysis that should inform future {record.industry} analyses?
Be specific and actionable. One sentence only."""

            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Fast, cheap model for reflection
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}],
            )

            insight = response.content[0].text.strip()
            logger.info(f"LLM reflection for {record.audit_id}: {insight}")
            return insight

        except Exception as e:
            logger.warning(f"LLM reflection failed (non-critical): {e}")
            return None

    def get_expertise_summary(self, industry: str) -> Dict[str, Any]:
        """Get a summary of current expertise for display/debugging."""
        industry_exp = self.store.get_industry_expertise(industry)
        vendor_exp = self.store.get_vendor_expertise()
        exec_exp = self.store.get_execution_expertise()

        return {
            "industry": {
                "name": industry,
                "analyses": industry_exp.total_analyses,
                "confidence": industry_exp.confidence,
                "top_pain_points": sorted(
                    [(k, v.frequency) for k, v in industry_exp.pain_points.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                "avg_ai_readiness": round(industry_exp.avg_ai_readiness, 1),
            },
            "vendors": {
                "total_recommendations": vendor_exp.total_recommendations,
                "most_recommended": sorted(
                    [(k, v.recommendation_count) for k, v in vendor_exp.vendors.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
            },
            "execution": {
                "total_executions": exec_exp.total_executions,
                "tool_reliability": {
                    k: round(v, 2) for k, v in exec_exp.tool_success_rates.items()
                },
            },
        }


# Singleton instance
_service: Optional[SelfImproveService] = None


def get_self_improve_service() -> SelfImproveService:
    """Get the singleton self-improve service instance."""
    global _service
    if _service is None:
        _service = SelfImproveService()
    return _service
