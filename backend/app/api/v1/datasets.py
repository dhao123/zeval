"""
Dataset (training/evaluation) API routes.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db, require_algo_engineer
from app.core.logging import get_logger
from app.schemas.common import ResponseModel
from app.schemas.data_pool import DatasetDownloadRequest, DatasetDownloadResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get("/training/download", response_model=ResponseModel[DatasetDownloadResponse])
async def download_training_set(
    category_l4: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_algo_engineer),
):
    """Download training dataset (with GT)."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/evaluation/download", response_model=ResponseModel[DatasetDownloadResponse])
async def download_evaluation_set(
    category_l4: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_algo_engineer),
):
    """Download evaluation dataset (input only, no GT)."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")
