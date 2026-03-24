"""
Category model for 4-level category management.
"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.synthetic import SyntheticData
    from app.models.data_pool import DataPool


class Category(Base):
    """Category model for managing 4-level classification system.
    
    Fields:
    - category_id: Global unique ID
    - l1_name ~ l4_name: 4-level category names
    - full_path: Full path like "L1/L2/L3/L4"
    - description: Optional description
    - source: Source of creation (upload/auto/manual)
    - is_active: Whether this category is active
    """
    
    __tablename__ = "categories"
    
    # Unique constraint on full category path
    __table_args__ = (
        UniqueConstraint('l1_name', 'l2_name', 'l3_name', 'l4_name', 
                        name='uix_category_full_path'),
    )
    
    # Global unique ID
    category_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True,
        comment="全局唯一ID，格式：cat_{uuid}"
    )
    
    # 4-level category names
    l1_name: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True,
        comment="一级类目"
    )
    l2_name: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True,
        comment="二级类目"
    )
    l3_name: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True,
        comment="三级类目"
    )
    l4_name: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True,
        comment="四级类目"
    )
    
    # Full path for quick display
    full_path: Mapped[str] = mapped_column(
        String(512), nullable=False,
        comment="完整路径：L1/L2/L3/L4"
    )
    
    # Optional fields
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="类目描述"
    )
    
    # Source tracking
    source: Mapped[str] = mapped_column(
        String(32), default="upload",
        comment="来源：upload(上传)/auto(自动推断)/manual(手动创建)"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        default=True,
        comment="是否激活"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间"
    )
    
    # Relationships
    synthetics: Mapped[list["SyntheticData"]] = relationship(
        "SyntheticData",
        primaryjoin="and_(Category.l1_name == foreign(SyntheticData.category_l1), "
                    "Category.l2_name == foreign(SyntheticData.category_l2), "
                    "Category.l3_name == foreign(SyntheticData.category_l3), "
                    "Category.l4_name == foreign(SyntheticData.category_l4))",
        viewonly=True
    )
