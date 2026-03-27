"""
Leaderboard API routes.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db, require_data_engineer
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse, PaginationParams, ResponseModel
from app.schemas.leaderboard import (
    LeaderboardComparisonRequest,
    LeaderboardComparisonResponse,
    LeaderboardEntry,
    LeaderboardFilter,
    LeaderboardVersionOptions,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=PaginatedResponse[List[LeaderboardEntry]])
async def get_leaderboard(
    model_version: Optional[str] = Query(None),
    prompt_version: Optional[str] = Query(None),
    rag_version: Optional[str] = Query(None),
    skill_version: Optional[str] = Query(None),
    data_version: Optional[str] = Query(None),
    category_l4: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_data_engineer),
):
    """Get leaderboard rankings."""
    # TODO: Implement
    return PaginatedResponse(code=0, message="success", data=[], pagination=None)


@router.get("/{category}", response_model=PaginatedResponse[List[LeaderboardEntry]])
async def get_leaderboard_by_category(
    category: str,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_data_engineer),
):
    """Get leaderboard for specific category."""
    # TODO: Implement
    return PaginatedResponse(code=0, message="success", data=[], pagination=None)


@router.post("/filter", response_model=PaginatedResponse[List[LeaderboardEntry]])
async def filter_leaderboard(
    filter_params: LeaderboardFilter,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_data_engineer),
):
    """Filter leaderboard by multiple dimensions."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/versions/options", response_model=ResponseModel[LeaderboardVersionOptions])
async def get_version_options(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_data_engineer),
):
    """Get available version options for filtering."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/compare", response_model=ResponseModel[LeaderboardComparisonResponse])
async def compare_entries(
    request: LeaderboardComparisonRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_data_engineer),
):
    """Compare multiple leaderboard entries."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")
