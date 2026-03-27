"""
Synthetic data model (Draft Pool).
"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.seed import Seed
    from app.models.skill import Skill
    from app.models.standard import Standard
    from app.models.user import User


class SyntheticData(Base):
    """Synthetic data model for draft pool.
    
    字段设计与Seed同构，便于统一处理：
    - id: 主键
    - synthetic_id: 全局唯一ID (与seed_id同格式)
    - input: 输入文本
    - gt: 标准答案 (Ground Truth)
    - category_l4: 四级类目
    - category_path: 类目路径
    - status: 状态 (draft/confirmed/rejected)
    - hash: SHA256哈希 (去重用)
    - version: 版本号
    - created_by/confirmed_by: 创建/确认用户
    - created_at/updated_at: 时间戳
    """
    
    __tablename__ = "synthetic_data"
    
    # 主键和全局唯一ID
    synthetic_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True,
        comment="全局唯一ID，格式：syn_{uuid}"
    )
    
    # 核心数据字段 (与Seed同构)
    input: Mapped[str] = mapped_column(Text, nullable=False, comment="输入文本")
    gt: Mapped[dict] = mapped_column(JSON, nullable=False, comment="标准答案")
    
    # 四级类目体系
    category_l1: Mapped[Optional[str]] = mapped_column(String(128), index=True, comment="一级类目")
    category_l2: Mapped[Optional[str]] = mapped_column(String(128), index=True, comment="二级类目")
    category_l3: Mapped[Optional[str]] = mapped_column(String(128), index=True, comment="三级类目")
    category_l4: Mapped[Optional[str]] = mapped_column(String(128), index=True, comment="四级类目")
    category_path: Mapped[Optional[str]] = mapped_column(String(512), comment="类目路径")
    
    # 状态管理
    status: Mapped[str] = mapped_column(
        String(32), default="draft", index=True,
        comment="状态：draft(草稿)/confirmed(已确认)/rejected(已拒绝)"
    )
    hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="SHA256哈希（去重）")
    version: Mapped[str] = mapped_column(String(32), default="1.0", comment="版本号")
    
    # 合成相关字段
    difficulty: Mapped[str] = mapped_column(String(32), default="medium", comment="难度：low/medium/high/ultra")
    synthesis_params: Mapped[Optional[dict]] = mapped_column(JSON, comment="合成参数")
    ai_check_result: Mapped[Optional[dict]] = mapped_column(JSON, comment="AI Double Check结果")
    ai_check_passed: Mapped[bool] = mapped_column(Boolean, default=False, comment="质检是否通过")
    
    # 血缘追踪
    seed_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("seeds.seed_id"), index=True, comment="关联的种子ID"
    )
    standard_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("standards.standard_id"), comment="关联的国标ID"
    )
    skill_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("skills.skill_id"), comment="关联的Skill ID"
    )
    
    # 用户追踪
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), comment="创建者")
    confirmed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), comment="确认者")
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), comment="确认时间")
    
    # 分流追踪 (确认后填写)
    route_batch_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, comment="分流批次ID")
    
    # 上传批次追踪
    upload_batch_id: Mapped[Optional[str]] = mapped_column(
        String(64), 
        index=True, 
        comment="上传批次ID（关联upload_batches）"
    )
    
    # Relationships
    seed: Mapped[Optional["Seed"]] = relationship("Seed", back_populates="synthetics")
    standard: Mapped[Optional["Standard"]] = relationship("Standard", back_populates="synthetics")
    skill: Mapped[Optional["Skill"]] = relationship("Skill", back_populates="synthetics")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])
    confirmer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[confirmed_by])
