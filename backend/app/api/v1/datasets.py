"""
Dataset download API routes.
"""
import io
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user_optional, require_data_engineer
from app.core.logging import get_logger
from app.schemas.common import ResponseModel
from app.schemas.dataset import (
    DatasetInfoResponse,
    DatasetVersionsResponse,
    DatasetDownloadRequest,
    ExportTaskCreate,
    ExportTaskResponse,
    ExportTaskStatusResponse,
)
from app.services.dataset_service import DatasetService

logger = get_logger(__name__)
router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/info", response_model=ResponseModel[DatasetInfoResponse])
async def get_dataset_info(
    category_l4: str = Query(..., description="Category L4 name"),
    pool_type: str = Query("both", description="Pool type: training/evaluation/both"),
    version: Optional[str] = Query(None, description="Specific version"),
    db: AsyncSession = Depends(get_db),
) -> ResponseModel[DatasetInfoResponse]:
    """Get dataset metadata."""
    service = DatasetService(db)
    info = await service.get_dataset_info(category_l4, pool_type, version)
    return ResponseModel(data=info)


@router.get("/versions", response_model=ResponseModel[DatasetVersionsResponse])
async def get_dataset_versions(
    category_l4: str = Query(..., description="Category L4 name"),
    db: AsyncSession = Depends(get_db),
) -> ResponseModel[DatasetVersionsResponse]:
    """Get available versions for a category."""
    from sqlalchemy import select
    from app.models.dataset_export import DatasetVersion
    
    query = select(DatasetVersion).where(
        DatasetVersion.category_l4 == category_l4
    ).order_by(DatasetVersion.created_at.desc())
    
    result = await db.execute(query)
    versions = result.scalars().all()
    
    if not versions:
        # Return default version if none exists
        return ResponseModel(
            data=DatasetVersionsResponse(
                category=category_l4,
                versions=[
                    {
                        "version": "v1.0.0",
                        "release_date": datetime.now(timezone.utc),
                        "changelog": "Initial version",
                        "is_latest": True
                    }
                ]
            )
        )
    
    return ResponseModel(
        data=DatasetVersionsResponse(
            category=category_l4,
            versions=[
                {
                    "version": v.version_id,
                    "release_date": v.created_at,
                    "changelog": v.changelog or "",
                    "is_latest": v.is_latest
                }
                for v in versions
            ]
        )
    )


@router.get("/download")
async def download_dataset(
    request: Request,
    category_l4: Optional[str] = Query(None, description="Category L4 name (optional, default: all categories)"),
    pool_type: str = Query(..., description="Pool type: training/evaluation"),
    format: str = Query("json", description="File format: json/csv/parquet"),
    version: Optional[str] = Query(None, description="Specific version"),
    limit: Optional[int] = Query(5000, ge=1, le=100000, description="Limit records (default: 5000)"),
    offset: int = Query(0, ge=0, description="Offset"),
    random: bool = Query(False, description="Random sample"),
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """Download dataset (streaming, for small files < 100MB).
    
    Args:
        category_l4: 类目L4名称（可选，不填则下载全部类目）
        pool_type: 池类型（training/evaluation）
        format: 文件格式（json/csv/parquet）
        limit: 下载数量（默认5000）
        random: 是否随机抽取
    """
    # Validate format
    if format not in ["json", "csv", "parquet"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {format}"
        )
    
    # Parquet requires async export
    if format == "parquet":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parquet format requires async export. Use /export endpoint."
        )
    
    # Get dataset info to check size
    service = DatasetService(db)
    info = await service.get_dataset_info(category_l4 or "all", pool_type)
    
    pool_info = info.pools.get(pool_type, {})
    estimated_size = pool_info.get("file_size", 0)
    record_count = pool_info.get("record_count", 0)
    
    # If estimated size > 100MB, suggest async export
    if estimated_size > 100 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large for direct download. Use async export."
        )
    
    # Build filename
    version_str = version or info.latest_version
    category_name = category_l4 or "all"
    filename = f"{pool_type}_{category_name}_{limit or 'all'}_{version_str}.{format}"
    
    # Set content type
    content_type_map = {
        "json": "application/json",
        "csv": "text/csv",
        "parquet": "application/octet-stream"
    }
    
    # Log download
    await service.log_download(
        user_id=user.get("id") if user else None,
        username=user.get("name") if user else None,
        category_l4=category_l4 or "all",
        pool_type=pool_type,
        format=format,
        version=version_str,
        record_count=limit or record_count,
        file_size=estimated_size,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    # Stream response
    return StreamingResponse(
        service.stream_dataset(category_l4, pool_type, format, limit, offset, random),
        media_type=content_type_map.get(format, "application/octet-stream"),
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Accept-Ranges": "bytes"
        }
    )


@router.post("/export", response_model=ResponseModel[ExportTaskResponse])
async def create_export_task(
    request_data: ExportTaskCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(get_current_user_optional),
) -> ResponseModel[ExportTaskResponse]:
    """Create async export task for large files."""
    service = DatasetService(db)
    
    # Create task
    task = await service.create_export_task(
        category_l4=request_data.category_l4,
        pool_type=request_data.pool_type,
        format=request_data.format,
        version=request_data.version,
        user_id=user.get("id") if user else None
    )
    
    # Trigger Celery task for async processing
    from app.tasks.export_tasks import export_dataset_task
    export_dataset_task.delay(
        task_id=task.task_id,
        category_l4=request_data.category_l4,
        pool_type=request_data.pool_type,
        format=request_data.format,
        version=request_data.version
    )
    
    return ResponseModel(
        data=ExportTaskResponse(
            task_id=task.task_id,
            status=task.status,
            progress=task.progress,
            file_size=task.file_size,
            record_count=task.record_count,
            created_at=task.created_at
        )
    )


@router.get("/export/{task_id}/status", response_model=ResponseModel[ExportTaskStatusResponse])
async def get_export_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> ResponseModel[ExportTaskStatusResponse]:
    """Get export task status."""
    service = DatasetService(db)
    task = await service.get_export_task(task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export task not found"
        )
    
    # Calculate estimated time
    estimated_time = None
    if task.status == "running" and task.progress > 0:
        # Rough estimate based on progress
        elapsed = (datetime.now(timezone.utc) - task.created_at).total_seconds()
        total_estimated = elapsed / (task.progress / 100)
        estimated_time = int(total_estimated - elapsed)
    
    return ResponseModel(
        data=ExportTaskStatusResponse(
            task_id=task.task_id,
            status=task.status,
            progress=task.progress,
            estimated_time=estimated_time,
            file_size=task.file_size,
            download_url=task.download_url,
            expires_at=task.expires_at,
            error_message=task.error_message
        )
    )


@router.get("/export/{task_id}/download")
async def download_exported_file(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """Download completed export file."""
    service = DatasetService(db)
    task = await service.get_export_task(task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export task not found"
        )
    
    if task.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export task not completed. Current status: {task.status}"
        )
    
    if not task.file_path or not os.path.exists(task.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found"
        )
    
    # Check if expired
    if task.expires_at and task.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Export file has expired. Please create a new export task."
        )
    
    # Build filename
    filename = f"{task.category_l4}_{task.pool_type}_{task.version}.{task.format}"
    
    return FileResponse(
        task.file_path,
        media_type="application/octet-stream",
        filename=filename
    )
