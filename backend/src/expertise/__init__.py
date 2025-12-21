"""
Expertise Module - Self-Improving Agent System

This module implements the "Agent Expert" pattern where the CRB agent
learns and improves from each analysis it performs.

Key Components:
- ExpertiseStore: Persistent storage for expertise files
- SelfImproveService: Learning engine that updates expertise after each analysis
- Schemas: Data models for industry, vendor, and execution expertise

Usage:
    from src.expertise import get_expertise_store, get_self_improve_service

    # Read expertise before analysis
    store = get_expertise_store()
    expertise = store.get_all_expertise_context("marketing-agencies")

    # Learn after analysis
    service = get_self_improve_service()
    await service.learn_from_analysis(audit_id, industry, company_size, context, metrics)
"""

from .store import get_expertise_store, ExpertiseStore
from .self_improve import get_self_improve_service, SelfImproveService
from .schemas import (
    IndustryExpertise,
    VendorExpertise,
    ExecutionExpertise,
    AnalysisRecord,
    PainPointPattern,
    ProcessInsight,
    RecommendationPattern,
    VendorFit,
)

__all__ = [
    # Store
    "get_expertise_store",
    "ExpertiseStore",
    # Self-improve
    "get_self_improve_service",
    "SelfImproveService",
    # Schemas
    "IndustryExpertise",
    "VendorExpertise",
    "ExecutionExpertise",
    "AnalysisRecord",
    "PainPointPattern",
    "ProcessInsight",
    "RecommendationPattern",
    "VendorFit",
]
