"""
Upload Batch Model for tracking file uploads.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UploadBatch(Base):
    """上传批次任务模型"""
    
    __tablename__ = "upload_batches"
    
    # 批次基本信息
    batch_id: Mapped[str] = mapped_column(
        String(64), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="批次唯一ID"
    )
    
    # 文件信息
    file_name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="原始文件名"
    )
    file_url: Mapped[str] = mapped_column(
        String(1024), 
        nullable=False,
        comment="OSS文件访问URL"
    )
    object_key: Mapped[str] = mapped_column(
        String(512), 
        nullable=False,
        comment="OSS对象存储键"
    )
    file_size: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="文件大小(字节)"
    )
    
    # 上传人信息
    owner_id: Mapped[Optional[str]] = mapped_column(
        String(64), 
        index=True,
        comment="上传人ID"
    )
    owner_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        comment="上传人姓名"
    )
    
    # 数据统计
    record_count: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="包含的case数量"
    )
    success_count: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="成功导入数量"
    )
    fail_count: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="失败数量"
    )
    
    # 状态
    status: Mapped[str] = mapped_column(
        String(32), 
        default="processing",
        comment="状态: processing/completed/failed"
    )
    
    # 备注/错误信息
    remark: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="备注或错误信息"
    )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "file_name": self.file_name,
            "file_url": self.file_url,
            "object_key": self.object_key,
            "file_size": self.file_size,
            "owner_id": self.owner_id,
            "owner_name": self.owner_name,
            "record_count": self.record_count,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "status": self.status,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
