"""
Dashboard API routes for data visualization and analytics.
提供数据看板所需的各种统计和趋势数据。
"""
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_data_engineer
from app.core.database import get_async_session
from app.models.data_pool import DataPool
from app.models.synthetic import SyntheticData
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.dashboard import (
    DashboardOverview,
    TrendDataPoint,
    TrendQuery,
    TrendResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=ResponseModel[DashboardOverview])
async def get_overview(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_data_engineer),
) -> ResponseModel[DashboardOverview]:
    """Get dashboard overview statistics.
    
    Returns:
        - total_categories: 总类目数
        - total_draft: 初创池草稿态数量
        - total_training: 训练池数量
        - total_evaluation: 评测池数量
        - total_data: 总数据量
    
    非管理员只能查看自己的数据统计。
    """
    # 判断是否为管理员
    is_admin = current_user.role is not None and current_user.role.name == "admin"
    
    # 构建基础查询条件
    draft_conditions = [SyntheticData.status == "draft"]
    pool_conditions = []
    
    if not is_admin:
        draft_conditions.append(SyntheticData.created_by == current_user.id)
        pool_conditions.append(DataPool.created_by == current_user.id)
    
    # 统计初创池草稿态数量
    draft_query = select(func.count()).select_from(SyntheticData).where(
        and_(*draft_conditions)
    )
    draft_result = await db.execute(draft_query)
    total_draft = draft_result.scalar() or 0
    
    # 统计训练池数量
    training_conditions = [DataPool.pool_type == "training"] + pool_conditions
    training_query = select(func.count()).select_from(DataPool).where(
        and_(*training_conditions)
    )
    training_result = await db.execute(training_query)
    total_training = training_result.scalar() or 0
    
    # 统计评测池数量
    evaluation_conditions = [DataPool.pool_type == "evaluation"] + pool_conditions
    evaluation_query = select(func.count()).select_from(DataPool).where(
        and_(*evaluation_conditions)
    )
    evaluation_result = await db.execute(evaluation_query)
    total_evaluation = evaluation_result.scalar() or 0
    
    # 统计总类目数（唯一的 category_l4）- 类目维度不过滤用户
    categories_result = await db.execute(
        select(func.count(func.distinct(SyntheticData.category_l4))).where(
            SyntheticData.category_l4.isnot(None)
        )
    )
    total_categories = categories_result.scalar() or 0
    
    return ResponseModel(
        data=DashboardOverview(
            total_categories=total_categories,
            total_draft=total_draft,
            total_training=total_training,
            total_evaluation=total_evaluation,
            total_data=total_draft + total_training + total_evaluation,
        )
    )


@router.get("/trend", response_model=ResponseModel[TrendResponse])
async def get_trend(
    days: int = Query(7, ge=1, le=90, description="时间范围天数"),
    start_date: Optional[date] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    category_l1: Optional[str] = Query(None, description="一级类目筛选"),
    category_l2: Optional[str] = Query(None, description="二级类目筛选"),
    category_l3: Optional[str] = Query(None, description="三级类目筛选"),
    category_l4: Optional[str] = Query(None, description="四级类目筛选"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_data_engineer),
) -> ResponseModel[TrendResponse]:
    """Get data trend over time.
    
    返回指定时间范围内的数据趋势，包含四个维度的数据：
    - total: 总数据量
    - draft: 初创池草稿态数量
    - training: 训练池数量
    - evaluation: 评测池数量
    
    数据关系：
    - 总数据量 = 初创池(草稿态) + 训练池 + 评测池
    - 初创池(已确认) = 训练池 + 评测池
    """
    # 计算日期范围
    if start_date and end_date:
        # 确保是 date 对象，不是 Query
        start_date_val = start_date if isinstance(start_date, date) else None
        end_date_val = end_date if isinstance(end_date, date) else None
        if start_date_val and end_date_val:
            end = datetime.combine(end_date_val, datetime.max.time())
            start = datetime.combine(start_date_val, datetime.min.time())
        else:
            end = datetime.now()
            start = end - timedelta(days=days)
    else:
        end = datetime.now()
        start = end - timedelta(days=days)
    
    # 生成日期列表
    date_list = []
    current = start
    while current <= end:
        date_list.append(current.date())
        current += timedelta(days=1)
    
    if not date_list:
        date_list = [start.date()]
    
    # 判断是否为管理员
    is_admin = current_user.role is not None and current_user.role.name == "admin"
    
    # 构建类目筛选条件
    category_filters_synthetic = []
    category_filters_datapool = []
    
    if category_l1:
        category_filters_synthetic.append(SyntheticData.category_l1 == category_l1)
    if category_l2:
        category_filters_synthetic.append(SyntheticData.category_l2 == category_l2)
    if category_l3:
        category_filters_synthetic.append(SyntheticData.category_l3 == category_l3)
    if category_l4:
        category_filters_synthetic.append(SyntheticData.category_l4 == category_l4)
        category_filters_datapool.append(DataPool.category_l4 == category_l4)
    
    # 用户数据隔离
    user_filters_synthetic = []
    user_filters_datapool = []
    if not is_admin:
        user_filters_synthetic.append(SyntheticData.created_by == current_user.id)
        user_filters_datapool.append(DataPool.created_by == current_user.id)
    
    # 查询每天的数据量
    trend_data = []
    
    for d in date_list:
        day_start = datetime.combine(d, datetime.min.time())
        day_end = datetime.combine(d, datetime.max.time())
        
        # 1. 查询初创池草稿态数量（按创建时间）
        draft_query = select(func.count()).select_from(SyntheticData).where(
            and_(
                SyntheticData.status == "draft",
                SyntheticData.created_at >= day_start,
                SyntheticData.created_at <= day_end,
                *category_filters_synthetic,
                *user_filters_synthetic
            )
        )
        draft_result = await db.execute(draft_query)
        draft_count = draft_result.scalar() or 0
        
        # 2. 查询训练池数量（按创建时间）
        training_query = select(func.count()).select_from(DataPool).where(
            and_(
                DataPool.pool_type == "training",
                DataPool.created_at >= day_start,
                DataPool.created_at <= day_end,
                *category_filters_datapool,
                *user_filters_datapool
            )
        )
        training_result = await db.execute(training_query)
        training_count = training_result.scalar() or 0
        
        # 3. 查询评测池数量（按创建时间）
        evaluation_query = select(func.count()).select_from(DataPool).where(
            and_(
                DataPool.pool_type == "evaluation",
                DataPool.created_at >= day_start,
                DataPool.created_at <= day_end,
                *category_filters_datapool,
                *user_filters_datapool
            )
        )
        evaluation_result = await db.execute(evaluation_query)
        evaluation_count = evaluation_result.scalar() or 0
        
        # 总数据量
        total_count = draft_count + training_count + evaluation_count
        
        trend_data.append(
            TrendDataPoint(
                date=d.strftime("%Y-%m-%d"),
                total=total_count,
                draft=draft_count,
                training=training_count,
                evaluation=evaluation_count,
            )
        )
    
    # 计算当前汇总值
    current_draft_query = select(func.count()).select_from(SyntheticData).where(
        and_(
            SyntheticData.status == "draft",
            *category_filters_synthetic,
            *user_filters_synthetic
        )
    )
    current_draft_result = await db.execute(current_draft_query)
    current_draft = current_draft_result.scalar() or 0
    
    current_training_query = select(func.count()).select_from(DataPool).where(
        and_(
            DataPool.pool_type == "training",
            *category_filters_datapool,
            *user_filters_datapool
        )
    )
    current_training_result = await db.execute(current_training_query)
    current_training = current_training_result.scalar() or 0
    
    current_evaluation_query = select(func.count()).select_from(DataPool).where(
        and_(
            DataPool.pool_type == "evaluation",
            *category_filters_datapool,
            *user_filters_datapool
        )
    )
    current_evaluation_result = await db.execute(current_evaluation_query)
    current_evaluation = current_evaluation_result.scalar() or 0
    
    return ResponseModel(
        data=TrendResponse(
            trend=trend_data,
            summary={
                "total_current": current_draft + current_training + current_evaluation,
                "draft_current": current_draft,
                "training_current": current_training,
                "evaluation_current": current_evaluation,
            },
        )
    )
