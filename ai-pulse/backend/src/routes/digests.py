"""
Digests Routes
"""

import logging
from fastapi import APIRouter, Depends, Query

from src.config.supabase_client import get_async_supabase
from src.middleware.auth import CurrentUser, require_subscriber
from src.models.schemas import DigestResponse, DigestListResponse, ArticleResponse
from src.models.enums import SourceType, ContentType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/digests", tags=["digests"])


@router.get("", response_model=DigestListResponse)
async def list_digests(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    current_user: CurrentUser = Depends(require_subscriber),
):
    """
    List past digests (subscribers only).

    Returns paginated list of digests the user has received.
    """
    supabase = await get_async_supabase()

    # Get digests that were sent to this user
    offset = (page - 1) * per_page

    result = await supabase.table("digest_sends").select(
        "*, digests(*)",
        count="exact"
    ).eq("user_id", current_user.id).order(
        "sent_at", desc=True
    ).range(offset, offset + per_page - 1).execute()

    digests = []
    for row in result.data:
        digest = row.get("digests", {})
        if digest:
            # Get articles for this digest
            article_ids = digest.get("article_ids", [])
            articles = []

            if article_ids:
                articles_result = await supabase.table("articles").select(
                    "*, sources(name, source_type)"
                ).in_("id", article_ids).execute()

                for article_row in articles_result.data:
                    source = article_row.get("sources", {})
                    articles.append(ArticleResponse(
                        id=article_row["id"],
                        source_name=source.get("name", "Unknown"),
                        source_type=SourceType(source.get("source_type", "rss")),
                        content_type=ContentType(article_row["content_type"]),
                        title=article_row["title"],
                        description=article_row.get("description"),
                        url=article_row["url"],
                        thumbnail_url=article_row.get("thumbnail_url"),
                        published_at=article_row["published_at"],
                        views=article_row.get("views"),
                        likes=article_row.get("likes"),
                        comments=article_row.get("comments"),
                        score=article_row.get("score", 0),
                        summary=article_row.get("summary"),
                        categories=article_row.get("categories", []),
                    ))

            digests.append(DigestResponse(
                id=digest["id"],
                created_at=digest["created_at"],
                subject_line=digest.get("subject_line", "AI Pulse Daily Digest"),
                articles=articles,
                stats=digest.get("stats", {}),
            ))

    total = result.count or 0
    has_more = offset + per_page < total

    return DigestListResponse(
        data=digests,
        total=total,
        page=page,
        per_page=per_page,
        has_more=has_more,
    )


@router.get("/{digest_id}", response_model=DigestResponse)
async def get_digest(
    digest_id: str,
    current_user: CurrentUser = Depends(require_subscriber),
):
    """Get a single digest by ID (subscribers only)."""
    supabase = await get_async_supabase()

    # Verify user received this digest
    send_check = await supabase.table("digest_sends").select("id").eq(
        "digest_id", digest_id
    ).eq("user_id", current_user.id).execute()

    if not send_check.data:
        from src.middleware.error_handler import NotFoundError
        raise NotFoundError("Digest", digest_id)

    # Get digest
    result = await supabase.table("digests").select("*").eq(
        "id", digest_id
    ).single().execute()

    if not result.data:
        from src.middleware.error_handler import NotFoundError
        raise NotFoundError("Digest", digest_id)

    digest = result.data

    # Get articles
    article_ids = digest.get("article_ids", [])
    articles = []

    if article_ids:
        articles_result = await supabase.table("articles").select(
            "*, sources(name, source_type)"
        ).in_("id", article_ids).execute()

        for article_row in articles_result.data:
            source = article_row.get("sources", {})
            articles.append(ArticleResponse(
                id=article_row["id"],
                source_name=source.get("name", "Unknown"),
                source_type=SourceType(source.get("source_type", "rss")),
                content_type=ContentType(article_row["content_type"]),
                title=article_row["title"],
                description=article_row.get("description"),
                url=article_row["url"],
                thumbnail_url=article_row.get("thumbnail_url"),
                published_at=article_row["published_at"],
                views=article_row.get("views"),
                likes=article_row.get("likes"),
                comments=article_row.get("comments"),
                score=article_row.get("score", 0),
                summary=article_row.get("summary"),
                categories=article_row.get("categories", []),
            ))

    return DigestResponse(
        id=digest["id"],
        created_at=digest["created_at"],
        subject_line=digest.get("subject_line", "AI Pulse Daily Digest"),
        articles=articles,
        stats=digest.get("stats", {}),
    )
