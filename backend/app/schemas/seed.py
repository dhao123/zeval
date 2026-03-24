"""
Seed data schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SeedBase(BaseModel):
    """Base seed schema."""
    input: str = Field(..., description="User input material description")
    gt: Dict[str, Any] = Field(..., description="Ground truth (attribute key-value pairs)")
    category_l4: str = Field(..., max_length=128, description="Level 4 category")
    category_path: Optional[str] = Field(default=None, max_length=512, description="Category path")


class SeedCreate(SeedBase):
    """Seed creation schema."""
    seed_id: Optional[str] = Field(default=None, max_length=64)


class SeedRead(SeedBase):
    """Seed read schema."""
    id: int
    seed_id: str
    status: str
    hash: str
    version: str
    created_by: Optional[int] = None
    confirmed_by: Optional[int] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SeedUpdate(BaseModel):
    """Seed update schema."""
    input: Optional[str] = None
    gt: Optional[Dict[str, Any]] = None
    category_l4: Optional[str] = Field(default=None, max_length=128)
    category_path: Optional[str] = Field(default=None, max_length=512)


class SeedUploadItem(SeedBase):
    """Single seed item for batch upload."""
    pass


class SeedUploadResponse(BaseModel):
    """Seed batch upload response."""
    total: int = Field(..., description="Total items processed")
    success: int = Field(..., description="Successfully created")
    duplicated: int = Field(..., description="Duplicated (skipped)")
    failed: int = Field(..., description="Failed")
    details: List[Dict[str, Any]] = Field(default_factory=list)


class SeedFilter(BaseModel):
    """Seed filter parameters."""
    category_l4: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(draft|official)$")
    keyword: Optional[str] = None
