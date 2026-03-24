"""
Standard document API routes.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db, require_admin
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse, PaginationParams, ResponseModel
from app.schemas.standard import (
    StandardCreate,
    StandardFilter,
    StandardParseResponse,
    StandardRead,
    StandardUpdate,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=PaginatedResponse[List[StandardRead]])
async def list_standards(
    status: Optional[str] = Query(None, pattern="^(uploaded|parsed|active)$"),
    keyword: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """List standard documents."""
    # TODO: Implement service
    return PaginatedResponse(code=0, message="success", data=[], pagination=None)


@router.get("/{standard_id}", response_model=ResponseModel[StandardRead])
async def get_standard(
    standard_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get standard by ID."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/upload", response_model=ResponseModel[StandardRead])
async def upload_standard(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Upload standard document."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{standard_id}/parse", response_model=ResponseModel[StandardParseResponse])
async def parse_standard(
    standard_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Trigger standard document parsing."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/{standard_id}", response_model=ResponseModel[StandardRead])
async def update_standard(
    standard_id: str,
    data: StandardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Update standard."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/{standard_id}", response_model=ResponseModel[dict])
async def delete_standard(
    standard_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Delete standard."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")
