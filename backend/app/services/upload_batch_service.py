"""
Upload Batch Service.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.upload_batch import UploadBatch
from app.models.synthetic import SyntheticData
from app.schemas.upload_batch import UploadBatchCreate, UploadBatchUpdate
from app.services.oss_service import get_oss_service

logger = get_logger(__name__)


class UploadBatchService:
    """上传批次服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_batch(
        self,
        file_name: str,
        file_url: str,
        object_key: str,
        file_size: int,
        owner_id: Optional[str] = None,
        owner_name: Optional[str] = None
    ) -> UploadBatch:
        """创建上传批次记录"""
        batch = UploadBatch(
            batch_id=f"batch_{uuid.uuid4().hex[:16]}",
            file_name=file_name,
            file_url=file_url,
            object_key=object_key,
            file_size=file_size,
            owner_id=owner_id,
            owner_name=owner_name,
            status="processing",
            record_count=0,
            success_count=0,
            fail_count=0
        )
        
        self.db.add(batch)
        await self.db.commit()
        await self.db.refresh(batch)
        
        logger.info(f"Upload batch created: {batch.batch_id}")
        return batch
    
    async def get_batch_by_id(self, batch_id: str) -> Optional[UploadBatch]:
        """根据ID获取批次"""
        query = select(UploadBatch).where(UploadBatch.batch_id == batch_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_batches(
        self,
        owner_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> tuple[list[UploadBatch], int]:
        """获取批次列表"""
        query = select(UploadBatch)
        
        # 筛选条件
        if owner_id:
            query = query.where(UploadBatch.owner_id == owner_id)
        if status:
            query = query.where(UploadBatch.status == status)
        
        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 分页排序
        query = query.order_by(desc(UploadBatch.created_at))
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return list(items), total
    
    async def update_batch(
        self,
        batch_id: str,
        update_data: UploadBatchUpdate
    ) -> Optional[UploadBatch]:
        """更新批次信息"""
        batch = await self.get_batch_by_id(batch_id)
        if not batch:
            return None
        
        # 更新字段
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(batch, key, value)
        
        await self.db.commit()
        await self.db.refresh(batch)
        
        logger.info(f"Upload batch updated: {batch_id}")
        return batch
    
    async def complete_batch(
        self,
        batch_id: str,
        record_count: int,
        success_count: int,
        fail_count: int,
        remark: Optional[str] = None
    ) -> Optional[UploadBatch]:
        """完成批次处理"""
        batch = await self.get_batch_by_id(batch_id)
        if not batch:
            return None
        
        batch.status = "completed"
        batch.record_count = record_count
        batch.success_count = success_count
        batch.fail_count = fail_count
        if remark:
            batch.remark = remark
        
        await self.db.commit()
        await self.db.refresh(batch)
        
        logger.info(f"Upload batch completed: {batch_id}, records: {record_count}")
        return batch
    
    async def fail_batch(
        self,
        batch_id: str,
        error_message: str
    ) -> Optional[UploadBatch]:
        """标记批次失败"""
        batch = await self.get_batch_by_id(batch_id)
        if not batch:
            return None
        
        batch.status = "failed"
        batch.remark = error_message
        
        await self.db.commit()
        await self.db.refresh(batch)
        
        logger.error(f"Upload batch failed: {batch_id}, error: {error_message}")
        return batch
    
    async def delete_batch(self, batch_id: str) -> bool:
        """删除批次"""
        batch = await self.get_batch_by_id(batch_id)
        if not batch:
            return False
        
        # 删除OSS文件
        try:
            oss_service = get_oss_service()
            if oss_service.is_configured():
                oss_service.delete_file(batch.object_key)
        except Exception as e:
            logger.warning(f"Failed to delete OSS file: {e}")
        
        # 删除数据库记录
        await self.db.delete(batch)
        await self.db.commit()
        
        logger.info(f"Upload batch deleted: {batch_id}")
        return True
    
    async def get_batch_cases(
        self,
        batch_id: str,
        page: int = 1,
        size: int = 20
    ) -> tuple[list[SyntheticData], int]:
        """获取批次下的case列表"""
        # 先检查批次是否存在
        batch = await self.get_batch_by_id(batch_id)
        if not batch:
            return [], 0
        
        # 查询case
        query = select(SyntheticData).where(
            SyntheticData.upload_batch_id == batch_id
        )
        
        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 分页排序
        query = query.order_by(desc(SyntheticData.created_at))
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        return list(items), total
    
    async def refresh_batch_stats(self, batch_id: str) -> Optional[UploadBatch]:
        """刷新批次统计信息"""
        batch = await self.get_batch_by_id(batch_id)
        if not batch:
            return None
        
        # 统计实际case数量
        count_query = select(func.count()).where(
            SyntheticData.upload_batch_id == batch_id
        )
        result = await self.db.execute(count_query)
        actual_count = result.scalar()
        
        # 更新统计
        batch.record_count = actual_count
        batch.success_count = actual_count
        
        await self.db.commit()
        await self.db.refresh(batch)
        
        return batch
