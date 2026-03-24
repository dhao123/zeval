"""
Common schemas for API responses.
"""
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginationInfo(BaseModel):
    """Pagination information."""
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total items count")
    pages: int = Field(..., description="Total pages count")


class ResponseModel(BaseModel, Generic[T]):
    """Standard API response model."""
    code: int = Field(default=0, description="Response code, 0 means success")
    message: str = Field(default="success", description="Response message")
    data: Optional[T] = Field(default=None, description="Response data")


class PaginatedResponse(ResponseModel[T]):
    """Paginated API response model."""
    pagination: Optional[PaginationInfo] = Field(
        default=None, description="Pagination information"
    )


class ErrorResponse(BaseModel):
    """Error response model."""
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    detail: Optional[Any] = Field(default=None, description="Error detail")
