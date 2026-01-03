"""
Embedding Service

Generates and manages embeddings for the knowledge base using OpenAI's
text-embedding-3-small model. Enables semantic search across vendors,
opportunities, benchmarks, and insights.

Cost: ~$0.02 per 1M tokens (very affordable)
Dimensions: 1536 (matches pgvector schema)
"""

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from openai import AsyncOpenAI
from pydantic import BaseModel

from src.config.settings import settings
from src.config.supabase_client import get_async_supabase

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
MAX_BATCH_SIZE = 100  # OpenAI limit is 2048, but smaller batches are safer
MAX_TOKENS_PER_TEXT = 8191  # Model limit


# =============================================================================
# SCHEMAS
# =============================================================================

class EmbeddingContent(BaseModel):
    """Content to be embedded."""
    content_type: str  # 'vendor', 'opportunity', 'benchmark', 'case_study', 'pattern', 'insight'
    content_id: str    # Unique ID within content type
    industry: Optional[str] = None
    title: str
    content: str       # The text to embed
    metadata: Dict[str, Any] = {}
    source_file: Optional[str] = None
    source_url: Optional[str] = None


class EmbeddingResult(BaseModel):
    """Result of embedding operation."""
    content_id: str
    content_type: str
    success: bool
    embedding_id: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# EMBEDDING SERVICE
# =============================================================================

class EmbeddingService:
    """
    Service for generating and managing embeddings.

    Uses OpenAI's text-embedding-3-small for cost-effective, high-quality embeddings.
    Stores in Supabase with pgvector for semantic search.
    """

    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the OpenAI client."""
        if self._initialized:
            return True

        if not settings.OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY not set - embeddings disabled")
            return False

        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._initialized = True
        logger.info("EmbeddingService initialized with OpenAI")
        return True

    def _compute_hash(self, content: str) -> str:
        """Compute hash of content for change detection."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _prepare_text(self, item: EmbeddingContent) -> str:
        """
        Prepare text for embedding.

        Combines title and content in a way that captures semantic meaning.
        """
        parts = [item.title]

        if item.industry:
            parts.append(f"Industry: {item.industry}")

        parts.append(item.content)

        # Add key metadata if present
        if item.metadata:
            if "category" in item.metadata:
                parts.append(f"Category: {item.metadata['category']}")
            if "tags" in item.metadata:
                parts.append(f"Tags: {', '.join(item.metadata['tags'])}")
            if "best_for" in item.metadata:
                parts.append(f"Best for: {item.metadata['best_for']}")

        text = "\n".join(parts)

        # Truncate if too long (rough estimate: 4 chars per token)
        max_chars = MAX_TOKENS_PER_TEXT * 4
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.warning(f"Truncated text for {item.content_id} to {max_chars} chars")

        return text

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.

        Returns list of floats (1536 dimensions) or None on error.
        """
        if not await self.initialize():
            return None

        try:
            response = await self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text,
                dimensions=EMBEDDING_DIMENSIONS
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    async def generate_embeddings_batch(
        self,
        texts: List[str]
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch.

        More efficient than individual calls for bulk operations.
        """
        if not await self.initialize():
            return [None] * len(texts)

        if not texts:
            return []

        results: List[Optional[List[float]]] = []

        # Process in batches
        for i in range(0, len(texts), MAX_BATCH_SIZE):
            batch = texts[i:i + MAX_BATCH_SIZE]

            try:
                response = await self.client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=batch,
                    dimensions=EMBEDDING_DIMENSIONS
                )

                # Sort by index to maintain order
                sorted_data = sorted(response.data, key=lambda x: x.index)
                batch_embeddings = [item.embedding for item in sorted_data]
                results.extend(batch_embeddings)

                logger.debug(f"Generated {len(batch)} embeddings in batch")

            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                results.extend([None] * len(batch))

        return results

    async def embed_and_store(
        self,
        items: List[EmbeddingContent],
        skip_unchanged: bool = True
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings and store in database.

        Args:
            items: List of content to embed
            skip_unchanged: Skip items whose content hash hasn't changed

        Returns:
            List of results for each item
        """
        if not await self.initialize():
            return [
                EmbeddingResult(
                    content_id=item.content_id,
                    content_type=item.content_type,
                    success=False,
                    error="EmbeddingService not initialized"
                )
                for item in items
            ]

        results: List[EmbeddingResult] = []
        supabase = await get_async_supabase()

        # Prepare texts and compute hashes
        items_to_process: List[Tuple[EmbeddingContent, str, str]] = []

        for item in items:
            text = self._prepare_text(item)
            content_hash = self._compute_hash(text)

            if skip_unchanged:
                # Check if content has changed
                existing = await supabase.table("knowledge_embeddings").select(
                    "content_hash"
                ).eq(
                    "content_type", item.content_type
                ).eq(
                    "content_id", item.content_id
                ).execute()

                if existing.data and existing.data[0].get("content_hash") == content_hash:
                    logger.debug(f"Skipping unchanged: {item.content_type}/{item.content_id}")
                    results.append(EmbeddingResult(
                        content_id=item.content_id,
                        content_type=item.content_type,
                        success=True,
                        error="Skipped (unchanged)"
                    ))
                    continue

            items_to_process.append((item, text, content_hash))

        if not items_to_process:
            logger.info("No items to process (all unchanged)")
            return results

        # Generate embeddings in batch
        texts = [text for _, text, _ in items_to_process]
        embeddings = await self.generate_embeddings_batch(texts)

        # Store in database
        for (item, text, content_hash), embedding in zip(items_to_process, embeddings):
            if embedding is None:
                results.append(EmbeddingResult(
                    content_id=item.content_id,
                    content_type=item.content_type,
                    success=False,
                    error="Embedding generation failed"
                ))
                continue

            try:
                # Upsert using the database function
                response = await supabase.rpc(
                    "upsert_knowledge_embedding",
                    {
                        "p_content_type": item.content_type,
                        "p_content_id": item.content_id,
                        "p_industry": item.industry,
                        "p_title": item.title,
                        "p_content": text,
                        "p_metadata": item.metadata,
                        "p_embedding": embedding,
                        "p_source_file": item.source_file,
                        "p_content_hash": content_hash
                    }
                ).execute()

                embedding_id = response.data if response.data else None

                results.append(EmbeddingResult(
                    content_id=item.content_id,
                    content_type=item.content_type,
                    success=True,
                    embedding_id=str(embedding_id) if embedding_id else None
                ))

                logger.debug(f"Stored embedding: {item.content_type}/{item.content_id}")

            except Exception as e:
                logger.error(f"Failed to store embedding {item.content_id}: {e}")
                results.append(EmbeddingResult(
                    content_id=item.content_id,
                    content_type=item.content_type,
                    success=False,
                    error=str(e)
                ))

        success_count = sum(1 for r in results if r.success and r.error != "Skipped (unchanged)")
        skip_count = sum(1 for r in results if r.error == "Skipped (unchanged)")
        fail_count = sum(1 for r in results if not r.success)

        logger.info(
            f"Embedding complete: {success_count} stored, {skip_count} skipped, {fail_count} failed"
        )

        return results

    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about stored embeddings."""
        try:
            supabase = await get_async_supabase()
            response = await supabase.rpc("get_embedding_stats").execute()

            if response.data:
                return {
                    "stats": response.data,
                    "total": sum(row["count"] for row in response.data)
                }
            return {"stats": [], "total": 0}

        except Exception as e:
            logger.error(f"Failed to get embedding stats: {e}")
            return {"stats": [], "total": 0, "error": str(e)}

    async def delete_embeddings(
        self,
        content_type: Optional[str] = None,
        content_id: Optional[str] = None,
        industry: Optional[str] = None
    ) -> int:
        """
        Delete embeddings matching criteria.

        Returns count of deleted items.
        """
        try:
            supabase = await get_async_supabase()
            query = supabase.table("knowledge_embeddings").delete()

            if content_type:
                query = query.eq("content_type", content_type)
            if content_id:
                query = query.eq("content_id", content_id)
            if industry:
                query = query.eq("industry", industry)

            response = await query.execute()
            count = len(response.data) if response.data else 0

            logger.info(f"Deleted {count} embeddings")
            return count

        except Exception as e:
            logger.error(f"Failed to delete embeddings: {e}")
            return 0


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_embedding_service: Optional[EmbeddingService] = None


async def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
