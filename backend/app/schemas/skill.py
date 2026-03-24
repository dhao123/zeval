"""
Skill/Rule schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    """Base skill schema."""
    skill_name: str = Field(..., max_length=128)
    category_l4: str = Field(..., max_length=128)
    rules: Dict[str, Any] = Field(..., description="Rule definitions")


class SkillCreate(SkillBase):
    """Skill creation schema."""
    skill_id: Optional[str] = Field(default=None, max_length=64)
    standard_id: Optional[str] = Field(default=None, max_length=64)
    prompt_template: Optional[str] = None


class SkillRead(SkillBase):
    """Skill read schema."""
    id: int
    skill_id: str
    standard_id: Optional[str] = None
    prompt_template: Optional[str] = None
    status: str
    version: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SkillUpdate(BaseModel):
    """Skill update schema."""
    skill_name: Optional[str] = Field(default=None, max_length=128)
    category_l4: Optional[str] = Field(default=None, max_length=128)
    rules: Optional[Dict[str, Any]] = None
    prompt_template: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(draft|official)$")


class SkillGenerateRequest(BaseModel):
    """Request to generate skills from standard."""
    standard_id: str
    category_l4: Optional[str] = None
    custom_prompt: Optional[str] = None


class SkillGenerateResponse(BaseModel):
    """Skill generation task response."""
    task_id: str
    status: str
    message: str


class SkillFilter(BaseModel):
    """Skill filter parameters."""
    category_l4: Optional[str] = None
    standard_id: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(draft|official)$")
