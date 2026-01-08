"""
Sources Routes
"""

import logging
from typing import Optional
from fastapi import APIRouter, Query

from src.config.sources import (
    get_enabled_sources,
    get_sources_by_type,
    SourceType,
)
from src.models.schemas import SourceResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("")
async def list_sources(
    source_type: Optional[str] = Query(None, description="Filter by source type"),
):
    """
    List all monitored sources (public).

    Shows what sources AI Pulse monitors for content.
    """
    if source_type:
        try:
            st = SourceType(source_type)
            sources = get_sources_by_type(st)
        except ValueError:
            sources = get_enabled_sources()
    else:
        sources = get_enabled_sources()

    return {
        "data": [
            SourceResponse(
                slug=s.slug,
                name=s.name,
                source_type=s.source_type,
                url=s.url,
                category=s.category,
                priority=s.priority,
                description=s.description,
                enabled=s.enabled,
            )
            for s in sources
        ],
        "total": len(sources),
    }


@router.get("/stats")
async def source_stats():
    """Get source statistics (public)."""
    sources = get_enabled_sources()

    by_type = {}
    by_category = {}

    for source in sources:
        # Count by type
        type_key = source.source_type.value
        by_type[type_key] = by_type.get(type_key, 0) + 1

        # Count by category
        cat_key = source.category.value
        by_category[cat_key] = by_category.get(cat_key, 0) + 1

    return {
        "total_sources": len(sources),
        "by_type": by_type,
        "by_category": by_category,
    }
