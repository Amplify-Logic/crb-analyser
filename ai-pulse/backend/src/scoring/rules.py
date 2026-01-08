"""
Rule-Based Scoring

Fast, free scoring using keyword matching and engagement metrics.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from src.scrapers.base import ScrapedArticle
from src.config.sources import Source

logger = logging.getLogger(__name__)


# High-signal keywords (boost score)
HIGH_SIGNAL_KEYWORDS = [
    # Model releases
    "gpt-5", "gpt5", "claude 4", "claude-4", "gemini 3", "gemini-3",
    "llama 4", "opus", "sonnet", "o3", "o4",
    # Companies
    "openai", "anthropic", "deepmind", "google ai", "meta ai", "xai",
    "mistral", "cohere", "together ai",
    # Concepts
    "agi", "artificial general intelligence", "reasoning", "agents",
    "agentic", "multimodal", "breakthrough", "state of the art", "sota",
    # News indicators
    "just released", "breaking", "launches", "announces", "unveiled",
    "introduces", "new model", "major update",
    # Tools
    "langchain", "langgraph", "crewai", "autogen", "cursor", "copilot",
    "windsurf", "claude code", "devin",
]

# Low-value patterns (reduce score)
LOW_VALUE_PATTERNS = [
    r"\bgaming\b", r"\bgame\b", r"\bcrypto\b", r"\bnft\b", r"\bweb3\b",
    r"\bsponsored\b", r"\b#ad\b", r"\breaction\b", r"\bdrama\b",
    r"\bcontroversy\b", r"\bscam\b", r"\bhype\b",
]


@dataclass
class ScoredArticle:
    """Article with scores."""
    article: ScrapedArticle
    source: Source
    novelty_score: float  # 0-1, how recent
    impact_score: float   # 0-1, engagement + keywords
    relevance_score: float  # 0-1, source priority
    final_score: float    # Combined score
    is_filtered: bool     # Should be excluded


class RuleScorer:
    """Rule-based content scorer."""

    def __init__(self):
        self.high_signal_pattern = re.compile(
            "|".join(re.escape(k) for k in HIGH_SIGNAL_KEYWORDS),
            re.IGNORECASE
        )
        self.low_value_patterns = [
            re.compile(p, re.IGNORECASE) for p in LOW_VALUE_PATTERNS
        ]

    def score_articles(
        self,
        articles: List[tuple[ScrapedArticle, Source]],
    ) -> List[ScoredArticle]:
        """Score a list of articles."""
        scored = []

        for article, source in articles:
            scored_article = self._score_article(article, source)
            scored.append(scored_article)

        # Sort by final score descending
        scored.sort(key=lambda x: x.final_score, reverse=True)

        return scored

    def _score_article(
        self,
        article: ScrapedArticle,
        source: Source,
    ) -> ScoredArticle:
        """Score a single article."""
        # Check if should be filtered
        is_filtered = self._should_filter(article)

        if is_filtered:
            return ScoredArticle(
                article=article,
                source=source,
                novelty_score=0,
                impact_score=0,
                relevance_score=0,
                final_score=0,
                is_filtered=True,
            )

        # Calculate component scores
        novelty_score = self._calculate_novelty(article.published_at)
        impact_score = self._calculate_impact(article)
        relevance_score = self._calculate_relevance(source)

        # Combine scores
        final_score = (
            novelty_score * 0.3 +
            impact_score * 0.3 +
            relevance_score * 0.4
        )

        return ScoredArticle(
            article=article,
            source=source,
            novelty_score=novelty_score,
            impact_score=impact_score,
            relevance_score=relevance_score,
            final_score=final_score,
            is_filtered=False,
        )

    def _should_filter(self, article: ScrapedArticle) -> bool:
        """Check if article should be filtered out."""
        text = f"{article.title} {article.description or ''}"

        # Check low-value patterns
        for pattern in self.low_value_patterns:
            if pattern.search(text):
                return True

        # Filter very short videos (< 60 seconds)
        if article.duration_seconds and article.duration_seconds < 60:
            return True

        return False

    def _calculate_novelty(self, published_at: datetime) -> float:
        """Calculate novelty score based on age."""
        now = datetime.utcnow()
        age = now - published_at

        if age < timedelta(hours=1):
            return 1.0
        elif age < timedelta(hours=4):
            return 0.95
        elif age < timedelta(hours=12):
            return 0.85
        elif age < timedelta(hours=24):
            return 0.7
        elif age < timedelta(hours=48):
            return 0.5
        elif age < timedelta(days=7):
            return 0.3
        else:
            return 0.1

    def _calculate_impact(self, article: ScrapedArticle) -> float:
        """Calculate impact score based on engagement and keywords."""
        score = 0.0

        # Views boost
        if article.views:
            if article.views >= 100000:
                score += 0.3
            elif article.views >= 50000:
                score += 0.2
            elif article.views >= 10000:
                score += 0.1
            elif article.views >= 1000:
                score += 0.05

        # Likes boost
        if article.likes:
            if article.likes >= 5000:
                score += 0.15
            elif article.likes >= 1000:
                score += 0.1
            elif article.likes >= 100:
                score += 0.05

        # Comments boost (indicates discussion)
        if article.comments:
            if article.comments >= 500:
                score += 0.1
            elif article.comments >= 100:
                score += 0.05

        # Keyword boost
        text = f"{article.title} {article.description or ''}"
        matches = self.high_signal_pattern.findall(text)
        keyword_boost = min(len(matches) * 0.05, 0.3)
        score += keyword_boost

        return min(score, 1.0)

    def _calculate_relevance(self, source: Source) -> float:
        """Calculate relevance score based on source priority."""
        # Priority is 1-10, normalize to 0-1
        return source.priority / 10.0

    def get_top_articles(
        self,
        scored: List[ScoredArticle],
        limit: int = 50,
        min_score: float = 0.0,
    ) -> List[ScoredArticle]:
        """Get top articles above threshold."""
        filtered = [
            s for s in scored
            if not s.is_filtered and s.final_score >= min_score
        ]
        return filtered[:limit]
