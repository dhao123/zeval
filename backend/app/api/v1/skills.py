"""
Skill/Rule API routes.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db, require_admin
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse, PaginationParams, ResponseModel
from app.schemas.skill import (
    SkillCreate,
    SkillFilter,
    SkillGenerateRequest,
    SkillGenerateResponse,
    SkillRead,
    SkillUpdate,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=PaginatedResponse[List[SkillRead]])
async def list_skills(
    category_l4: Optional[str] = Query(None),
    standard_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, pattern="^(draft|official)$"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """List skills."""
    # TODO: Implement
    return PaginatedResponse(code=0, message="success", data=[], pagination=None)


@router.get("/{skill_id}", response_model=ResponseModel[SkillRead])
async def get_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get skill by ID."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/generate", response_model=ResponseModel[SkillGenerateResponse])
async def generate_skills(
    request: SkillGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Generate skills from standard document."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("", response_model=ResponseModel[SkillRead])
async def create_skill(
    data: SkillCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Create skill manually."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/{skill_id}", response_model=ResponseModel[SkillRead])
async def update_skill(
    skill_id: str,
    data: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Update skill."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/{skill_id}", response_model=ResponseModel[dict])
async def delete_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Delete skill."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")
