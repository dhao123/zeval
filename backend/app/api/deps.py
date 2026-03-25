"""
API dependencies (AITest compatible).

Uses SSO authentication only, no local database user lookup.
"""
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_session
from app.core.logging import get_logger
# Import SSO dependencies (AITest compatible)
from app.auth.dependencies import (
    get_current_user as get_sso_user,
    get_current_user_optional as get_sso_user_optional,
    require_admin as require_sso_admin,
)

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in get_async_session():
        yield session


# Re-export SSO dependencies for API use
get_current_user = get_sso_user
get_current_user_optional = get_sso_user_optional
require_admin = require_sso_admin


# Type alias for dependency injection
CurrentUser = Optional[dict]  # SSO user info dict


# For backward compatibility - these now just check SSO auth
async def get_current_active_user(
    user: dict = Depends(get_sso_user)
) -> dict:
    """Get current active user (SSO only)."""
    # SSO users are always active
    return user


class RoleChecker:
    """Role-based access control checker (SSO only)."""
    
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self,
        user: dict = Depends(get_sso_user),
    ) -> dict:
        """Check if user has required role."""
        # Get role from SSO user info
        role_ids = user.get("roleIds", [])
        
        # For now, allow all authenticated users
        # In production, map roleIds to role names
        return user


# Predefined role dependencies (now just check auth)
require_data_engineer = get_sso_user
require_algo_engineer = get_sso_user
require_pm = get_sso_user
