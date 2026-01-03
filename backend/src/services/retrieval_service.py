"""
Retrieval Service

Semantic search over the knowledge base using vector embeddings.
Provides the RAG (Retrieval Augmented Generation) layer for the CRB agent.

Usage:
    service = await get_retrieval_service()

    # Find relevant opportunities for a pain point
    results = await service.search_opportunities(
        query="spending too much time on scheduling",
        industry="dental",
        limit=5
    )

    # Find similar vendors
    vendors = await service.search_vendors(
        query="AI receptionist for phone calls",
        limit=5
    )

    # Comprehensive search across all knowledge
    context = await service.get_relevant_context(
        query="automate patient intake and scheduling",
        industry="dental"
    )
"""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from src.config.supabase_client import get_async_supabase
from src.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================

class SearchResult(BaseModel):
    """A single search result from vector search."""
    id: str
    content_type: str
    content_id: str
    industry: Optional[str]
    title: str
    content: str
    metadata: Dict[str, Any]
    similarity: float  # 0-1, higher is more similar

    @property
    def is_highly_relevant(self) -> bool:
        """Check if result is highly relevant (>0.7 similarity)."""
        return self.similarity > 0.7


class RetrievalContext(BaseModel):
    """
    Aggregated context from multiple search types.

    This is what gets injected into the agent's prompt.
    """
    query: str
    industry: Optional[str]

    # Results by type
    vendors: List[SearchResult] = []
    opportunities: List[SearchResult] = []
    case_studies: List[SearchResult] = []
    patterns: List[SearchResult] = []
    benchmarks: List[SearchResult] = []

    # Metadata
    total_results: int = 0
    search_time_ms: float = 0

    def to_prompt_context(self) -> str:
        """
        Format results for injection into LLM prompt.

        Returns a structured text block with relevant knowledge.
        """
        sections = []

        if self.vendors:
            vendor_text = "\n".join([
                f"- **{r.title}** (similarity: {r.similarity:.0%}): {r.content[:200]}..."
                for r in self.vendors[:5]
            ])
            sections.append(f"## Relevant Vendors\n{vendor_text}")

        if self.opportunities:
            opp_text = "\n".join([
                f"- **{r.title}** [{r.industry}] (similarity: {r.similarity:.0%}): {r.content[:200]}..."
                for r in self.opportunities[:5]
            ])
            sections.append(f"## Relevant Opportunities\n{opp_text}")

        if self.case_studies:
            case_text = "\n".join([
                f"- **{r.title}** (similarity: {r.similarity:.0%}): {r.content[:300]}..."
                for r in self.case_studies[:3]
            ])
            sections.append(f"## Similar Case Studies\n{case_text}")

        if self.patterns:
            pattern_text = "\n".join([
                f"- **{r.title}** (similarity: {r.similarity:.0%}): {r.content[:200]}..."
                for r in self.patterns[:3]
            ])
            sections.append(f"## Relevant Patterns\n{pattern_text}")

        if not sections:
            return "No relevant knowledge found for this query."

        header = f"# Retrieved Knowledge Context\n\nQuery: \"{self.query}\""
        if self.industry:
            header += f" | Industry: {self.industry}"
        header += f"\nTotal results: {self.total_results}\n"

        return header + "\n\n" + "\n\n".join(sections)


# =============================================================================
# RETRIEVAL SERVICE
# =============================================================================

class RetrievalService:
    """
    Semantic search service for the knowledge base.

    Provides high-level methods for finding relevant content
    based on natural language queries.
    """

    def __init__(self):
        self._embedding_service = None

    async def _get_embedding_service(self):
        """Lazy load embedding service."""
        if self._embedding_service is None:
            self._embedding_service = await get_embedding_service()
        return self._embedding_service

    async def _get_query_embedding(self, query: str) -> Optional[List[float]]:
        """Generate embedding for a search query."""
        service = await self._get_embedding_service()
        return await service.generate_embedding(query)

    async def search(
        self,
        query: str,
        content_type: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.5
    ) -> List[SearchResult]:
        """
        Generic semantic search across knowledge base.

        Args:
            query: Natural language search query
            content_type: Filter by type (vendor, opportunity, etc.)
            industry: Filter by industry
            limit: Max results to return
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of SearchResult ordered by similarity
        """
        embedding = await self._get_query_embedding(query)
        if embedding is None:
            logger.error("Failed to generate query embedding")
            return []

        try:
            supabase = await get_async_supabase()

            # Use the database search function
            response = await supabase.rpc(
                "search_knowledge",
                {
                    "query_embedding": embedding,
                    "match_count": limit,
                    "filter_content_type": content_type,
                    "filter_industry": industry,
                    "similarity_threshold": similarity_threshold
                }
            ).execute()

            if not response.data:
                return []

            return [
                SearchResult(
                    id=str(row["id"]),
                    content_type=row["content_type"],
                    content_id=row["content_id"],
                    industry=row.get("industry"),
                    title=row["title"],
                    content=row["content"],
                    metadata=row.get("metadata", {}),
                    similarity=row["similarity"]
                )
                for row in response.data
            ]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def search_vendors(
        self,
        query: str,
        industry: Optional[str] = None,
        limit: int = 5
    ) -> List[SearchResult]:
        """
        Find vendors matching a query.

        Example: "AI receptionist for phone calls" -> Smith.ai, Ruby, etc.
        """
        return await self.search(
            query=query,
            content_type="vendor",
            industry=industry,
            limit=limit
        )

    async def search_opportunities(
        self,
        query: str,
        industry: Optional[str] = None,
        limit: int = 5
    ) -> List[SearchResult]:
        """
        Find AI opportunities matching a pain point.

        Example: "too much time on scheduling" -> AI scheduling opportunities
        """
        return await self.search(
            query=query,
            content_type="opportunity",
            industry=industry,
            limit=limit
        )

    async def search_case_studies(
        self,
        query: str,
        limit: int = 3
    ) -> List[SearchResult]:
        """
        Find relevant case studies and examples.

        Example: "voice AI ROI" -> Auto Ace, Barti examples
        """
        return await self.search(
            query=query,
            content_type="case_study",
            limit=limit
        )

    async def search_patterns(
        self,
        query: str,
        limit: int = 3
    ) -> List[SearchResult]:
        """
        Find implementation patterns and best practices.

        Example: "demand expansion" -> Jevons Effect patterns
        """
        return await self.search(
            query=query,
            content_type="pattern",
            limit=limit
        )

    async def get_relevant_context(
        self,
        query: str,
        industry: Optional[str] = None,
        vendors_limit: int = 5,
        opportunities_limit: int = 5,
        case_studies_limit: int = 3,
        patterns_limit: int = 3
    ) -> RetrievalContext:
        """
        Comprehensive search across all knowledge types.

        This is the main entry point for the agent to get
        relevant context for analysis.

        Returns aggregated results from all content types,
        formatted for injection into prompts.
        """
        import time
        start = time.time()

        embedding = await self._get_query_embedding(query)
        if embedding is None:
            return RetrievalContext(query=query, industry=industry)

        try:
            supabase = await get_async_supabase()

            # Use the multi-type search function
            response = await supabase.rpc(
                "search_all_knowledge",
                {
                    "query_embedding": embedding,
                    "match_count_per_type": max(
                        vendors_limit, opportunities_limit,
                        case_studies_limit, patterns_limit
                    ),
                    "filter_industry": industry
                }
            ).execute()

            results = response.data or []

            # Group by content type
            vendors = []
            opportunities = []
            case_studies = []
            patterns = []
            benchmarks = []

            for row in results:
                result = SearchResult(
                    id=str(row["id"]),
                    content_type=row["content_type"],
                    content_id=row["content_id"],
                    industry=row.get("industry"),
                    title=row["title"],
                    content=row["content"],
                    metadata=row.get("metadata", {}),
                    similarity=row["similarity"]
                )

                if row["content_type"] == "vendor":
                    vendors.append(result)
                elif row["content_type"] == "opportunity":
                    opportunities.append(result)
                elif row["content_type"] in ("case_study", "insight"):
                    case_studies.append(result)
                elif row["content_type"] == "pattern":
                    patterns.append(result)
                elif row["content_type"] == "benchmark":
                    benchmarks.append(result)

            elapsed_ms = (time.time() - start) * 1000

            return RetrievalContext(
                query=query,
                industry=industry,
                vendors=vendors[:vendors_limit],
                opportunities=opportunities[:opportunities_limit],
                case_studies=case_studies[:case_studies_limit],
                patterns=patterns[:patterns_limit],
                benchmarks=benchmarks,
                total_results=len(results),
                search_time_ms=elapsed_ms
            )

        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return RetrievalContext(query=query, industry=industry)

    async def find_similar_to_finding(
        self,
        finding_text: str,
        industry: str,
        limit: int = 5
    ) -> Dict[str, List[SearchResult]]:
        """
        Find content similar to a discovered finding.

        Useful for enriching findings with examples and vendor options.
        """
        context = await self.get_relevant_context(
            query=finding_text,
            industry=industry,
            vendors_limit=limit,
            opportunities_limit=limit,
            case_studies_limit=3
        )

        return {
            "vendors": context.vendors,
            "opportunities": context.opportunities,
            "case_studies": context.case_studies,
            "patterns": context.patterns
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_retrieval_service: Optional[RetrievalService] = None


async def get_retrieval_service() -> RetrievalService:
    """Get or create the retrieval service singleton."""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
