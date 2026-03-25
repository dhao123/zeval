"""
Authentication module for SSO integration.
"""
from app.auth.dependencies import (
    CurrentUser,
    CurrentAdmin,
    OptionalUser,
    get_current_user,
    get_current_user_optional,
    require_admin,
)
from app.auth.middleware import auth_middleware

__all__ = [
    "CurrentUser",
    "CurrentAdmin", 
    "OptionalUser",
    "get_current_user",
    "get_current_user_optional",
    "require_admin",
    "auth_middleware",
]
