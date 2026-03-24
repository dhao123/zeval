"""
Reports and Analytics API routes.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.core.logging import get_logger
from app.schemas.common import ResponseModel
from app.schemas.report import ReportExport, ReportRead

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{eval_id}", response_model=ResponseModel[ReportRead])
async def get_report(
    eval_id: str,
    report_type: Optional[str] = Query(None, pattern="^(overview|attribute|badcase|trend)$"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get evaluation report."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{eval_id}/export")
async def export_report(
    eval_id: str,
    format: str = Query(..., pattern="^(pdf|excel)$"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Export report to PDF or Excel."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/analytics/overview")
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get data overview analytics."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/analytics/badcases")
async def get_analytics_badcases(
    eval_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get badcase analysis."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/analytics/trends")
async def get_analytics_trends(
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get trend analysis."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/analytics/long-tail")
async def get_analytics_long_tail(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get long-tail distribution analysis."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")
