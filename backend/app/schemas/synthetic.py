"""
Synthetic data schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SyntheticBase(BaseModel):
    """Base synthetic data schema - 与SeedBase同构."""
    input: str = Field(..., description="输入文本")
    gt: Dict[str, Any] = Field(..., description="标准答案 (Ground Truth)")
    category_l1: Optional[str] = Field(default=None, max_length=128, description="一级类目")
    category_l2: Optional[str] = Field(default=None, max_length=128, description="二级类目")
    category_l3: Optional[str] = Field(default=None, max_length=128, description="三级类目")
    category_l4: Optional[str] = Field(default=None, max_length=128, description="四级类目")
    category_path: Optional[str] = Field(default=None, max_length=512, description="类目路径")


class SyntheticCreate(SyntheticBase):
    """Synthetic data creation schema."""
    synthetic_id: Optional[str] = Field(default=None, max_length=64, description="自定义ID，不填则自动生成")
    seed_id: Optional[str] = Field(default=None, description="关联的种子ID")
    standard_id: Optional[str] = Field(default=None, description="关联的国标ID")
    skill_id: Optional[str] = Field(default=None, description="关联的Skill ID")
    difficulty: str = Field(default="medium", pattern="^(low|medium|high|ultra)$", description="难度等级")
    synthesis_params: Optional[Dict[str, Any]] = Field(default=None, description="合成参数")
    ai_check_result: Optional[Dict[str, Any]] = Field(default=None, description="AI质检结果")
    ai_check_passed: bool = Field(default=False, description="AI质检是否通过")


class SyntheticRead(SyntheticBase):
    """Synthetic data read schema - 与SeedRead同构."""
    id: int = Field(..., description="数据库自增ID")
    synthetic_id: str = Field(..., description="全局唯一ID")
    
    # 状态字段
    status: str = Field(..., description="状态：draft/confirmed/rejected")
    hash: str = Field(..., description="SHA256哈希值")
    version: str = Field(..., description="版本号")
    
    # 四级类目
    category_l1: Optional[str] = Field(default=None, description="一级类目")
    category_l2: Optional[str] = Field(default=None, description="二级类目")
    category_l3: Optional[str] = Field(default=None, description="三级类目")
    category_l4: Optional[str] = Field(default=None, description="四级类目")
    
    # 血缘追踪
    seed_id: Optional[str] = Field(default=None, description="关联种子ID")
    standard_id: Optional[str] = Field(default=None, description="关联国标ID")
    skill_id: Optional[str] = Field(default=None, description="关联Skill ID")
    
    # 合成信息
    difficulty: str = Field(..., description="难度等级")
    ai_check_passed: bool = Field(..., description="AI质检是否通过")
    
    # 分流信息
    route_batch_id: Optional[str] = Field(default=None, description="分流批次ID")
    pool_location: Optional[str] = Field(default=None, description="所在池位置：training/evaluation/null")
    
    # 用户追踪
    created_by: Optional[int] = Field(default=None, description="创建者ID")
    confirmed_by: Optional[int] = Field(default=None, description="确认者ID")
    confirmed_at: Optional[datetime] = Field(default=None, description="确认时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class SyntheticUpdate(BaseModel):
    """Synthetic data update schema."""
    input: Optional[str] = Field(default=None, description="输入文本")
    gt: Optional[Dict[str, Any]] = Field(default=None, description="标准答案")
    category_l1: Optional[str] = Field(default=None, max_length=128, description="一级类目")
    category_l2: Optional[str] = Field(default=None, max_length=128, description="二级类目")
    category_l3: Optional[str] = Field(default=None, max_length=128, description="三级类目")
    category_l4: Optional[str] = Field(default=None, max_length=128, description="四级类目")
    category_path: Optional[str] = Field(default=None, max_length=512, description="类目路径")


class SyntheticConfirmRequest(BaseModel):
    """确认合成数据请求."""
    action: str = Field(..., pattern="^(confirm|reject)$", description="操作：确认或拒绝")
    reason: Optional[str] = Field(default=None, description="拒绝原因（拒绝时必填）")


class SyntheticConfirmResponse(BaseModel):
    """确认合成数据响应."""
    success: bool = Field(..., description="是否成功")
    synthetic_id: str = Field(..., description="合成数据ID")
    action: str = Field(..., description="执行的操作")
    message: str = Field(..., description="提示信息")
    
    # 分流结果（确认时返回）
    route_result: Optional[Dict[str, Any]] = Field(default=None, description="分流结果")


# 上传/下载相关
class SyntheticUploadItem(BaseModel):
    """单条合成数据上传项 - 与种子数据格式一致."""
    input: str = Field(..., description="输入文本")
    gt: Dict[str, Any] = Field(..., description="标准答案")
    category_l4: str = Field(..., description="四级类目")
    category_path: Optional[str] = Field(default=None, description="类目路径")
    difficulty: Optional[str] = Field(default="medium", description="难度等级")


class SyntheticUploadResponse(BaseModel):
    """批量上传响应."""
    total: int = Field(..., description="总条数")
    success: int = Field(..., description="成功条数")
    duplicated: int = Field(..., description="重复条数")
    failed: int = Field(..., description="失败条数")
    details: List[Dict[str, Any]] = Field(default_factory=list, description="详细结果")


class SyntheticFilter(BaseModel):
    """合成数据筛选条件."""
    category_l4: Optional[str] = Field(default=None, description="四级类目")
    status: Optional[str] = Field(default=None, pattern="^(draft|confirmed|rejected)$", description="状态")
    seed_id: Optional[str] = Field(default=None, description="关联种子ID")
    keyword: Optional[str] = Field(default=None, description="关键词搜索")


# 任务相关
class SynthesisTaskCreate(BaseModel):
    """创建合成任务请求."""
    seed_ids: Optional[List[str]] = Field(default=None, description="指定种子ID列表")
    category_l4: Optional[str] = Field(default=None, description="按类目筛选")
    standard_id: Optional[str] = Field(default=None, description="关联国标")
    skill_id: Optional[str] = Field(default=None, description="关联Skill")
    difficulty: str = Field(default="medium", pattern="^(low|medium|high|ultra)$", description="难度等级")
    count_per_seed: int = Field(default=5, ge=1, le=20, description="每个种子生成数量")
    use_ai_check: bool = Field(default=True, description="是否启用AI质检")


class SynthesisTaskResponse(BaseModel):
    """合成任务响应."""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="提示信息")
    total_seeds: int = Field(..., description="种子数量")
    estimated_count: int = Field(..., description="预计生成数量")


class SynthesisTaskStatus(BaseModel):
    """合成任务状态."""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="状态：pending/running/completed/failed")
    progress: int = Field(..., ge=0, le=100, description="进度百分比")
    total: int = Field(..., description="总数")
    completed: int = Field(..., description="已完成数")
    failed: int = Field(..., description="失败数")
    message: Optional[str] = Field(default=None, description="状态信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
