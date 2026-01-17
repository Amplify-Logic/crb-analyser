"""
Insight Extraction Skill

Extracts structured insights from raw content (transcripts, articles, reports)
using AI to identify trends, frameworks, case studies, statistics, and quotes.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

from src.models.insight import (
    AudienceRelevance,
    CredibilityLevel,
    ExtractedInsights,
    Insight,
    InsightSource,
    InsightTags,
    InsightType,
    SURFACE_RELEVANCE_RULES,
    SupportingData,
    UseIn,
    UserStage,
)
from src.skills.base import LLMSkill, SkillContext, SkillError

logger = logging.getLogger(__name__)


class ExtractionInput(BaseModel):
    """Input for insight extraction."""
    raw_content: str = Field(..., description="The raw content to extract from")
    source_title: str = Field(..., description="Title of the source")
    source_author: Optional[str] = None
    source_url: Optional[str] = None
    source_date: Optional[str] = None
    source_type: str = Field(default="article", description="youtube, article, report, etc.")


class InsightExtractionSkill(LLMSkill[ExtractedInsights]):
    """
    Extracts structured insights from raw content.

    Takes unstructured content (transcripts, articles) and uses AI to identify:
    - Trends with supporting data
    - Actionable frameworks
    - Case studies with outcomes
    - Statistics with sources
    - Quotable insights
    - Predictions
    """

    name = "insight-extraction"
    description = "Extract structured insights from raw content"
    version = "1.0.0"

    default_model = "claude-sonnet-4-5-20250929"  # Claude Sonnet 4.5
    default_max_tokens = 8000

    EXTRACTION_SYSTEM_PROMPT = """You are an expert at extracting valuable insights for a SPECIFIC audience.

## TARGET AUDIENCE (Critical - filter everything through this lens)

SMB owner-operators of service businesses ($500K-$20M revenue):
- Dentists, lawyers, plumbers, coaches, recruiters, home services
- Their PAIN: Admin work eats time they'd rather spend on their craft
- Their QUESTION: "How can AI save me time/money so I can focus on what I love?"
- They are NOT: Tech companies, AI researchers, enterprise, or policy makers

## WHAT THEY CARE ABOUT
- Specific time/money savings ("save 10 hrs/week on scheduling")
- Real business outcomes ("reduced no-shows by 40%")
- Practical implementation ("works with existing tools")
- Risk and complexity ("can my team actually use this?")

## WHAT THEY DO NOT CARE ABOUT
- AGI timelines, superintelligence, AI existential risk
- Geopolitics of AI, chip wars, US-China dynamics
- Technical AI architecture, model training, alignment research
- Theoretical capabilities, benchmark scores, parameter counts
- What might happen in 5+ years

## AUDIENCE RELEVANCE SCORING (Required for every insight)

HIGH: Directly answers "How do I save time/money with AI?"
- Specific ROI examples, implementation success stories
- Practical frameworks they can apply this week
- Stats about productivity gains in service businesses
- Use for: landing page, quiz results, reports, emails

MEDIUM: Useful context but not directly actionable
- General AI adoption trends that affect their decisions
- Market shifts they should be aware of
- Use for: reports only (provides context)

LOW: Does not help their business decision - DO NOT EXTRACT
- AGI/superintelligence speculation
- AI safety research, alignment problems
- Geopolitical implications
- Technical deep-dives on model architecture
- Predictions about things 5+ years away

## EXTRACTION RULES

1. FILTER FIRST: If content is not relevant to SMB service businesses, skip it entirely
2. REFRAME: Translate technical insights into business language
3. SO WHAT: Every insight must answer "So what should this dentist/plumber/coach DO?"
4. BE RUTHLESS: Better to extract 3 highly relevant insights than 10 marginally relevant ones

## CREDIBILITY LEVELS
- peer_reviewed: Academic journals with peer review
- academic: Academic institutions, not peer-reviewed
- industry_research: McKinsey, Gartner, Forrester
- industry_data: Real platform data (surveys, benchmarks)
- analyst: Expert opinion with track record
- anecdotal: Personal experience, unverified

Output valid JSON matching the exact schema provided."""

    EXTRACTION_PROMPT = """Analyze this content for insights relevant to SMB service business owners.

SOURCE METADATA:
- Title: {source_title}
- Author: {source_author}
- Date: {source_date}
- Type: {source_type}
- URL: {source_url}

CONTENT:
{raw_content}

---

Remember: Our audience is dentists, lawyers, plumbers, coaches - NOT tech companies or AI researchers.
Only extract insights that help them decide "Should I use AI? How? What will it save me?"

Extract insights and return as JSON with this structure:
{{
  "insights": [
    {{
      "id": "unique-slug-for-this-insight",
      "type": "trend|framework|case_study|statistic|quote|prediction",
      "title": "Short descriptive title",
      "content": "The main insight content - clear and complete",
      "supporting_data": [
        {{
          "claim": "Specific data point or claim",
          "source": "Source name",
          "source_url": "URL if available",
          "date": "YYYY-MM or YYYY",
          "credibility": "peer_reviewed|academic|industry_research|industry_data|analyst|anecdotal"
        }}
      ],
      "actionable_insight": "What should a dentist/plumber/coach DO with this? (required for HIGH relevance)",
      "audience_relevance": "high|medium|low",
      "relevance_reason": "Why this relevance level - be specific",
      "tags": {{
        "topics": ["relevant", "topic", "tags"],
        "industries": ["all"] or ["dental", "home-services", "professional-services", etc.],
        "use_in": ["report", "quiz_results", "landing", "email"],
        "user_stages": ["considering", "early_adopter", "scaling"]
      }}
    }}
  ],
  "extraction_notes": "Content relevance assessment and any caveats",
  "skipped_topics": ["List topics in content that were skipped as not relevant to SMB audience"]
}}

RELEVANCE-BASED EXTRACTION RULES:
- HIGH relevance: Extract and include actionable_insight (required)
- MEDIUM relevance: Extract only if provides useful business context
- LOW relevance: DO NOT EXTRACT - skip entirely and note in skipped_topics

USE_IN RULES (based on audience_relevance):
- "landing": Only if HIGH relevance
- "quiz_results": Only if HIGH relevance
- "report": HIGH or MEDIUM relevance
- "email": Only if HIGH relevance

Guidelines:
- Generate unique, descriptive IDs like "stat-ai-scheduling-40pct-savings"
- For case_study: must have specific business outcomes (%, hours, $)
- For statistic: must be relevant to SMB operations, not AI research
- For quote: must resonate with business owners, not technologists
- For framework: must be implementable by a small business this quarter
- For trend: must affect how SMBs should think about AI adoption
- For prediction: max 2-3 years out, must be actionable

Quality over quantity. Extract 3-8 highly relevant insights, not 15 marginal ones."""

    async def execute(self, context: SkillContext) -> ExtractedInsights:
        """
        Extract insights from raw content.

        Args:
            context: Must contain metadata.extraction_input with ExtractionInput data

        Returns:
            ExtractedInsights with list of extracted insights
        """
        # Get extraction input from context
        extraction_data = context.metadata.get("extraction_input")
        if not extraction_data:
            raise SkillError(
                self.name,
                "Missing extraction_input in context.metadata",
                recoverable=False
            )

        # Parse input
        if isinstance(extraction_data, dict):
            extraction_input = ExtractionInput(**extraction_data)
        else:
            extraction_input = extraction_data

        # Build the prompt
        prompt = self.EXTRACTION_PROMPT.format(
            source_title=extraction_input.source_title,
            source_author=extraction_input.source_author or "Unknown",
            source_date=extraction_input.source_date or "Unknown",
            source_type=extraction_input.source_type,
            source_url=extraction_input.source_url or "N/A",
            raw_content=extraction_input.raw_content,
        )

        # Call LLM
        response = await self.call_llm_json(
            prompt=prompt,
            system=self.EXTRACTION_SYSTEM_PROMPT,
        )

        # Parse response into structured insights
        source = InsightSource(
            title=extraction_input.source_title,
            author=extraction_input.source_author,
            url=extraction_input.source_url,
            date=extraction_input.source_date,
            type=extraction_input.source_type,
        )

        insights = []
        skipped_low_relevance = 0
        for raw_insight in response.get("insights", []):
            try:
                insight = self._parse_insight(raw_insight, source)
                if insight is not None:
                    insights.append(insight)
                else:
                    skipped_low_relevance += 1
            except Exception as e:
                logger.warning(f"Failed to parse insight: {e}")
                continue

        if skipped_low_relevance > 0:
            logger.info(f"Skipped {skipped_low_relevance} LOW relevance insights")

        # Add skipped topics to extraction notes
        skipped_topics = response.get("skipped_topics", [])
        extraction_notes = response.get("extraction_notes", "")
        if skipped_topics:
            extraction_notes += f"\n\nSkipped topics (not relevant to SMB audience): {', '.join(skipped_topics)}"

        return ExtractedInsights(
            source=source,
            extracted_at=datetime.now().strftime("%Y-%m-%d"),
            insights=insights,
            extraction_notes=extraction_notes.strip() if extraction_notes else None,
        )

    def _parse_insight(self, raw: Dict[str, Any], source: InsightSource) -> Optional[Insight]:
        """Parse a raw insight dict into an Insight model.

        Returns None if insight is LOW relevance (should not be stored).
        """
        # Parse audience relevance - skip LOW relevance insights entirely
        relevance_str = raw.get("audience_relevance", "medium").lower()
        try:
            audience_relevance = AudienceRelevance(relevance_str)
        except ValueError:
            audience_relevance = AudienceRelevance.MEDIUM

        # Skip LOW relevance insights - they shouldn't be in our system
        if audience_relevance == AudienceRelevance.LOW:
            logger.info(f"Skipping LOW relevance insight: {raw.get('title', 'Unknown')}")
            return None

        # Parse supporting data
        supporting_data = []
        for sd in raw.get("supporting_data", []):
            supporting_data.append(SupportingData(
                claim=sd.get("claim", ""),
                source=sd.get("source", "Unknown"),
                source_url=sd.get("source_url"),
                date=sd.get("date"),
                credibility=CredibilityLevel(sd.get("credibility", "anecdotal")),
            ))

        # Parse tags and filter use_in based on audience relevance
        raw_tags = raw.get("tags", {})
        raw_use_in = raw_tags.get("use_in", [])

        # Filter use_in to only include surfaces appropriate for this relevance level
        filtered_use_in = []
        for surface in raw_use_in:
            try:
                use_in_enum = UseIn(surface)
                allowed_relevances = SURFACE_RELEVANCE_RULES.get(surface, [])
                if audience_relevance in allowed_relevances:
                    filtered_use_in.append(use_in_enum)
                else:
                    logger.debug(
                        f"Filtered out '{surface}' for insight '{raw.get('id')}' "
                        f"(relevance={audience_relevance.value}, allowed={[r.value for r in allowed_relevances]})"
                    )
            except ValueError:
                continue

        # If HIGH relevance but no use_in specified, default to all surfaces
        if audience_relevance == AudienceRelevance.HIGH and not filtered_use_in:
            filtered_use_in = [UseIn.REPORT, UseIn.QUIZ_RESULTS, UseIn.LANDING]

        # If MEDIUM relevance but no use_in, default to report only
        if audience_relevance == AudienceRelevance.MEDIUM and not filtered_use_in:
            filtered_use_in = [UseIn.REPORT]

        tags = InsightTags(
            topics=raw_tags.get("topics", []),
            industries=raw_tags.get("industries", ["all"]),
            use_in=filtered_use_in,
            user_stages=[UserStage(s) for s in raw_tags.get("user_stages", []) if s in UserStage.__members__.values()],
        )

        return Insight(
            id=raw.get("id", f"insight-{datetime.now().timestamp()}"),
            type=InsightType(raw.get("type", "trend")),
            title=raw.get("title", "Untitled"),
            content=raw.get("content", ""),
            supporting_data=supporting_data,
            actionable_insight=raw.get("actionable_insight"),
            tags=tags,
            source=source,
            audience_relevance=audience_relevance,
            relevance_reason=raw.get("relevance_reason"),
            reviewed=False,  # Always starts as unreviewed
        )


async def extract_insights_from_content(
    client: Any,
    raw_content: str,
    source_title: str,
    source_author: Optional[str] = None,
    source_url: Optional[str] = None,
    source_date: Optional[str] = None,
    source_type: str = "article",
) -> ExtractedInsights:
    """
    Convenience function to extract insights from content.

    Args:
        client: Anthropic client
        raw_content: The content to extract from
        source_title: Title of the source
        source_author: Author name
        source_url: URL to source
        source_date: Publication date
        source_type: Type (youtube, article, report, etc.)

    Returns:
        ExtractedInsights with all extracted insights
    """
    skill = InsightExtractionSkill(client=client)

    context = SkillContext(
        industry="general",
        metadata={
            "extraction_input": {
                "raw_content": raw_content,
                "source_title": source_title,
                "source_author": source_author,
                "source_url": source_url,
                "source_date": source_date,
                "source_type": source_type,
            }
        }
    )

    result = await skill.run(context)

    if not result.success:
        raise SkillError(
            "insight-extraction",
            f"Extraction failed: {result.warnings}",
            recoverable=True
        )

    return result.data
