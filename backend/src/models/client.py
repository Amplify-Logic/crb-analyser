"""
Client Models
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class ClientBase(BaseModel):
    """Base client fields."""
    name: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., min_length=1, max_length=100)
    company_size: Optional[str] = Field(
        None,
        pattern="^(solo|2-10|11-50|51-200|201-500|500\\+|200\\+)$"
    )
    revenue_range: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_name: Optional[str] = Field(None, max_length=100)


class ClientCreate(ClientBase):
    """Request model for creating a client."""
    pass


class ClientUpdate(BaseModel):
    """Request model for updating a client."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    industry: Optional[str] = Field(None, min_length=1, max_length=100)
    company_size: Optional[str] = Field(
        None,
        pattern="^(solo|2-10|11-50|51-200|201-500|500\\+|200\\+)$"
    )
    revenue_range: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_name: Optional[str] = Field(None, max_length=100)


class ClientResponse(ClientBase):
    """Response model for a client."""
    id: str
    workspace_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClientListResponse(BaseModel):
    """Response model for client list."""
    data: List[ClientResponse]
    total: int


# Industry options for dropdowns
INDUSTRIES = [
    "marketing_agency",
    "creative_agency",
    "retail",
    "ecommerce",
    "technology",
    "tech_company",  # Frontend alias
    "music_entertainment",
    "music_company",  # Frontend alias
    "professional_services",
    "manufacturing",
    "healthcare",
    "education",
    "finance",
    "real_estate",
    "hospitality",
    "other"
]

COMPANY_SIZES = [
    {"value": "solo", "label": "Solo (1)"},
    {"value": "2-10", "label": "Micro (2-10)"},
    {"value": "11-50", "label": "Small (11-50)"},
    {"value": "51-200", "label": "Medium (51-200)"},
    {"value": "201-500", "label": "Large (201-500)"},
    {"value": "500+", "label": "Enterprise (500+)"}
]
