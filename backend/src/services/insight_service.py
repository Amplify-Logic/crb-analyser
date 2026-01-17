"""
Insight Service

Handles storage, retrieval, and management of curated insights.
Provides tag-based filtering and semantic search capabilities.
"""

import json
import logging
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.models.insight import (
    AudienceRelevance,
    CredibilityLevel,
    ExtractedInsights,
    Insight,
    InsightCollection,
    InsightSearchQuery,
    InsightSearchResult,
    InsightType,
    SURFACE_RELEVANCE_RULES,
    UseIn,
)

logger = logging.getLogger(__name__)

# Paths
INSIGHTS_BASE_PATH = Path(__file__).parent.parent / "knowledge" / "insights"
CURATED_PATH = INSIGHTS_BASE_PATH / "curated"
RAW_PATH = INSIGHTS_BASE_PATH / "raw"
EMBEDDINGS_PATH = INSIGHTS_BASE_PATH / "embeddings"

# Type to file mapping
TYPE_FILES = {
    InsightType.TREND: "trends.json",
    InsightType.FRAMEWORK: "frameworks.json",
    InsightType.CASE_STUDY: "case_studies.json",
    InsightType.STATISTIC: "statistics.json",
    InsightType.QUOTE: "quotes.json",
    InsightType.PREDICTION: "predictions.json",
}


class InsightService:
    """
    Service for managing curated insights.

    Provides:
    - CRUD operations for insights
    - Tag-based filtering
    - Semantic search (when embeddings available)
    - Retrieval for specific surfaces (report, quiz, landing)
    """

    def __init__(self):
        self._cache: Dict[InsightType, InsightCollection] = {}
        self._cache_time: Optional[datetime] = None
        self._cache_ttl_seconds = 300  # 5 minute cache

    def _load_collection(self, insight_type: InsightType) -> InsightCollection:
        """Load a single insight collection from disk."""
        file_name = TYPE_FILES.get(insight_type)
        if not file_name:
            return InsightCollection(type=insight_type, description="", insights=[])

        file_path = CURATED_PATH / file_name

        if not file_path.exists():
            logger.warning(f"Insight file not found: {file_path}")
            return InsightCollection(type=insight_type, description="", insights=[])

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            # Parse insights
            insights = []
            for raw in data.get("insights", []):
                try:
                    insight = Insight(**raw)
                    insights.append(insight)
                except Exception as e:
                    logger.warning(f"Failed to parse insight: {e}")

            return InsightCollection(
                type=insight_type,
                description=data.get("description", ""),
                last_updated=data.get("last_updated", ""),
                insights=insights,
            )
        except Exception as e:
            logger.error(f"Failed to load insight collection {insight_type}: {e}")
            return InsightCollection(type=insight_type, description="", insights=[])

    def _save_collection(self, collection: InsightCollection) -> bool:
        """Save an insight collection to disk."""
        file_name = TYPE_FILES.get(collection.type)
        if not file_name:
            return False

        file_path = CURATED_PATH / file_name

        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dict for JSON serialization
            data = {
                "type": collection.type.value if isinstance(collection.type, InsightType) else collection.type,
                "description": collection.description,
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "insights": [
                    insight.model_dump(exclude={"embedding"})
                    for insight in collection.insights
                ],
            }

            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, default=str)

            # Clear entire cache to force full reload on next request
            # This ensures consistency when types are updated
            self._cache.clear()
            self._cache_time = None

            return True
        except Exception as e:
            logger.error(f"Failed to save insight collection: {e}")
            return False

    def _maybe_refresh_cache(self) -> None:
        """Refresh cache if expired."""
        if self._cache_time:
            elapsed = (datetime.now() - self._cache_time).total_seconds()
            if elapsed < self._cache_ttl_seconds:
                return

        # Reload all collections
        self._cache = {}
        for insight_type in InsightType:
            self._cache[insight_type] = self._load_collection(insight_type)
        self._cache_time = datetime.now()

    def get_all_insights(self, reviewed_only: bool = True) -> List[Insight]:
        """Get all insights across all types."""
        self._maybe_refresh_cache()

        insights = []
        for collection in self._cache.values():
            for insight in collection.insights:
                if reviewed_only and not insight.reviewed:
                    continue
                insights.append(insight)

        return insights

    def get_insights_by_type(
        self,
        insight_type: InsightType,
        reviewed_only: bool = True
    ) -> List[Insight]:
        """Get all insights of a specific type."""
        self._maybe_refresh_cache()

        collection = self._cache.get(insight_type)
        if not collection:
            return []

        if reviewed_only:
            return [i for i in collection.insights if i.reviewed]
        return collection.insights

    def get_insight_by_id(self, insight_id: str) -> Optional[Insight]:
        """Get a specific insight by ID."""
        self._maybe_refresh_cache()

        for collection in self._cache.values():
            for insight in collection.insights:
                if insight.id == insight_id:
                    return insight
        return None

    def search_insights(self, query: InsightSearchQuery) -> List[InsightSearchResult]:
        """
        Search insights with tag filtering and optional semantic matching.

        Args:
            query: Search parameters including filters and context

        Returns:
            List of matching insights with relevance scores
        """
        self._maybe_refresh_cache()

        results = []

        # Get base set of insights
        if query.types:
            candidates = []
            for t in query.types:
                candidates.extend(self.get_insights_by_type(t, query.reviewed_only))
        else:
            candidates = self.get_all_insights(query.reviewed_only)

        for insight in candidates:
            score = 1.0
            match_reasons = []

            # Filter by use_in
            if query.use_in:
                use_in_values = [u.value if isinstance(u, UseIn) else u for u in insight.tags.use_in]
                query_use_in = query.use_in.value if isinstance(query.use_in, UseIn) else query.use_in
                if query_use_in not in use_in_values:
                    continue
                match_reasons.append(f"use_in:{query_use_in}")

            # Filter by industries
            if query.industries:
                insight_industries = insight.tags.industries
                if "all" not in insight_industries:
                    if not any(ind in insight_industries for ind in query.industries):
                        continue
                match_reasons.append(f"industry match")

            # Filter by topics
            if query.topics:
                insight_topics = insight.tags.topics
                matching_topics = [t for t in query.topics if t in insight_topics]
                if not matching_topics:
                    # Partial match - reduce score
                    score *= 0.5
                else:
                    match_reasons.append(f"topics:{matching_topics}")

            # Filter by user stage
            if query.user_stage:
                user_stage_values = [s.value if hasattr(s, 'value') else s for s in insight.tags.user_stages]
                query_stage = query.user_stage.value if hasattr(query.user_stage, 'value') else query.user_stage
                if query_stage not in user_stage_values:
                    score *= 0.7  # Soft filter - reduce score but don't exclude

            # Semantic matching (basic keyword matching for now)
            if query.context_query:
                context_lower = query.context_query.lower()
                insight_text = f"{insight.title} {insight.content} {insight.actionable_insight or ''}".lower()

                # Simple keyword overlap scoring
                query_words = set(context_lower.split())
                insight_words = set(insight_text.split())
                overlap = len(query_words & insight_words)

                if overlap > 0:
                    semantic_score = min(overlap / len(query_words), 1.0)
                    score *= (0.5 + 0.5 * semantic_score)
                    match_reasons.append(f"semantic:{overlap} words")
                else:
                    score *= 0.3

            results.append(InsightSearchResult(
                insight=insight,
                relevance_score=score,
                match_reason=", ".join(match_reasons) if match_reasons else None,
            ))

        # Sort by relevance score
        results.sort(key=lambda r: r.relevance_score, reverse=True)

        # Apply limit
        if query.limit:
            results = results[:query.limit]

        return results

    def get_insights_for_surface(
        self,
        use_in: UseIn,
        industry: Optional[str] = None,
        topics: Optional[List[str]] = None,
        context: Optional[str] = None,
        limit: int = 5,
    ) -> List[Insight]:
        """
        Convenience method to get insights for a specific surface.

        Enforces audience relevance rules - only returns insights
        appropriate for the requested surface.

        Args:
            use_in: Where the insight will be displayed
            industry: User's industry (optional)
            topics: Relevant topics (optional)
            context: Natural language context for semantic matching
            limit: Max insights to return

        Returns:
            List of relevant insights (filtered by audience relevance)
        """
        query = InsightSearchQuery(
            use_in=use_in,
            industries=[industry] if industry else None,
            topics=topics,
            context_query=context,
            limit=limit * 2,  # Fetch extra in case some are filtered
        )

        results = self.search_insights(query)

        # Second-layer relevance filter (defense in depth)
        # This catches any insights that slipped through extraction
        surface_key = use_in.value if isinstance(use_in, UseIn) else use_in
        allowed_relevances = SURFACE_RELEVANCE_RULES.get(surface_key, [])

        filtered = []
        for result in results:
            insight = result.insight
            # Get relevance, defaulting to MEDIUM for legacy insights
            relevance = getattr(insight, 'audience_relevance', None)
            if relevance is None:
                relevance = AudienceRelevance.MEDIUM

            if isinstance(relevance, str):
                try:
                    relevance = AudienceRelevance(relevance)
                except ValueError:
                    relevance = AudienceRelevance.MEDIUM

            if relevance in allowed_relevances:
                filtered.append(insight)
            else:
                logger.debug(
                    f"Filtered insight '{insight.id}' from {surface_key}: "
                    f"relevance={relevance.value}, allowed={[r.value for r in allowed_relevances]}"
                )

        return filtered[:limit]

    def add_insight(self, insight: Insight) -> bool:
        """
        Add a new insight to the appropriate collection.

        Args:
            insight: The insight to add

        Returns:
            True if successful
        """
        self._maybe_refresh_cache()

        collection = self._cache.get(insight.type)
        if not collection:
            collection = InsightCollection(
                type=insight.type,
                description=f"{insight.type.value} insights",
                insights=[],
            )
            self._cache[insight.type] = collection

        # Check for duplicate ID
        existing_ids = {i.id for i in collection.insights}
        if insight.id in existing_ids:
            logger.warning(f"Insight with ID {insight.id} already exists")
            return False

        collection.insights.append(insight)
        return self._save_collection(collection)

    def add_insights_batch(self, insights: List[Insight]) -> Dict[str, int]:
        """
        Add multiple insights in batch.

        Args:
            insights: List of insights to add

        Returns:
            Dict with counts: {"added": N, "skipped": M}
        """
        added = 0
        skipped = 0

        # Group by type for efficient saving
        by_type: Dict[InsightType, List[Insight]] = {}
        for insight in insights:
            if insight.type not in by_type:
                by_type[insight.type] = []
            by_type[insight.type].append(insight)

        for insight_type, type_insights in by_type.items():
            collection = self._cache.get(insight_type) or self._load_collection(insight_type)
            existing_ids = {i.id for i in collection.insights}

            for insight in type_insights:
                if insight.id in existing_ids:
                    skipped += 1
                    continue

                collection.insights.append(insight)
                existing_ids.add(insight.id)
                added += 1

            self._save_collection(collection)
            self._cache[insight_type] = collection

        return {"added": added, "skipped": skipped}

    def update_insight(self, insight_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing insight.

        Args:
            insight_id: ID of insight to update
            updates: Dict of fields to update

        Returns:
            True if successful
        """
        self._maybe_refresh_cache()

        for collection in self._cache.values():
            for i, insight in enumerate(collection.insights):
                if insight.id == insight_id:
                    # Apply updates
                    updated_data = insight.model_dump()
                    updated_data.update(updates)

                    try:
                        updated_insight = Insight(**updated_data)
                        collection.insights[i] = updated_insight
                        return self._save_collection(collection)
                    except Exception as e:
                        logger.error(f"Failed to update insight: {e}")
                        return False

        return False

    def mark_reviewed(self, insight_id: str, reviewed: bool = True) -> bool:
        """Mark an insight as reviewed or unreviewed."""
        return self.update_insight(insight_id, {"reviewed": reviewed})

    def delete_insight(self, insight_id: str) -> bool:
        """Delete an insight by ID."""
        self._maybe_refresh_cache()

        for collection in self._cache.values():
            for i, insight in enumerate(collection.insights):
                if insight.id == insight_id:
                    collection.insights.pop(i)
                    return self._save_collection(collection)

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the insights collection."""
        self._maybe_refresh_cache()

        total = 0
        reviewed = 0
        by_type = {}
        by_use_in = {"report": 0, "quiz_results": 0, "landing": 0, "email": 0}
        by_relevance = {"high": 0, "medium": 0, "low": 0}

        for collection in self._cache.values():
            type_count = len(collection.insights)
            type_reviewed = sum(1 for i in collection.insights if i.reviewed)

            total += type_count
            reviewed += type_reviewed
            by_type[collection.type.value if isinstance(collection.type, InsightType) else collection.type] = {
                "total": type_count,
                "reviewed": type_reviewed,
            }

            for insight in collection.insights:
                for use_in in insight.tags.use_in:
                    key = use_in.value if isinstance(use_in, UseIn) else use_in
                    if key in by_use_in:
                        by_use_in[key] += 1

                # Track audience relevance
                relevance = getattr(insight, 'audience_relevance', None)
                if relevance:
                    key = relevance.value if isinstance(relevance, AudienceRelevance) else relevance
                    if key in by_relevance:
                        by_relevance[key] += 1
                else:
                    by_relevance["medium"] += 1  # Default for legacy

        return {
            "total": total,
            "reviewed": reviewed,
            "unreviewed": total - reviewed,
            "by_type": by_type,
            "by_use_in": by_use_in,
            "by_relevance": by_relevance,
        }

    def save_extracted_insights(self, extracted: ExtractedInsights) -> Dict[str, int]:
        """
        Save insights from an extraction result.

        Args:
            extracted: ExtractedInsights from the extraction skill

        Returns:
            Dict with counts: {"added": N, "skipped": M}
        """
        return self.add_insights_batch(extracted.insights)


# Singleton instance
_service: Optional[InsightService] = None


def get_insight_service() -> InsightService:
    """Get the singleton insight service instance."""
    global _service
    if _service is None:
        _service = InsightService()
    return _service
