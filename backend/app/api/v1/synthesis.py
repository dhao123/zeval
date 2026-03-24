"""
Data synthesis API routes.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db, require_admin
from app.core.logging import get_logger
from app.schemas.common import ResponseModel
from app.schemas.synthetic import (
    SynthesisTaskCreate,
    SynthesisTaskResponse,
    SynthesisTaskStatus,
)

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=ResponseModel[SynthesisTaskResponse])
async def create_synthesis_task(
    request: SynthesisTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Create data synthesis task."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{task_id}/status", response_model=ResponseModel[SynthesisTaskStatus])
async def get_synthesis_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get synthesis task status."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{task_id}/cancel", response_model=ResponseModel[dict])
async def cancel_synthesis_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Cancel synthesis task."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")
