"""
Leaderboard and Report models.
"""
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.evaluation import Evaluation


class Leaderboard(Base):
    """Leaderboard ranking model."""
    
    __tablename__ = "leaderboard"
    
    eval_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("evaluations.eval_id"), index=True
    )
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rag_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    skill_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    data_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    category_l4: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    rank: Mapped[int] = mapped_column(Integer, index=True)
    score: Mapped[float] = mapped_column(Numeric(5, 4))
    metrics: Mapped[Optional[dict]] = mapped_column(JSON)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    evaluation: Mapped[Optional["Evaluation"]] = relationship("Evaluation")


class Report(Base):
    """Evaluation report model."""
    
    __tablename__ = "reports"
    
    report_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    eval_id: Mapped[str] = mapped_column(ForeignKey("evaluations.eval_id"), index=True)
    report_type: Mapped[str] = mapped_column(String(32), nullable=False)  # overview/attribute/badcase/trend
    report_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    chart_configs: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Relationships
    evaluation: Mapped["Evaluation"] = relationship("Evaluation")
