"""
Category service for managing 4-level category system.
"""
import uuid
from typing import List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.data_pool import DataPool
from app.models.synthetic import SyntheticData
from app.schemas.category import (
    CategoryCreate,
    CategoryFilter,
    CategoryRead,
    CategoryStats,
    CategoryUpdate,
    DashboardStats,
)
from app.services.base import BaseService


class CategoryService(BaseService[Category]):
    """Service for category management."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Category)
    
    @staticmethod
    def generate_category_id() -> str:
        """Generate unique category ID."""
        return f"cat_{uuid.uuid4().hex[:16]}"
    
    @staticmethod
    def build_full_path(l1: str, l2: str, l3: str, l4: str) -> str:
        """Build full category path."""
        return f"{l1}/{l2}/{l3}/{l4}"
    
    async def get_by_category_id(self, category_id: str) -> Optional[Category]:
        """Get category by category_id."""
        result = await self.db.execute(
            select(Category).where(Category.category_id == category_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_full_path(
        self, l1: str, l2: str, l3: str, l4: str
    ) -> Optional[Category]:
        """Get category by L1-L4 names."""
        result = await self.db.execute(
            select(Category).where(
                and_(
                    Category.l1_name == l1,
                    Category.l2_name == l2,
                    Category.l3_name == l3,
                    Category.l4_name == l4,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_or_create(
        self,
        l1: str,
        l2: str,
        l3: str,
        l4: str,
        source: str = "upload",
    ) -> Category:
        """Get existing category or create new one."""
        existing = await self.get_by_full_path(l1, l2, l3, l4)
        if existing:
            return existing
        
        full_path = self.build_full_path(l1, l2, l3, l4)
        category = Category(
            category_id=self.generate_category_id(),
            l1_name=l1,
            l2_name=l2,
            l3_name=l3,
            l4_name=l4,
            full_path=full_path,
            source=source,
            is_active=True,
        )
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category
    
    async def create(self, data: CategoryCreate) -> Category:
        """Create new category."""
        existing = await self.get_by_full_path(
            data.l1_name, data.l2_name, data.l3_name, data.l4_name
        )
        if existing:
            raise ValueError(
                f"Category already exists: {data.l1_name}/{data.l2_name}/"
                f"{data.l3_name}/{data.l4_name}"
            )
        
        full_path = self.build_full_path(
            data.l1_name, data.l2_name, data.l3_name, data.l4_name
        )
        
        category = Category(
            category_id=data.category_id or self.generate_category_id(),
            l1_name=data.l1_name,
            l2_name=data.l2_name,
            l3_name=data.l3_name,
            l4_name=data.l4_name,
            full_path=full_path,
            description=data.description,
            source=data.source,
            is_active=True,
        )
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category
    
    async def update(
        self, category_id: str, data: CategoryUpdate
    ) -> Optional[Category]:
        """Update category."""
        category = await self.get_by_category_id(category_id)
        if not category:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(category, key, value)
        
        await self.db.commit()
        await self.db.refresh(category)
        return category
    
    async def get_list(
        self,
        filter_params: CategoryFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Category], int]:
        """Get category list with filtering."""
        query = select(Category)
        
        if filter_params.l1_name:
            query = query.where(Category.l1_name == filter_params.l1_name)
        if filter_params.l2_name:
            query = query.where(Category.l2_name == filter_params.l2_name)
        if filter_params.l3_name:
            query = query.where(Category.l3_name == filter_params.l3_name)
        if filter_params.l4_name:
            query = query.where(Category.l4_name == filter_params.l4_name)
        if filter_params.is_active is not None:
            query = query.where(Category.is_active == filter_params.is_active)
        if filter_params.keyword:
            keyword = f"%{filter_params.keyword}%"
            query = query.where(Category.full_path.ilike(keyword))
        
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        
        query = query.order_by(Category.l1_name, Category.l2_name, 
                              Category.l3_name, Category.l4_name)
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return list(items), total
    
    async def get_category_stats(self, category: Category) -> CategoryStats:
        """Get statistics for a category."""
        # Draft pool count - 只统计草稿态(status='draft')
        draft_result = await self.db.execute(
            select(func.count()).select_from(SyntheticData).where(
                and_(
                    SyntheticData.category_l1 == category.l1_name,
                    SyntheticData.category_l2 == category.l2_name,
                    SyntheticData.category_l3 == category.l3_name,
                    SyntheticData.category_l4 == category.l4_name,
                    SyntheticData.status == "draft",
                )
            )
        )
        draft_count = draft_result.scalar() or 0
        
        # Training pool count - DataPool only has category_l4
        training_result = await self.db.execute(
            select(func.count()).select_from(DataPool).where(
                and_(
                    DataPool.category_l4 == category.l4_name,
                    DataPool.pool_type == "training",
                )
            )
        )
        training_count = training_result.scalar() or 0
        
        # Evaluation pool count - DataPool only has category_l4
        evaluation_result = await self.db.execute(
            select(func.count()).select_from(DataPool).where(
                and_(
                    DataPool.category_l4 == category.l4_name,
                    DataPool.pool_type == "evaluation",
                )
            )
        )
        evaluation_count = evaluation_result.scalar() or 0
        
        return CategoryStats(
            draft_count=draft_count,
            training_count=training_count,
            evaluation_count=evaluation_count,
            total_confirmed=training_count + evaluation_count,
        )
    
    async def get_dashboard_stats(self) -> DashboardStats:
        """Get dashboard statistics for all categories."""
        result = await self.db.execute(
            select(Category).where(Category.is_active == True)
        )
        categories = result.scalars().all()
        
        total_categories = len(categories)
        total_draft = 0
        total_training = 0
        total_evaluation = 0
        
        categories_with_stats = []
        for category in categories:
            stats = await self.get_category_stats(category)
            total_draft += stats.draft_count
            total_training += stats.training_count
            total_evaluation += stats.evaluation_count
            
            cat_read = CategoryRead.model_validate(category)
            cat_read.stats = stats
            categories_with_stats.append(cat_read)
        
        return DashboardStats(
            total_categories=total_categories,
            total_draft=total_draft,
            total_training=total_training,
            total_evaluation=total_evaluation,
            total_data=total_draft + total_training + total_evaluation,
            categories=categories_with_stats,
        )
