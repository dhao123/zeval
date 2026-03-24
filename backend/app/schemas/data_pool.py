"""
Data Pool and Route Config schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DataPoolRead(BaseModel):
    """Data pool item read schema."""
    id: int
    pool_id: str
    data_type: str  # seed/synthetic
    source_id: str
    pool_type: str  # training/evaluation
    category_l4: str
    input: str
    gt: Optional[Dict[str, Any]] = None  # Hidden for evaluation pool
    route_batch_id: Optional[str] = None
    route_ratio: Optional[float] = None
    is_frozen: bool
    download_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DatasetDownloadRequest(BaseModel):
    """Dataset download request."""
    category_l4: Optional[str] = None
    pool_type: str = Field(..., pattern="^(training|evaluation)$")
    format: str = Field(default="excel", pattern="^(excel|json|csv)$")


class DatasetDownloadResponse(BaseModel):
    """Dataset download response."""
    download_url: str
    batch_id: str
    total_count: int
    expires_in: int = Field(default=3600, description="URL expiration time in seconds")


class RouteConfigRead(BaseModel):
    """Route config read schema."""
    id: int
    category_l4: str
    train_ratio: float = Field(..., ge=0, le=1)
    eval_ratio: float = Field(..., ge=0, le=1)
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RouteConfigUpdate(BaseModel):
    """Route config update schema."""
    train_ratio: float = Field(..., ge=0, le=1)
    eval_ratio: float = Field(..., ge=0, le=1)
    is_active: Optional[bool] = None


class RouteExecuteRequest(BaseModel):
    """Execute data routing request."""
    category_l4: Optional[str] = None  # None means all categories
    dry_run: bool = Field(default=False, description="Preview without actual routing")


class RouteExecuteResponse(BaseModel):
    """Route execution response."""
    batch_id: str
    status: str
    summary: Dict[str, Any]
    details: List[Dict[str, Any]]


class RouteBatchStatus(BaseModel):
    """Route batch status."""
    batch_id: str
    status: str
    total_categories: int
    total_cases: int
    train_count: int
    eval_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None


class DataPoolFilter(BaseModel):
    """Data pool filter parameters."""
    category_l4: Optional[str] = None
    pool_type: Optional[str] = Field(default=None, pattern="^(training|evaluation)$")
    data_type: Optional[str] = Field(default=None, pattern="^(seed|synthetic)$")
