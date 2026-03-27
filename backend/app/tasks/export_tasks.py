"""
Dataset export background tasks.

Handles large file generation asynchronously.
"""
import json
import csv
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from celery import Task
from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import sessionmaker

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.logging import get_logger
from app.models.dataset_export import ExportTask

logger = get_logger(__name__)

# Database setup for sync operations
sync_engine = create_engine(settings.database_url_sync)
SyncSession = sessionmaker(bind=sync_engine)

# Export storage directory
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


class ExportDatasetTask(Task):
    """Base task for dataset export with error handling."""
    
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes between retries
    retry_kwargs = {"max_retries": 3}
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Update task status on failure."""
        logger.error(f"Export task {task_id} failed: {exc}")
        self._update_task_status(task_id, "failed", str(exc))
    
    def _update_task_status(self, task_id: str, status: str, error_message: str = None):
        """Update task status in database."""
        try:
            db = SyncSession()
            task = db.query(ExportTask).filter(ExportTask.task_id == task_id).first()
            if task:
                task.status = status
                if error_message:
                    task.error_message = error_message
                if status == "completed":
                    task.completed_at = datetime.now(timezone.utc)
                db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")


@celery_app.task(bind=True, base=ExportDatasetTask)
def export_dataset_task(
    self,
    task_id: str,
    category_l4: str,
    pool_type: str,
    format: str,
    version: Optional[str] = None
):
    """
    Export dataset to file asynchronously.
    
    Args:
        task_id: Export task ID
        category_l4: Category L4 name
        pool_type: Pool type (training/evaluation/both)
        format: File format (json/csv/parquet)
        version: Dataset version
    
    Returns:
        dict: Export result with file path and metadata
    """
    logger.info(f"Starting export task {task_id}: {category_l4}/{pool_type} as {format}")
    
    # Update status to running
    self._update_task_status(task_id, "running")
    self.update_state(state="PROGRESS", meta={"progress": 0, "stage": "querying"})
    
    db = SyncSession()
    
    try:
        # Query data from database
        from app.models.data_pool import DataPool
        
        query = select(DataPool).where(
            and_(
                DataPool.category_l4 == category_l4,
            )
        )
        
        # Apply pool_type filter
        if pool_type != "both":
            query = query.where(DataPool.pool_type == pool_type)
        
        result = db.execute(query)
        records = result.scalars().all()
        
        total_records = len(records)
        logger.info(f"Found {total_records} records for export")
        
        self.update_state(state="PROGRESS", meta={"progress": 10, "stage": "generating"})
        
        # Generate file
        filename = f"{category_l4.replace('/', '_')}_{pool_type}_{version or 'latest'}_{uuid.uuid4().hex[:8]}.{format}"
        filepath = os.path.join(EXPORT_DIR, filename)
        
        if format == "json":
            file_size = _export_json(records, filepath, pool_type, self)
        elif format == "csv":
            file_size = _export_csv(records, filepath, pool_type, self)
        elif format == "parquet":
            file_size = _export_parquet(records, filepath, pool_type, self)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        self.update_state(state="PROGRESS", meta={"progress": 90, "stage": "finalizing"})
        
        # Update task with file info
        task = db.query(ExportTask).filter(ExportTask.task_id == task_id).first()
        if task:
            task.status = "completed"
            task.file_path = filepath
            task.file_size = file_size
            task.record_count = total_records
            task.completed_at = datetime.now(timezone.utc)
            task.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            db.commit()
        
        self.update_state(state="SUCCESS", meta={"progress": 100, "stage": "completed"})
        
        logger.info(f"Export task {task_id} completed: {filepath} ({file_size} bytes)")
        
        return {
            "task_id": task_id,
            "status": "completed",
            "file_path": filepath,
            "file_size": file_size,
            "record_count": total_records,
        }
        
    except Exception as e:
        logger.error(f"Export task {task_id} failed: {e}")
        self._update_task_status(task_id, "failed", str(e))
        raise
    
    finally:
        db.close()


def _export_json(records, filepath: str, pool_type: str, task) -> int:
    """Export records to JSON file."""
    data = {
        "metadata": {
            "format": "json",
            "pool_type": pool_type,
            "record_count": len(records),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "data": []
    }
    
    total = len(records)
    for i, record in enumerate(records):
        item = {
            "id": record.pool_id,
            "input": record.input,
            "category_l4": record.category_l4,
        }
        
        if record.pool_type == "training" and record.gt:
            item["gt"] = record.gt
        
        data["data"].append(item)
        
        # Update progress every 1000 records
        if i % 1000 == 0 and total > 0:
            progress = 10 + int((i / total) * 70)
            task.update_state(state="PROGRESS", meta={"progress": progress, "stage": "generating"})
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return os.path.getsize(filepath)


def _export_csv(records, filepath: str, pool_type: str, task) -> int:
    """Export records to CSV file."""
    # Determine fields based on pool types in records
    has_training = any(r.pool_type == "training" for r in records)
    
    fieldnames = ["id", "input", "pool_type", "category_l4"]
    if has_training:
        fieldnames.append("gt")
    
    total = len(records)
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, record in enumerate(records):
            row = {
                "id": record.pool_id,
                "input": record.input,
                "pool_type": record.pool_type,
                "category_l4": record.category_l4,
            }
            
            if has_training and record.gt:
                row["gt"] = json.dumps(record.gt, ensure_ascii=False)
            
            writer.writerow(row)
            
            # Update progress every 1000 records
            if i % 1000 == 0 and total > 0:
                progress = 10 + int((i / total) * 70)
                task.update_state(state="PROGRESS", meta={"progress": progress, "stage": "generating"})
    
    return os.path.getsize(filepath)


def _export_parquet(records, filepath: str, pool_type: str, task) -> int:
    """Export records to Parquet file."""
    # Convert records to pandas DataFrame
    data = []
    total = len(records)
    
    for i, record in enumerate(records):
        item = {
            "id": record.pool_id,
            "input": record.input,
            "pool_type": record.pool_type,
            "category_l4": record.category_l4,
        }
        
        if record.pool_type == "training" and record.gt:
            item["gt"] = json.dumps(record.gt, ensure_ascii=False)
        else:
            item["gt"] = None
        
        data.append(item)
        
        # Update progress every 1000 records
        if i % 1000 == 0 and total > 0:
            progress = 10 + int((i / total) * 70)
            task.update_state(state="PROGRESS", meta={"progress": progress, "stage": "generating"})
    
    df = pd.DataFrame(data)
    
    # Convert to PyArrow table and write to Parquet
    table = pa.Table.from_pandas(df)
    pq.write_table(table, filepath, compression="snappy")
    
    return os.path.getsize(filepath)


@celery_app.task
def cleanup_expired_exports():
    """Clean up expired export files."""
    logger.info("Running cleanup of expired exports")
    
    db = SyncSession()
    
    try:
        # Find expired tasks
        expired_tasks = db.query(ExportTask).filter(
            and_(
                ExportTask.status == "completed",
                ExportTask.expires_at < datetime.now(timezone.utc)
            )
        ).all()
        
        deleted_count = 0
        for task in expired_tasks:
            if task.file_path and os.path.exists(task.file_path):
                try:
                    os.remove(task.file_path)
                    deleted_count += 1
                    logger.info(f"Deleted expired export: {task.file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete {task.file_path}: {e}")
            
            # Mark as expired
            task.status = "expired"
        
        db.commit()
        logger.info(f"Cleanup completed: {deleted_count} files deleted")
        
        return {"deleted_count": deleted_count}
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise
    
    finally:
        db.close()
