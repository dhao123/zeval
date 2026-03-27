"""
Upload Batch API routes.
"""
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.upload_batch import (
    UploadBatchResponse,
    UploadBatchUpdate,
    FileUploadResponse,
)
from app.services.upload_batch_service import UploadBatchService
from app.services.oss_service import get_oss_service

logger = get_logger(__name__)
router = APIRouter(prefix="/upload-batches", tags=["Upload Batches"])


@router.get("", response_model=PaginatedResponse[list[UploadBatchResponse]])
async def list_upload_batches(
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取上传批次列表"""
    service = UploadBatchService(db)
    
    # 普通用户只能看自己的，管理员可以看全部
    owner_id = None
    # TODO: 判断是否为管理员
    # if not current_user.get("is_admin"):
    #     owner_id = current_user.get("id")
    
    items, total = await service.list_batches(
        owner_id=owner_id,
        status=status,
        page=page,
        size=size
    )
    
    pages = (total + size - 1) // size
    
    return {
        "code": 0,
        "message": "success",
        "data": [item.to_dict() for item in items],
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "pages": pages
        }
    }


@router.get("/{batch_id}", response_model=ResponseModel[UploadBatchResponse])
async def get_upload_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取批次详情"""
    service = UploadBatchService(db)
    batch = await service.get_batch_by_id(batch_id)
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="批次不存在"
        )
    
    return ResponseModel(
        code=0,
        message="success",
        data=batch.to_dict()
    )


@router.get("/{batch_id}/cases", response_model=PaginatedResponse[dict])
async def get_batch_cases(
    batch_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取批次下的case列表"""
    service = UploadBatchService(db)
    
    items, total = await service.get_batch_cases(
        batch_id=batch_id,
        page=page,
        size=size
    )
    
    pages = (total + size - 1) // size
    
    return PaginatedResponse(
        code=0,
        message="success",
        data=[{
            "id": item.id,
            "synthetic_id": item.synthetic_id,
            "input": item.input,
            "gt": item.gt,
            "category_l4": item.category_l4,
            "status": item.status,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        } for item in items],
        pagination={
            "page": page,
            "size": size,
            "total": total,
            "pages": pages
        }
    )


@router.post("/upload", response_model=ResponseModel[FileUploadResponse])
async def upload_file(
    file: UploadFile = File(..., description="上传的文件"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """上传文件并创建批次"""
    # 检查文件
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空"
        )
    
    # 读取文件内容
    content = await file.read()
    file_size = len(content)
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件不能为空"
        )
    
    # 上传到OSS
    oss_service = get_oss_service()
    if not oss_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OSS服务未配置"
        )
    
    try:
        object_key, file_url = await oss_service.upload_file(
            file_content=content,
            filename=file.filename,
            folder="draft_pool_uploads"
        )
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )
    
    # 创建批次记录
    service = UploadBatchService(db)
    batch = await service.create_batch(
        file_name=file.filename,
        file_url=file_url,
        object_key=object_key,
        file_size=file_size,
        owner_id=current_user.get("id"),
        owner_name=current_user.get("name")
    )
    
    return ResponseModel(
        code=0,
        message="文件上传成功",
        data={
            "batch_id": batch.batch_id,
            "file_name": batch.file_name,
            "file_url": batch.file_url,
            "object_key": batch.object_key,
            "file_size": batch.file_size,
            "message": "文件已上传，正在处理中..."
        }
    )


@router.delete("/{batch_id}", response_model=ResponseModel[dict])
async def delete_upload_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """删除上传批次"""
    service = UploadBatchService(db)
    
    # 获取批次
    batch = await service.get_batch_by_id(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="批次不存在"
        )
    
    # 权限检查（只有Owner或管理员可以删除）
    # TODO: 管理员判断
    if batch.owner_id != current_user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此批次"
        )
    
    # 删除批次
    success = await service.delete_batch(batch_id)
    
    if success:
        return ResponseModel(
            code=0,
            message="删除成功",
            data={"deleted": True}
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除失败"
        )


@router.get("/{batch_id}/file-url", response_model=ResponseModel[dict])
async def get_file_signed_url(
    batch_id: str,
    expire_seconds: int = Query(3600, ge=60, le=86400, description="链接有效期(秒)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取文件的临时访问链接"""
    service = UploadBatchService(db)
    batch = await service.get_batch_by_id(batch_id)
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="批次不存在"
        )
    
    # 生成签名URL
    oss_service = get_oss_service()
    if not oss_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OSS服务未配置"
        )
    
    try:
        signed_url = oss_service.get_signed_url(batch.object_key, expire_seconds)
        return ResponseModel(
            code=0,
            message="success",
            data={
                "file_url": signed_url,
                "expire_seconds": expire_seconds
            }
        )
    except Exception as e:
        logger.error(f"Generate signed URL failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成链接失败"
        )
