"""
Authentication dependencies for SSO integration (AITest compatible).

This module provides dependencies for authenticating users via the external
security service (SSO). It validates the access_token from cookies or headers
by calling the security service's /accounts/username endpoint.
"""
import time
from typing import Annotated, Optional, Dict, Tuple

import httpx
from fastapi import Depends, HTTPException, Request, status

from app.auth.constants import auth_constants
from app.core.logging import get_logger

logger = get_logger(__name__)

# Simple in-memory cache for token validation results
# Format: {token_hash: (user_info, expiry_timestamp)}
_token_cache: Dict[str, Tuple[Optional[dict], float]] = {}
CACHE_TTL_SECONDS = 300  # Cache for 5 minutes


def _get_cached_user(token: str) -> Optional[Optional[dict]]:
    """Get cached user info if valid."""
    token_hash = hash(token) & 0xFFFFFFFF  # Simple hash
    if token_hash in _token_cache:
        user_info, expiry = _token_cache[token_hash]
        if time.time() < expiry:
            return user_info
        # Expired, remove from cache
        del _token_cache[token_hash]
    return None  # Not in cache or expired


def _cache_user(token: str, user_info: Optional[dict]):
    """Cache user info."""
    token_hash = hash(token) & 0xFFFFFFFF
    _token_cache[token_hash] = (user_info, time.time() + CACHE_TTL_SECONDS)


async def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extract authentication token from request.
    
    Token can be provided either via:
    1. Authorization header (Bearer token)
    2. access_token cookie
    
    Args:
        request: FastAPI request object
        
    Returns:
        The token string or None if not found
    """
    # Try Authorization header first
    authorization = request.headers.get("Authorization")
    if authorization:
        return authorization
    
    # Fallback to cookie
    access_token = request.cookies.get("access_token")
    if access_token:
        return f"Bearer {access_token}"
    
    return None


async def verify_token_with_security_service(token: str) -> Optional[dict]:
    """
    Verify token with the external security service.
    Uses in-memory cache to reduce external calls.
    
    Args:
        token: The JWT token to verify
        
    Returns:
        User info dict if valid, None otherwise
    """
    # Check cache first
    cached = _get_cached_user(token)
    if cached is not None:  # Found in cache (could be None for invalid token)
        logger.debug("Token found in cache")
        return cached
    
    try:
        url = auth_constants.get_security_host() + "/accounts/username"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, 
                headers={"Authorization": token},
                timeout=5.0  # Reduced timeout for faster failure
            )
        
        if response.status_code != 200:
            logger.debug(f"Token verification failed: {response.status_code}")
            _cache_user(token, None)  # Cache negative result
            return None
        
        user_info = response.json()
        
        # Normalize roleIds to integers
        role_ids = user_info.get("roleIds", [])
        user_info["roleIds"] = [int(rid) for rid in role_ids]
        
        # Add is_admin flag
        admin_role_id = auth_constants.admin_role_id
        user_info["is_admin"] = admin_role_id in user_info["roleIds"]
        
        # Cache the result
        _cache_user(token, user_info)
        
        return user_info
        
    except httpx.RequestError as e:
        logger.error(f"Network error verifying token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None


async def get_current_user_optional(request: Request) -> Optional[dict]:
    """
    Get current user info if authenticated, otherwise None.
    
    This is useful for endpoints that work with or without authentication.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User info dict or None
    """
    token = await get_token_from_request(request)
    if not token:
        return None
    
    return await verify_token_with_security_service(token)


async def get_current_user(request: Request) -> dict:
    """
    Get current authenticated user (required).
    
    Raises HTTPException 401 if user is not authenticated.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User info dict
        
    Raises:
        HTTPException: 401 if not authenticated
    """
    user_info = await get_current_user_optional(request)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_info


async def require_admin(request: Request) -> dict:
    """
    Require current user to be an admin.
    
    Raises HTTPException 401 if not authenticated, 403 if not admin.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User info dict
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin
    """
    user_info = await get_current_user(request)
    
    if not user_info.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    
    return user_info


# Type aliases for dependency injection
CurrentUser = Annotated[dict, Depends(get_current_user)]
CurrentAdmin = Annotated[dict, Depends(require_admin)]
OptionalUser = Annotated[Optional[dict], Depends(get_current_user_optional)]
