"""
Evaluation schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EvaluationBase(BaseModel):
    """Base evaluation schema."""
    eval_name: str = Field(..., max_length=128)
    model_version: Optional[str] = Field(default=None, max_length=64)
    prompt_version: Optional[str] = Field(default=None, max_length=64)
    rag_version: Optional[str] = Field(default=None, max_length=64)
    skill_version: Optional[str] = Field(default=None, max_length=64)
    data_version: Optional[str] = Field(default=None, max_length=64)
    category_l4: Optional[str] = Field(default=None, max_length=128)


class EvaluationCreate(EvaluationBase):
    """Evaluation creation schema."""
    pass


class EvaluationRead(EvaluationBase):
    """Evaluation read schema."""
    id: int
    eval_id: str
    status: str  # pending/running/completed/failed
    result_file_path: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    score: Optional[float] = None
    submitted_by: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class EvaluationSubmit(BaseModel):
    """Submit evaluation results."""
    # Results will be uploaded as file, this is metadata
    file_format: str = Field(default="json", pattern="^(json|excel)$")


class EvaluationMetrics(BaseModel):
    """Evaluation metrics."""
    accuracy: float = Field(..., ge=0, le=1)
    precision: float = Field(..., ge=0, le=1)
    recall: float = Field(..., ge=0, le=1)
    f1_score: float = Field(..., ge=0, le=1)
    field_accuracy: Optional[Dict[str, float]] = None


class EvaluationDetailRead(BaseModel):
    """Evaluation detail read schema."""
    id: int
    case_id: str
    input: str
    prediction: Dict[str, Any]
    ground_truth: Dict[str, Any]
    field_scores: Optional[Dict[str, Any]] = None
    is_correct: Optional[bool] = None
    error_type: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class EvaluationFilter(BaseModel):
    """Evaluation filter parameters."""
    status: Optional[str] = Field(default=None, pattern="^(pending|running|completed|failed)$")
    category_l4: Optional[str] = None
    submitted_by: Optional[int] = None


class EvaluationRetryRequest(BaseModel):
    """Retry evaluation request."""
    reason: Optional[str] = None
