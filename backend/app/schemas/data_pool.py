"""
Data Pool schemas for training and evaluation pools.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DataPoolBase(BaseModel):
    """Base data pool schema."""
    input: str = Field(..., description="输入文本")
    category_l4: str = Field(..., description="四级类目")


class DataPoolRead(DataPoolBase):
    """Data pool read schema."""
    id: int = Field(..., description="数据库ID")
    pool_id: str = Field(..., description="池子数据ID")
    data_type: str = Field(..., description="数据类型：seed/synthetic")
    source_id: str = Field(..., description="来源数据ID")
    pool_type: str = Field(..., description="池子类型：training/evaluation")
    
    # Category info (from synthetic_data)
    category_l1: Optional[str] = Field(default=None, description="一级类目")
    category_l2: Optional[str] = Field(default=None, description="二级类目")
    category_l3: Optional[str] = Field(default=None, description="三级类目")
    
    # GT handling:
    # - Training pool: GT is visible
    # - Evaluation pool: GT is hidden (for scoring only)
    gt: Optional[Dict[str, Any]] = Field(default=None, description="标准答案")
    
    # Routing info
    route_batch_id: Optional[str] = Field(default=None, description="分流批次ID")
    route_ratio: Optional[float] = Field(default=None, description="分流比例")
    
    # Status
    is_frozen: bool = Field(default=False, description="是否冻结")
    download_count: int = Field(default=0, description="下载次数")
    
    # User info (from upload_batches via synthetic_data)
    owner_name: Optional[str] = Field(default=None, description="数据Owner名称")
    
    # Timestamps
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DataPoolFilter(BaseModel):
    """Data pool filter parameters."""
    category_l4: Optional[str] = Field(default=None, description="四级类目")
    keyword: Optional[str] = Field(default=None, description="关键词搜索")
    pool_type: Optional[str] = Field(default=None, pattern="^(training|evaluation)$")


class RouteConfigRead(BaseModel):
    """Route config read schema."""
    id: int
    category_l4: str
    train_ratio: float
    eval_ratio: float
    is_active: bool
    
    class Config:
        from_attributes = True


class RouteConfigUpdate(BaseModel):
    """Route config update schema."""
    train_ratio: Optional[float] = Field(default=None, ge=0, le=1)
    eval_ratio: Optional[float] = Field(default=None, ge=0, le=1)
    is_active: Optional[bool] = None


class DatasetDownloadRequest(BaseModel):
    """Dataset download request."""
    category_l4: Optional[str] = Field(default=None, description="四级类目筛选")
    format: str = Field(default="json", pattern="^(json|csv|xlsx)$", description="下载格式")


class DatasetDownloadResponse(BaseModel):
    """Dataset download response."""
    download_url: str = Field(..., description="下载链接")
    filename: str = Field(..., description="文件名")
    record_count: int = Field(..., description="记录数")
    expires_at: datetime = Field(..., description="过期时间")


class RouteExecuteRequest(BaseModel):
    """Route execution request."""
    category_l4: Optional[str] = Field(default=None, description="指定类目执行分流")
    synthetic_ids: Optional[List[str]] = Field(default=None, description="指定数据ID列表")


class RouteExecuteResponse(BaseModel):
    """Route execution response."""
    success: bool = Field(..., description="是否成功")
    batch_id: Optional[str] = Field(default=None, description="分流批次ID")
    total: int = Field(..., description="总处理数")
    training: int = Field(..., description="训练池数量")
    evaluation: int = Field(..., description="评测池数量")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")


class RouteBatchStatus(BaseModel):
    """Route batch status."""
    batch_id: str = Field(..., description="批次ID")
    total: int = Field(..., description="总数")
    training: int = Field(..., description="训练池数量")
    evaluation: int = Field(..., description="评测池数量")
    categories: Dict[str, Any] = Field(..., description="各类目统计")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
