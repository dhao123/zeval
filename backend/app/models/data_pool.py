"""
Data Pool and Route Config models.
"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class DataPool(Base):
    """Data Pool model (Training + Evaluation)."""
    
    __tablename__ = "data_pool"
    
    pool_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    data_type: Mapped[str] = mapped_column(String(32), nullable=False)  # seed/synthetic
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    pool_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # training/evaluation
    category_l4: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    input: Mapped[str] = mapped_column(Text, nullable=False)
    gt: Mapped[Optional[dict]] = mapped_column(JSON)  # Hidden for evaluation pool
    route_batch_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    route_ratio: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False)
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 用户追踪（用于数据隔离）
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), comment="创建者/上传者")
    
    # Relationships
    creator: Mapped[Optional["User"]] = relationship("User")


class RouteConfig(Base):
    """Route configuration for train/eval split."""
    
    __tablename__ = "route_configs"
    
    category_l4: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    train_ratio: Mapped[float] = mapped_column(Numeric(3, 2), default=0.5)
    eval_ratio: Mapped[float] = mapped_column(Numeric(3, 2), default=0.5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class DownloadLog(Base):
    """Download log for tracking case popularity."""
    
    __tablename__ = "download_logs"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    download_type: Mapped[str] = mapped_column(String(32), nullable=False)  # training/evaluation
    batch_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    category_l4: Mapped[Optional[str]] = mapped_column(String(128))
    case_count: Mapped[Optional[int]] = mapped_column(Integer)
    case_ids: Mapped[Optional[list]] = mapped_column(JSON)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
