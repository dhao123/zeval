"""
Authentication middleware for SSO integration.

This middleware automatically checks authentication for all incoming requests
except those in the exempt list (health checks, docs, etc.).
"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.auth.dependencies import get_current_user_optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Paths that don't require authentication
EXEMPT_PATHS = {
    # Health check
    "/health",
    "/",
    # API docs
    "/docs",
    "/redoc",
    "/openapi.json",
    # API prefix docs
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
}

# Path prefixes that don't require authentication
EXEMPT_PREFIXES = [
    "/static/",
    "/api/v1/auth/login",  # Keep local login endpoint for backward compatibility
    "/api-security/",  # Security service proxy handles its own auth
]


def is_exempt_from_auth(path: str) -> bool:
    """
    Check if a path is exempt from authentication.
    
    Args:
        path: The request path
        
    Returns:
        True if path is exempt, False otherwise
    """
    # Check exact match
    if path in EXEMPT_PATHS:
        return True
    
    # Check prefix match
    for prefix in EXEMPT_PREFIXES:
        if path.startswith(prefix):
            return True
    
    return False


async def auth_middleware(request: Request, call_next):
    """
    Global authentication middleware.
    
    Validates authentication for all requests except exempt paths.
    Returns 401 if authentication is required but missing/invalid.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/handler in chain
        
    Returns:
        Response from next handler or 401 error response
    """
    path = request.url.path
    
    # Skip auth check for exempt paths
    if is_exempt_from_auth(path):
        return await call_next(request)
    
    try:
        # Check if user is authenticated
        user_info = await get_current_user_optional(request)
        
        if not user_info:
            # Return 401 for API requests
            if path.startswith("/api/"):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "code": 401,
                        "message": "未登录或登录已过期",
                        "data": None,
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )
            # For non-API requests, you might want to redirect or handle differently
            # For now, we return 401 as well
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "code": 401,
                    "message": "未登录或登录已过期",
                    "data": None,
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Store user info in request state for later use
        request.state.user = user_info
        
        # Continue processing
        response = await call_next(request)
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Authentication middleware error: {e}", exc_info=True)
        # Return 500 for unexpected errors with detailed message in debug mode
        error_msg = str(e) if settings.debug else "认证服务异常"
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": 500,
                "message": f"认证服务异常: {error_msg}",
                "data": None,
            },
        )
