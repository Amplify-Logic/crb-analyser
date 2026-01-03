"""
Knowledge Base Admin Routes

CRUD operations for managing the knowledge base content:
- Vendors, Opportunities, Benchmarks, Case Studies, Patterns, Insights

Plus embedding management:
- Stats, re-embed, similarity testing
"""

import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query, status, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from src.config.supabase_client import get_async_supabase
from src.middleware.auth import require_workspace, CurrentUser
from src.services.embedding_service import (
    get_embedding_service,
    EmbeddingContent,
)
from src.services.retrieval_service import get_retrieval_service
from src.knowledge import KNOWLEDGE_BASE_PATH, list_supported_industries, VENDOR_CATEGORIES

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

ContentType = Literal["vendor", "opportunity", "benchmark", "case_study", "pattern", "insight"]


class KnowledgeItem(BaseModel):
    """A knowledge base item."""
    id: Optional[str] = None
    content_type: ContentType
    content_id: str
    industry: Optional[str] = None
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_file: Optional[str] = None

    # Embedding info
    embedded_at: Optional[datetime] = None
    content_hash: Optional[str] = None
    is_embedded: bool = False
    needs_update: bool = False


class KnowledgeItemCreate(BaseModel):
    """Create a new knowledge item."""
    content_type: ContentType
    content_id: str
    industry: Optional[str] = None
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_file: Optional[str] = None


class KnowledgeItemUpdate(BaseModel):
    """Update a knowledge item."""
    title: Optional[str] = None
    content: Optional[str] = None
    industry: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeListResponse(BaseModel):
    """Paginated list response."""
    items: List[KnowledgeItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class EmbeddingStats(BaseModel):
    """Embedding statistics."""
    total_embeddings: int
    by_type: Dict[str, Dict[str, int]]
    last_sync: Optional[datetime] = None
    needs_update_count: int


class SimilarityTestResult(BaseModel):
    """Similarity search test result."""
    content_id: str
    content_type: str
    title: str
    industry: Optional[str]
    similarity: float
    preview: str


class SimilarityTestResponse(BaseModel):
    """Similarity test response."""
    query: str
    industry: Optional[str]
    results: List[SimilarityTestResult]
    search_time_ms: float


# =============================================================================
# HELPERS
# =============================================================================

def compute_hash(content: str) -> str:
    """Compute content hash for change detection."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


async def get_knowledge_items_from_db(
    content_type: Optional[str] = None,
    industry: Optional[str] = None,
    embedded_only: Optional[bool] = None,
    needs_update: Optional[bool] = None,
    search_query: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[List[Dict], int]:
    """Get knowledge items from database with filtering."""
    supabase = await get_async_supabase()

    query = supabase.table("knowledge_embeddings").select("*", count="exact")

    if content_type:
        query = query.eq("content_type", content_type)
    if industry:
        query = query.eq("industry", industry)
    if search_query:
        query = query.ilike("title", f"%{search_query}%")

    # Pagination
    offset = (page - 1) * page_size
    query = query.range(offset, offset + page_size - 1)
    query = query.order("updated_at", desc=True)

    result = await query.execute()

    return result.data or [], result.count or 0


# =============================================================================
# LIST & SEARCH ENDPOINTS
# =============================================================================

@router.get("/", response_model=KnowledgeListResponse)
async def list_knowledge_items(
    content_type: Optional[ContentType] = None,
    industry: Optional[str] = None,
    embedded: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    List knowledge base items with optional filtering.
    """
    items, total = await get_knowledge_items_from_db(
        content_type=content_type,
        industry=industry,
        embedded_only=embedded,
        search_query=search,
        page=page,
        page_size=page_size,
    )

    # Convert to KnowledgeItem objects
    knowledge_items = []
    for item in items:
        knowledge_items.append(KnowledgeItem(
            id=item.get("id"),
            content_type=item.get("content_type"),
            content_id=item.get("content_id"),
            industry=item.get("industry"),
            title=item.get("title"),
            content=item.get("content"),
            metadata=item.get("metadata", {}),
            source_file=item.get("source_file"),
            embedded_at=item.get("embedded_at"),
            content_hash=item.get("content_hash"),
            is_embedded=item.get("embedding") is not None,
            needs_update=False,  # TODO: Compute based on hash
        ))

    return KnowledgeListResponse(
        items=knowledge_items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/search")
async def search_knowledge(
    q: str = Query(..., min_length=2),
    content_type: Optional[ContentType] = None,
    industry: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Semantic search across knowledge base.
    """
    retrieval_service = await get_retrieval_service()

    results = await retrieval_service.search(
        query=q,
        content_type=content_type,
        industry=industry,
        limit=limit,
    )

    return {
        "query": q,
        "results": [
            {
                "id": r.id,
                "content_type": r.content_type,
                "content_id": r.content_id,
                "industry": r.industry,
                "title": r.title,
                "preview": r.content[:200] + "..." if len(r.content) > 200 else r.content,
                "similarity": r.similarity,
                "metadata": r.metadata,
            }
            for r in results
        ],
        "count": len(results),
    }


@router.get("/types")
async def get_content_types(
    current_user: CurrentUser = Depends(require_workspace),
):
    """Get available content types and their counts."""
    supabase = await get_async_supabase()

    result = await supabase.rpc("get_embedding_stats").execute()

    types = {
        "vendor": {"label": "Vendors", "count": 0, "categories": VENDOR_CATEGORIES},
        "opportunity": {"label": "Opportunities", "count": 0, "industries": list_supported_industries()},
        "benchmark": {"label": "Benchmarks", "count": 0, "industries": list_supported_industries()},
        "case_study": {"label": "Case Studies", "count": 0},
        "pattern": {"label": "Patterns", "count": 0},
        "insight": {"label": "Insights", "count": 0},
    }

    if result.data:
        for row in result.data:
            ct = row.get("content_type")
            if ct in types:
                types[ct]["count"] = row.get("count", 0)

    return {"types": types}


@router.get("/industries")
async def get_industries(
    current_user: CurrentUser = Depends(require_workspace),
):
    """Get supported industries."""
    return {"industries": list_supported_industries()}


# =============================================================================
# CRUD ENDPOINTS
# =============================================================================

@router.get("/{content_type}/{content_id}")
async def get_knowledge_item(
    content_type: ContentType,
    content_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """Get a single knowledge item."""
    supabase = await get_async_supabase()

    result = await supabase.table("knowledge_embeddings").select("*").eq(
        "content_type", content_type
    ).eq(
        "content_id", content_id
    ).single().execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item not found: {content_type}/{content_id}"
        )

    item = result.data
    return KnowledgeItem(
        id=item.get("id"),
        content_type=item.get("content_type"),
        content_id=item.get("content_id"),
        industry=item.get("industry"),
        title=item.get("title"),
        content=item.get("content"),
        metadata=item.get("metadata", {}),
        source_file=item.get("source_file"),
        embedded_at=item.get("embedded_at"),
        content_hash=item.get("content_hash"),
        is_embedded=item.get("embedding") is not None,
        needs_update=False,
    )


@router.post("/{content_type}", status_code=status.HTTP_201_CREATED)
async def create_knowledge_item(
    content_type: ContentType,
    item: KnowledgeItemCreate,
    embed: bool = Query(True, description="Generate embedding immediately"),
    current_user: CurrentUser = Depends(require_workspace),
):
    """Create a new knowledge item."""
    supabase = await get_async_supabase()

    # Check if already exists
    existing = await supabase.table("knowledge_embeddings").select("id").eq(
        "content_type", content_type
    ).eq(
        "content_id", item.content_id
    ).execute()

    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Item already exists: {content_type}/{item.content_id}"
        )

    # Compute content hash
    content_hash = compute_hash(item.content)

    # Insert without embedding first
    insert_data = {
        "content_type": content_type,
        "content_id": item.content_id,
        "industry": item.industry,
        "title": item.title,
        "content": item.content,
        "metadata": item.metadata,
        "source_file": item.source_file,
        "content_hash": content_hash,
    }

    result = await supabase.table("knowledge_embeddings").insert(insert_data).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create item"
        )

    created_item = result.data[0]

    # Generate embedding if requested
    if embed:
        try:
            embedding_service = await get_embedding_service()
            embed_content = EmbeddingContent(
                content_type=content_type,
                content_id=item.content_id,
                industry=item.industry,
                title=item.title,
                content=item.content,
                metadata=item.metadata,
            )
            embed_results = await embedding_service.embed_and_store([embed_content], skip_unchanged=False)
            created_item["is_embedded"] = embed_results[0].success if embed_results else False
        except Exception as e:
            logger.warning(f"Failed to embed new item: {e}")
            created_item["is_embedded"] = False

    return created_item


@router.put("/{content_type}/{content_id}")
async def update_knowledge_item(
    content_type: ContentType,
    content_id: str,
    updates: KnowledgeItemUpdate,
    re_embed: bool = Query(True, description="Re-generate embedding if content changed"),
    current_user: CurrentUser = Depends(require_workspace),
):
    """Update a knowledge item."""
    supabase = await get_async_supabase()

    # Get existing item
    existing = await supabase.table("knowledge_embeddings").select("*").eq(
        "content_type", content_type
    ).eq(
        "content_id", content_id
    ).single().execute()

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item not found: {content_type}/{content_id}"
        )

    # Build update data
    update_data = {"updated_at": datetime.utcnow().isoformat()}
    content_changed = False

    if updates.title is not None:
        update_data["title"] = updates.title
    if updates.content is not None:
        update_data["content"] = updates.content
        update_data["content_hash"] = compute_hash(updates.content)
        content_changed = True
    if updates.industry is not None:
        update_data["industry"] = updates.industry
    if updates.metadata is not None:
        update_data["metadata"] = updates.metadata

    # Update in database
    result = await supabase.table("knowledge_embeddings").update(update_data).eq(
        "content_type", content_type
    ).eq(
        "content_id", content_id
    ).execute()

    updated_item = result.data[0] if result.data else existing.data

    # Re-embed if content changed
    if re_embed and content_changed:
        try:
            embedding_service = await get_embedding_service()
            embed_content = EmbeddingContent(
                content_type=content_type,
                content_id=content_id,
                industry=updates.industry or existing.data.get("industry"),
                title=updates.title or existing.data.get("title"),
                content=updates.content,
                metadata=updates.metadata or existing.data.get("metadata", {}),
            )
            await embedding_service.embed_and_store([embed_content], skip_unchanged=False)
            updated_item["re_embedded"] = True
        except Exception as e:
            logger.warning(f"Failed to re-embed updated item: {e}")
            updated_item["re_embedded"] = False

    return updated_item


@router.delete("/{content_type}/{content_id}")
async def delete_knowledge_item(
    content_type: ContentType,
    content_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """Delete a knowledge item and its embedding."""
    supabase = await get_async_supabase()

    # Check exists
    existing = await supabase.table("knowledge_embeddings").select("id").eq(
        "content_type", content_type
    ).eq(
        "content_id", content_id
    ).execute()

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item not found: {content_type}/{content_id}"
        )

    # Delete
    await supabase.table("knowledge_embeddings").delete().eq(
        "content_type", content_type
    ).eq(
        "content_id", content_id
    ).execute()

    return {"success": True, "deleted": f"{content_type}/{content_id}"}


# =============================================================================
# EMBEDDING MANAGEMENT
# =============================================================================

@router.get("/stats/embeddings", response_model=EmbeddingStats)
async def get_embedding_stats(
    current_user: CurrentUser = Depends(require_workspace),
):
    """Get embedding statistics."""
    embedding_service = await get_embedding_service()
    stats = await embedding_service.get_embedding_stats()

    by_type = {}
    for row in stats.get("stats", []):
        ct = row.get("content_type")
        by_type[ct] = {
            "count": row.get("count", 0),
            "industries": row.get("industries", []),
            "last_updated": row.get("last_updated"),
        }

    return EmbeddingStats(
        total_embeddings=stats.get("total", 0),
        by_type=by_type,
        last_sync=None,  # TODO: Track last sync time
        needs_update_count=0,  # TODO: Count items needing update
    )


@router.post("/embed/{content_type}/{content_id}")
async def embed_single_item(
    content_type: ContentType,
    content_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """Re-embed a single knowledge item."""
    supabase = await get_async_supabase()

    # Get item
    result = await supabase.table("knowledge_embeddings").select("*").eq(
        "content_type", content_type
    ).eq(
        "content_id", content_id
    ).single().execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item not found: {content_type}/{content_id}"
        )

    item = result.data

    # Re-embed
    embedding_service = await get_embedding_service()
    embed_content = EmbeddingContent(
        content_type=content_type,
        content_id=content_id,
        industry=item.get("industry"),
        title=item.get("title"),
        content=item.get("content"),
        metadata=item.get("metadata", {}),
    )

    results = await embedding_service.embed_and_store([embed_content], skip_unchanged=False)

    if results and results[0].success:
        return {"success": True, "message": f"Re-embedded {content_type}/{content_id}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Embedding failed"
        )


@router.post("/embed/all")
async def embed_all_items(
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="Re-embed even if unchanged"),
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Trigger re-embedding of all knowledge items.
    Runs in background.
    """
    async def run_vectorization():
        try:
            from src.scripts.vectorize_knowledge import vectorize_all
            await vectorize_all(force=force)
        except Exception as e:
            logger.error(f"Background vectorization failed: {e}")

    background_tasks.add_task(run_vectorization)

    return {
        "success": True,
        "message": "Vectorization started in background",
        "force": force,
    }


@router.post("/embed/type/{content_type}")
async def embed_by_type(
    content_type: ContentType,
    background_tasks: BackgroundTasks,
    force: bool = Query(False),
    current_user: CurrentUser = Depends(require_workspace),
):
    """Re-embed all items of a specific type."""
    async def run_vectorization():
        try:
            from src.scripts.vectorize_knowledge import vectorize_all
            await vectorize_all(force=force, content_type=content_type)
        except Exception as e:
            logger.error(f"Background vectorization failed: {e}")

    background_tasks.add_task(run_vectorization)

    return {
        "success": True,
        "message": f"Vectorization of {content_type} started in background",
    }


@router.post("/embed/outdated")
async def embed_outdated(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(require_workspace),
):
    """Re-embed only items that have changed (needs_update=true)."""
    async def run_vectorization():
        try:
            # Get items needing update and re-embed them
            supabase = await get_async_supabase()
            result = await supabase.table("knowledge_embeddings").select(
                "content_type, content_id"
            ).eq("needs_update", True).execute()

            if result.data:
                embedding_service = await get_embedding_service()
                for item in result.data:
                    # Get the full content and re-embed
                    content_result = await supabase.table("knowledge_embeddings").select(
                        "*"
                    ).eq("content_type", item["content_type"]).eq(
                        "content_id", item["content_id"]
                    ).single().execute()

                    if content_result.data:
                        await embedding_service.embed_and_store([
                            EmbeddingContent(
                                content_type=content_result.data["content_type"],
                                content_id=content_result.data["content_id"],
                                title=content_result.data.get("title", ""),
                                content=content_result.data.get("content", ""),
                                industry=content_result.data.get("industry"),
                                metadata=content_result.data.get("metadata", {}),
                            )
                        ], skip_unchanged=False)
                logger.info(f"Re-embedded {len(result.data)} outdated items")
        except Exception as e:
            logger.error(f"Background re-embedding of outdated items failed: {e}")

    background_tasks.add_task(run_vectorization)

    return {
        "success": True,
        "message": "Re-embedding of outdated items started in background",
    }


@router.get("/test-search", response_model=SimilarityTestResponse)
async def test_similarity_search(
    q: str = Query(..., min_length=2),
    industry: Optional[str] = None,
    limit: int = Query(10, ge=1, le=20),
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Test similarity search to debug vector retrieval.
    Returns similarity scores for inspection.
    """
    import time
    start = time.time()

    retrieval_service = await get_retrieval_service()
    results = await retrieval_service.search(
        query=q,
        industry=industry,
        limit=limit,
        similarity_threshold=0.3,  # Lower threshold for testing
    )

    elapsed_ms = (time.time() - start) * 1000

    return SimilarityTestResponse(
        query=q,
        industry=industry,
        results=[
            SimilarityTestResult(
                content_id=r.content_id,
                content_type=r.content_type,
                title=r.title,
                industry=r.industry,
                similarity=round(r.similarity, 4),
                preview=r.content[:150] + "..." if len(r.content) > 150 else r.content,
            )
            for r in results
        ],
        search_time_ms=round(elapsed_ms, 2),
    )


# =============================================================================
# SYNC ENDPOINTS
# =============================================================================

@router.post("/sync")
async def sync_knowledge_from_files(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Sync knowledge from JSON files to database.
    This loads all JSON files and updates the database.
    """
    async def run_sync():
        try:
            from src.scripts.vectorize_knowledge import vectorize_all
            await vectorize_all(force=False)
        except Exception as e:
            logger.error(f"Sync failed: {e}")

    background_tasks.add_task(run_sync)

    return {
        "success": True,
        "message": "Sync started in background",
    }


@router.get("/sync/sources")
async def get_knowledge_sources(
    current_user: CurrentUser = Depends(require_workspace),
):
    """Get information about knowledge source files."""
    sources = []

    # Vendor files
    vendors_path = KNOWLEDGE_BASE_PATH / "vendors"
    if vendors_path.exists():
        for category in VENDOR_CATEGORIES:
            file_path = vendors_path / f"{category}.json"
            if file_path.exists():
                sources.append({
                    "type": "vendor",
                    "category": category,
                    "path": str(file_path.relative_to(KNOWLEDGE_BASE_PATH)),
                    "exists": True,
                })

    # Industry files
    for industry in list_supported_industries():
        industry_path = KNOWLEDGE_BASE_PATH / industry
        if industry_path.exists():
            for file_type in ["opportunities", "benchmarks", "processes", "vendors"]:
                file_path = industry_path / f"{file_type}.json"
                sources.append({
                    "type": file_type,
                    "industry": industry,
                    "path": str(file_path.relative_to(KNOWLEDGE_BASE_PATH)),
                    "exists": file_path.exists(),
                })

    # Pattern files
    patterns_path = KNOWLEDGE_BASE_PATH / "patterns"
    if patterns_path.exists():
        for file_path in patterns_path.glob("*.json"):
            sources.append({
                "type": "pattern",
                "path": str(file_path.relative_to(KNOWLEDGE_BASE_PATH)),
                "exists": True,
            })

    return {"sources": sources, "count": len(sources)}
