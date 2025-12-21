"""
Expertise API Routes

Endpoints to view and manage the agent's self-improving expertise.
Useful for debugging and understanding what the agent has learned.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any, List

from src.expertise import get_expertise_store, get_self_improve_service

router = APIRouter(prefix="/api/expertise", tags=["expertise"])


@router.get("/")
async def get_expertise_overview() -> Dict[str, Any]:
    """Get an overview of all expertise the agent has accumulated."""
    store = get_expertise_store()

    industries = store.list_industries_with_expertise()
    vendor_exp = store.get_vendor_expertise()
    exec_exp = store.get_execution_expertise()

    return {
        "industries_with_expertise": industries,
        "total_vendor_recommendations": vendor_exp.total_recommendations,
        "total_executions": exec_exp.total_executions,
        "tool_reliability": exec_exp.tool_success_rates,
    }


@router.get("/industry/{industry}")
async def get_industry_expertise(industry: str) -> Dict[str, Any]:
    """Get detailed expertise for a specific industry."""
    service = get_self_improve_service()
    return service.get_expertise_summary(industry)


@router.get("/industries")
async def list_industry_expertise() -> List[Dict[str, Any]]:
    """List all industries with expertise summaries."""
    store = get_expertise_store()
    service = get_self_improve_service()

    industries = store.list_industries_with_expertise()
    return [service.get_expertise_summary(ind) for ind in industries]


@router.get("/vendors")
async def get_vendor_expertise() -> Dict[str, Any]:
    """Get accumulated vendor expertise."""
    store = get_expertise_store()
    expertise = store.get_vendor_expertise()

    return {
        "last_updated": expertise.last_updated.isoformat(),
        "total_recommendations": expertise.total_recommendations,
        "vendors": {
            name: {
                "recommendation_count": v.recommendation_count,
                "good_for": v.good_for,
                "not_good_for": v.not_good_for,
                "company_size_fit": v.company_size_fit,
            }
            for name, v in expertise.vendors.items()
        },
    }


@router.get("/execution")
async def get_execution_expertise() -> Dict[str, Any]:
    """Get execution expertise (tool effectiveness, failure patterns)."""
    store = get_expertise_store()
    expertise = store.get_execution_expertise()

    return {
        "last_updated": expertise.last_updated.isoformat(),
        "total_executions": expertise.total_executions,
        "tool_success_rates": expertise.tool_success_rates,
        "failure_patterns": expertise.failure_patterns[-10:],  # Last 10
    }
