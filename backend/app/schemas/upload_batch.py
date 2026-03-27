"""
Upload Batch schemas.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UploadBatchBase(BaseModel):
    """上传批次基础模型"""
    file_name: str = Field(..., description="原始文件名")
    file_size: int = Field(0, description="文件大小(字节)")
    remark: Optional[str] = Field(None, description="备注")


class UploadBatchCreate(UploadBatchBase):
    """创建上传批次请求"""
    pass


class UploadBatchUpdate(BaseModel):
    """更新上传批次请求"""
    status: Optional[str] = Field(None, description="状态")
    record_count: Optional[int] = Field(None, description="记录数")
    success_count: Optional[int] = Field(None, description="成功数")
    fail_count: Optional[int] = Field(None, description="失败数")
    remark: Optional[str] = Field(None, description="备注")


class UploadBatchResponse(BaseModel):
    """上传批次响应"""
    id: int
    batch_id: str
    file_name: str
    file_url: str
    object_key: str
    file_size: int
    owner_id: Optional[str]
    owner_name: Optional[str]
    record_count: int
    success_count: int
    fail_count: int
    status: str
    remark: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    
    model_config = {"from_attributes": True}


class UploadBatchListResponse(BaseModel):
    """上传批次列表响应"""
    items: list[UploadBatchResponse]
    total: int
    page: int
    size: int
    pages: int


class UploadBatchDetailResponse(UploadBatchResponse):
    """上传批次详情（包含case列表）"""
    cases: list[dict] = Field([], description="包含的case列表")


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    batch_id: str
    file_name: str
    file_url: str
    object_key: str
    file_size: int
    message: str
