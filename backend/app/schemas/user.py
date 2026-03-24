"""
User and Role schemas.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# Role Schemas
class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., max_length=32)
    description: Optional[str] = Field(default=None, max_length=256)


class RoleCreate(RoleBase):
    """Role creation schema."""
    permissions: List[str] = Field(default_factory=list)


class RoleRead(RoleBase):
    """Role read schema."""
    id: int
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime
    
    class Config:
        from_attributes = True


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., max_length=64)
    email: EmailStr = Field(..., max_length=128)
    department: Optional[str] = Field(default=None, max_length=64)
    is_active: bool = Field(default=True)


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8, max_length=128)
    role_id: Optional[int] = None


class UserRead(UserBase):
    """User read schema."""
    id: int
    role: Optional[RoleRead] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """User update schema."""
    username: Optional[str] = Field(default=None, max_length=64)
    email: Optional[EmailStr] = Field(default=None, max_length=128)
    department: Optional[str] = Field(default=None, max_length=64)
    is_active: Optional[bool] = None
    role_id: Optional[int] = None


class UserPasswordUpdate(BaseModel):
    """User password update schema."""
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8, max_length=128)


# Auth Schemas
class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Token payload schema."""
    sub: Optional[str] = None
    type: Optional[str] = None
    exp: Optional[datetime] = None


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str
