"""
Evaluation models.
"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Evaluation(Base):
    """Evaluation task model."""
    
    __tablename__ = "evaluations"
    
    eval_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    eval_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(64))
    prompt_version: Mapped[Optional[str]] = mapped_column(String(64))
    rag_version: Mapped[Optional[str]] = mapped_column(String(64))
    skill_version: Mapped[Optional[str]] = mapped_column(String(64))
    data_version: Mapped[Optional[str]] = mapped_column(String(64))
    category_l4: Mapped[Optional[str]] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    result_file_path: Mapped[Optional[str]] = mapped_column(String(512))
    metrics: Mapped[Optional[dict]] = mapped_column(JSON)
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Foreign keys
    submitted_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Relationships
    submitter: Mapped["User"] = relationship("User", back_populates="evaluations")
    details: Mapped[List["EvaluationDetail"]] = relationship(
        "EvaluationDetail", back_populates="evaluation"
    )


class EvaluationDetail(Base):
    """Evaluation detail (per case result)."""
    
    __tablename__ = "evaluation_details"
    
    eval_id: Mapped[str] = mapped_column(
        ForeignKey("evaluations.eval_id"), index=True, nullable=False
    )
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    input: Mapped[str] = mapped_column(Text, nullable=False)
    prediction: Mapped[dict] = mapped_column(JSON, nullable=False)
    ground_truth: Mapped[dict] = mapped_column(JSON, nullable=False)
    field_scores: Mapped[Optional[dict]] = mapped_column(JSON)
    is_correct: Mapped[Optional[bool]] = mapped_column()
    error_type: Mapped[Optional[str]] = mapped_column(String(64))
    
    # Relationships
    evaluation: Mapped["Evaluation"] = relationship(
        "Evaluation", back_populates="details"
    )
