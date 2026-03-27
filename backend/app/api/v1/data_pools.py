"""
Training and Evaluation Pool API routes.
参考 GAIA Benchmark 设计：
- 训练池：Input + GT 公开，供模型训练
- 评测池：Input 公开，GT 隐藏，用于评测
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_data_engineer, get_current_user_optional
from app.core.database import get_async_session
from app.core.logging import get_logger
from app.models.data_pool import DataPool
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams, ResponseModel
from app.schemas.data_pool import DataPoolRead, DataPoolFilter

logger = get_logger(__name__)
router = APIRouter()


@router.get("/training", response_model=PaginatedResponse[List[DataPoolRead]])
async def list_training_pool(
    category_l4: Optional[str] = Query(None, description="按四级类目筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_data_engineer),
):
    """
    训练池数据列表。
    
    训练池数据包含完整的 Input + GT，供模型训练使用。
    支持按类目、关键词筛选。
    """
    query = select(DataPool).where(DataPool.pool_type == "training")
    
    # 用户数据隔离（简化版，SSO用户暂时不过滤）
    # is_admin = current_user.get("is_admin", False)
    # if not is_admin:
    #     query = query.where(DataPool.created_by == current_user.get("id"))
    
    # Apply filters
    if category_l4:
        query = query.where(DataPool.category_l4 == category_l4)
    
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.where(DataPool.input.ilike(keyword_pattern))
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Pagination
    query = query.order_by(desc(DataPool.created_at))
    query = query.offset((pagination.page - 1) * pagination.size).limit(pagination.size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    pages = (total + pagination.size - 1) // pagination.size
    
    return PaginatedResponse(
        code=0,
        message="success",
        data=list(items),
        pagination={
            "page": pagination.page,
            "size": pagination.size,
            "total": total,
            "pages": pages,
        },
    )


@router.get("/evaluation", response_model=PaginatedResponse[List[DataPoolRead]])
async def list_evaluation_pool(
    category_l4: Optional[str] = Query(None, description="按四级类目筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_data_engineer),
):
    """
    评测池数据列表。
    
    评测池数据只包含 Input，GT 被隐藏用于评测评分。
    支持按类目、关键词筛选。
    """
    query = select(DataPool).where(DataPool.pool_type == "evaluation")
    
    # 用户数据隔离（简化版，SSO用户暂时不过滤）
    # is_admin = current_user.get("is_admin", False)
    # if not is_admin:
    #     query = query.where(DataPool.created_by == current_user.get("id"))
    
    # Apply filters
    if category_l4:
        query = query.where(DataPool.category_l4 == category_l4)
    
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.where(DataPool.input.ilike(keyword_pattern))
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Pagination
    query = query.order_by(desc(DataPool.created_at))
    query = query.offset((pagination.page - 1) * pagination.size).limit(pagination.size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    pages = (total + pagination.size - 1) // pagination.size
    
    return PaginatedResponse(
        code=0,
        message="success",
        data=list(items),
        pagination={
            "page": pagination.page,
            "size": pagination.size,
            "total": total,
            "pages": pages,
        },
    )


@router.get("/stats", response_model=ResponseModel[dict])
async def get_pool_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user = Depends(get_current_active_user),
):
    """
    获取训练池和评测池的统计信息。
    """
    # Training pool count
    training_count_result = await db.execute(
        select(func.count()).where(DataPool.pool_type == "training")
    )
    training_count = training_count_result.scalar()
    
    # Evaluation pool count
    eval_count_result = await db.execute(
        select(func.count()).where(DataPool.pool_type == "evaluation")
    )
    eval_count = eval_count_result.scalar()
    
    # Category breakdown
    category_result = await db.execute(
        select(DataPool.category_l4, DataPool.pool_type, func.count())
        .group_by(DataPool.category_l4, DataPool.pool_type)
    )
    category_stats = {}
    for row in category_result.all():
        cat, pool_type, count = row
        if cat not in category_stats:
            category_stats[cat] = {}
        category_stats[cat][pool_type] = count
    
    return ResponseModel(
        code=0,
        message="success",
        data={
            "training": {"total": training_count},
            "evaluation": {"total": eval_count},
            "category_breakdown": category_stats,
        },
    )


# ========== 测试用API（无需认证） ==========

@router.get("/test/training", response_model=PaginatedResponse[List[DataPoolRead]])
async def test_list_training_pool(
    category_l4: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),):
    """【测试用】训练池数据列表（无需认证）。"""
    query = select(DataPool).where(DataPool.pool_type == "training")
    
    if category_l4:
        query = query.where(DataPool.category_l4 == category_l4)
    
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.where(DataPool.input.ilike(keyword_pattern))
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.order_by(desc(DataPool.created_at))
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    pages = (total + size - 1) // size
    
    return PaginatedResponse(
        code=0,
        message="success",
        data=list(items),
        pagination={"page": page, "size": size, "total": total, "pages": pages},
    )


@router.get("/test/evaluation", response_model=PaginatedResponse[List[DataPoolRead]])
async def test_list_evaluation_pool(
    category_l4: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),):
    """【测试用】评测池数据列表（无需认证）。"""
    query = select(DataPool).where(DataPool.pool_type == "evaluation")
    
    if category_l4:
        query = query.where(DataPool.category_l4 == category_l4)
    
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.where(DataPool.input.ilike(keyword_pattern))
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.order_by(desc(DataPool.created_at))
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    pages = (total + size - 1) // size
    
    return PaginatedResponse(
        code=0,
        message="success",
        data=list(items),
        pagination={"page": page, "size": size, "total": total, "pages": pages},
    )
