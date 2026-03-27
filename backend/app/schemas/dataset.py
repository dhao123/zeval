"""
Dataset download schemas.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DatasetPoolInfo(BaseModel):
    """Dataset pool information."""
    record_count: int = Field(default=0, description="Number of records")
    file_size: int = Field(default=0, description="File size in bytes")
    fields: List[str] = Field(default_factory=list, description="Available fields")
    updated_at: Optional[datetime] = Field(None, description="Last update time")


class DatasetInfoResponse(BaseModel):
    """Dataset metadata response."""
    category: str = Field(..., description="Category L4 name")
    versions: List[str] = Field(default_factory=list, description="Available versions")
    latest_version: str = Field(..., description="Latest version")
    formats: List[str] = Field(default_factory=lambda: ["json", "csv", "parquet"])
    pools: dict = Field(default_factory=dict, description="Training and evaluation pool info")


class DatasetVersionInfo(BaseModel):
    """Dataset version information."""
    version: str
    release_date: Optional[datetime]
    changelog: Optional[str]
    is_latest: bool


class DatasetVersionsResponse(BaseModel):
    """Dataset versions list response."""
    category: str
    versions: List[DatasetVersionInfo]


class DatasetDownloadRequest(BaseModel):
    """Dataset download request parameters."""
    category_l4: str = Field(..., description="Category L4 name")
    pool_type: str = Field(..., description="Pool type: training/evaluation")
    format: str = Field(default="json", description="File format: json/csv/parquet")
    version: Optional[str] = Field(None, description="Specific version, default latest")
    limit: Optional[int] = Field(None, ge=1, le=100000, description="Limit number of records")
    offset: Optional[int] = Field(0, ge=0, description="Offset for pagination")


class ExportTaskCreate(BaseModel):
    """Export task creation request."""
    category_l4: str = Field(..., description="Category L4 name")
    pool_type: str = Field(..., description="Pool type: training/evaluation")
    format: str = Field(default="json", description="File format")
    version: Optional[str] = Field(None, description="Specific version")


class ExportTaskResponse(BaseModel):
    """Export task response."""
    task_id: str
    status: str  # pending/running/completed/failed
    progress: int = Field(0, ge=0, le=100)
    file_size: int = Field(0)
    record_count: int = Field(0)
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExportTaskStatusResponse(BaseModel):
    """Export task status response."""
    task_id: str
    status: str
    progress: int
    estimated_time: Optional[int] = Field(None, description="Estimated seconds remaining")
    file_size: int = Field(0)
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None


class DownloadMetadata(BaseModel):
    """Downloaded dataset metadata."""
    category: str
    pool_type: str
    version: str
    record_count: int
    fields: List[str]
    format: str
    generated_at: datetime
    note: Optional[str] = None
