"""
User management API routes.
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db, require_admin
from app.auth.dependencies import CurrentUser, get_current_user_optional
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse, PaginationParams, ResponseModel
from app.schemas.user import UserCreate, UserRead, UserUpdate

logger = get_logger(__name__)
router = APIRouter()


@router.get("/me", response_model=ResponseModel[dict])
async def get_current_user_info(current_user: CurrentUser):
    """
    Get current authenticated user information from SSO.
    
    Returns the user info from the security service including:
    - id: User ID
    - username: Login username
    - nickname: Display name
    - email: User email
    - roleIds: List of role IDs
    - is_admin: Whether user has admin role
    """
    return ResponseModel(
        code=0,
        message="success",
        data=current_user
    )


@router.get("/sso/status", response_model=ResponseModel[dict])
async def get_sso_status():
    """
    Get SSO authentication status.
    
    Returns whether SSO is enabled and the admin role ID.
    """
    return ResponseModel(
        code=0,
        message="success",
        data={
            "sso_enabled": settings.sso_enabled,
            "admin_role_id": settings.admin_role_id,
        }
    )


@router.get("", response_model=PaginatedResponse[List[UserRead]])
async def list_users(
    is_active: Optional[bool] = Query(None),
    role_id: Optional[int] = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """List users."""
    # TODO: Implement
    return PaginatedResponse(code=0, message="success", data=[], pagination=None)


@router.get("/{user_id}", response_model=ResponseModel[UserRead])
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Get user by ID."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("", response_model=ResponseModel[UserRead])
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Create user."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/{user_id}", response_model=ResponseModel[UserRead])
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Update user."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.patch("/{user_id}/status", response_model=ResponseModel[UserRead])
async def update_user_status(
    user_id: int,
    is_active: bool,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Update user status (activate/deactivate)."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/{user_id}", response_model=ResponseModel[dict])
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """Delete user."""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")
