"""
Software Research Models

Models for researching unknown software API capabilities.
Used in the Connect vs Replace feature for evaluating user's existing stack.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class SoftwareCapabilities(BaseModel):
    """
    Research results for an unknown software's API/integration capabilities.

    Used to determine if existing software supports automation via API,
    webhooks, or integration platforms (Zapier, Make, n8n).
    """
    name: str = Field(..., description="Software name as entered by user")
    estimated_api_score: int = Field(
        ...,
        ge=1,
        le=5,
        description=(
            "Estimated API openness score 1-5: "
            "5=Full REST API+webhooks+OAuth, "
            "4=Good API with some limitations, "
            "3=Basic API or limited endpoints, "
            "2=Zapier/Make only (no direct API), "
            "1=Closed system with no integrations"
        )
    )
    has_api: bool = Field(default=False, description="Has documented API")
    has_webhooks: bool = Field(default=False, description="Supports webhooks")
    has_zapier: bool = Field(default=False, description="Listed on Zapier")
    has_make: bool = Field(default=False, description="Listed on Make (Integromat)")
    has_oauth: bool = Field(default=False, description="Supports OAuth authentication")
    reasoning: str = Field(
        ...,
        description="Brief explanation of why this score was given"
    )
    source_urls: List[str] = Field(
        default_factory=list,
        description="URLs where information was found"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in the research results (0-1)"
    )
    researched_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this research was performed"
    )


class SoftwareResearchRequest(BaseModel):
    """Request to research unknown software."""
    name: str = Field(..., min_length=1, description="Software name to research")
    context: Optional[str] = Field(
        None,
        description="Optional context about the software type or industry"
    )


class SoftwareResearchResult(BaseModel):
    """Result of software research including capabilities and metadata."""
    name: str
    capabilities: Optional[SoftwareCapabilities] = None
    found: bool = Field(default=False, description="Whether research found results")
    error: Optional[str] = Field(None, description="Error message if research failed")
    cached: bool = Field(default=False, description="Whether result was from cache")


class ExistingStackItemResearched(BaseModel):
    """
    An existing stack item after research has been performed.

    Extends the basic ExistingStackItem with research results.
    """
    slug: str = Field(..., description="Vendor slug or custom identifier")
    source: str = Field(..., description="'selected' or 'free_text'")
    name: Optional[str] = Field(None, description="Display name")
    researched: bool = Field(default=False, description="Whether research was performed")
    api_score: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="API openness score from research or vendor DB"
    )
    reasoning: Optional[str] = Field(
        None,
        description="Explanation of API capabilities"
    )
    has_api: Optional[bool] = None
    has_webhooks: Optional[bool] = None
    has_zapier: Optional[bool] = None
