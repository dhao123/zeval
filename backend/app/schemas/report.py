"""
Report schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReportRead(BaseModel):
    """Report read schema."""
    id: int
    report_id: str
    eval_id: str
    report_type: str  # overview/attribute/badcase/trend
    report_data: Dict[str, Any]
    chart_configs: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReportExport(BaseModel):
    """Report export request/response."""
    format: str = Field(..., pattern="^(pdf|excel)$")
    download_url: Optional[str] = None
    expires_in: Optional[int] = None


class OverviewReportData(BaseModel):
    """Overview report data."""
    total_cases: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    score_trend: List[Dict[str, Any]]
    top_errors: List[Dict[str, Any]]


class AttributeReportData(BaseModel):
    """Attribute analysis report data."""
    field_accuracies: List[Dict[str, Any]]
    field_comparison: Dict[str, Any]


class BadcaseReportData(BaseModel):
    """Badcase analysis report data."""
    total_badcases: int
    badcase_rate: float
    error_categories: List[Dict[str, Any]]
    badcases: List[Dict[str, Any]]


class TrendReportData(BaseModel):
    """Trend analysis report data."""
    time_range: str
    score_trend: List[Dict[str, Any]]
    metric_trends: Dict[str, List[Dict[str, Any]]]


class ReportFilter(BaseModel):
    """Report filter parameters."""
    eval_id: str
    report_type: Optional[str] = Field(default=None, pattern="^(overview|attribute|badcase|trend)$")
