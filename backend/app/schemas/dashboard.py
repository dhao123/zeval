"""
Dashboard schemas for data visualization.
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DashboardOverview(BaseModel):
    """Dashboard overview statistics."""
    total_categories: int = Field(..., description="总类目数")
    total_draft: int = Field(..., description="初创池草稿态数量")
    total_training: int = Field(..., description="训练池数量")
    total_evaluation: int = Field(..., description="评测池数量")
    total_data: int = Field(..., description="总数据量")


class TrendDataPoint(BaseModel):
    """Single data point for trend chart."""
    date: str = Field(..., description="日期 (YYYY-MM-DD)")
    total: int = Field(..., description="总数据量")
    draft: int = Field(..., description="初创池草稿态数量")
    training: int = Field(..., description="训练池数量")
    evaluation: int = Field(..., description="评测池数量")


class TrendSummary(BaseModel):
    """Summary statistics for trend data."""
    total_current: int = Field(..., description="当前总数据量")
    draft_current: int = Field(..., description="当前初创池草稿态数量")
    training_current: int = Field(..., description="当前训练池数量")
    evaluation_current: int = Field(..., description="当前评测池数量")


class TrendResponse(BaseModel):
    """Trend data response."""
    trend: List[TrendDataPoint] = Field(..., description="趋势数据列表")
    summary: Dict[str, int] = Field(..., description="当前汇总数据")


class TrendQuery(BaseModel):
    """Query parameters for trend API."""
    days: int = Field(default=7, ge=1, le=90, description="时间范围天数")
    start_date: Optional[date] = Field(default=None, description="开始日期")
    end_date: Optional[date] = Field(default=None, description="结束日期")
    category_l1: Optional[str] = Field(default=None, description="一级类目")
    category_l2: Optional[str] = Field(default=None, description="二级类目")
    category_l3: Optional[str] = Field(default=None, description="三级类目")
    category_l4: Optional[str] = Field(default=None, description="四级类目")
