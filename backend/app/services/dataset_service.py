"""
Dataset download service.
"""
import io
import json
import csv
import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator, Optional, List, Dict, Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.config import settings
from app.models.data_pool import DataPool
from app.models.synthetic import SyntheticData
from app.models.dataset_export import DatasetVersion, ExportTask, DownloadLog
from app.models.upload_batch import UploadBatch
from app.models.user import User
from app.schemas.dataset import DatasetInfoResponse, DatasetPoolInfo

logger = get_logger(__name__)


class DatasetService:
    """Service for dataset download operations."""
    
    # Chunk size for streaming (1000 records)
    CHUNK_SIZE = 1000
    
    # Large file threshold (100MB)
    LARGE_FILE_THRESHOLD = 100 * 1024 * 1024
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_dataset_info(
        self,
        category_l4: str,
        pool_type: str = "both",
        version: Optional[str] = None
    ) -> DatasetInfoResponse:
        """Get dataset metadata."""
        # Query training pool stats
        training_stats = await self._get_pool_stats(category_l4, "training")
        
        # Query evaluation pool stats
        evaluation_stats = await self._get_pool_stats(category_l4, "evaluation")
        
        # Get available versions
        versions = await self._get_versions(category_l4)
        
        # Get latest version
        latest_version = versions[0] if versions else "v1.0.0"
        
        pools = {}
        if pool_type in ("training", "both"):
            pools["training"] = training_stats
        if pool_type in ("evaluation", "both"):
            pools["evaluation"] = evaluation_stats
        
        return DatasetInfoResponse(
            category=category_l4,
            versions=versions,
            latest_version=latest_version,
            formats=["json", "csv", "parquet"],
            pools=pools
        )
    
    async def _get_pool_stats(self, category_l4: str, pool_type: str) -> Dict:
        """Get pool statistics.
        
        Args:
            category_l4: 类目L4名称，"all"表示全部类目
            pool_type: 池类型
        """
        # Build conditions
        conditions = [DataPool.pool_type == pool_type]
        if category_l4 and category_l4 != "all":
            conditions.append(DataPool.category_l4 == category_l4)
        
        # Get record count from data_pool table
        count_query = select(func.count()).select_from(DataPool).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        record_count = count_result.scalar() or 0
        
        # Estimate file size (rough estimate: 500 bytes per record for JSON)
        estimated_size = record_count * 500
        
        # Determine fields based on pool type
        if pool_type == "training":
            fields = ["id", "input", "gt", "category_l1", "category_l2", "category_l3", "category_l4"]
        else:  # evaluation
            fields = ["id", "input", "category_l1", "category_l2", "category_l3", "category_l4"]
        
        return {
            "record_count": record_count,
            "file_size": estimated_size,
            "fields": fields,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _get_versions(self, category_l4: str) -> List[str]:
        """Get available versions for a category."""
        query = select(DatasetVersion.version_id).where(
            DatasetVersion.category_l4 == category_l4
        ).order_by(DatasetVersion.created_at.desc())
        
        result = await self.db.execute(query)
        versions = result.scalars().all()
        
        if not versions:
            # Return default version if none exists
            return ["v1.0.0"]
        
        return list(versions)
    
    async def _get_owner_name(self, source_id: str) -> Optional[str]:
        """Get owner_name from upload_batches via synthetic_data."""
        result = await self.db.execute(
            select(UploadBatch.owner_name)
            .join(SyntheticData, SyntheticData.upload_batch_id == UploadBatch.batch_id, isouter=True)
            .where(SyntheticData.synthetic_id == source_id)
        )
        row = result.first()
        return row[0] if row else None
    
    async def stream_dataset(
        self,
        category_l4: Optional[str],
        pool_type: str,
        format: str = "json",
        limit: Optional[int] = None,
        offset: int = 0,
        random: bool = False
    ) -> AsyncGenerator[bytes, None]:
        """Stream dataset records in chunks.
        
        Args:
            category_l4: 类目L4名称（None表示全部类目）
            pool_type: 池类型
            format: 文件格式
            limit: 限制数量
            offset: 偏移量
            random: 是否随机抽取
        """
        from sqlalchemy import func
        from sqlalchemy.orm import selectinload
        
        # Build query
        conditions = [DataPool.pool_type == pool_type]
        if category_l4:
            conditions.append(DataPool.category_l4 == category_l4)
        
        query = select(DataPool).where(and_(*conditions))
        
        # Random ordering if requested (SQLite uses RANDOM(), PostgreSQL uses random())
        if random:
            from sqlalchemy import text
            query = query.order_by(text("RANDOM()"))
        
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        # Execute query
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        # Stream based on format
        if format == "json":
            async for chunk in self._stream_json(records, pool_type, category_l4):
                yield chunk
        elif format == "csv":
            async for chunk in self._stream_csv(records, pool_type):
                yield chunk
        elif format == "parquet":
            # Parquet requires full file generation, not streaming
            raise NotImplementedError("Parquet format requires async export")
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def _stream_json(
        self,
        records: List[DataPool],
        pool_type: str,
        category_l4: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """Stream records as JSON."""
        # Start JSON structure
        category_display = category_l4 if category_l4 else (records[0].category_l4 if records else "all")
        metadata = {
            "metadata": {
                "category": category_display,
                "pool_type": pool_type,
                "version": "v1.0.0",
                "record_count": len(records),
                "fields": ["id", "input", "gt", "category_l4", "owner_name"] if pool_type == "training" else ["id", "input", "category_l4", "owner_name"],
                "generated_at": datetime.now(timezone.utc).isoformat()
            },
            "data": []
        }
        
        # Yield metadata header
        header = json.dumps(metadata, ensure_ascii=False, indent=2)
        # Remove the closing "data": [] part
        header = header.rsplit('"data": []', 1)[0] + '"data": [\n'
        yield header.encode('utf-8')
        
        # Yield records
        for i, record in enumerate(records):
            # Get owner_name from upload_batches
            owner_name = await self._get_owner_name(record.source_id)
            
            item = {
                "id": record.pool_id,
                "input": record.input,
                "category_l4": record.category_l4,
                "owner_name": owner_name
            }
            
            if pool_type == "training" and record.gt:
                item["gt"] = record.gt
            
            # Convert to JSON
            json_str = json.dumps(item, ensure_ascii=False)
            
            # Add comma if not last record
            if i < len(records) - 1:
                json_str += ",\n"
            else:
                json_str += "\n"
            
            yield json_str.encode('utf-8')
        
        # Yield footer
        yield b"]}\n"
    
    async def _stream_csv(
        self,
        records: List[DataPool],
        pool_type: str
    ) -> AsyncGenerator[bytes, None]:
        """Stream records as CSV."""
        import csv
        import io
        
        # Create CSV writer
        output = io.StringIO()
        
        # Determine fields (including owner_name)
        if pool_type == "training":
            fieldnames = ["id", "input", "gt", "category_l4", "owner_name"]
        else:
            fieldnames = ["id", "input", "category_l4", "owner_name"]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        yield output.getvalue().encode('utf-8')
        output.seek(0)
        output.truncate()
        
        # Write records
        for record in records:
            # Get owner_name from upload_batches
            owner_name = await self._get_owner_name(record.source_id)
            
            row = {
                "id": record.pool_id,
                "input": record.input,
                "category_l4": record.category_l4,
                "owner_name": owner_name or ""
            }
            
            if pool_type == "training":
                row["gt"] = json.dumps(record.gt, ensure_ascii=False) if record.gt else ""
            
            writer.writerow(row)
            yield output.getvalue().encode('utf-8')
            output.seek(0)
            output.truncate()
    
    async def create_export_task(
        self,
        category_l4: str,
        pool_type: str,
        format: str,
        version: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> ExportTask:
        """Create async export task for large files."""
        task_id = f"export_{uuid.uuid4().hex[:12]}"
        
        task = ExportTask(
            task_id=task_id,
            status="pending",
            category_l4=category_l4,
            pool_type=pool_type,
            format=format,
            version=version or "v1.0.0",
            params={
                "requested_by": user_id,
                "requested_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        logger.info(f"Created export task {task_id} for {category_l4}/{pool_type}")
        
        return task
    
    async def get_export_task(self, task_id: str) -> Optional[ExportTask]:
        """Get export task by ID."""
        query = select(ExportTask).where(ExportTask.task_id == task_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def log_download(
        self,
        user_id: Optional[int],
        username: Optional[str],
        category_l4: str,
        pool_type: str,
        format: str,
        version: Optional[str],
        record_count: int,
        file_size: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log download for audit."""
        log = DownloadLog(
            user_id=user_id,
            username=username,
            category_l4=category_l4,
            pool_type=pool_type,
            format=format,
            version=version,
            record_count=record_count,
            file_size=file_size,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(log)
        await self.db.commit()
