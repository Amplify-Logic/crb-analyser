"""
Industry Benchmarker Skill

Compares company to industry benchmarks.

This skill:
1. Gets company metrics from quiz/interview data
2. Loads industry benchmarks
3. Calculates percentile rankings
4. Identifies strengths and gaps

Output Schema:
{
    "company_profile": {
        "industry": "dental",
        "size": "smb",
        "region": "Netherlands"
    },
    "ai_readiness": {
        "score": 65,
        "percentile": 72,
        "compared_to": "dental practices in Europe"
    },
    "benchmarks": [
        {
            "metric": "Digital adoption",
            "company_value": 60,
            "industry_average": 45,
            "percentile": 75,
            "status": "above_average"
        }
    ],
    "strengths": ["Tech adoption", "Data quality"],
    "gaps": ["Process documentation", "Integration"],
    "recommendations": [
        "Focus on process documentation to reach top quartile"
    ]
}
"""

import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError
from src.knowledge import (
    get_benchmarks_for_metrics,
    load_industry_data,
    normalize_industry,
    get_industry_context,
)

logger = logging.getLogger(__name__)

# Metric categories and their weights for AI readiness
AI_READINESS_METRICS = {
    "tech_adoption": {
        "weight": 0.25,
        "description": "Current technology stack and digital tools",
    },
    "data_quality": {
        "weight": 0.20,
        "description": "Data organization, accessibility, and cleanliness",
    },
    "process_maturity": {
        "weight": 0.20,
        "description": "Documented, standardized processes",
    },
    "team_capability": {
        "weight": 0.15,
        "description": "Team comfort with technology",
    },
    "budget_availability": {
        "weight": 0.10,
        "description": "Budget for technology investment",
    },
    "leadership_buy_in": {
        "weight": 0.10,
        "description": "Leadership support for AI initiatives",
    },
}


class IndustryBenchmarkerSkill(LLMSkill[Dict[str, Any]]):
    """
    Compare company metrics to industry benchmarks.

    Provides context by showing where the company stands
    relative to peers in their industry.
    """

    name = "industry-benchmarker"
    description = "Compare company to industry benchmarks"
    version = "1.0.0"

    requires_llm = True
    requires_knowledge = True

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Generate benchmark comparison.

        Args:
            context: SkillContext with:
                - quiz_answers: Company data from quiz
                - industry: Company's industry
                - metadata.company_context: Additional context

        Returns:
            Benchmark comparison with strengths and gaps
        """
        quiz_answers = context.quiz_answers or {}
        company_context = context.metadata.get("company_context", {})
        industry = normalize_industry(context.industry)

        # Load industry benchmarks
        benchmarks_data = load_industry_data(industry, "benchmarks")
        industry_context = get_industry_context(industry)

        if not benchmarks_data:
            # Use generic benchmarks
            benchmarks_data = {"benchmarks": {}}

        # Extract company metrics
        company_metrics = self._extract_company_metrics(quiz_answers, company_context)

        # Calculate benchmark comparisons
        benchmark_results = self._calculate_benchmarks(
            company_metrics=company_metrics,
            industry_benchmarks=benchmarks_data.get("benchmarks", {}),
        )

        # Calculate AI readiness score
        ai_readiness = self._calculate_ai_readiness(company_metrics, benchmark_results)

        # Identify strengths and gaps
        strengths, gaps = self._identify_strengths_gaps(benchmark_results)

        # Use LLM to generate recommendations
        recommendations = await self._generate_recommendations(
            strengths=strengths,
            gaps=gaps,
            industry=industry,
            ai_readiness=ai_readiness,
        )

        # Get comparison context
        region = quiz_answers.get("region", company_context.get("region", "Europe"))
        size = self._determine_company_size(quiz_answers, company_context)

        return {
            "company_profile": {
                "industry": industry,
                "size": size,
                "region": region,
            },
            "ai_readiness": {
                "score": ai_readiness["score"],
                "percentile": ai_readiness["percentile"],
                "compared_to": f"{industry.replace('-', ' ')} businesses in {region}",
            },
            "benchmarks": benchmark_results,
            "strengths": strengths,
            "gaps": gaps,
            "recommendations": recommendations,
        }

    def _extract_company_metrics(
        self,
        quiz_answers: Dict[str, Any],
        company_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract company metrics from quiz and context."""
        metrics = {}

        # Tech adoption (0-100)
        tech_tools = quiz_answers.get("current_tools", [])
        if isinstance(tech_tools, list):
            metrics["tech_adoption"] = min(100, len(tech_tools) * 15)
        else:
            metrics["tech_adoption"] = 40  # Default

        # Data quality (0-100)
        data_org = quiz_answers.get("data_organization", "")
        if "organized" in str(data_org).lower() or "structured" in str(data_org).lower():
            metrics["data_quality"] = 70
        elif "scattered" in str(data_org).lower() or "manual" in str(data_org).lower():
            metrics["data_quality"] = 30
        else:
            metrics["data_quality"] = 50

        # Process maturity (0-100)
        process_doc = quiz_answers.get("processes_documented", "")
        if "yes" in str(process_doc).lower() or "fully" in str(process_doc).lower():
            metrics["process_maturity"] = 80
        elif "some" in str(process_doc).lower() or "partial" in str(process_doc).lower():
            metrics["process_maturity"] = 50
        else:
            metrics["process_maturity"] = 30

        # Team capability (0-100)
        tech_comfort = quiz_answers.get("team_tech_comfort", 5)
        if isinstance(tech_comfort, (int, float)):
            metrics["team_capability"] = min(100, int(tech_comfort) * 10)
        else:
            metrics["team_capability"] = 50

        # Budget availability (0-100)
        budget = quiz_answers.get("monthly_tech_budget", 0)
        if isinstance(budget, (int, float)):
            if budget >= 1000:
                metrics["budget_availability"] = 80
            elif budget >= 500:
                metrics["budget_availability"] = 60
            elif budget >= 100:
                metrics["budget_availability"] = 40
            else:
                metrics["budget_availability"] = 20
        else:
            metrics["budget_availability"] = 40

        # Leadership buy-in (0-100)
        leadership = quiz_answers.get("leadership_ai_support", "")
        if "strong" in str(leadership).lower() or "champion" in str(leadership).lower():
            metrics["leadership_buy_in"] = 90
        elif "interested" in str(leadership).lower() or "open" in str(leadership).lower():
            metrics["leadership_buy_in"] = 60
        else:
            metrics["leadership_buy_in"] = 40

        return metrics

    def _calculate_benchmarks(
        self,
        company_metrics: Dict[str, Any],
        industry_benchmarks: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Calculate benchmark comparisons."""
        results = []

        for metric, value in company_metrics.items():
            # Get industry average
            industry_avg = industry_benchmarks.get(metric, {})
            if isinstance(industry_avg, dict):
                avg_value = industry_avg.get("average", 50)
                top_quartile = industry_avg.get("top_quartile", 75)
            else:
                avg_value = 50  # Default
                top_quartile = 75

            # Calculate percentile (simplified)
            if value >= top_quartile:
                percentile = 75 + ((value - top_quartile) / (100 - top_quartile)) * 25
            elif value >= avg_value:
                percentile = 50 + ((value - avg_value) / (top_quartile - avg_value)) * 25
            else:
                percentile = (value / avg_value) * 50

            percentile = min(99, max(1, int(percentile)))

            # Determine status
            if percentile >= 75:
                status = "above_average"
            elif percentile >= 50:
                status = "average"
            elif percentile >= 25:
                status = "below_average"
            else:
                status = "needs_attention"

            results.append({
                "metric": metric.replace("_", " ").title(),
                "company_value": value,
                "industry_average": avg_value,
                "percentile": percentile,
                "status": status,
            })

        return results

    def _calculate_ai_readiness(
        self,
        company_metrics: Dict[str, Any],
        benchmark_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate overall AI readiness score."""
        total_score = 0
        total_weight = 0

        for metric, config in AI_READINESS_METRICS.items():
            value = company_metrics.get(metric, 50)
            weight = config["weight"]
            total_score += value * weight
            total_weight += weight

        if total_weight > 0:
            score = int(total_score / total_weight)
        else:
            score = 50

        # Calculate percentile based on score distribution
        # Assume normal distribution centered at 50
        if score >= 80:
            percentile = 90
        elif score >= 70:
            percentile = 75
        elif score >= 60:
            percentile = 60
        elif score >= 50:
            percentile = 50
        elif score >= 40:
            percentile = 35
        else:
            percentile = 20

        return {
            "score": score,
            "percentile": percentile,
        }

    def _identify_strengths_gaps(
        self,
        benchmark_results: List[Dict[str, Any]],
    ) -> tuple:
        """Identify strengths and gaps from benchmarks."""
        strengths = []
        gaps = []

        for result in benchmark_results:
            metric = result["metric"]
            if result["status"] == "above_average":
                strengths.append(metric)
            elif result["status"] in ["below_average", "needs_attention"]:
                gaps.append(metric)

        return strengths[:3], gaps[:3]

    def _determine_company_size(
        self,
        quiz_answers: Dict[str, Any],
        company_context: Dict[str, Any],
    ) -> str:
        """Determine company size category."""
        employee_count = (
            quiz_answers.get("employee_count") or
            quiz_answers.get("team_size") or
            company_context.get("employee_count") or
            10
        )

        if isinstance(employee_count, str):
            if "1-10" in employee_count:
                return "startup"
            elif "50" in employee_count or "100" in employee_count:
                return "mid-market"
            else:
                return "smb"

        if employee_count <= 10:
            return "startup"
        elif employee_count <= 50:
            return "smb"
        elif employee_count <= 200:
            return "mid-market"
        else:
            return "enterprise"

    async def _generate_recommendations(
        self,
        strengths: List[str],
        gaps: List[str],
        industry: str,
        ai_readiness: Dict[str, Any],
    ) -> List[str]:
        """Generate actionable recommendations."""
        if not gaps and not self.client:
            return ["Maintain current performance across all metrics"]

        if not self.client:
            # Fallback recommendations
            return [f"Focus on improving {gap}" for gap in gaps[:2]]

        prompt = f"""Based on this company's benchmark analysis, provide 2-3 specific recommendations.

INDUSTRY: {industry}
AI READINESS SCORE: {ai_readiness['score']}/100 (percentile: {ai_readiness['percentile']})

STRENGTHS: {strengths}
GAPS: {gaps}

Provide actionable, specific recommendations to improve AI readiness.
Focus on the gaps while leveraging strengths.

Return ONLY a JSON object:
{{"recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"]}}"""

        try:
            result = await self.call_llm_json(
                prompt=prompt,
                system="You are a business consultant specializing in digital transformation. Provide specific, actionable advice."
            )
            return result.get("recommendations", [])[:3]

        except Exception as e:
            logger.warning(f"LLM recommendation generation failed: {e}")
            return [f"Focus on improving {gap}" for gap in gaps[:2]]


# For skill discovery
__all__ = ["IndustryBenchmarkerSkill"]
