"""
Client Routes

CRUD operations for clients (businesses being audited).
All routes require authentication and workspace context.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.config.supabase_client import get_async_supabase
from src.middleware.auth import require_workspace, CurrentUser
from src.models.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientListResponse,
    INDUSTRIES,
    COMPANY_SIZES,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=ClientListResponse)
async def list_clients(
    current_user: CurrentUser = Depends(require_workspace),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None, min_length=1),
    industry: Optional[str] = Query(default=None),
):
    """
    List all clients in the workspace.

    Supports pagination and filtering by search term or industry.
    """
    try:
        supabase = await get_async_supabase()

        # Build query
        query = supabase.table("clients").select(
            "*", count="exact"
        ).eq("workspace_id", current_user.workspace_id)

        # Apply filters
        if search:
            query = query.ilike("name", f"%{search}%")

        if industry:
            query = query.eq("industry", industry)

        # Apply pagination and ordering
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        result = await query.execute()

        clients = [ClientResponse(**client) for client in result.data]

        return ClientListResponse(
            data=clients,
            total=result.count or len(clients)
        )

    except Exception as e:
        logger.error(f"List clients error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list clients"
        )


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    request: ClientCreate,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Create a new client.
    """
    try:
        supabase = await get_async_supabase()

        client_data = {
            **request.model_dump(exclude_none=True),
            "workspace_id": current_user.workspace_id,
        }

        result = await supabase.table("clients").insert(client_data).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create client"
            )

        logger.info(f"Client created: {result.data[0]['id']} by {current_user.email}")

        return ClientResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create client error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create client"
        )


@router.get("/industries")
async def get_industries():
    """
    Get list of available industries for dropdown.
    """
    return {"industries": INDUSTRIES}


@router.get("/company-sizes")
async def get_company_sizes():
    """
    Get list of company sizes for dropdown.
    """
    return {"company_sizes": COMPANY_SIZES}


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get a single client by ID.
    """
    try:
        supabase = await get_async_supabase()

        result = await supabase.table("clients").select("*").eq(
            "id", client_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )

        return ClientResponse(**result.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get client error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    request: ClientUpdate,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Update a client.
    """
    try:
        supabase = await get_async_supabase()

        # First verify client exists and belongs to workspace
        existing = await supabase.table("clients").select("id").eq(
            "id", client_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )

        # Update only provided fields
        update_data = request.model_dump(exclude_none=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        result = await supabase.table("clients").update(
            update_data
        ).eq("id", client_id).execute()

        logger.info(f"Client updated: {client_id} by {current_user.email}")

        return ClientResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update client error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update client"
        )


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Delete a client.

    This will also cascade delete all related audits.
    """
    try:
        supabase = await get_async_supabase()

        # First verify client exists and belongs to workspace
        existing = await supabase.table("clients").select("id").eq(
            "id", client_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )

        # Delete client (cascade deletes audits)
        await supabase.table("clients").delete().eq("id", client_id).execute()

        logger.info(f"Client deleted: {client_id} by {current_user.email}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete client error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete client"
        )


@router.get("/{client_id}/audits")
async def get_client_audits(
    client_id: str,
    current_user: CurrentUser = Depends(require_workspace),
):
    """
    Get all audits for a specific client.
    """
    try:
        supabase = await get_async_supabase()

        # Verify client belongs to workspace
        client_check = await supabase.table("clients").select("id").eq(
            "id", client_id
        ).eq(
            "workspace_id", current_user.workspace_id
        ).single().execute()

        if not client_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )

        # Get audits
        result = await supabase.table("audits").select("*").eq(
            "client_id", client_id
        ).order("created_at", desc=True).execute()

        return {"data": result.data, "total": len(result.data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get client audits error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get client audits"
        )
