"""
Standard document schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StandardBase(BaseModel):
    """Base standard schema."""
    name: str = Field(..., max_length=256, description="Standard name (e.g., GB/T 4219.1)")
    description: Optional[str] = Field(default=None, description="Standard description")


class StandardCreate(StandardBase):
    """Standard creation schema."""
    standard_id: Optional[str] = Field(default=None, max_length=64)


class StandardRead(StandardBase):
    """Standard read schema."""
    id: int
    standard_id: str
    file_path: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    parsed_content: Optional[str] = None
    status: str
    version: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StandardUpdate(BaseModel):
    """Standard update schema."""
    name: Optional[str] = Field(default=None, max_length=256)
    description: Optional[str] = None
    parsed_content: Optional[str] = None


class StandardParseResponse(BaseModel):
    """Standard parse task response."""
    task_id: str
    status: str
    message: str


class StandardFilter(BaseModel):
    """Standard filter parameters."""
    status: Optional[str] = Field(default=None, pattern="^(uploaded|parsed|active)$")
    keyword: Optional[str] = None
