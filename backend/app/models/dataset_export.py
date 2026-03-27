"""
Dataset export models for download functionality.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DatasetVersion(Base):
    """Dataset version model for tracking dataset snapshots."""
    
    __tablename__ = "dataset_versions"
    
    version_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    category_l4: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    pool_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # training/evaluation
    format: Mapped[str] = mapped_column(String(32), nullable=False, default="json")  # json/csv/parquet
    file_size: Mapped[int] = mapped_column(Integer, default=0)  # bytes
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    checksum: Mapped[Optional[str]] = mapped_column(String(64))  # MD5
    file_path: Mapped[Optional[str]] = mapped_column(String(512))  # Storage path
    download_url: Mapped[Optional[str]] = mapped_column(String(1024))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_latest: Mapped[bool] = mapped_column(default=False)
    changelog: Mapped[Optional[str]] = mapped_column(Text)
    
    # Composite unique constraint
    __table_args__ = (
        # Ensure version uniqueness per category/pool/format
        {'sqlite_autoincrement': True},
    )


class ExportTask(Base):
    """Async export task model for large file generation."""
    
    __tablename__ = "export_tasks"
    
    task_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending/running/completed/failed
    category_l4: Mapped[str] = mapped_column(String(128), nullable=False)
    pool_type: Mapped[str] = mapped_column(String(32), nullable=False)
    format: Mapped[str] = mapped_column(String(32), default="json")
    version: Mapped[Optional[str]] = mapped_column(String(32))
    file_path: Mapped[Optional[str]] = mapped_column(String(512))
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Store params as JSON for flexibility
    params: Mapped[Optional[dict]] = mapped_column(JSON)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "category_l4": self.category_l4,
            "pool_type": self.pool_type,
            "format": self.format,
            "version": self.version,
            "progress": self.progress,
            "file_size": self.file_size,
            "record_count": self.record_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "error_message": self.error_message,
        }


class DownloadLog(Base):
    """Audit log for dataset downloads."""
    
    __tablename__ = "download_logs"
    
    user_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(128))
    category_l4: Mapped[str] = mapped_column(String(128), nullable=False)
    pool_type: Mapped[str] = mapped_column(String(32), nullable=False)
    format: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[Optional[str]] = mapped_column(String(32))
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
