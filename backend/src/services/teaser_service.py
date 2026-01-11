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

# Score interpretation thresholds (internal assessment framework)
# These are NOT industry benchmarks - just our scoring rubric
SCORE_THRESHOLDS = {
    "early_stage": {"max": 30, "label": "Early Stage", "meaning": "Just starting the AI journey"},
    "developing": {"max": 50, "label": "Developing", "meaning": "Foundation in place, room to grow"},
    "established": {"max": 70, "label": "Established", "meaning": "Good systems, ready for optimization"},
    "advanced": {"max": 100, "label": "Advanced", "meaning": "Well-positioned for AI adoption"},
}

# Quick wins - practical advice without unsourced statistics
# These are actionable suggestions, not promises of specific outcomes
QUICK_WINS = {
    "scheduling": {
        "title": "Automate Your Appointment Reminders",
        "description": "Set up automated SMS/email reminders 24 hours before appointments. Reduces no-shows and saves time chasing confirmations.",
        "action": "Most calendar tools (Google Calendar, Calendly, even basic CRMs) have this built-in. Takes about 15 minutes to set up.",
        "impact": "Less time spent on reminder calls and rescheduling missed appointments",
    },
    "customer_communication": {
        "title": "Create a Response Template Library",
        "description": "Document your most common customer questions and create ready-to-use responses. Improves consistency and speed.",
        "action": "Start a simple doc or use your email's template feature. Add one template per day until you've covered the common ones.",
        "impact": "Faster response times and more consistent, professional communication",
    },
    "document_processing": {
        "title": "Digitize Your Most-Used Form",
        "description": "Take your most frequently used paper form and make it a simple online form (Google Forms, Typeform, JotForm are free).",
        "action": "Pick ONE form you use weekly. Create a digital version today. Share the link instead of paper.",
        "impact": "Reduces manual data entry and the errors that come with it",
    },
    "billing": {
        "title": "Enable Online Payments",
        "description": "If you're still doing checks/cash, adding a simple payment link makes it easier for customers to pay promptly.",
        "action": "Square, Stripe, or PayPal invoicing takes minutes to set up. Add a 'Pay Now' link to your invoices.",
        "impact": "Removes friction from getting paid - customers can pay immediately",
    },
    "operations": {
        "title": "Create a Daily Checklist",
        "description": "Write down the 5-7 things that MUST happen every day. Simple but effective for consistency.",
        "action": "Spend 10 minutes listing daily must-dos. Use a free tool like Notion, Trello, or even paper.",
        "impact": "Fewer forgotten tasks and clearer accountability",
    },
    "default": {
        "title": "Start Tracking Time on One Task",
        "description": "Pick your most repetitive task and track how long it actually takes for one week. Data drives decisions.",
        "action": "Use your phone timer or a free app like Toggl. Just track one thing to start.",
        "impact": "Reveals where your time actually goes - often different from what you'd guess",
    },
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
    company_profile: Dict[str, Any],
    interview_data: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Extract user reflections from quiz answers - what they told us.

    These are verbatim or close paraphrases of their inputs.
    Cannot be "wrong" - we're just reflecting their words back.

    Searches multiple locations for data:
    - quiz_answers directly
    - company_profile.extracted_facts
    - interview_data.messages
    """
    reflections = []

    # Get extracted facts from company profile (where quiz engine stores them)
    extracted_facts = company_profile.get("extracted_facts", {})

    # Pain points - check multiple locations
    pain_points = (
        quiz_answers.get("pain_points", []) or
        extracted_facts.get("pain_points", []) or
        company_profile.get("pain_points", [])
    )
    if isinstance(pain_points, str):
        pain_points = [pain_points]

    # Extract pain point values (may be dicts with "value" key)
    pain_texts = []
    for pain in pain_points[:4]:
        if isinstance(pain, dict):
            pain_texts.append(pain.get("value", pain.get("fact", str(pain))))
        elif isinstance(pain, str) and pain:
            pain_texts.append(pain)

    for pain_text in pain_texts:
        reflections.append({
            "type": "pain_point",
            "what_you_told_us": pain_text,
            "source": "quiz_response",
        })

    # Goals - check multiple locations
    goals = (
        quiz_answers.get("goals", []) or
        quiz_answers.get("goals_priorities", []) or
        extracted_facts.get("goals_priorities", []) or
        company_profile.get("goals", [])
    )
    if isinstance(goals, str):
        goals = [goals]

    for goal in goals[:2]:
        goal_text = goal.get("value", goal) if isinstance(goal, dict) else goal
        if goal_text:
            reflections.append({
                "type": "goal",
                "what_you_told_us": f"Priority: {goal_text}",
                "source": "quiz_response",
            })

    # Operations/processes mentioned
    operations = extracted_facts.get("operations", [])
    for op in operations[:2]:
        op_text = op.get("value", op) if isinstance(op, dict) else op
        if op_text:
            reflections.append({
                "type": "current_state",
                "what_you_told_us": op_text,
                "source": "quiz_response",
            })

    # Current tools/tech stack
    tech_stack = company_profile.get("tech_stack", {})
    technologies = tech_stack.get("technologies_detected", [])
    if not technologies:
        technologies = extracted_facts.get("tech_stack", [])

    if technologies:
        tech_names = []
        for t in technologies[:5]:
            if isinstance(t, dict):
                tech_names.append(t.get("value", t.get("name", str(t))))
            else:
                tech_names.append(str(t))
        if tech_names:
            reflections.append({
                "type": "current_state",
                "what_you_told_us": f"Currently using: {', '.join(tech_names)}",
                "source": "company_research",
            })

    # Extract from interview messages if available
    if interview_data:
        messages = interview_data.get("messages", [])
        for msg in messages:
            if msg.get("role") == "user" and len(msg.get("content", "")) > 20:
                # User said something substantial
                content = msg["content"][:150]
                if len(msg["content"]) > 150:
                    content += "..."
                reflections.append({
                    "type": "pain_point",
                    "what_you_told_us": f'"{content}"',
                    "source": "interview",
                })
                if len(reflections) >= 6:
                    break

    # Company size context (lower priority, add at end)
    size = company_profile.get("size", {})
    employee_range = size.get("employee_range", {})
    if isinstance(employee_range, dict):
        employee_range = employee_range.get("value", "")
    if employee_range and len(reflections) < 6:
        reflections.append({
            "type": "current_state",
            "what_you_told_us": f"Team size: {employee_range} employees",
            "source": "quiz_response",
        })

    return reflections[:6]  # Max 6 reflections


def _get_score_context(score: int) -> Dict[str, Any]:
    """
    Get context for the score based on our assessment framework.

    NOTE: We do NOT claim industry benchmarks since we don't have verified data.
    Instead, we explain what the score means in our framework.
    """
    # Determine level based on our scoring rubric
    if score >= 70:
        level = "advanced"
        level_label = "Advanced"
        context_text = "Your systems and processes are well-suited for AI adoption"
        next_step = "Focus on optimization and advanced automation"
    elif score >= 50:
        level = "established"
        level_label = "Established"
        context_text = "You have a solid foundation to build on"
        next_step = "Identify high-impact areas for targeted automation"
    elif score >= 30:
        level = "developing"
        level_label = "Developing"
        context_text = "You're building the foundation for AI readiness"
        next_step = "Start with quick wins to build momentum"
    else:
        level = "early_stage"
        level_label = "Early Stage"
        context_text = "You're at the beginning of your AI journey"
        next_step = "Focus on fundamentals before automation"

    return {
        "your_score": score,
        "level": level,
        "level_label": level_label,
        "context_text": context_text,
        "next_step": next_step,
        # Explicitly note we're not comparing to others
        "note": "Based on our assessment framework",
    }


def _get_quick_win(
    industry: str,
    score: int,
    opportunity_areas: List[Dict[str, Any]],
    pain_points: List[str]
) -> Dict[str, Any]:
    """
    Select the most relevant quick win based on their situation.

    This is FREE actionable value - something they can do TODAY.
    """
    # Try to match to their opportunity areas first
    if opportunity_areas:
        first_area = opportunity_areas[0].get("category", "")
        if first_area in QUICK_WINS:
            return QUICK_WINS[first_area]

    # Try to match pain points to quick wins
    pain_text = " ".join(pain_points).lower()

    if any(word in pain_text for word in ["schedule", "appointment", "booking", "calendar", "no-show"]):
        return QUICK_WINS["scheduling"]
    elif any(word in pain_text for word in ["email", "respond", "customer", "client", "phone", "call"]):
        return QUICK_WINS["customer_communication"]
    elif any(word in pain_text for word in ["paper", "form", "document", "file", "data entry"]):
        return QUICK_WINS["document_processing"]
    elif any(word in pain_text for word in ["invoice", "payment", "billing", "collect", "pay"]):
        return QUICK_WINS["billing"]
    elif any(word in pain_text for word in ["process", "workflow", "task", "forget", "track"]):
        return QUICK_WINS["operations"]

    # Default based on industry patterns
    industry_defaults = {
        "plumbing": "scheduling",
        "hvac": "scheduling",
        "electrical": "scheduling",
        "dental": "customer_communication",
        "legal": "document_processing",
        "accounting": "document_processing",
        "real-estate": "customer_communication",
        "construction": "operations",
    }

    default_category = industry_defaults.get(industry, "default")
    return QUICK_WINS.get(default_category, QUICK_WINS["default"])


async def _generate_personalized_insight(
    company_name: str,
    industry: str,
    score: int,
    pain_points: List[str],
    benchmarks: List[Dict[str, Any]],
    user_reflections: List[Dict[str, Any]],
    score_context: Dict[str, Any],
) -> Dict[str, str]:
    """
    Generate a personalized insight using Claude Haiku.

    This is SAFE personalization because it:
    - References what the user actually said
    - Uses only verified benchmark data (if available)
    - Does NOT recommend specific tools or solutions
    - Does NOT promise specific ROI or make up statistics

    Returns a headline and body text.
    """
    try:
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("No Anthropic API key - using default insight")
            return _get_default_insight(company_name, industry, score, score_context)

        # Get actual things they said
        their_words = []
        for ref in user_reflections[:3]:
            if ref.get("type") == "pain_point":
                their_words.append(ref.get("what_you_told_us", ""))

        # Only include benchmarks if we have real verified data
        benchmark_context = ""
        if benchmarks:
            benchmark_context = "\n".join([
                f"- {b['metric']}: {b['value']} (Source: {b['source']['name']})"
                for b in benchmarks[:3]
            ])

        # Use score context (our framework, not fake industry benchmarks)
        score_level = score_context.get("level_label", "Developing")
        score_meaning = score_context.get("context_text", "")

        prompt = f"""You are writing a brief, warm, personalized insight for a business teaser report.

CONTEXT:
- Company: {company_name}
- Industry: {industry.replace('-', ' ')}
- AI Readiness Score: {score}/100 ({score_level})
- What this means: {score_meaning}

WHAT THEY TOLD US:
{chr(10).join(['- ' + w for w in their_words]) if their_words else '- (Limited information provided)'}

{f"VERIFIED INDUSTRY DATA:{chr(10)}{benchmark_context}" if benchmark_context else ""}

TASK: Write a 2-3 sentence personalized insight that:
1. References something SPECIFIC they mentioned (use their actual words if available)
2. Provides one meaningful observation about their situation
3. Creates curiosity about what deeper analysis would reveal

CRITICAL RULES:
- Be specific, not generic. Reference what they actually said.
- Be warm and conversational, not corporate
- DO NOT make up statistics or industry benchmarks
- DO NOT recommend specific tools or vendors
- DO NOT promise specific ROI or savings numbers
- DO NOT claim "businesses like yours" save X% - we don't have that data
- Keep it under 60 words
- Address them as "you"

Return ONLY the insight text, no quotes or formatting."""

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",  # Fast + cheap
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        insight_text = message.content[0].text.strip()

        # Generate a more specific headline based on their situation
        if pain_points:
            first_pain = pain_points[0].lower()
            if "schedule" in first_pain or "appointment" in first_pain:
                headline = "Your Scheduling Opportunity"
            elif "customer" in first_pain or "client" in first_pain or "communication" in first_pain:
                headline = "Your Customer Experience Opportunity"
            elif "time" in first_pain or "hour" in first_pain:
                headline = "Your Time Recovery Opportunity"
            else:
                headline = f"Your {industry.replace('-', ' ').title()} Opportunity"
        else:
            headline = f"Your {industry.replace('-', ' ').title()} Opportunity"

        return {
            "headline": headline,
            "body": insight_text,
        }

    except Exception as e:
        logger.error(f"Failed to generate personalized insight: {e}")
        return _get_default_insight(company_name, industry, score, score_context)


def _get_default_insight(
    company_name: str,
    industry: str,
    score: int,
    score_context: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """Fallback insight when LLM is unavailable. No fabricated statistics."""
    industry_display = industry.replace('-', ' ')

    if score_context:
        level = score_context.get("level_label", "Developing")
        context = score_context.get("context_text", "")
        next_step = score_context.get("next_step", "")
        body = f"Your score of {score}/100 puts you at the '{level}' stage. {context}. {next_step}"
    else:
        if score >= 50:
            body = f"Based on what you've shared, you have a solid foundation to build on. The workshop will help identify your highest-impact opportunities."
        else:
            body = f"Many {industry_display} businesses face similar challenges. The workshop will help us understand your specific situation and identify practical next steps."

    return {
        "headline": f"Your {industry_display.title()} Opportunity",
        "body": body,
    }


def _get_fallback_benchmarks(industry: str) -> List[Dict[str, Any]]:
    """
    Provide general context when Supabase has no industry-specific data.

    NOTE: We don't fabricate statistics. These are general observations
    that we label clearly as general patterns, not specific research.
    """
    # Return empty - better to show nothing than fake data
    # The full report will have real, researched data
    return []


def _get_fallback_opportunities(industry: str) -> List[Dict[str, Any]]:
    """
    Provide general opportunity areas when Supabase has no industry-specific data.

    These are common patterns, not promises of specific outcomes.
    """
    # Common opportunities for most service businesses - no specific claims
    return [
        {
            "category": "customer_communication",
            "label": "Customer Communication",
            "potential": "high",
            "matched_because": "A common area where businesses find room to improve",
            "in_full_report": [
                "Specific tools for your situation",
                "Estimated time savings based on your answers",
                "Step-by-step implementation approach",
            ],
        },
        {
            "category": "scheduling",
            "label": "Scheduling & Coordination",
            "potential": "high",
            "matched_because": "Often a significant time investment for service businesses",
            "in_full_report": [
                "Automation options comparison",
                "Integration with your existing tools",
                "Personalized ROI estimate",
            ],
        },
    ]


async def generate_teaser_report(
    company_profile: Dict[str, Any],
    quiz_answers: Dict[str, Any],
    interview_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate insights-first teaser report with FREE actionable value.

    Returns:
    - ai_readiness: Score + breakdown + industry comparison
    - quick_win: ONE actionable thing they can do TODAY (free value!)
    - diagnostics: User reflections + industry benchmarks
    - opportunity_areas: Categories with what full report reveals
    - next_steps: Workshop info + what full report includes
    """
    # Ensure we have valid dicts
    company_profile = company_profile or {}
    quiz_answers = quiz_answers or {}
    interview_data = interview_data or {}

    # Extract and normalize industry
    industry_obj = company_profile.get("industry", {})
    raw_industry = industry_obj.get("primary_industry", {}).get("value", "")
    industry = normalize_industry(raw_industry) if raw_industry else "professional-services"

    company_name = _extract_company_name(company_profile)
    industry_display = industry_obj.get("primary_industry", {}).get("value", industry.replace("-", " ").title())

    # Calculate AI Readiness Score (from quiz inputs - diagnostic)
    score_data = _calculate_ai_readiness_score(company_profile, quiz_answers)
    score = score_data["score"]

    # Get score context (our framework - NOT fake industry benchmarks)
    score_context = _get_score_context(score)

    # Extract user reflections (what they told us - from all sources)
    user_reflections = _extract_user_reflections(quiz_answers, company_profile, interview_data)

    # Get verified benchmarks from Supabase (with sources)
    industry_benchmarks = await _get_verified_benchmarks_from_supabase(industry)

    # Use fallback if no benchmarks found
    if not industry_benchmarks:
        industry_benchmarks = _get_fallback_benchmarks(industry)
        logger.info(f"Using fallback benchmarks for {industry}")

    # Get pain points for category mapping - check multiple sources
    extracted_facts = company_profile.get("extracted_facts", {})
    pain_points = (
        quiz_answers.get("pain_points", []) or
        extracted_facts.get("pain_points", []) or
        []
    )
    if isinstance(pain_points, str):
        pain_points = [pain_points]

    # Extract text from pain point dicts
    pain_texts = []
    for p in pain_points:
        if isinstance(p, dict):
            pain_texts.append(p.get("value", p.get("fact", str(p))))
        elif isinstance(p, str):
            pain_texts.append(p)

    # Map pain points to opportunity categories (not specific recommendations)
    opportunity_areas = await _get_opportunity_categories_from_supabase(industry, pain_texts)

    # Use fallback if no opportunities found
    if not opportunity_areas:
        opportunity_areas = _get_fallback_opportunities(industry)
        logger.info(f"Using fallback opportunities for {industry}")

    # Get quick win - FREE actionable value!
    quick_win = _get_quick_win(industry, score, opportunity_areas, pain_texts)

    # Generate personalized insight (soft LLM for warmth)
    personalized_insight = await _generate_personalized_insight(
        company_name=company_name,
        industry=industry,
        score=score,
        pain_points=pain_texts,
        benchmarks=industry_benchmarks,
        user_reflections=user_reflections,
        score_context=score_context,
    )

    logger.info(
        f"Teaser generated for {company_name}: "
        f"score={score}, "
        f"reflections={len(user_reflections)}, "
        f"benchmarks={len(industry_benchmarks)}, "
        f"opportunity_areas={len(opportunity_areas)}, "
        f"quick_win={quick_win['title']}"
    )

    return {
        # Metadata
        "generated_at": datetime.utcnow().isoformat(),
        "company_name": company_name,
        "industry": industry_display,
        "industry_slug": industry,

        # Personalized insight (LLM-generated warmth)
        "personalized_insight": personalized_insight,

        # NEW: Quick Win - free actionable value
        "quick_win": quick_win,

        # Section 1: AI Readiness Score (diagnostic) with context
        "ai_readiness": {
            "score": score,
            "breakdown": score_data["breakdown"],
            "interpretation": _get_score_interpretation(score),
            "score_context": score_context,
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
        "ai_readiness_score": score,
        "score_breakdown": score_data["breakdown"],
        "score_interpretation": _get_score_interpretation(score),
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
