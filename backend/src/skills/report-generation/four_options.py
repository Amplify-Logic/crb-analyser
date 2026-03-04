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
from src.services.vendor_validation_service import VendorValidationService
from src.utils.quiz_utils import get_complexity_level, get_viable_option_types
from src.knowledge import (
    get_vendor_recommendations,
    load_vendor_category,
    search_vendors,
    normalize_industry,
    VENDOR_CATEGORIES,
)
from src.skills.report_generation_utils import (
    format_vendors_for_prompt,
    get_relevant_vendor_categories,
    load_kb_vendors_for_finding,
)

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
        """Build LLM prompt with user profile, finding, and KB vendor data."""
        finding = context.finding or {}
        profile: UserProfile = context.user_profile
        vendors = context.vendors or []
        industry = context.industry or "ecommerce"
        currency_symbol = context.currency_symbol
        quiz_answers = context.quiz_answers or {}

        # Load KB vendor data relevant to this finding
        kb_vendors = load_kb_vendors_for_finding(
            finding=finding,
            industry=industry,
            context_vendors=vendors,
            max_vendors=15,
        )
        vendor_context = format_vendors_for_prompt(
            kb_vendors,
            currency_symbol=currency_symbol,
        )

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

        # Get complexity level and viable options
        complexity = get_complexity_level(quiz_answers)
        viable_options = get_viable_option_types(quiz_answers)

        # Build complexity guidance
        complexity_guidance = self._get_complexity_guidance(complexity, viable_options)

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

VIABLE OPTIONS FOR THIS USER: {', '.join(viable_options).upper()}
Non-viable options should still be included but with clear warnings about why they're not recommended.

{complexity_guidance}

Generate all 4 options with realistic details:

1. BUY: A specific SaaS product that solves this
   - MUST use a vendor from the VENDOR CATALOG above if one fits
   - Use the exact pricing from the catalog
   - Setup time should be realistic (hours to days)
   - If no vendor from the catalog fits, say "Custom development required" in vendor_name

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
- For BUY: ONLY recommend vendors from the VENDOR CATALOG above. Use their exact pricing.
- If no vendor fits this finding, set vendor_name to "No matching vendor" and explain in cons.
- Do NOT invent vendor names or prices. Every vendor and price must come from the catalog.
- Be specific about what gets connected/built
- Pros/cons must reference user's specific situation
- If an option isn't viable for this user, still include it but note why in cons
"""

    def _get_complexity_guidance(self, complexity: str, viable_options: List[str]) -> str:
        """Get writing guidance based on user's technical complexity level."""
        guidance = {
            "simple": """LANGUAGE COMPLEXITY: SIMPLE
Write for someone who avoids anything technical:
- Use plain English, no jargon
- Step-by-step explanations
- Avoid acronyms (or explain them)
- Focus on outcomes, not implementation details
- Example: "Click this button, then wait for the email" not "Trigger the webhook endpoint"
""",
            "basic": """LANGUAGE COMPLEXITY: BASIC
Write for someone who can follow tutorials:
- Light technical terms are OK if explained
- Clear step-by-step instructions
- Visual references when helpful
- Example: "Connect the apps using Zapier (a tool that links software together)"
""",
            "intermediate": """LANGUAGE COMPLEXITY: INTERMEDIATE
Write for someone comfortable with automation:
- Technical terms like API, webhook, automation are fine
- Can reference tools like Make, Zapier, n8n directly
- Include integration specifics
- Example: "Set up a Zap that triggers on new form submission"
""",
            "advanced": """LANGUAGE COMPLEXITY: ADVANCED
Write for someone who codes or uses AI coding tools:
- Full technical depth appreciated
- Include code snippets if helpful
- Reference specific APIs and SDKs
- Example: "Use the Claude API with function calling to process incoming data"
""",
            "technical": """LANGUAGE COMPLEXITY: TECHNICAL
Write for developers or teams with technical resources:
- Full technical specifications welcome
- Include architecture considerations
- Reference specific frameworks and patterns
- Example: "Implement an event-driven architecture using webhooks and a message queue"
""",
        }

        base_guidance = guidance.get(complexity, guidance["basic"])

        # Add warnings for non-viable options
        non_viable = [opt for opt in ["buy", "connect", "build", "hire"] if opt not in viable_options]
        if non_viable:
            base_guidance += f"\n\nNON-VIABLE OPTIONS ({', '.join(non_viable).upper()}): Include these but add clear cons explaining why they're not recommended for this user's skill level."

        return base_guidance

    def _build_system_prompt(self, currency: str = "EUR") -> str:
        """System prompt for consistent output."""
        return f"""You are a technical consultant generating implementation options.

RULES:
- For BUY options: ONLY use vendors and pricing from the VENDOR CATALOG provided in the prompt. Never invent vendors or prices.
- Be specific, not vague - name actual tools and platforms
- Pros/cons must be specific to THIS user's profile
- Never use buzzwords: seamless, robust, scalable, leverage, unlock
- All costs in {currency}
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
        system = self._build_system_prompt(currency=context.currency)

        try:
            response = await self.call_llm_json(prompt, system=system)
            options_data = response
        except SkillError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise SkillError(self.name, f"Invalid JSON from LLM: {e}")

        # Validate BUY vendor against knowledge base
        vendor_validation = self._validate_buy_vendor(
            options_data.get("buy", {}),
            context.industry
        )

        # Build option models
        buy = BuyOption(
            vendor_slug=options_data.get("buy", {}).get("vendor_slug", "unknown"),
            vendor_name=options_data.get("buy", {}).get("vendor_name", "Unknown"),
            price=options_data.get("buy", {}).get("price", "N/A"),
            setup_time=options_data.get("buy", {}).get("setup_time", "Unknown"),
            pros=options_data.get("buy", {}).get("pros", []),
            cons=options_data.get("buy", {}).get("cons", []),
            cost=CostEstimate(
                year_one_total=options_data.get("buy", {}).get("year_one_cost") or 0
            ),
            vendor_verified=vendor_validation.get("verified", False),
            vendor_match_type=vendor_validation.get("match_type", "none"),
            kb_monthly_price=vendor_validation.get("kb_price"),
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
                year_one_total=connect_data.get("year_one_cost") or 0
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
                year_one_total=build_data.get("year_one_cost") or 0
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
                year_one_total=hire_data.get("year_one_cost") or 0
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

    def _validate_buy_vendor(
        self,
        buy_data: Dict[str, Any],
        industry: Optional[str]
    ) -> Dict[str, Any]:
        """
        Validate the BUY option vendor against knowledge base.

        Args:
            buy_data: The buy option data from LLM
            industry: Industry for context-specific lookup

        Returns:
            Validation result with verified flag and KB pricing
        """
        result = {
            "verified": False,
            "match_type": "none",
            "kb_price": None,
            "warnings": []
        }

        vendor_name = buy_data.get("vendor_name") or buy_data.get("vendor_slug", "")
        if not vendor_name:
            return result

        try:
            validator = VendorValidationService(industry=industry)
            match = validator.lookup_vendor(vendor_name)

            result["verified"] = match.found
            result["match_type"] = match.match_type

            if match.found and match.matched_vendor:
                # Extract KB pricing for comparison
                kb_pricing = validator._extract_kb_pricing(match.matched_vendor)
                if kb_pricing:
                    result["kb_price"] = kb_pricing.get("monthly")

                if match.match_type == "fuzzy_name":
                    result["warnings"].append(
                        f"Vendor '{vendor_name}' matched via fuzzy match to '{match.matched_vendor.get('name')}'"
                    )
            else:
                result["warnings"].append(
                    f"BUY vendor '{vendor_name}' not found in knowledge base"
                )
                logger.warning(f"Vendor validation: BUY vendor '{vendor_name}' not in KB")

        except Exception as e:
            logger.error(f"Vendor validation failed for '{vendor_name}': {e}")
            result["warnings"].append(f"Validation error: {str(e)}")

        return result


# For skill discovery
__all__ = ["FourOptionsSkill"]
