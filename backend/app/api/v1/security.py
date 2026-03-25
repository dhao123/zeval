"""
Security service proxy endpoints (AITest compatible).

These endpoints proxy to the company SSO service for user info.
"""
from fastapi import APIRouter, HTTPException, Request, status

from app.auth.dependencies import get_current_user_optional
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/accounts/username")
async def get_current_username(request: Request):
    """Get current authenticated user info from SSO (AITest compatible).
    
    This endpoint uses the same logic as the auth middleware
    to validate the token and get user information.
    
    Returns:
        User info including name, email, roleIds, etc.
        
    Raises:
        HTTPException: 401 if not authenticated
    """
    # Use existing auth dependency (handles token validation)
    user_info = await get_current_user_optional(request)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Ensure required fields exist (AITest compatible)
    if "roleIds" not in user_info:
        user_info["roleIds"] = []
    if "is_admin" not in user_info:
        user_info["is_admin"] = False
        
    return user_info


@router.get("/accounts/me")
async def get_current_user_me(request: Request):
    """Get current user basic info (AITest compatible).
    
    Returns just the username for simpler checks.
    """
    # Reuse the same logic as /accounts/username
    user_info = await get_current_username(request)
    return {"name": user_info.get("name") or user_info.get("username")}
