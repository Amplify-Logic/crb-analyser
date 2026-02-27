"""
AIOS Options Skill (formerly Three Options)

Generates recommendations in the AIOS connect-first format:
- Option A: Connect & Automate (wire existing tools with AI workflows)
- Option B: Enhance with AI (add intelligence layer on top)
- Option C: Targeted Upgrade (adopt dedicated tool when it's genuinely the best fit)

This skill:
1. Takes a finding and generates three solution options (best-fit-first)
2. Integrates vendor pricing from knowledge base
3. Calculates ROI with confidence adjustment
4. Provides specific "our recommendation" with rationale
5. Includes Claude Code hours and MCP servers for connect option

Backward compatible: maps old keys (off_the_shelf, best_in_class, custom_solution)
to new keys (connect_and_automate, enhance_with_ai, targeted_upgrade).

Output Schema:
{
    "id": "rec-001",
    "finding_id": "finding-001",
    "title": "...",
    "description": "...",
    "why_it_matters": {"customer_value": "...", "business_health": "..."},
    "priority": "high|medium|low",
    "options": {
        "connect_and_automate": {...},
        "enhance_with_ai": {...},
        "targeted_upgrade": {...}
    },
    "our_recommendation": "connect_and_automate|enhance_with_ai|targeted_upgrade",
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
from src.services.vendor_validation_service import VendorValidationService
from src.knowledge import (
    get_vendor_recommendations,
    load_vendor_category,
    normalize_industry,
    VENDOR_CATEGORIES,
)
from src.skills.report_generation_utils import (
    format_vendors_for_prompt,
    get_relevant_vendor_categories,
    load_kb_vendors_for_finding,
)

logger = logging.getLogger(__name__)


    # Backward compatibility mapping: old keys → new keys
OPTION_KEY_MAPPING = {
    "off_the_shelf": "targeted_upgrade",
    "best_in_class": "enhance_with_ai",
    "custom_solution": "connect_and_automate",
}

# Valid AIOS option keys
AIOS_OPTION_KEYS = {"connect_and_automate", "enhance_with_ai", "targeted_upgrade"}

# Valid legacy option keys
LEGACY_OPTION_KEYS = {"off_the_shelf", "best_in_class", "custom_solution"}


class ThreeOptionsSkill(LLMSkill[Dict[str, Any]]):
    """
    Generate AIOS Options recommendations for findings.

    Best-fit-first philosophy: recommend whatever genuinely serves this
    specific company best. Prefer connect as tiebreaker when options are close.
    """

    name = "three-options"
    description = "Format recommendations in AIOS best-fit-first structure"
    version = "2.0.0"

    requires_llm = True
    requires_knowledge = True

    # Default option templates (AIOS format)
    CONNECT_AND_AUTOMATE_TEMPLATE = {
        "approach": "",
        "build_time": "",
        "tools_used": [],
        "mcp_servers": [],
        "monthly_cost": "",
        "aios_layers_touched": ["connections", "intelligence"],
        "skills_created": None,
        "context_needed": None,
        "education_prereq": None,
        "cowork_tasks": None,
        "pros": ["Uses your existing stack", "Ships this week", "Fully customized"],
        "cons": ["Requires API access", "Needs maintenance", "Development labor cost"],
    }

    ENHANCE_WITH_AI_TEMPLATE = {
        "approach": "",
        "build_time": "",
        "tools_used": [],
        "monthly_cost": "",
        "pros": ["Autonomous handling", "Learns and improves", "Scalable"],
        "cons": ["More complex setup", "Needs training data"],
    }

    TARGETED_UPGRADE_TEMPLATE = {
        "when_needed": "",
        "tools": [],
        "cost_range": "",
        "migration_time": "",
        "pros": ["Pre-built solution", "Quick setup", "Vendor-managed maintenance", "Purpose-built for this problem"],
        "cons": ["Monthly SaaS cost", "Less customization"],
    }

    # Legacy templates (for backward compat)
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

        # Get vendor data - handle nested vendor_categories structure
        vendors = []
        if context.knowledge:
            vendor_data = context.knowledge.get("vendors", {})
            if isinstance(vendor_data, dict):
                # Extract vendors from vendor_categories structure
                vendor_categories = vendor_data.get("vendor_categories", [])
                for cat in vendor_categories:
                    if isinstance(cat, dict):
                        cat_vendors = cat.get("vendors", [])
                        # Add category info to each vendor
                        for v in cat_vendors:
                            if isinstance(v, dict):
                                v["categories"] = [cat.get("category", "general")]
                                vendors.append(v)
            elif isinstance(vendor_data, list):
                vendors = [v for v in vendor_data if isinstance(v, dict)]

        # Get company context
        company_context = {
            "name": context.company_name or "the company",
            "size": context.company_size or "SMB",
            "tech_comfort": context.quiz_answers.get("tech_comfort", "medium") if context.quiz_answers else "medium",
            "budget_range": context.quiz_answers.get("budget_range", "5000-10000") if context.quiz_answers else "5000-10000",
        }

        # Get excluded vendors (already used in other recommendations)
        exclude_vendors = context.metadata.get("exclude_vendors", [])

        # Get readiness profile for adaptive recommendations
        readiness_profile = context.metadata.get("readiness_profile", {})

        # Generate recommendation
        recommendation = await self._generate_recommendation(
            finding=finding,
            vendors=vendors,
            industry=context.industry,
            company_context=company_context,
            expertise=context.expertise,
            exclude_vendors=exclude_vendors,
            readiness_profile=readiness_profile,
        )

        # Apply confidence-adjusted ROI
        recommendation = self._adjust_roi_for_confidence(
            recommendation,
            finding.get("confidence", "medium")
        )

        # Validate and normalize
        recommendation = self._validate_recommendation(recommendation, finding)

        # Validate vendors against knowledge base
        recommendation = self._validate_vendors(recommendation, context.industry)

        return recommendation

    async def _generate_recommendation(
        self,
        finding: Dict[str, Any],
        vendors: List[Dict[str, Any]],
        industry: str,
        company_context: Dict[str, Any],
        expertise: Optional[Dict[str, Any]],
        exclude_vendors: Optional[List[str]] = None,
        readiness_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate recommendation using Claude."""
        # Build set of excluded vendors (already used in other recommendations)
        excluded = set(v.lower() for v in (exclude_vendors or []))

        # Filter context vendors
        relevant_vendors = [
            v for v in vendors
            if v.get("slug", "").lower() not in excluded
            and v.get("name", "").lower().replace(" ", "-") not in excluded
        ]

        # Load KB vendor data relevant to this finding
        kb_vendors = load_kb_vendors_for_finding(
            finding=finding,
            industry=industry,
            context_vendors=relevant_vendors,
            max_vendors=15,
        )

        # Format vendor catalog for prompt
        vendor_catalog = format_vendors_for_prompt(kb_vendors, currency_symbol="€")

        # Note for LLM about excluded vendors
        exclude_note = ""
        if excluded:
            exclude_note = f"\n\nIMPORTANT: Do NOT recommend these vendors (already used in other recommendations): {', '.join(excluded)}"

        # Get AI tools context
        ai_tools_context = self._get_ai_tools_context()

        # Build readiness profile block for prompt
        rp = readiness_profile or {}
        readiness_block = f"""
CLIENT READINESS PROFILE:
- Infrastructure: {rp.get('infrastructure', 'unknown')}
- Build Willingness: {rp.get('build_willingness', 'unknown')}
- AI Experience: {rp.get('ai_experience', 'unknown')}
- Stack API Readiness: {rp.get('stack_api_readiness', 'unknown')}
- Urgency: {rp.get('urgency', 'unknown')}
- Preference: {rp.get('preference', 'unknown')}
"""

        prompt = f"""Generate a recommendation with AIOS OPTIONS for this finding.

FINDING:
{json.dumps(finding, indent=2)}

COMPANY CONTEXT:
- Industry: {industry}
- Size: {company_context['size']}
- Tech Comfort: {company_context['tech_comfort']}
- Budget Range: €{company_context['budget_range']}
{readiness_block}
{vendor_catalog}{exclude_note}

{ai_tools_context}

═══════════════════════════════════════════════════════════════════════════════
AIOS OPTIONS PATTERN (Best-Fit-First Philosophy)
═══════════════════════════════════════════════════════════════════════════════

Generate ALL THREE options:

Option A: CONNECT & AUTOMATE
- Wire existing tools together with AI workflows
- Build with Claude Code, MCP servers, APIs
- Include specific build time and tools used
- Best for: Companies with engineering capacity, API-ready stacks, unique workflows

Option B: ENHANCE WITH AI
- Add an AI intelligence layer on top of existing data
- Deploy agents, predictive workflows, dashboards
- Best for: When data exists but isn't being acted on

Option C: TARGETED UPGRADE
- Adopt a dedicated SaaS tool that solves this problem natively
- Best for: Lower total cost of ownership (including dev labor), compliance/certification requirements, companies with no engineering resources, dramatically faster time-to-value

═══════════════════════════════════════════════════════════════════════════════
RECOMMENDATION DECISION (evaluate per finding)
═══════════════════════════════════════════════════════════════════════════════

1. If no digital tool exists for this business function → recommend "targeted_upgrade"
   Buy the foundation. Recommend tools with strong APIs so they become
   connectable later. Frame as: "This is your foundation — once set up, we can
   wire AI workflows on top."

2. If existing tool is a dead end (no API, no data export, fundamentally broken)
   → recommend "targeted_upgrade"
   Replace with API-ready alternative. Frame as: "Your current tool traps your
   data. [Replacement] opens up integration possibilities."

3. If a dedicated SaaS solves it natively AND any of these apply:
   - Total cost including dev labor is lower than building custom
   - Company lacks engineering capacity to build and maintain
   - Compliance or certification is required (e.g., FDA, HIPAA, PCI)
   - Dramatically faster time-to-value (weeks vs months)
   → recommend "targeted_upgrade" or "enhance_with_ai"

4. If company has engineering capacity AND custom integration adds genuine value
   (unique workflows, competitive differentiation, lower long-term cost)
   → recommend "connect_and_automate"

5. If options are genuinely close → prefer "connect_and_automate" as tiebreaker

Always generate ALL THREE options regardless of recommendation.
Always explain WHY this recommendation fits THIS client's situation.
Never say "you're not technical enough" — AI-assisted building is accessible to everyone.
Adapt the HOW, not the WHETHER.
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
        "connect_and_automate": {{
            "approach": "<how to wire existing tools with AI workflows>",
            "build_time": "<e.g., 2 weeks (solo) / 4 days (guided)>",
            "tools_used": ["Claude Code", "<existing tool 1>", "<existing tool 2>"],
            "mcp_servers": ["<mcp-server-name if applicable>"],
            "monthly_cost": "<e.g., EUR 50-150 (API usage)>",
            "prerequisite": "<optional: what must be in place first, e.g. 'digital scheduling tool'>",
            "diy_complexity": "low|moderate|high",
            "automation_flow": {{
                "nodes": [
                    {{"id": "n1", "label": "<tool name>", "type": "existing_tool|new_tool|ai_layer|output"}},
                    {{"id": "n2", "label": "<AI processing>", "type": "ai_layer"}},
                    {{"id": "n3", "label": "<result>", "type": "output"}}
                ],
                "edges": [
                    {{"from": "n1", "to": "n2", "label": "<what data flows>"}},
                    {{"from": "n2", "to": "n3", "label": "<processed output>"}}
                ]
            }},
            "aios_layers_touched": ["connections", "intelligence"],
            "skills_created": ["<optional: /skill-name if this creates a reusable Claude Code skill>"],
            "context_needed": ["<optional: Context OS data needed, e.g., 'client profiles', 'process documentation'>"],
            "education_prereq": "<optional: what to learn first, e.g., 'Claude Code basics' or 'MCP setup'>",
            "cowork_tasks": ["<optional: ongoing tasks Claude Cowork handles, e.g., 'daily report generation'>"],
            "pros": ["<pro1>", "<pro2>"],
            "cons": ["<con1>", "<con2>"]
        }},
        "enhance_with_ai": {{
            "approach": "<what the AI agent/layer does>",
            "build_time": "<e.g., 2-3 weeks>",
            "tools_used": ["Claude API", "<data source>", "<dashboard>"],
            "monthly_cost": "<e.g., EUR 200-400>",
            "pros": ["<pro1>", "<pro2>"],
            "cons": ["<con1>", "<con2>"]
        }},
        "targeted_upgrade": {{
            "when_needed": "<explain when this option genuinely makes sense for this company>",
            "tools": ["<vendor1>", "<vendor2>"],
            "cost_range": "<e.g., EUR 200-500/month>",
            "migration_time": "<e.g., 4-6 weeks>",
            "pros": ["<pro1>", "<pro2>"],
            "cons": ["<con1>", "<con2>"]
        }}
    }},
    "our_recommendation": "connect_and_automate|enhance_with_ai|targeted_upgrade",
    "recommendation_rationale": "<why THIS recommendation fits THIS client's readiness level — reference their infrastructure, build willingness, and existing stack>",

    "comparison_summary": {{
        "table": [
            {{"aspect": "Monthly cost", "connect_and_automate": "€X", "enhance_with_ai": "€Y", "targeted_upgrade": "€Z"}},
            {{"aspect": "Build/setup time", "connect_and_automate": "X hours", "enhance_with_ai": "Y weeks", "targeted_upgrade": "Z weeks"}},
            {{"aspect": "Time to value", "connect_and_automate": "<actual estimate>", "enhance_with_ai": "<actual estimate>", "targeted_upgrade": "<actual estimate>"}},
            {{"aspect": "Disruption", "connect_and_automate": "<actual estimate>", "enhance_with_ai": "<actual estimate>", "targeted_upgrade": "<actual estimate>"}},
            {{"aspect": "Maintenance", "connect_and_automate": "API monitoring", "enhance_with_ai": "Model tuning", "targeted_upgrade": "Vendor managed"}}
        ],
        "winner_for_this_company": "connect_and_automate|enhance_with_ai|targeted_upgrade",
        "why_winner": "<1-2 sentences explaining why this wins GIVEN THIS COMPANY's readiness level and context>"
    }},

    "assumptions": [
        "<assumption 1 - MUST include number AND source>",
        "<assumption 2 - MUST include number AND source>",
        "<assumption 3 - MUST include number AND source>"
    ]
}}

NOTE: For the comparison_summary table, do NOT default to favorable values for any option.
Evaluate Time to value and Disruption honestly per situation.

═══════════════════════════════════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════════════════════════════════
- Evaluate the RECOMMENDATION DECISION logic above for EACH finding independently
- Do NOT recommend "targeted_upgrade" SOLELY because a newer tool exists without clear benefit
- Every connect_and_automate option MUST include build_time, tools_used, and automation_flow
- For connect_and_automate: include "aios_layers_touched" (which AIOS layers this builds: stack, connections, intelligence, data_os, skills, context_os, dashboard)
- For connect_and_automate: include "skills_created" if a reusable Claude Code skill results from this
- For connect_and_automate: include "context_needed" if Context OS data is required
- For connect_and_automate: include "education_prereq" when the client needs to learn something first
- For connect_and_automate: include "cowork_tasks" for ongoing tasks Claude Cowork handles
- For connect_and_automate: include "prerequisite" when the client lacks infrastructure
- For connect_and_automate: include "diy_complexity" to set expectations
- automation_flow: 3-6 nodes max, node types: "existing_tool" (green), "new_tool" (blue), "ai_layer" (purple), "output" (gray)
- Include MCP servers where applicable
- If ROI > 500%: MUST explain why this is exceptional (not typical)
- When recommending targeted_upgrade, frame it as the foundation for future automation

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
        return """You are an expert AI architecture consultant generating AIOS (AI Operating System) recommendations for CRB Analysis reports.

Your role: Help businesses connect what they have, automate what slows them down, and build what doesn't exist. Recommend what actually serves THIS company best.

═══════════════════════════════════════════════════════════════════════════════
BANNED LANGUAGE - Using any of these INVALIDATES your output:
═══════════════════════════════════════════════════════════════════════════════
- "seamless integration", "robust", "scalable", "enterprise-grade"
- "unlock value", "drive efficiency", "optimize", "streamline"
- "best-in-class solution"
- "cutting-edge", "revolutionary", "transform your business"

Naming specific tools IS fine when justified. What's banned is empty marketing language.

INSTEAD OF: "Consider migrating to a best-in-class solution"
USE: "Pearl provides FDA-cleared imaging analysis — the only viable path for diagnostic AI"

═══════════════════════════════════════════════════════════════════════════════
KEY PRINCIPLES (Best-Fit-First)
═══════════════════════════════════════════════════════════════════════════════
1. EVALUATE HONESTLY: Recommend what genuinely serves THIS company best
2. VENDOR CATALOG: For targeted_upgrade options, ONLY use vendors from the VENDOR CATALOG. Never invent vendor names or prices.
3. HONEST TRADE-OFFS: Every option has pros AND cons
4. CONTEXT-AWARE: Recommendation MUST match company's existing stack, size, tech comfort
5. BUILD TIME: Every connect option MUST include specific Claude Code hours
6. TOTAL COST OF OWNERSHIP: Include development labor, not just API costs, for connect options

═══════════════════════════════════════════════════════════════════════════════
NOTE: roi_percentage and payback_months will be calculated by the ROI Calculator Skill.
Do NOT generate these values - they will be computed using canonical formulas.
═══════════════════════════════════════════════════════════════════════════════
ADAPTIVE RECOMMENDATION RULES
═══════════════════════════════════════════════════════════════════════════════
- Evaluate each finding against the client's readiness profile
- If no tool exists or tool is a dead end → recommend "targeted_upgrade" (buy API-ready foundation)
- If dedicated SaaS solves it natively AND (total cost incl. dev labor is lower, OR company lacks build capacity, OR compliance required, OR dramatically faster time-to-value) → recommend "targeted_upgrade" or "enhance_with_ai"
- If company has engineering capacity AND custom integration adds genuine value → recommend "connect_and_automate"
- If options are genuinely close → prefer "connect_and_automate" as tiebreaker
- AI-assisted building is accessible to everyone — adapt the HOW, not the WHETHER
- Be honest about implementation complexity and ongoing maintenance burden"""

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
        """
        Mark recommendation with confidence level.

        NOTE: ROI adjustment is handled by ROI Calculator Skill using canonical formulas.
        This method now only records the confidence level for the ROI Calculator to use.
        """
        recommendation["confidence_level"] = confidence
        # ROI values will be calculated by ROI Calculator Skill - set to 0 as placeholder
        recommendation["roi_percentage"] = 0
        recommendation["payback_months"] = 0
        recommendation["roi_pending_calculation"] = True
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

        # Validate options — detect whether AIOS or legacy format
        options = recommendation.get("options", {})
        option_keys = set(options.keys())

        if option_keys & AIOS_OPTION_KEYS:
            # AIOS format (new) — validate AIOS options
            ca = options.get("connect_and_automate", {})
            rec_ca = self.CONNECT_AND_AUTOMATE_TEMPLATE.copy()
            rec_ca.update({k: v for k, v in ca.items() if v})

            ea = options.get("enhance_with_ai", {})
            rec_ea = self.ENHANCE_WITH_AI_TEMPLATE.copy()
            rec_ea.update({k: v for k, v in ea.items() if v})

            tu = options.get("targeted_upgrade", {})
            rec_tu = self.TARGETED_UPGRADE_TEMPLATE.copy()
            rec_tu.update({k: v for k, v in tu.items() if v})

            rec["options"] = {
                "connect_and_automate": rec_ca,
                "enhance_with_ai": rec_ea,
                "targeted_upgrade": rec_tu,
            }
        elif option_keys & LEGACY_OPTION_KEYS:
            # Legacy format — map to AIOS keys for backward compatibility
            logger.info("Mapping legacy option keys to AIOS format")

            # Map old → new
            ots = options.get("off_the_shelf", {})
            bic = options.get("best_in_class", {})
            cs = options.get("custom_solution", {})

            rec["options"] = {
                "connect_and_automate": cs if cs else self.CONNECT_AND_AUTOMATE_TEMPLATE.copy(),
                "enhance_with_ai": bic if bic else self.ENHANCE_WITH_AI_TEMPLATE.copy(),
                "targeted_upgrade": ots if ots else self.TARGETED_UPGRADE_TEMPLATE.copy(),
            }
        else:
            # Unknown format — use defaults
            rec["options"] = {
                "connect_and_automate": self.CONNECT_AND_AUTOMATE_TEMPLATE.copy(),
                "enhance_with_ai": self.ENHANCE_WITH_AI_TEMPLATE.copy(),
                "targeted_upgrade": self.TARGETED_UPGRADE_TEMPLATE.copy(),
            }

        # Our recommendation — normalize to AIOS keys
        our_rec = recommendation.get("our_recommendation", "connect_and_automate")
        if our_rec in OPTION_KEY_MAPPING:
            our_rec = OPTION_KEY_MAPPING[our_rec]
        if our_rec not in AIOS_OPTION_KEYS:
            our_rec = "connect_and_automate"
        rec["our_recommendation"] = our_rec

        rec["recommendation_rationale"] = recommendation.get(
            "recommendation_rationale", ""
        )
        # ROI values are calculated by ROI Calculator Skill, not LLM
        rec["roi_percentage"] = 0
        rec["payback_months"] = 0
        rec["roi_pending_calculation"] = True
        rec["assumptions"] = recommendation.get("assumptions", [])

        return rec

    def _validate_vendors(
        self,
        recommendation: Dict[str, Any],
        industry: str
    ) -> Dict[str, Any]:
        """
        Validate vendors in recommendation against knowledge base.

        Adds verification flags to each option indicating whether the
        vendor exists in our knowledge base.

        Args:
            recommendation: The recommendation with options
            industry: Industry for context-specific vendor lookup

        Returns:
            Recommendation with vendor validation metadata
        """
        try:
            validator = VendorValidationService(industry=industry)
            validation_result = validator.validate_recommendation(recommendation)
            recommendation = validator.apply_validation(recommendation, validation_result)

            # Log warnings for monitoring
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(f"Vendor validation: {warning}")

        except Exception as e:
            # Don't fail the recommendation if validation fails
            logger.error(f"Vendor validation failed: {e}")
            recommendation["vendor_validation"] = {
                "all_verified": False,
                "warnings": [f"Validation error: {str(e)}"],
                "validated_at": "error"
            }

        return recommendation

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
                "connect_and_automate": self.CONNECT_AND_AUTOMATE_TEMPLATE.copy(),
                "enhance_with_ai": self.ENHANCE_WITH_AI_TEMPLATE.copy(),
                "targeted_upgrade": self.TARGETED_UPGRADE_TEMPLATE.copy(),
            },
            "our_recommendation": "connect_and_automate",
            "recommendation_rationale": "Recommendation pending — evaluate all three options for your specific situation.",
            "roi_percentage": 0,
            "payback_months": 0,
            "roi_pending_calculation": True,
            "assumptions": ["ROI to be calculated by ROI Calculator Skill"],
        }


# For skill discovery
__all__ = ["ThreeOptionsSkill"]
