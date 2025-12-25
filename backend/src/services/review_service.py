"""
Review Service

Multi-model review and agentic refinement service for CRB reports.
Pattern: Generate (fast) -> Review (smart) -> Research & Refine (smart with tools)

This service ensures:
- Quote accuracy against interview transcripts
- Calculation verification
- Grounding in first-party knowledge base data
- Scientific rigor in all claims
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from anthropic import Anthropic

from src.config.settings import settings
from src.config.model_routing import CLAUDE_MODELS, get_model_for_task
from src.knowledge import (
    get_benchmarks_for_metrics,
    search_vendors,
    get_industry_context,
    normalize_industry,
)
from src.expertise import get_self_improve_service, get_expertise_store

logger = logging.getLogger(__name__)


# =============================================================================
# PROMPTS
# =============================================================================

REVIEW_SYSTEM_PROMPT = """You are a senior analyst reviewing CRB reports for accuracy and completeness.

Your job is to verify:
1. Every quote matches the actual interview transcript
2. Every calculation is mathematically correct
3. Every claim has a verifiable source
4. No valuable interview insights were missed

Be rigorous. Clients pay for accurate, grounded analysis."""


REVIEW_FINDINGS_PROMPT = """Review these CRB findings against the original data sources.

GENERATED FINDINGS:
{findings}

═══════════════════════════════════════════════════════════════════════════════
ORIGINAL SOURCES - VERIFY ALL QUOTES AGAINST THESE
═══════════════════════════════════════════════════════════════════════════════

QUIZ DATA:
{quiz}

INTERVIEW TRANSCRIPT (FULL - check every quote here):
{interview_transcript}

RESEARCH DATA:
{research}

═══════════════════════════════════════════════════════════════════════════════
VERIFICATION CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

1. QUOTE ACCURACY
   - Is every interview quote an EXACT or near-exact match from the transcript?
   - Check word-for-word, including punctuation

2. CALCULATION ACCURACY
   - Verify: formula × inputs = stated result
   - Flag any math errors

3. UNUSED INSIGHTS
   - What valuable quotes from the interview were NOT used?
   - What quiz data was ignored?
   - Prioritize by potential value (HIGH/MEDIUM/LOW)

4. SOURCE CITATIONS
   - Does every finding cite real data from quiz/interview?
   - Flag any generic claims without specific sources

Return JSON:
{{
  "quote_verification": [
    {{"finding_id": "F01", "quoted": "...", "actual_from_transcript": "...", "status": "EXACT|CLOSE|MISSING|WRONG"}}
  ],
  "calculation_errors": [
    {{"finding_id": "F01", "formula": "...", "inputs": {{}}, "expected": 0, "got": 0, "status": "CORRECT|ERROR"}}
  ],
  "unused_insights": [
    {{"source": "interview|quiz", "quote_or_data": "...", "potential_finding": "...", "estimated_value": "€X", "priority": "HIGH|MEDIUM|LOW"}}
  ],
  "quality_scores": {{
    "quote_accuracy": 0,
    "calculation_accuracy": 0,
    "interview_coverage": 0,
    "source_grounding": 0,
    "overall": 0
  }},
  "critical_issues": ["List of must-fix issues"],
  "finding_count": {{
    "current": 0,
    "recommended": 0,
    "not_recommended": 0
  }}
}}"""


REFINE_SYSTEM_PROMPT = """You are a senior analyst refining a CRB report based on review feedback.

You have access to:
1. The company's proprietary knowledge base (industry benchmarks, vendor pricing)
2. Past learnings from similar analyses (expertise store)
3. Tools to verify and research

Your refinement must:
- PRESERVE all original findings (never drop findings)
- FIX all errors identified in the review
- ADD new findings from unused insights
- GROUND all claims in verifiable data
- ENSURE mathematical accuracy

Scientific rigor is non-negotiable."""


REFINE_PROMPT = """Refine this CRB report based on review feedback.

ORIGINAL FINDINGS:
{original}

REVIEW FEEDBACK:
{review}

═══════════════════════════════════════════════════════════════════════════════
KNOWLEDGE BASE DATA (Your proprietary first-party data - USE THIS FIRST)
═══════════════════════════════════════════════════════════════════════════════

INDUSTRY BENCHMARKS:
{benchmarks}

VENDOR PRICING:
{vendors}

EXPERTISE (Learnings from past analyses):
{expertise}

═══════════════════════════════════════════════════════════════════════════════
ORIGINAL SOURCES
═══════════════════════════════════════════════════════════════════════════════

INTERVIEW TRANSCRIPT:
{interview}

QUIZ DATA:
{quiz}

═══════════════════════════════════════════════════════════════════════════════
REFINEMENT REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════

1. PRESERVE ALL ORIGINAL FINDINGS
   - Every finding from the original must appear in your output
   - You may improve them, but never remove them

2. FIX ALL ERRORS
   - Correct any calculation errors noted in review
   - Fix any misquoted interview text
   - Update any incorrect prices with knowledge base data

3. ADD NEW FINDINGS FROM UNUSED INSIGHTS
   - Create findings from high-priority unused_insights in review
   - Each new finding needs: title, calculation, sources, value
   - Target: 8-12 total findings (including 2-3 not-recommended)

4. GROUND ALL CLAIMS
   - Use knowledge base benchmarks (cite: "Source: CRB Knowledge Base, {industry}")
   - Use knowledge base vendor pricing (verified dates included)
   - If no KB data, mark confidence as LOW

5. SCIENTIFIC RIGOR
   - Every ROI: Formula + Inputs + Step-by-step calculation + Result
   - Every benchmark: Source name + Year + Specific metric
   - No generic claims like "industry average" without specifics

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════════════════════

Return complete JSON:
{{
  "findings": [
    {{
      "id": "F01",
      "title": "...",
      "category": "efficiency|growth|risk",
      "confidence": "high|medium|low",
      "sources": {{
        "quiz": "Specific quiz data used",
        "interview": "EXACT quote from transcript",
        "benchmark": "Source: CRB Knowledge Base, [industry] - [specific metric]"
      }},
      "calculation": {{
        "formula": "A × B × C",
        "inputs": {{"A": 10, "B": 50, "C": 12}},
        "step_by_step": "10 × 50 = 500, 500 × 12 = 6000",
        "result": "€6,000"
      }},
      "value": {{"saves": 0, "creates": 0}},
      "recommendation": {{
        "action": "...",
        "vendor": "...",
        "price": "€X/mo (Source: CRB Vendor DB, verified [date])",
        "fits_budget": true
      }},
      "is_not_recommended": false
    }}
  ],
  "executive_summary_updates": {{
    "total_value_potential": {{"min": 0, "max": 0}},
    "headline": "Updated if needed"
  }},
  "refinement_log": {{
    "errors_fixed": ["..."],
    "findings_added": ["..."],
    "sources_grounded": ["..."]
  }}
}}"""


# =============================================================================
# REVIEW SERVICE CLASS
# =============================================================================

class ReviewService:
    """
    Multi-model review and agentic refinement service.

    Ensures report quality through:
    - Quote verification against transcripts
    - Calculation accuracy checking
    - Knowledge base grounding
    - Unused insight capture
    """

    def __init__(self, tier: str = "quick"):
        self.tier = tier
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.expertise_store = get_expertise_store()
        self.self_improve_service = get_self_improve_service()

    async def review_and_refine(
        self,
        content: Dict[str, Any],
        content_type: str,
        original_sources: Dict[str, Any],
        industry: str = "general",
    ) -> Dict[str, Any]:
        """
        Review generated content and refine with research.

        Args:
            content: Generated content (e.g., {"findings": [...]})
            content_type: Type of content ("findings", "executive_summary", "recommendations")
            original_sources: {"quiz": {...}, "interview": {...}, "research": {...}}
            industry: Industry for knowledge base lookups

        Returns:
            {
                "content": <refined content>,
                "review_scores": {...},
                "corrections_applied": int,
                "findings_added": int,
            }
        """
        logger.info(f"Starting review for {content_type}")

        # Step 1: Review the content
        review = await self._review(content, content_type, original_sources)

        # Step 2: Load knowledge base data for grounding
        kb_data = await self._load_knowledge_base(industry, original_sources)

        # Step 3: Refine with research
        refined = await self._refine(content, review, original_sources, kb_data)

        # Step 4: Update expertise store with learnings
        await self._update_expertise(industry, content, refined, review)

        return {
            "content": refined.get("findings", content.get("findings", [])),
            "review_scores": review.get("quality_scores", {}),
            "corrections_applied": len(review.get("critical_issues", [])),
            "findings_added": len(refined.get("refinement_log", {}).get("findings_added", [])),
            "executive_summary_updates": refined.get("executive_summary_updates", {}),
        }

    async def _review(
        self,
        content: Dict[str, Any],
        content_type: str,
        original_sources: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Review content against original sources."""

        # Format interview transcript
        interview = original_sources.get("interview", {})
        transcript = interview.get("transcript", [])
        transcript_text = self._format_transcript(transcript)

        if content_type == "findings":
            prompt = REVIEW_FINDINGS_PROMPT.format(
                findings=json.dumps(content.get("findings", []), indent=2),
                quiz=json.dumps(original_sources.get("quiz", {}), indent=2),
                interview_transcript=transcript_text,
                research=json.dumps(original_sources.get("research", {}), indent=2),
            )
        else:
            # Generic review for other content types
            prompt = f"Review this {content_type}:\n{json.dumps(content, indent=2)}"

        try:
            response = self.client.messages.create(
                model=CLAUDE_MODELS["opus"],
                max_tokens=6000,
                system=REVIEW_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            review_text = response.content[0].text
            review = self._parse_json(review_text)

            if not review:
                logger.warning("Failed to parse review JSON, using defaults")
                review = {
                    "quality_scores": {"overall": 5},
                    "critical_issues": [],
                    "unused_insights": [],
                }

            # Log quality scores
            scores = review.get("quality_scores", {})
            logger.info(
                f"Review complete - Quote: {scores.get('quote_accuracy', '?')}/10, "
                f"Calc: {scores.get('calculation_accuracy', '?')}/10, "
                f"Overall: {scores.get('overall', '?')}/10"
            )

            return review

        except Exception as e:
            logger.error(f"Review failed: {e}")
            return {
                "quality_scores": {"overall": 0},
                "critical_issues": [f"Review failed: {str(e)}"],
                "unused_insights": [],
            }

    async def _load_knowledge_base(
        self,
        industry: str,
        original_sources: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Load knowledge base data for grounding."""

        normalized_industry = normalize_industry(industry)

        # Get benchmarks
        benchmarks = get_benchmarks_for_metrics(normalized_industry)

        # Get vendor pricing for common categories
        categories = ["automation", "crm", "scheduling", "ai_assistants"]
        vendors = {}
        for category in categories:
            category_vendors = search_vendors(
                category=category,
                company_size=original_sources.get("quiz", {}).get("company_size", "11-50"),
            )
            if category_vendors:
                vendors[category] = category_vendors[:5]  # Top 5 per category

        # Get industry expertise (learnings from past analyses)
        expertise = {}
        try:
            expertise = self.expertise_store.get_all_expertise_context(normalized_industry)
        except Exception as e:
            logger.warning(f"Could not load expertise: {e}")

        return {
            "benchmarks": benchmarks,
            "vendors": vendors,
            "expertise": expertise,
        }

    async def _refine(
        self,
        content: Dict[str, Any],
        review: Dict[str, Any],
        original_sources: Dict[str, Any],
        kb_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Refine content using review feedback and knowledge base."""

        # Format interview transcript
        interview = original_sources.get("interview", {})
        transcript = interview.get("transcript", [])
        transcript_text = self._format_transcript(transcript)

        prompt = REFINE_PROMPT.format(
            original=json.dumps(content.get("findings", []), indent=2),
            review=json.dumps(review, indent=2),
            benchmarks=json.dumps(kb_data.get("benchmarks", {}), indent=2),
            vendors=json.dumps(kb_data.get("vendors", {}), indent=2),
            expertise=json.dumps(kb_data.get("expertise", {}), indent=2),
            interview=transcript_text,
            quiz=json.dumps(original_sources.get("quiz", {}), indent=2),
        )

        try:
            response = self.client.messages.create(
                model=CLAUDE_MODELS["opus"],
                max_tokens=12000,
                system=REFINE_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            refined_text = response.content[0].text
            refined = self._parse_json(refined_text)

            if not refined:
                logger.warning("Failed to parse refined JSON, returning original")
                return {"findings": content.get("findings", [])}

            # Validate finding count
            findings = refined.get("findings", [])
            logger.info(
                f"Refinement complete - "
                f"Findings: {len(findings)}, "
                f"Added: {len(refined.get('refinement_log', {}).get('findings_added', []))}"
            )

            return refined

        except Exception as e:
            logger.error(f"Refinement failed: {e}")
            return {"findings": content.get("findings", [])}

    async def _update_expertise(
        self,
        industry: str,
        original: Dict[str, Any],
        refined: Dict[str, Any],
        review: Dict[str, Any],
    ) -> None:
        """Log learnings from this review for future expertise updates."""
        try:
            # Extract patterns that worked
            findings = refined.get("findings", [])
            high_value_findings = [
                f for f in findings
                if (f.get("value", {}).get("saves", 0) + f.get("value", {}).get("creates", 0)) > 10000
            ]

            if high_value_findings:
                logger.info(
                    f"Review identified {len(high_value_findings)} high-value findings for {industry}: "
                    f"{[f.get('title') for f in high_value_findings[:3]]}"
                )

            # Log any critical issues for future avoidance
            critical_issues = review.get("critical_issues", [])
            if critical_issues:
                logger.info(f"Review identified {len(critical_issues)} issues to avoid: {critical_issues[:3]}")

            # Note: Full expertise learning happens in the main report flow via SelfImproveService
            # This method logs observations for debugging and future enhancement

        except Exception as e:
            logger.warning(f"Could not log expertise observations: {e}")

    def _format_transcript(self, transcript: List[Dict]) -> str:
        """Format transcript messages for prompt."""
        if not transcript:
            return "No interview transcript available."

        lines = []
        for msg in transcript:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")

        return "\n\n".join(lines)

    def _parse_json(self, text: str) -> Optional[Dict]:
        """Parse JSON from LLM response."""
        # Remove markdown code blocks
        if "```json" in text:
            match = re.search(r'```json\s*([\s\S]*?)```', text)
            if match:
                text = match.group(1)
        elif "```" in text:
            match = re.search(r'```\s*([\s\S]*?)```', text)
            if match:
                text = match.group(1)

        text = text.strip()

        # Remove trailing commas
        text = re.sub(r',\s*([}\]])', r'\1', text)

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            # Try to find JSON object
            try:
                match = re.search(r'\{[\s\S]*\}', text)
                if match:
                    return json.loads(match.group())
            except:
                pass
            return None


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def get_review_service(tier: str = "quick") -> ReviewService:
    """Get a ReviewService instance."""
    return ReviewService(tier=tier)
