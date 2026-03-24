"""
Data Router (train/eval split) API routes.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db, require_admin
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse, PaginationParams, ResponseModel
from app.schemas.data_pool import (
    RouteBatchStatus,
    RouteConfigRead,
    RouteConfigUpdate,
    RouteExecuteRequest,
    RouteExecuteResponse,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/configs", response_model=PaginatedResponse[List[RouteConfigRead]])
async def list_route_configs(
    category_l4: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """List route configurations."""
    # TODO: Implement
    return PaginatedResponse(code=0, message="success", data=[], pagination=None)


@router.put("/configs/{category_l4}", response_model=ResponseModel[RouteConfigRead])
async def update_route_config(
    category_l4: str,
    data: RouteConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Update route configuration for a category."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/execute", response_model=ResponseModel[RouteExecuteResponse])
async def execute_routing(
    request: RouteExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Execute data routing (train/eval split)."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/batches/{batch_id}", response_model=ResponseModel[RouteBatchStatus])
async def get_batch_status(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get routing batch status."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")
