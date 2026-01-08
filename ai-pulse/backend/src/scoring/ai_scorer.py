"""
AI-Enhanced Scoring

Uses Gemini Flash for cheap scoring and Claude for summaries.
"""

import logging
import json
from typing import List, Optional

import httpx

from src.config.settings import settings
from src.scoring.rules import ScoredArticle

logger = logging.getLogger(__name__)


class AIScorer:
    """AI-enhanced content scorer."""

    def __init__(self):
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.anthropic_url = "https://api.anthropic.com/v1/messages"

    async def refine_scores(
        self,
        articles: List[ScoredArticle],
        top_n: int = 50,
    ) -> List[ScoredArticle]:
        """
        Refine scores using Gemini Flash.

        Takes top N articles from rule-based scoring and
        re-scores them using AI for better relevance.
        """
        if not settings.GOOGLE_API_KEY:
            logger.warning("Google API key not configured, skipping AI scoring")
            return articles

        # Only process top articles
        to_score = articles[:top_n]

        try:
            prompt = self._build_scoring_prompt(to_score)

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.gemini_url}?key={settings.GOOGLE_API_KEY}",
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.1,
                            "maxOutputTokens": 2000,
                        }
                    }
                )
                response.raise_for_status()

            result = response.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"]

            # Parse scores from response
            ai_scores = self._parse_scores(text, len(to_score))

            # Update scores
            for i, scored_article in enumerate(to_score):
                if i < len(ai_scores):
                    # Blend AI score with rule score
                    ai_score = ai_scores[i]
                    scored_article.final_score = (
                        scored_article.final_score * 0.4 +
                        ai_score * 0.6
                    )

            # Re-sort by final score
            articles.sort(key=lambda x: x.final_score, reverse=True)
            return articles

        except Exception as e:
            logger.error(f"AI scoring failed: {e}")
            return articles

    async def generate_summaries(
        self,
        articles: List[ScoredArticle],
        top_n: int = 10,
    ) -> dict[str, str]:
        """
        Generate summaries for top articles using Claude Haiku.

        Returns dict of article_id -> summary.
        """
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("Anthropic API key not configured, skipping summaries")
            return {}

        to_summarize = articles[:top_n]

        try:
            prompt = self._build_summary_prompt(to_summarize)

            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    self.anthropic_url,
                    headers={
                        "x-api-key": settings.ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": settings.SUMMARY_MODEL,
                        "max_tokens": 2000,
                        "messages": [{"role": "user", "content": prompt}],
                    }
                )
                response.raise_for_status()

            result = response.json()
            text = result["content"][0]["text"]

            # Parse summaries
            return self._parse_summaries(text, to_summarize)

        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return {}

    def _build_scoring_prompt(self, articles: List[ScoredArticle]) -> str:
        """Build prompt for AI scoring."""
        items = []
        for i, scored in enumerate(articles):
            article = scored.article
            items.append(f"{i+1}. {article.title}")
            if article.description:
                items.append(f"   {article.description[:200]}")

        items_text = "\n".join(items)

        return f"""Rate these AI news articles for relevance and importance to AI practitioners (developers, researchers, business leaders).

Score each from 0.0 to 1.0 where:
- 1.0 = Major breakthrough, new model release, critical industry news
- 0.7-0.9 = Important update, useful tool release, significant research
- 0.4-0.6 = Interesting but not essential, tutorials, opinion pieces
- 0.1-0.3 = Low relevance, promotional, off-topic

Articles:
{items_text}

Respond with ONLY a JSON array of scores in order, like: [0.8, 0.6, 0.9, ...]"""

    def _build_summary_prompt(self, articles: List[ScoredArticle]) -> str:
        """Build prompt for summary generation."""
        items = []
        for i, scored in enumerate(articles):
            article = scored.article
            items.append(f"[{i+1}] Title: {article.title}")
            items.append(f"URL: {article.url}")
            if article.description:
                items.append(f"Description: {article.description[:300]}")
            items.append("")

        items_text = "\n".join(items)

        return f"""Write a 2-3 sentence summary for each of these AI news items. Focus on what's new and why it matters.

Articles:
{items_text}

Format your response as:
[1] Summary here...
[2] Summary here...
etc."""

    def _parse_scores(self, text: str, expected_count: int) -> List[float]:
        """Parse AI scores from response."""
        try:
            # Try to extract JSON array
            import re
            match = re.search(r'\[[\d.,\s]+\]', text)
            if match:
                scores = json.loads(match.group())
                return [float(s) for s in scores]
        except Exception as e:
            logger.warning(f"Failed to parse AI scores: {e}")

        # Return default scores
        return [0.5] * expected_count

    def _parse_summaries(
        self,
        text: str,
        articles: List[ScoredArticle],
    ) -> dict[str, str]:
        """Parse summaries from response."""
        summaries = {}

        import re
        pattern = r'\[(\d+)\]\s*(.+?)(?=\[\d+\]|$)'
        matches = re.findall(pattern, text, re.DOTALL)

        for idx_str, summary in matches:
            try:
                idx = int(idx_str) - 1
                if 0 <= idx < len(articles):
                    article_id = articles[idx].article.external_id
                    summaries[article_id] = summary.strip()
            except (ValueError, IndexError):
                continue

        return summaries
