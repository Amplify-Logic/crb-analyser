"""
Teaser Report Service - Insights-First Approach

Generates the free teaser report with DIAGNOSTIC INSIGHTS (not recommendations):
- AI Readiness Score (calculated from quiz inputs)
- User reflections (what they told us - verbatim)
- Industry benchmarks (from Supabase KB with verified sources only)
- Opportunity areas (categories, not specific solutions)
- Personalized insight (soft LLM for warmth - no specific recommendations)

Uses verified data from Supabase + light LLM personalization.
This prevents contradictions with full report after workshop.

See: docs/plans/2026-01-03-insights-first-teaser-design.md
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta

import anthropic
from src.config.supabase_client import get_async_supabase
from src.config.settings import settings
from src.knowledge import normalize_industry

logger = logging.getLogger(__name__)

# Category labels for opportunity areas
CATEGORY_LABELS = {
    "customer_communication": "Customer Communication",
    "document_processing": "Document & Data Handling",
    "scheduling": "Scheduling & Coordination",
    "reporting": "Reporting & Analytics",
    "sales_pipeline": "Sales & Lead Management",
    "onboarding": "Client Onboarding",
    "operations": "Operations & Workflow",
    "billing": "Billing & Invoicing",
    "marketing": "Marketing & Outreach",
}


def _is_stale(verified_date: str, months: int = 18) -> bool:
    """Check if a verified_date is older than the specified months."""
    try:
        # Parse YYYY-MM format
        if len(verified_date) == 7:  # YYYY-MM
            year, month = verified_date.split("-")
            check_date = datetime(int(year), int(month), 1)
        else:  # YYYY-MM-DD
            check_date = datetime.fromisoformat(verified_date.replace("Z", ""))

        cutoff = datetime.now() - relativedelta(months=months)
        return check_date < cutoff
    except (ValueError, AttributeError):
        return True  # If we can't parse, consider it stale


async def _get_verified_benchmarks_from_supabase(industry: str) -> List[Dict[str, Any]]:
    """
    Get verified benchmarks from Supabase knowledge_embeddings table.

    Handles both formats:
    - New format: metadata.source = {name, verified_date, url}
    - Current format: metadata.source = "Source Name, Year"

    Defaults verified_date to current year if not explicitly provided.
    """
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("knowledge_embeddings").select(
            "content_id, title, content, metadata"
        ).eq("content_type", "benchmark").eq("industry", industry).execute()

        verified = []
        for row in result.data or []:
            metadata = row.get("metadata", {})
            raw_source = metadata.get("source")

            # Handle both formats
            if isinstance(raw_source, dict):
                # New format: {name, verified_date, url}
                source_name = raw_source.get("name")
                verified_date = raw_source.get("verified_date")
                source_url = raw_source.get("url")
            elif isinstance(raw_source, str) and raw_source:
                # Current format: "Source Name, Year"
                source_name = raw_source
                source_url = None
                # Check for verified_date in metadata first (vectorized data has this)
                verified_date = metadata.get("verified_date")
                if not verified_date:
                    # Fall back to extracting year from source string
                    if "2024" in raw_source:
                        verified_date = "2024-06"  # Assume mid-year
                    elif "2025" in raw_source:
                        verified_date = "2025-06"
                    else:
                        verified_date = "2024-01"  # Default to 2024
            else:
                # No source - skip
                logger.debug(f"Skipping benchmark without source: {row.get('content_id')}")
                continue

            if not source_name:
                logger.debug(f"Skipping benchmark with empty source: {row.get('content_id')}")
                continue

            # Check staleness (benchmarks older than 18 months)
            if _is_stale(verified_date, months=18):
                logger.debug(f"Skipping stale benchmark: {row.get('content_id')} (verified: {verified_date})")
                continue

            # Extract value from metadata or content
            value = metadata.get("value")
            if not value:
                # Try to parse from content (format: "Description\nValue: X")
                content = row.get("content", "")
                if "Value:" in content:
                    value = content.split("Value:")[-1].split("\n")[0].strip()
                else:
                    value = content[:100] if content else "See full report"

            verified.append({
                "metric": row.get("title", metadata.get("name", "Unknown")),
                "value": str(value),
                "source": {
                    "name": source_name,
                    "url": source_url,
                    "verified_date": verified_date,
                },
                "relevance": metadata.get("relevance_template"),
            })

        logger.info(f"Found {len(verified)} verified benchmarks for {industry}")
        return verified[:5]  # Limit to 5 benchmarks for teaser

    except Exception as e:
        logger.error(f"Failed to get benchmarks from Supabase: {e}")
        return []


async def _get_opportunity_categories_from_supabase(
    industry: str,
    pain_points: List[str]
) -> List[Dict[str, Any]]:
    """
    Map user pain points to opportunity categories from Supabase.

    Returns categories (not specific recommendations).
    """
    try:
        supabase = await get_async_supabase()

        # Get opportunities for this industry
        result = await supabase.table("knowledge_embeddings").select(
            "content_id, title, metadata"
        ).eq("content_type", "opportunity").eq("industry", industry).execute()

        # Build category map from opportunities
        categories: Dict[str, Dict[str, Any]] = {}
        for row in result.data or []:
            metadata = row.get("metadata", {})
            category = metadata.get("category")
            keywords = metadata.get("keywords", [])

            if not category:
                continue

            if category not in categories:
                categories[category] = {
                    "category": category,
                    "label": CATEGORY_LABELS.get(category, category.replace("_", " ").title()),
                    "keywords": set(keywords),
                    "matched_pain_points": [],
                    "in_full_report": metadata.get("in_full_report", [
                        "Specific automation tools with pricing",
                        "ROI calculation for your situation",
                        "Implementation timeline"
                    ]),
                }
            else:
                # Merge keywords
                categories[category]["keywords"].update(keywords)

        # Match pain points to categories
        for pain in pain_points:
            pain_lower = pain.lower()
            for cat_id, cat_data in categories.items():
                for keyword in cat_data["keywords"]:
                    if keyword.lower() in pain_lower or pain_lower in keyword.lower():
                        if pain not in cat_data["matched_pain_points"]:
                            cat_data["matched_pain_points"].append(pain)
                        break

        # Sort by number of matches, return top 3
        matched = [c for c in categories.values() if c["matched_pain_points"]]
        matched.sort(key=lambda c: len(c["matched_pain_points"]), reverse=True)

        result_categories = []
        for i, cat in enumerate(matched[:3]):
            result_categories.append({
                "category": cat["category"],
                "label": cat["label"],
                "potential": "high" if i < 2 else "medium",
                "matched_because": f"You mentioned: {', '.join(cat['matched_pain_points'][:2])}",
                "in_full_report": cat["in_full_report"][:3],
            })

        logger.info(f"Matched {len(result_categories)} opportunity categories for {industry}")
        return result_categories

    except Exception as e:
        logger.error(f"Failed to get opportunity categories from Supabase: {e}")
        return []


def _extract_user_reflections(
    quiz_answers: Dict[str, Any],
    company_profile: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Extract user reflections from quiz answers - what they told us.

    These are verbatim or close paraphrases of their inputs.
    Cannot be "wrong" - we're just reflecting their words back.
    """
    reflections = []

    # Pain points - most important
    pain_points = quiz_answers.get("pain_points", [])
    if isinstance(pain_points, str):
        pain_points = [pain_points]
    if pain_points:
        for pain in pain_points[:3]:  # Max 3 pain points
            reflections.append({
                "type": "pain_point",
                "what_you_told_us": f"'{pain}' is consuming significant time",
                "source": "quiz_response",
            })

    # Goals if provided
    goals = quiz_answers.get("goals", quiz_answers.get("goals_priorities", []))
    if isinstance(goals, str):
        goals = [goals]
    if goals:
        reflections.append({
            "type": "goal",
            "what_you_told_us": f"Your priority: {goals[0] if goals else 'improving efficiency'}",
            "source": "quiz_response",
        })

    # Current tools/tech stack
    tech_stack = company_profile.get("tech_stack", {})
    technologies = tech_stack.get("technologies_detected", [])
    if technologies:
        tech_names = []
        for t in technologies[:5]:
            if isinstance(t, dict):
                tech_names.append(t.get("value", str(t)))
            else:
                tech_names.append(str(t))
        if tech_names:
            reflections.append({
                "type": "current_state",
                "what_you_told_us": f"Currently using: {', '.join(tech_names)}",
                "source": "company_research",
            })

    # Company size context
    size = company_profile.get("size", {})
    employee_range = size.get("employee_range", {})
    if isinstance(employee_range, dict):
        employee_range = employee_range.get("value", "")
    if employee_range:
        reflections.append({
            "type": "current_state",
            "what_you_told_us": f"Team size: {employee_range} employees",
            "source": "quiz_response",
        })

    return reflections[:5]  # Max 5 reflections


async def _generate_personalized_insight(
    company_name: str,
    industry: str,
    score: int,
    pain_points: List[str],
    benchmarks: List[Dict[str, Any]],
) -> Dict[str, str]:
    """
    Generate a personalized insight using Claude Haiku.

    This is SAFE personalization because it:
    - Connects their situation to verified industry data
    - Frames the workshop as the next step
    - Does NOT recommend specific tools or solutions
    - Does NOT promise specific ROI

    Returns a headline and body text.
    """
    try:
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("No Anthropic API key - using default insight")
            return _get_default_insight(company_name, industry, score)

        # Build context from verified data
        pain_summary = ", ".join(pain_points[:3]) if pain_points else "operational efficiency"
        benchmark_context = ""
        if benchmarks:
            benchmark_context = "\n".join([
                f"- {b['metric']}: {b['value']} (Source: {b['source']['name']})"
                for b in benchmarks[:3]
            ])

        prompt = f"""You are writing a brief, warm, personalized insight for a business teaser report.

CONTEXT:
- Company: {company_name}
- Industry: {industry}
- AI Readiness Score: {score}/100
- Their pain points: {pain_summary}
- Relevant industry benchmarks:
{benchmark_context or "No specific benchmarks available"}

TASK: Write a 2-3 sentence personalized insight that:
1. Acknowledges what they shared (pain points)
2. Connects it to industry context (use the benchmarks if relevant)
3. Creates curiosity about what the workshop will uncover

RULES:
- Be warm and conversational, not corporate
- DO NOT recommend specific tools or vendors
- DO NOT promise specific ROI or savings
- DO NOT make claims we can't verify
- Keep it under 50 words
- Address them as "you" not by company name

Return ONLY the insight text, no quotes or formatting."""

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",  # Fast + cheap
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )

        insight_text = message.content[0].text.strip()

        return {
            "headline": f"Your {industry.replace('-', ' ').title()} AI Opportunity",
            "body": insight_text,
        }

    except Exception as e:
        logger.error(f"Failed to generate personalized insight: {e}")
        return _get_default_insight(company_name, industry, score)


def _get_default_insight(company_name: str, industry: str, score: int) -> Dict[str, str]:
    """Fallback insight when LLM is unavailable."""
    if score >= 60:
        body = f"Based on what you've shared, you're ahead of many {industry.replace('-', ' ')} businesses in AI readiness. The workshop will help identify your highest-impact opportunities."
    else:
        body = f"Many {industry.replace('-', ' ')} businesses face similar challenges. The workshop will help us understand your specific situation and identify the most practical next steps."

    return {
        "headline": f"Your {industry.replace('-', ' ').title()} AI Opportunity",
        "body": body,
    }


async def generate_teaser_report(
    company_profile: Dict[str, Any],
    quiz_answers: Dict[str, Any],
    interview_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate insights-first teaser report.

    NO AI GENERATION - only verified data from Supabase.
    Returns diagnostic insights that cannot contradict the full report.

    Output schema:
    - ai_readiness: Score + breakdown (calculated from inputs)
    - diagnostics: User reflections + industry benchmarks (with sources)
    - opportunity_areas: Categories only (not specific recommendations)
    - next_steps: Workshop info + what full report includes
    """
    # Ensure we have valid dicts
    company_profile = company_profile or {}
    quiz_answers = quiz_answers or {}

    # Extract and normalize industry
    industry_obj = company_profile.get("industry", {})
    raw_industry = industry_obj.get("primary_industry", {}).get("value", "")
    industry = normalize_industry(raw_industry) if raw_industry else "professional-services"

    company_name = _extract_company_name(company_profile)
    industry_display = industry_obj.get("primary_industry", {}).get("value", industry.replace("-", " ").title())

    # Calculate AI Readiness Score (from quiz inputs - diagnostic)
    score_data = _calculate_ai_readiness_score(company_profile, quiz_answers)

    # Extract user reflections (what they told us - verbatim)
    user_reflections = _extract_user_reflections(quiz_answers, company_profile)

    # Get verified benchmarks from Supabase (with sources)
    industry_benchmarks = await _get_verified_benchmarks_from_supabase(industry)

    # Get pain points for category mapping
    pain_points = quiz_answers.get("pain_points", [])
    if isinstance(pain_points, str):
        pain_points = [pain_points]

    # Map pain points to opportunity categories (not specific recommendations)
    opportunity_areas = await _get_opportunity_categories_from_supabase(industry, pain_points)

    # Generate personalized insight (soft LLM for warmth)
    personalized_insight = await _generate_personalized_insight(
        company_name=company_name,
        industry=industry,
        score=score_data["score"],
        pain_points=pain_points,
        benchmarks=industry_benchmarks,
    )

    logger.info(
        f"Teaser generated for {company_name}: "
        f"score={score_data['score']}, "
        f"reflections={len(user_reflections)}, "
        f"benchmarks={len(industry_benchmarks)}, "
        f"opportunity_areas={len(opportunity_areas)}"
    )

    return {
        # Metadata
        "generated_at": datetime.utcnow().isoformat(),
        "company_name": company_name,
        "industry": industry_display,
        "industry_slug": industry,

        # Personalized insight (LLM-generated warmth)
        "personalized_insight": personalized_insight,

        # Section 1: AI Readiness Score (diagnostic)
        "ai_readiness": {
            "score": score_data["score"],
            "breakdown": score_data["breakdown"],
            "interpretation": _get_score_interpretation(score_data["score"]),
        },

        # Section 2: Diagnostics (verified data only)
        "diagnostics": {
            "user_reflections": user_reflections,
            "industry_benchmarks": industry_benchmarks,
        },

        # Section 3: Opportunity Areas (categories, not prescriptions)
        "opportunity_areas": opportunity_areas,

        # Section 4: What's Next (workshop + full report)
        "next_steps": {
            "workshop": {
                "what_it_is": "AI-powered deep-dive conversation",
                "duration": "~90 minutes (can pause/resume)",
                "phases": [
                    {"name": "Confirmation", "description": "Verify our research about your business"},
                    {"name": "Deep-Dive", "description": "Explore your pain points in detail"},
                    {"name": "Synthesis", "description": "Prioritize opportunities for your report"},
                ],
                "outcome": "Validated priorities and personalized findings",
            },
            "full_report_includes": [
                {"icon": "📊", "title": "Prioritized Findings", "description": "10-15 opportunities ranked by impact"},
                {"icon": "💰", "title": "ROI Calculations", "description": "Specific estimates for your situation"},
                {"icon": "🛠️", "title": "Vendor Recommendations", "description": "3 options per finding with pricing"},
                {"icon": "📋", "title": "Implementation Roadmap", "description": "Week-by-week action plan"},
            ],
        },

        # Legacy fields for backward compatibility (will be deprecated)
        "ai_readiness_score": score_data["score"],
        "score_breakdown": score_data["breakdown"],
        "score_interpretation": _get_score_interpretation(score_data["score"]),
    }


# Sync wrapper for routes that don't use async
def generate_teaser_report_sync(
    company_profile: Dict[str, Any],
    quiz_answers: Dict[str, Any],
    interview_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Sync version for routes that don't use async."""
    import asyncio

    # Check if we're already in an async context
    try:
        loop = asyncio.get_running_loop()
        # We're in async context, create task
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                generate_teaser_report(company_profile, quiz_answers, interview_data)
            )
            return future.result()
    except RuntimeError:
        # No running loop, safe to use asyncio.run
        return asyncio.run(generate_teaser_report(company_profile, quiz_answers, interview_data))


def _extract_company_name(company_profile: Dict[str, Any]) -> str:
    """Extract company name from profile."""
    basics = company_profile.get("basics", {})
    name = basics.get("name", {})
    if isinstance(name, dict):
        return name.get("value", "Your Company")
    return str(name) if name else "Your Company"


def _calculate_ai_readiness_score(
    company_profile: Dict[str, Any],
    quiz_answers: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calculate AI readiness score with breakdown.

    Purely diagnostic - based on quiz inputs only.
    Does not use KB or make predictions.
    """
    # Ensure we have valid dicts
    company_profile = company_profile or {}
    quiz_answers = quiz_answers or {}

    breakdown = {}

    # Tech maturity (0-25 points)
    tech_stack = company_profile.get("tech_stack") or {}
    technologies = tech_stack.get("technologies_detected") or []
    tech_count = len(technologies) if isinstance(technologies, list) else 0
    tech_score = min(25, tech_count * 5)
    breakdown["tech_maturity"] = {
        "score": tech_score,
        "max": 25,
        "factors": ["Current tech stack", "Tool adoption"]
    }

    # Process clarity (0-25 points)
    pain_points = quiz_answers.get("pain_points") or []
    if isinstance(pain_points, str):
        pain_points = [pain_points]
    has_documented = quiz_answers.get("processes_documented", False)
    process_score = 10 if has_documented else 5
    process_score += min(15, len(pain_points) * 3 if isinstance(pain_points, list) else 3)
    breakdown["process_clarity"] = {
        "score": process_score,
        "max": 25,
        "factors": ["Documented processes", "Identified pain points"]
    }

    # Data readiness (0-25 points)
    size = company_profile.get("size") or {}
    employee_count_obj = size.get("employee_count") or {}
    employee_count = employee_count_obj.get("value", 10) if isinstance(employee_count_obj, dict) else 10
    if isinstance(employee_count, str):
        try:
            if "-" in str(employee_count):
                parts = str(employee_count).split("-")
                employee_count = int(parts[0])
            else:
                employee_count = int(str(employee_count).replace("+", ""))
        except (ValueError, AttributeError):
            employee_count = 10
    if not isinstance(employee_count, int):
        employee_count = 10
    data_score = min(25, 5 + (employee_count // 10) * 2)
    breakdown["data_readiness"] = {
        "score": data_score,
        "max": 25,
        "factors": ["Company size", "Data generation potential"]
    }

    # AI experience (0-25 points)
    current_tools = quiz_answers.get("current_tools") or []
    ai_experience = quiz_answers.get("ai_experience") or "none"
    ai_score = 5
    if ai_experience == "experimenting":
        ai_score = 12
    elif ai_experience == "using":
        ai_score = 20
    elif ai_experience == "scaling":
        ai_score = 25
    ai_score += min(5, len(current_tools) if isinstance(current_tools, list) else 0)
    ai_score = min(25, ai_score)
    breakdown["ai_experience"] = {
        "score": ai_score,
        "max": 25,
        "factors": ["Current AI usage", "Tool adoption"]
    }

    total_score = sum(b["score"] for b in breakdown.values())

    return {
        "score": total_score,
        "breakdown": breakdown
    }


def _get_score_interpretation(score: int) -> Dict[str, Any]:
    """Get interpretation text for score."""
    if score >= 80:
        return {
            "level": "Excellent",
            "summary": "Your organization is highly ready for AI implementation.",
            "recommendation": "Focus on strategic AI initiatives that drive competitive advantage."
        }
    elif score >= 60:
        return {
            "level": "Good",
            "summary": "You have a solid foundation for AI adoption.",
            "recommendation": "Address a few gaps to maximize AI ROI."
        }
    elif score >= 40:
        return {
            "level": "Developing",
            "summary": "There are opportunities to strengthen your AI readiness.",
            "recommendation": "Start with quick wins while building foundational capabilities."
        }
    else:
        return {
            "level": "Early Stage",
            "summary": "You're at the beginning of your AI journey.",
            "recommendation": "Focus on foundational improvements before major AI investments."
        }
