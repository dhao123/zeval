"""
Category API routes for 4-level category management.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.api.deps import get_current_user, require_data_engineer
from app.schemas.category import (
    CategoryCreate,
    CategoryFilter,
    CategoryListResponse,
    CategoryRead,
    CategoryUpdate,
    DashboardStats,
)
from app.schemas.common import ResponseModel
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/l4-options", response_model=ResponseModel[List[dict]])
async def get_l4_category_options(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_data_engineer),
) -> ResponseModel[List[dict]]:
    """Get L4 category options for AutoComplete.
    
    Returns list of {value, label} for AutoComplete component.
    """
    service = CategoryService(db)
    
    filter_params = CategoryFilter(
        keyword=keyword,
        is_active=True,
    )
    
    items, _ = await service.get_list(filter_params, skip=0, limit=100)
    
    # Format for AutoComplete: {value: l4_name, label: full_path}
    options = [
        {
            "value": item.l4_name,
            "label": f"{item.l1_name}/{item.l2_name}/{item.l3_name}/{item.l4_name}",
            "l1_name": item.l1_name,
            "l2_name": item.l2_name,
            "l3_name": item.l3_name,
            "l4_name": item.l4_name,
        }
        for item in items
    ]
    
    return ResponseModel(data=options)


@router.get("/dashboard", response_model=ResponseModel[DashboardStats])
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_data_engineer),
) -> ResponseModel[DashboardStats]:
    """Get dashboard statistics with category breakdown."""
    service = CategoryService(db)
    stats = await service.get_dashboard_stats()
    return ResponseModel(data=stats)


@router.get("", response_model=ResponseModel[CategoryListResponse])
async def list_categories(
    l1_name: Optional[str] = Query(None, description="Filter by L1 category"),
    l2_name: Optional[str] = Query(None, description="Filter by L2 category"),
    l3_name: Optional[str] = Query(None, description="Filter by L3 category"),
    l4_name: Optional[str] = Query(None, description="Filter by L4 category"),
    keyword: Optional[str] = Query(None, description="Search keyword"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Skip N items"),
    limit: int = Query(100, ge=1, le=1000, description="Limit to N items"),
    include_stats: bool = Query(False, description="Include statistics"),
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_data_engineer),
) -> ResponseModel[CategoryListResponse]:
    """List categories with optional filtering and statistics."""
    service = CategoryService(db)
    
    filter_params = CategoryFilter(
        l1_name=l1_name,
        l2_name=l2_name,
        l3_name=l3_name,
        l4_name=l4_name,
        keyword=keyword,
        is_active=is_active,
    )
    
    items, total = await service.get_list(filter_params, skip=skip, limit=limit)
    
    # Include stats if requested
    items_with_stats = []
    for item in items:
        cat_read = CategoryRead.model_validate(item)
        if include_stats:
            cat_read.stats = await service.get_category_stats(item)
        items_with_stats.append(cat_read)
    
    return ResponseModel(
        data=CategoryListResponse(items=items_with_stats, total=total)
    )


@router.get("/{category_id}", response_model=ResponseModel[CategoryRead])
async def get_category(
    category_id: str,
    include_stats: bool = Query(False, description="Include statistics"),
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(require_data_engineer),
) -> ResponseModel[CategoryRead]:
    """Get single category by ID."""
    service = CategoryService(db)
    category = await service.get_by_category_id(category_id)
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    cat_read = CategoryRead.model_validate(category)
    if include_stats:
        cat_read.stats = await service.get_category_stats(category)
    
    return ResponseModel(data=cat_read)


@router.post("", response_model=ResponseModel[CategoryRead])
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_async_session),
) -> ResponseModel[CategoryRead]:
    """Create new category."""
    service = CategoryService(db)
    try:
        category = await service.create(data)
        return ResponseModel(data=CategoryRead.model_validate(category))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{category_id}", response_model=ResponseModel[CategoryRead])
async def update_category(
    category_id: str,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_async_session),
) -> ResponseModel[CategoryRead]:
    """Update category."""
    service = CategoryService(db)
    category = await service.update(category_id, data)
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return ResponseModel(data=CategoryRead.model_validate(category))


@router.delete("/{category_id}", response_model=ResponseModel[dict])
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_async_session),
) -> ResponseModel[dict]:
    """Soft delete category by setting is_active to False."""
    service = CategoryService(db)
    category = await service.get_by_category_id(category_id)
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Soft delete
    category.is_active = False
    await db.commit()
    
    return ResponseModel(data={"deleted": True, "category_id": category_id})
