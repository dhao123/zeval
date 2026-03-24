"""
Category schemas for 4-level category management.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """Base category schema."""
    l1_name: str = Field(..., max_length=128, description="一级类目")
    l2_name: str = Field(..., max_length=128, description="二级类目")
    l3_name: str = Field(..., max_length=128, description="三级类目")
    l4_name: str = Field(..., max_length=128, description="四级类目")
    description: Optional[str] = Field(default=None, description="类目描述")


class CategoryCreate(CategoryBase):
    """Create category schema."""
    category_id: Optional[str] = Field(default=None, max_length=64, description="自定义ID")
    source: str = Field(default="manual", pattern="^(upload|auto|manual)$", description="来源")


class CategoryUpdate(BaseModel):
    """Update category schema."""
    description: Optional[str] = Field(default=None, description="类目描述")
    is_active: Optional[bool] = Field(default=None, description="是否激活")


class CategoryRead(CategoryBase):
    """Read category schema."""
    id: int = Field(..., description="数据库ID")
    category_id: str = Field(..., description="全局唯一ID")
    full_path: str = Field(..., description="完整路径")
    source: str = Field(..., description="来源")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # Statistics (optional, populated by API)
    stats: Optional["CategoryStats"] = Field(default=None, description="统计数据")
    
    class Config:
        from_attributes = True


class CategoryStats(BaseModel):
    """Category statistics."""
    draft_count: int = Field(default=0, description="初创池数量（草稿+已确认）")
    training_count: int = Field(default=0, description="训练池数量")
    evaluation_count: int = Field(default=0, description="评测池数量")
    total_confirmed: int = Field(default=0, description="总确认量（训练+评测）")


class CategoryListResponse(BaseModel):
    """Category list response."""
    items: List[CategoryRead]
    total: int


class CategoryFilter(BaseModel):
    """Category filter parameters."""
    l1_name: Optional[str] = Field(default=None, description="一级类目筛选")
    l2_name: Optional[str] = Field(default=None, description="二级类目筛选")
    l3_name: Optional[str] = Field(default=None, description="三级类目筛选")
    l4_name: Optional[str] = Field(default=None, description="四级类目筛选")
    keyword: Optional[str] = Field(default=None, description="关键词搜索")
    is_active: Optional[bool] = Field(default=None, description="是否激活")


class DashboardStats(BaseModel):
    """Dashboard statistics for all categories."""
    total_categories: int = Field(..., description="总类目数")
    total_draft: int = Field(..., description="初创池总数")
    total_training: int = Field(..., description="训练池总数")
    total_evaluation: int = Field(..., description="评测池总数")
    total_data: int = Field(..., description="总数据量")
    categories: List[CategoryRead] = Field(..., description="各类目详情")


# Update forward references
CategoryRead.model_rebuild()
