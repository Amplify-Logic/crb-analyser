"""
Four Options Skill

Generates personalized recommendations in 4-option format:
- BUY: Pre-built SaaS (turnkey)
- CONNECT: Integrate existing tools (Make/Zapier)
- BUILD: Custom solution (AI coding tools)
- HIRE: Agency/freelancer

Uses weighted scoring based on user profile:
- Capability (30%)
- Preference (20%)
- Budget (20%)
- Time (15%)
- Value (15%)
"""

import json
import logging
from typing import Dict, Any, List, Optional

from src.skills.base import LLMSkill, SkillContext, SkillError
from src.models.user_profile import UserProfile, CapabilityLevel
from src.models.four_options import (
    OptionType,
    OptionScore,
    BuyOption,
    ConnectOption,
    BuildOption,
    HireOption,
    FourOptionRecommendation,
    CostEstimate,
)
from src.services.option_scoring import get_recommendations

logger = logging.getLogger(__name__)


class FourOptionsSkill(LLMSkill[Dict[str, Any]]):
    """
    Generate Four Options recommendations for findings.

    Creates personalized BUY/CONNECT/BUILD/HIRE options
    with weighted scoring based on user profile.
    """

    name = "four-options"
    description = "Generate personalized 4-option recommendations"
    version = "1.0.0"

    requires_llm = True
    requires_knowledge = True

    def _build_prompt(self, context: SkillContext) -> str:
        """Build LLM prompt with user profile and finding."""
        finding = context.finding or {}
        profile: UserProfile = context.user_profile
        vendors = context.vendors or []
        industry = context.industry or "general"

        # Format vendor context
        vendor_context = ""
        if vendors:
            vendor_list = "\n".join([
                f"- {v.get('name', 'Unknown')}: €{v.get('monthly_price', 'N/A')}/mo"
                for v in vendors[:10]
            ])
            vendor_context = f"\n\nRELEVANT VENDORS:\n{vendor_list}"

        # Determine capability description
        cap_desc = "Can handle any option"
        if profile.capability in [CapabilityLevel.NON_TECHNICAL, CapabilityLevel.TUTORIAL_FOLLOWER]:
            cap_desc = "Limited to simpler options (BUY, HIRE preferred)"
        elif profile.capability == CapabilityLevel.AUTOMATION_USER:
            cap_desc = "Good with automation, CONNECT is viable"

        # Budget description
        budget_desc = "Can afford all options"
        if profile.budget.value in ["low", "moderate"]:
            budget_desc = "Budget constrained - prefer cost-effective options"

        return f"""Generate a 4-option recommendation for this finding.

FINDING:
- Title: {finding.get('title', '')}
- Description: {finding.get('description', '')}
- Category: {finding.get('category', '')}

USER PROFILE:
- Technical Capability: {profile.capability.value}
- Implementation Preference: {profile.preference.value}
- Budget Tier: {profile.budget.value}
- Urgency: {profile.urgency.value if profile.urgency else 'not specified'}
- Industry: {industry}
- Existing Stack API-Ready: {profile.existing_stack_api_ready}
{vendor_context}

SCORING CONTEXT:
The user's profile determines which options are viable:
- Capability={profile.capability.value}: {cap_desc}
- Preference={profile.preference.value}: User prefers {profile.preference.value.upper()} approach
- Budget={profile.budget.value}: {budget_desc}

Generate all 4 options with realistic details:

1. BUY: A specific SaaS product that solves this
   - Use real vendor from list if applicable
   - Include actual pricing
   - Setup time should be realistic (hours to days)

2. CONNECT: How to integrate their existing tools
   - Specify Make, n8n, or Zapier
   - Which tools would be connected
   - Estimated setup hours
   - Only viable if they have API-ready tools

3. BUILD: Custom solution with AI coding tools
   - Recommended tech stack
   - Realistic cost and time estimates
   - Skills needed
   - Whether AI coding tools (Cursor, Claude Code) make this achievable

4. HIRE: Agency/freelancer option
   - Type: Agency, Freelancer, or Consultant
   - Realistic cost range
   - Timeline
   - Where to find (Upwork, Toptal, etc.)

For each option include:
- 2-3 pros specific to this user's situation
- 1-2 cons specific to this user's situation
- Cost estimate (upfront + monthly)
- Time to value

OUTPUT FORMAT (JSON):
{{
    "buy": {{
        "vendor_slug": "calendly",
        "vendor_name": "Calendly",
        "price": "12/mo",
        "setup_time": "30 minutes",
        "pros": ["..."],
        "cons": ["..."],
        "year_one_cost": 144
    }},
    "connect": {{
        "integration_platform": "Make",
        "connects_to": ["HubSpot", "Gmail"],
        "estimated_hours": 4,
        "complexity": "low",
        "pros": ["..."],
        "cons": ["..."],
        "year_one_cost": 0
    }},
    "build": {{
        "recommended_stack": ["Claude Code", "Supabase", "Vercel"],
        "estimated_cost": "2K-5K",
        "estimated_hours": "20-40",
        "skills_needed": ["Python or TypeScript"],
        "ai_coding_viable": true,
        "approach": "Build custom reminder system...",
        "pros": ["..."],
        "cons": ["..."],
        "year_one_cost": 3000
    }},
    "hire": {{
        "service_type": "Freelancer",
        "estimated_cost": "500-2K",
        "estimated_timeline": "1-2 weeks",
        "where_to_find": ["Upwork", "Fiverr"],
        "pros": ["..."],
        "cons": ["..."],
        "year_one_cost": 1000
    }}
}}

IMPORTANT:
- Use REAL vendors with REAL pricing
- Be specific about what gets connected/built
- Pros/cons must reference user's specific situation
- If an option isn't viable for this user, still include it but note why in cons
"""

    def _build_system_prompt(self) -> str:
        """System prompt for consistent output."""
        return """You are a technical consultant generating implementation options.

RULES:
- Use ONLY real vendors and real pricing (2024-2025 data)
- Be specific, not vague - name actual tools and platforms
- Pros/cons must be specific to THIS user's profile
- Never use buzzwords: seamless, robust, scalable, leverage, unlock
- All costs in EUR
- Be honest about limitations and requirements
- Output valid JSON only"""

    async def execute(self, context: SkillContext) -> Dict[str, Any]:
        """
        Generate 4-option recommendation with scoring.

        1. Call LLM to generate option details
        2. Calculate weighted scores based on user profile
        3. Determine recommended option
        4. Return complete FourOptionRecommendation
        """
        # Validate required context
        if not context.finding:
            raise SkillError(
                self.name,
                "No finding provided in context",
                recoverable=False
            )
        if not context.user_profile:
            raise SkillError(
                self.name,
                "No user_profile provided in context",
                recoverable=False
            )

        # Get LLM-generated options
        prompt = self._build_prompt(context)
        system = self._build_system_prompt()

        try:
            response = await self.call_llm_json(prompt, system_prompt=system)
            options_data = response
        except SkillError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise SkillError(self.name, f"Invalid JSON from LLM: {e}")

        # Build option models
        buy = BuyOption(
            vendor_slug=options_data.get("buy", {}).get("vendor_slug", "unknown"),
            vendor_name=options_data.get("buy", {}).get("vendor_name", "Unknown"),
            price=options_data.get("buy", {}).get("price", "N/A"),
            setup_time=options_data.get("buy", {}).get("setup_time", "Unknown"),
            pros=options_data.get("buy", {}).get("pros", []),
            cons=options_data.get("buy", {}).get("cons", []),
            cost=CostEstimate(
                year_one_total=options_data.get("buy", {}).get("year_one_cost", 0)
            ),
        )

        connect_data = options_data.get("connect", {})
        connect = ConnectOption(
            integration_platform=connect_data.get("integration_platform", "Make"),
            connects_to=connect_data.get("connects_to", []),
            estimated_hours=connect_data.get("estimated_hours", 4),
            complexity=connect_data.get("complexity", "medium"),
            pros=connect_data.get("pros", []),
            cons=connect_data.get("cons", []),
            cost=CostEstimate(
                year_one_total=connect_data.get("year_one_cost", 0)
            ),
        )

        build_data = options_data.get("build", {})
        build = BuildOption(
            recommended_stack=build_data.get("recommended_stack", []),
            estimated_cost=build_data.get("estimated_cost", "N/A"),
            estimated_hours=build_data.get("estimated_hours", "N/A"),
            skills_needed=build_data.get("skills_needed", []),
            ai_coding_viable=build_data.get("ai_coding_viable", True),
            approach=build_data.get("approach", ""),
            pros=build_data.get("pros", []),
            cons=build_data.get("cons", []),
            cost=CostEstimate(
                year_one_total=build_data.get("year_one_cost", 0)
            ),
        )

        hire_data = options_data.get("hire", {})
        hire = HireOption(
            service_type=hire_data.get("service_type", "Freelancer"),
            estimated_cost=hire_data.get("estimated_cost", "N/A"),
            estimated_timeline=hire_data.get("estimated_timeline", "N/A"),
            where_to_find=hire_data.get("where_to_find", []),
            pros=hire_data.get("pros", []),
            cons=hire_data.get("cons", []),
            cost=CostEstimate(
                year_one_total=hire_data.get("year_one_cost", 0)
            ),
        )

        # Calculate scores
        profile: UserProfile = context.user_profile
        option_costs = {
            OptionType.BUY: buy.cost,
            OptionType.CONNECT: connect.cost,
            OptionType.BUILD: build.cost,
            OptionType.HIRE: hire.cost,
        }
        option_times = {
            OptionType.BUY: buy.setup_time,
            OptionType.CONNECT: f"{connect.estimated_hours} hours",
            OptionType.BUILD: build.estimated_hours,
            OptionType.HIRE: hire.estimated_timeline,
        }

        scores = get_recommendations(profile, option_costs, option_times)
        recommended = scores[0].option if scores else OptionType.BUY

        # Check for no good match
        no_good_match = all(s.score < 50 for s in scores)
        fallback_message = None
        if no_good_match:
            fallback_message = self._generate_fallback_message(scores, profile)

        # Build recommendation reasoning
        top_score = scores[0] if scores else None
        reasoning = self._build_reasoning(top_score, profile) if top_score else ""

        return FourOptionRecommendation(
            finding_id=context.finding.get("id", ""),
            finding_title=context.finding.get("title", ""),
            buy=buy,
            connect=connect,
            build=build,
            hire=hire,
            scores=scores,
            recommended=recommended,
            recommendation_reasoning=reasoning,
            no_good_match=no_good_match,
            fallback_message=fallback_message,
        ).model_dump()

    def _build_reasoning(
        self,
        top_score: OptionScore,
        profile: UserProfile
    ) -> str:
        """Build recommendation reasoning from score."""
        reasons = top_score.match_reasons[:3]
        if not reasons:
            return f"{top_score.option.value.upper()} is the best match for your profile."
        return f"{top_score.option.value.upper()} is recommended because: {'; '.join(reasons)}."

    def _generate_fallback_message(
        self,
        scores: List[OptionScore],
        profile: UserProfile
    ) -> str:
        """Generate message when no option scores well."""
        # Find the limiting factor
        if profile.budget.value == "low":
            return (
                "Your current budget limits the options for this finding. "
                "Consider prioritizing other findings first, or look for "
                "free/freemium tiers of BUY options."
            )
        if profile.capability == CapabilityLevel.NON_TECHNICAL:
            return (
                "This automation requires technical skills beyond your current level. "
                "Consider the HIRE option if budget allows, or start with simpler "
                "findings to build confidence."
            )
        return (
            "This is a complex automation that doesn't fit standard patterns. "
            "Consider booking a consultation to discuss custom approaches."
        )


# For skill discovery
__all__ = ["FourOptionsSkill"]
