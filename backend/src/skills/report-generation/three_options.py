"""
Three Options Skill

Generates recommendations in the Three Options format:
- Option A: Off-the-Shelf (fastest, plug-and-play)
- Option B: Best-in-Class (premium, full-featured)
- Option C: Custom Solution (AI/API-based, competitive advantage)

This skill:
1. Takes a finding and generates three solution options
2. Integrates vendor pricing from knowledge base
3. Calculates ROI with confidence adjustment
4. Provides specific "our recommendation" with rationale
5. Includes Build It Yourself details for custom solutions

Output Schema:
{
    "id": "rec-001",
    "finding_id": "finding-001",
    "title": "...",
    "description": "...",
    "why_it_matters": {"customer_value": "...", "business_health": "..."},
    "priority": "high|medium|low",
    "options": {
        "off_the_shelf": {...},
        "best_in_class": {...},
        "custom_solution": {...}
    },
    "our_recommendation": "off_the_shelf|best_in_class|custom_solution",
    "recommendation_rationale": "...",
    "roi_percentage": N,
    "payback_months": N,
    "assumptions": [...]
}
"""

import json
import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)

# Confidence-adjusted ROI factors
CONFIDENCE_FACTORS = {
    "high": 1.0,
    "medium": 0.85,
    "low": 0.70
}


class ThreeOptionsSkill(LLMSkill[Dict[str, Any]]):
    """
    Generate Three Options recommendations for findings.

    This is an LLM-powered skill that creates comprehensive
    recommendations with three solution options: off-the-shelf,
    best-in-class, and custom solution.
    """

    name = "three-options"
    description = "Format recommendations in Three Options structure"
    version = "1.0.0"

    requires_llm = True
    requires_knowledge = True  # Works best with vendor data

    # Default option templates
    OFF_THE_SHELF_TEMPLATE = {
        "name": "",
        "vendor": "",
        "monthly_cost": 0,
        "implementation_weeks": 2,
        "implementation_cost": 0,
        "pros": [],
        "cons": [],
    }

    BEST_IN_CLASS_TEMPLATE = {
        "name": "",
        "vendor": "",
        "monthly_cost": 0,
        "implementation_weeks": 4,
        "implementation_cost": 0,
        "pros": [],
        "cons": [],
    }

    CUSTOM_SOLUTION_TEMPLATE = {
        "approach": "",
        "estimated_cost": {"min": 0, "max": 0},
        "monthly_running_cost": 0,
        "implementation_weeks": 6,
        "pros": ["Perfect fit for your needs", "Competitive advantage", "Full control"],
        "cons": ["Higher upfront investment", "Requires maintenance"],
        "build_tools": ["Claude API", "Cursor", "Vercel", "Supabase"],
        "model_recommendation": "Claude Sonnet 4 for balanced quality and cost",
        "skills_required": ["Python or TypeScript", "Basic API integration"],
        "dev_hours_estimate": "40-80 hours",
    }

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Generate Three Options recommendation for a finding.

        Args:
            context: SkillContext with finding in metadata, plus vendors/knowledge

        Returns:
            Recommendation dictionary with three options
        """
        # Get the finding to recommend for
        finding = context.metadata.get("finding", {})
        if not finding:
            raise SkillError(
                self.name,
                "No finding provided in context.metadata",
                recoverable=False
            )

        # Get vendor data
        vendors = []
        if context.knowledge:
            vendors = context.knowledge.get("vendors", [])

        # Get company context
        company_context = {
            "name": context.company_name or "the company",
            "size": context.company_size or "SMB",
            "tech_comfort": context.quiz_answers.get("tech_comfort", "medium") if context.quiz_answers else "medium",
            "budget_range": context.quiz_answers.get("budget_range", "5000-10000") if context.quiz_answers else "5000-10000",
        }

        # Generate recommendation
        recommendation = await self._generate_recommendation(
            finding=finding,
            vendors=vendors,
            industry=context.industry,
            company_context=company_context,
            expertise=context.expertise,
        )

        # Apply confidence-adjusted ROI
        recommendation = self._adjust_roi_for_confidence(
            recommendation,
            finding.get("confidence", "medium")
        )

        # Validate and normalize
        recommendation = self._validate_recommendation(recommendation, finding)

        return recommendation

    async def _generate_recommendation(
        self,
        finding: Dict[str, Any],
        vendors: List[Dict[str, Any]],
        industry: str,
        company_context: Dict[str, Any],
        expertise: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate recommendation using Claude."""
        # Filter vendors relevant to finding category
        category = finding.get("category", "efficiency")
        relevant_vendors = [
            v for v in vendors
            if category in v.get("categories", []) or not v.get("categories")
        ][:10]

        # Get AI tools context
        ai_tools_context = self._get_ai_tools_context()

        prompt = f"""Generate a recommendation with THREE OPTIONS for this finding.

FINDING:
{json.dumps(finding, indent=2)}

COMPANY CONTEXT:
- Industry: {industry}
- Size: {company_context['size']}
- Tech Comfort: {company_context['tech_comfort']}
- Budget Range: €{company_context['budget_range']}

AVAILABLE VENDORS:
{json.dumps(relevant_vendors, indent=2) if relevant_vendors else "Use general market vendors"}

{ai_tools_context}

═══════════════════════════════════════════════════════════════════════════════
THREE OPTIONS PATTERN
═══════════════════════════════════════════════════════════════════════════════

Generate ALL THREE options:

Option A: OFF-THE-SHELF
- Fastest to deploy, lowest risk
- Existing SaaS product, plug-and-play
- Best for: Quick wins, proven solutions

Option B: BEST-IN-CLASS
- Premium vendor, more features
- Better support and ecosystem
- Best for: Scaling, enterprise needs

Option C: CUSTOM SOLUTION
- Built with AI/APIs (Claude, etc.)
- Full control and ownership
- Best for: Competitive advantage, unique requirements

═══════════════════════════════════════════════════════════════════════════════

Generate a JSON object with this structure:
{{
    "title": "<recommendation title>",
    "description": "<what to do and why>",
    "why_it_matters": {{
        "customer_value": "<specific benefit to customers>",
        "business_health": "<specific benefit to business>"
    }},
    "priority": "high|medium|low",
    "options": {{
        "off_the_shelf": {{
            "name": "<specific product name>",
            "vendor": "<company name>",
            "monthly_cost": <number>,
            "implementation_weeks": <number>,
            "implementation_cost": <number>,
            "pros": ["<pro1>", "<pro2>"],
            "cons": ["<con1>", "<con2>"]
        }},
        "best_in_class": {{
            "name": "<specific product name>",
            "vendor": "<company name>",
            "monthly_cost": <number>,
            "implementation_weeks": <number>,
            "implementation_cost": <number>,
            "pros": ["<pro1>", "<pro2>"],
            "cons": ["<con1>", "<con2>"]
        }},
        "custom_solution": {{
            "approach": "<description of custom solution>",
            "estimated_cost": {{"min": <number>, "max": <number>}},
            "monthly_running_cost": <number>,
            "implementation_weeks": <number>,
            "pros": ["Perfect fit", "Competitive advantage", "Full control"],
            "cons": ["Higher upfront investment", "Requires maintenance"],
            "build_tools": ["Claude API", "Cursor", "Vercel", "Supabase"],
            "model_recommendation": "<specific model> because <reason>",
            "skills_required": ["<skill1>", "<skill2>"],
            "dev_hours_estimate": "<min>-<max> hours"
        }}
    }},
    "our_recommendation": "off_the_shelf|best_in_class|custom_solution",
    "recommendation_rationale": "<why this option is best for THIS company based on size, budget, tech comfort>",
    "roi_percentage": <calculated ROI>,
    "payback_months": <months to recover investment>,
    "assumptions": [
        "<assumption with specific numbers>",
        "<assumption with specific numbers>"
    ]
}}

DECISION GUIDANCE for our_recommendation:
- off_the_shelf: Small budget, low tech comfort, need quick win
- best_in_class: Growing business, need scalability, can afford premium
- custom_solution: High tech comfort, unique needs, want competitive advantage

Return ONLY the JSON object."""

        try:
            response = await self.call_llm_json(
                prompt=prompt,
                system=self._get_system_prompt(),
            )
            return response

        except SkillError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate recommendation: {e}")
            return self._get_default_recommendation(finding)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for recommendation generation."""
        return """You are an expert AI business consultant generating recommendations for CRB Analysis reports.

Your role is to provide balanced, honest recommendations across three solution types.

Key principles:
1. REAL VENDORS: Use actual product names and realistic pricing
2. HONEST TRADE-OFFS: Every option has pros AND cons
3. CONTEXT-AWARE: Recommendation should match company size, budget, tech comfort
4. TRANSPARENT ROI: Show calculation assumptions
5. COMPLETE OPTIONS: All three options must be fully specified

Never recommend custom solutions for companies with low tech comfort unless absolutely necessary.
Never recommend best-in-class if it's clearly out of budget.
Be honest about implementation complexity and maintenance requirements."""

    def _get_ai_tools_context(self) -> str:
        """Get AI tools context for custom solutions."""
        return """
AI TOOLS FOR CUSTOM SOLUTIONS:

DEVELOPMENT TOOLS:
- Claude Code: AI-assisted development, full codebase understanding
- Cursor: AI-native IDE, excellent for rapid prototyping
- VS Code + Cline: AI coding extension, flexible

MODEL RECOMMENDATIONS:
- Claude Opus 4.5: Complex reasoning, highest quality ($15/$75 per MTok)
- Claude Sonnet 4: Balanced quality/cost, best for most use cases ($3/$15 per MTok)
- Claude Haiku 3.5: Speed-critical, high volume ($0.80/$4 per MTok)

STACK RECOMMENDATIONS:
- Backend: FastAPI (Python) or Express (TypeScript)
- Database: Supabase (PostgreSQL + Auth + Realtime)
- Frontend: React + Vite or Next.js
- Deployment: Railway or Vercel
- AI Integration: Anthropic SDK (Python or TypeScript)
"""

    def _adjust_roi_for_confidence(
        self,
        recommendation: Dict[str, Any],
        confidence: str
    ) -> Dict[str, Any]:
        """Apply confidence-adjusted ROI."""
        factor = CONFIDENCE_FACTORS.get(confidence.lower(), 0.85)

        if "roi_percentage" in recommendation:
            original_roi = recommendation["roi_percentage"]
            adjusted_roi = int(original_roi * factor)
            recommendation["roi_percentage"] = adjusted_roi
            recommendation["roi_confidence_adjusted"] = True
            recommendation["confidence_level"] = confidence

            # Add note about adjustment
            if factor < 1.0:
                assumptions = recommendation.get("assumptions", [])
                assumptions.append(
                    f"ROI adjusted by {int((1-factor)*100)}% for {confidence} confidence"
                )
                recommendation["assumptions"] = assumptions

        return recommendation

    def _validate_recommendation(
        self,
        recommendation: Dict[str, Any],
        finding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and normalize recommendation structure."""
        # Ensure basic fields
        rec = {
            "id": recommendation.get("id", f"rec-for-{finding.get('id', 'unknown')}"),
            "finding_id": finding.get("id", "unknown"),
            "title": recommendation.get("title", finding.get("title", "Recommendation")),
            "description": recommendation.get("description", ""),
            "why_it_matters": recommendation.get("why_it_matters", {
                "customer_value": "",
                "business_health": ""
            }),
            "priority": recommendation.get("priority", "medium"),
        }

        # Validate options
        options = recommendation.get("options", {})

        # Validate off_the_shelf
        ots = options.get("off_the_shelf", {})
        rec_ots = self.OFF_THE_SHELF_TEMPLATE.copy()
        rec_ots.update({k: v for k, v in ots.items() if v})

        # Validate best_in_class
        bic = options.get("best_in_class", {})
        rec_bic = self.BEST_IN_CLASS_TEMPLATE.copy()
        rec_bic.update({k: v for k, v in bic.items() if v})

        # Validate custom_solution
        cs = options.get("custom_solution", {})
        rec_cs = self.CUSTOM_SOLUTION_TEMPLATE.copy()
        rec_cs.update({k: v for k, v in cs.items() if v})

        rec["options"] = {
            "off_the_shelf": rec_ots,
            "best_in_class": rec_bic,
            "custom_solution": rec_cs,
        }

        # Our recommendation
        rec["our_recommendation"] = recommendation.get(
            "our_recommendation", "off_the_shelf"
        )
        if rec["our_recommendation"] not in ("off_the_shelf", "best_in_class", "custom_solution"):
            rec["our_recommendation"] = "off_the_shelf"

        rec["recommendation_rationale"] = recommendation.get(
            "recommendation_rationale", ""
        )
        rec["roi_percentage"] = recommendation.get("roi_percentage", 0)
        rec["payback_months"] = recommendation.get("payback_months", 0)
        rec["assumptions"] = recommendation.get("assumptions", [])

        return rec

    def _get_default_recommendation(
        self,
        finding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Return a default recommendation when LLM fails."""
        return {
            "id": f"rec-for-{finding.get('id', 'unknown')}",
            "finding_id": finding.get("id", "unknown"),
            "title": f"Address: {finding.get('title', 'Finding')}",
            "description": "Evaluate solution options for this opportunity.",
            "why_it_matters": {
                "customer_value": "Potential customer experience improvement",
                "business_health": "Potential operational efficiency gain"
            },
            "priority": "medium",
            "options": {
                "off_the_shelf": self.OFF_THE_SHELF_TEMPLATE.copy(),
                "best_in_class": self.BEST_IN_CLASS_TEMPLATE.copy(),
                "custom_solution": self.CUSTOM_SOLUTION_TEMPLATE.copy(),
            },
            "our_recommendation": "off_the_shelf",
            "recommendation_rationale": "Start with proven solutions for faster implementation.",
            "roi_percentage": 0,
            "payback_months": 0,
            "assumptions": ["Insufficient data for ROI calculation"],
        }


# For skill discovery
__all__ = ["ThreeOptionsSkill"]
