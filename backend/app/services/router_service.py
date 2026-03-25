"""
Data Router Service - 5:5分流核心算法.
"""
import random
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_pool import DataPool, RouteConfig
from app.models.synthetic import SyntheticData
from app.services.base import BaseService


class RouterService(BaseService[RouteConfig]):
    """Data router service for 5:5 split."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, RouteConfig)
    
    async def get_config_by_category(self, category_l4: str) -> Optional[RouteConfig]:
        """Get routing config for a category."""
        result = await self.db.execute(
            select(RouteConfig).where(RouteConfig.category_l4 == category_l4)
        )
        return result.scalar_one_or_none()
    
    async def get_or_create_config(self, category_l4: str) -> RouteConfig:
        """Get or create default routing config for a category."""
        config = await self.get_config_by_category(category_l4)
        if not config:
            # Create default 5:5 config
            config = RouteConfig(
                category_l4=category_l4,
                train_ratio=0.5,
                eval_ratio=0.5,
                is_active=True,
            )
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
        return config
    
    async def execute_5_5_routing(
        self,
        synthetic_ids: Optional[List[str]] = None,
        category_l4: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Execute 5:5 routing for confirmed synthetic data.
        
        核心算法：
        1. 获取已确认的合成数据
        2. 按category_l4分组
        3. 每组内随机打乱
        4. 按5:5比例分割
        5. 分别写入训练池和评测池
        
        Args:
            synthetic_ids: 指定的合成数据ID列表，为空则处理所有confirmed数据
            category_l4: 按类目筛选
            
        Returns:
            分流结果统计
        """
        # 1. 获取待分流的合成数据
        query = select(SyntheticData).where(SyntheticData.status == "confirmed")
        
        if synthetic_ids:
            query = query.where(SyntheticData.synthetic_id.in_(synthetic_ids))
        
        if category_l4:
            query = query.where(SyntheticData.category_l4 == category_l4)
        
        # 排除已经分流的
        query = query.where(SyntheticData.route_batch_id.is_(None))
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        if not items:
            return {
                "success": True,
                "message": "No confirmed synthetic data to route",
                "batch_id": None,
                "total": 0,
                "training": 0,
                "evaluation": 0,
                "details": {},
            }
        
        # 2. 按category_l4分组
        groups = defaultdict(list)
        for item in items:
            groups[item.category_l4].append(item)
        
        # 生成批次ID
        batch_id = f"route_{uuid.uuid4().hex[:12]}"
        
        # 统计结果
        total_train = 0
        total_eval = 0
        details = {}
        
        # 3. 每个类目独立处理
        for cat, cat_items in groups.items():
            # 获取该类目的分流配置
            config = await self.get_or_create_config(cat)
            
            if not config.is_active:
                continue
            
            # 4. 随机打乱
            shuffled = cat_items.copy()
            random.shuffle(shuffled)
            
            # 5. 按比例分割（默认5:5）
            total = len(shuffled)
            split_idx = int(total * config.train_ratio)
            
            train_items = shuffled[:split_idx]
            eval_items = shuffled[split_idx:]
            
            # 6. 写入训练池（含GT）
            for idx, item in enumerate(train_items):
                data_pool = DataPool(
                    pool_id=f"dp_{uuid.uuid4().hex[:16]}",
                    data_type="synthetic",
                    source_id=item.synthetic_id,
                    pool_type="training",
                    category_l4=item.category_l4,
                    input=item.input,
                    gt=item.gt,  # 训练池包含GT
                    route_batch_id=batch_id,
                    route_ratio=config.train_ratio,
                    created_by=item.created_by,  # 继承创建者
                )
                self.db.add(data_pool)
                
                # 更新合成数据状态
                item.route_batch_id = batch_id
            
            # 7. 写入评测池（GT也存储但API会隐藏）
            for idx, item in enumerate(eval_items):
                data_pool = DataPool(
                    pool_id=f"dp_{uuid.uuid4().hex[:16]}",
                    data_type="synthetic",
                    source_id=item.synthetic_id,
                    pool_type="evaluation",
                    category_l4=item.category_l4,
                    input=item.input,
                    gt=item.gt,  # 评测池也存储GT，用于评分
                    route_batch_id=batch_id,
                    route_ratio=config.eval_ratio,
                    created_by=item.created_by,  # 继承创建者
                )
                self.db.add(data_pool)
                
                # 更新合成数据状态
                item.route_batch_id = batch_id
            
            total_train += len(train_items)
            total_eval += len(eval_items)
            
            details[cat] = {
                "total": total,
                "training": len(train_items),
                "evaluation": len(eval_items),
                "train_ratio": config.train_ratio,
                "eval_ratio": config.eval_ratio,
            }
        
        await self.db.commit()
        
        return {
            "success": True,
            "message": f"Successfully routed {len(items)} synthetic data",
            "batch_id": batch_id,
            "total": len(items),
            "training": total_train,
            "evaluation": total_eval,
            "details": details,
        }
    
    async def get_batch_status(self, batch_id: str) -> Optional[Dict]:
        """Get routing batch status."""
        query = select(DataPool).where(DataPool.route_batch_id == batch_id)
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        if not items:
            return None
        
        training_count = sum(1 for item in items if item.pool_type == "training")
        evaluation_count = sum(1 for item in items if item.pool_type == "evaluation")
        
        # 按类目统计
        categories = defaultdict(lambda: {"training": 0, "evaluation": 0})
        for item in items:
            categories[item.category_l4][item.pool_type] += 1
        
        return {
            "batch_id": batch_id,
            "total": len(items),
            "training": training_count,
            "evaluation": evaluation_count,
            "categories": dict(categories),
            "created_at": items[0].created_at if items else None,
        }
    
    async def preview_routing(
        self,
        synthetic_ids: Optional[List[str]] = None,
        category_l4: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Preview routing result without actual execution.
        
        用于预览分流结果，不实际写入数据库。
        """
        # 获取待分流的合成数据（同上）
        query = select(SyntheticData).where(SyntheticData.status == "confirmed")
        
        if synthetic_ids:
            query = query.where(SyntheticData.synthetic_id.in_(synthetic_ids))
        
        if category_l4:
            query = query.where(SyntheticData.category_l4 == category_l4)
        
        query = query.where(SyntheticData.route_batch_id.is_(None))
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        if not items:
            return {
                "preview": True,
                "message": "No confirmed synthetic data to route",
                "total": 0,
                "training": 0,
                "evaluation": 0,
                "details": {},
            }
        
        # 按类目分组并预览
        groups = defaultdict(list)
        for item in items:
            groups[item.category_l4].append(item)
        
        total_train = 0
        total_eval = 0
        details = {}
        
        for cat, cat_items in groups.items():
            config = await self.get_or_create_config(cat)
            
            total = len(cat_items)
            split_idx = int(total * config.train_ratio)
            
            train_count = split_idx
            eval_count = total - split_idx
            
            total_train += train_count
            total_eval += eval_count
            
            details[cat] = {
                "total": total,
                "training": train_count,
                "evaluation": eval_count,
                "train_ratio": config.train_ratio,
                "eval_ratio": config.eval_ratio,
                "sample_training_ids": [item.synthetic_id for item in cat_items[:3]],
                "sample_evaluation_ids": [item.synthetic_id for item in cat_items[split_idx:split_idx+3]],
            }
        
        return {
            "preview": True,
            "message": f"Preview routing for {len(items)} synthetic data",
            "total": len(items),
            "training": total_train,
            "evaluation": total_eval,
            "details": details,
        }
