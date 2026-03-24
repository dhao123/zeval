"""
Evaluation API routes.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db, require_algo_engineer
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse, PaginationParams, ResponseModel
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationFilter,
    EvaluationRead,
    EvaluationRetryRequest,
    EvaluationSubmit,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=PaginatedResponse[List[EvaluationRead]])
async def list_evaluations(
    status: Optional[str] = Query(None, pattern="^(pending|running|completed|failed)$"),
    category_l4: Optional[str] = Query(None),
    submitted_by: Optional[int] = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """List evaluation tasks."""
    # TODO: Implement
    return PaginatedResponse(code=0, message="success", data=[], pagination=None)


@router.get("/{eval_id}", response_model=ResponseModel[EvaluationRead])
async def get_evaluation(
    eval_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get evaluation by ID."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("", response_model=ResponseModel[EvaluationRead])
async def create_evaluation(
    data: EvaluationCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_algo_engineer),
):
    """Create evaluation task."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{eval_id}/submit", response_model=ResponseModel[EvaluationRead])
async def submit_evaluation_result(
    eval_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_algo_engineer),
):
    """Submit evaluation result file."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{eval_id}/retry", response_model=ResponseModel[EvaluationRead])
async def retry_evaluation(
    eval_id: str,
    request: EvaluationRetryRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_algo_engineer),
):
    """Retry evaluation."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{eval_id}/details")
async def get_evaluation_details(
    eval_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get evaluation details (per case results)."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")
