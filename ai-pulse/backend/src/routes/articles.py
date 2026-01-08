"""
Articles Routes
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query

from src.config.supabase_client import get_async_supabase
from src.middleware.auth import CurrentUser, get_current_user, require_subscriber
from src.models.schemas import ArticleResponse, ArticleListResponse
from src.models.enums import SourceType, ContentType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=ArticleListResponse)
async def list_articles(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    source_type: Optional[SourceType] = None,
    content_type: Optional[ContentType] = None,
    category: Optional[str] = None,
    current_user: CurrentUser = Depends(require_subscriber),
):
    """
    List articles (subscribers only).

    Returns paginated list of articles from the last 7 days.
    """
    supabase = await get_async_supabase()

    # Build query
    query = supabase.table("articles").select(
        "*, sources(name, source_type)",
        count="exact"
    ).order("published_at", desc=True)

    # Apply filters
    if source_type:
        query = query.eq("sources.source_type", source_type.value)
    if content_type:
        query = query.eq("content_type", content_type.value)
    if category:
        query = query.contains("categories", [category])

    # Pagination
    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1)

    result = await query.execute()

    articles = []
    for row in result.data:
        source = row.get("sources", {})
        articles.append(ArticleResponse(
            id=row["id"],
            source_name=source.get("name", "Unknown"),
            source_type=SourceType(source.get("source_type", "rss")),
            content_type=ContentType(row["content_type"]),
            title=row["title"],
            description=row.get("description"),
            url=row["url"],
            thumbnail_url=row.get("thumbnail_url"),
            published_at=row["published_at"],
            views=row.get("views"),
            likes=row.get("likes"),
            comments=row.get("comments"),
            score=row.get("score", 0),
            summary=row.get("summary"),
            categories=row.get("categories", []),
        ))

    total = result.count or 0
    has_more = offset + per_page < total

    return ArticleListResponse(
        data=articles,
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )


@router.get("/preview")
async def preview_articles():
    """
    Preview top 3 articles (public).

    Used on landing page to show sample content.
    """
    supabase = await get_async_supabase()

    result = await supabase.table("articles").select(
        "*, sources(name, source_type)"
    ).order("score", desc=True).limit(3).execute()

    articles = []
    for row in result.data:
        source = row.get("sources", {})
        articles.append({
            "id": row["id"],
            "source_name": source.get("name", "Unknown"),
            "source_type": source.get("source_type", "rss"),
            "content_type": row["content_type"],
            "title": row["title"],
            "description": row.get("description"),
            "url": row["url"],
            "thumbnail_url": row.get("thumbnail_url"),
            "published_at": row["published_at"],
            "score": row.get("score", 0),
        })

    return {"data": articles}


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: str,
    current_user: CurrentUser = Depends(require_subscriber),
):
    """Get a single article by ID (subscribers only)."""
    supabase = await get_async_supabase()

    result = await supabase.table("articles").select(
        "*, sources(name, source_type)"
    ).eq("id", article_id).single().execute()

    if not result.data:
        from src.middleware.error_handler import NotFoundError
        raise NotFoundError("Article", article_id)

    row = result.data
    source = row.get("sources", {})

    return ArticleResponse(
        id=row["id"],
        source_name=source.get("name", "Unknown"),
        source_type=SourceType(source.get("source_type", "rss")),
        content_type=ContentType(row["content_type"]),
        title=row["title"],
        description=row.get("description"),
        url=row["url"],
        thumbnail_url=row.get("thumbnail_url"),
        published_at=row["published_at"],
        views=row.get("views"),
        likes=row.get("likes"),
        comments=row.get("comments"),
        score=row.get("score", 0),
        summary=row.get("summary"),
        categories=row.get("categories", []),
    )
