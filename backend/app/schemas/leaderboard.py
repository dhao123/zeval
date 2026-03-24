"""
Leaderboard schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LeaderboardEntry(BaseModel):
    """Leaderboard entry schema."""
    id: int
    eval_id: Optional[str] = None
    model_version: str
    prompt_version: str
    rag_version: str
    skill_version: str
    data_version: str
    category_l4: Optional[str] = None
    rank: int
    score: float
    metrics: Optional[Dict[str, Any]] = None
    is_public: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class LeaderboardFilter(BaseModel):
    """Leaderboard filter parameters."""
    model_version: Optional[str] = None
    prompt_version: Optional[str] = None
    rag_version: Optional[str] = None
    skill_version: Optional[str] = None
    data_version: Optional[str] = None
    category_l4: Optional[str] = None


class LeaderboardVersionOptions(BaseModel):
    """Available version options for leaderboard filtering."""
    model_versions: List[str]
    prompt_versions: List[str]
    rag_versions: List[str]
    skill_versions: List[str]
    data_versions: List[str]
    categories: List[str]


class LeaderboardComparisonRequest(BaseModel):
    """Request to compare multiple leaderboard entries."""
    eval_ids: List[str] = Field(..., min_length=2, max_length=5)


class LeaderboardComparisonResponse(BaseModel):
    """Leaderboard comparison response."""
    entries: List[LeaderboardEntry]
    comparison_chart: Dict[str, Any]
