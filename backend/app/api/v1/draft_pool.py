"""
Draft Pool (synthetic data) API routes.
提供了初创池的完整CRUD、上传、下载、确认/拒绝等功能。
确认后会自动执行5:5分流。
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db, require_admin, require_data_engineer
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse, PaginationParams, ResponseModel
from app.schemas.synthetic import (
    SyntheticConfirmRequest,
    SyntheticConfirmResponse,
    SyntheticFilter,
    SyntheticRead,
    SyntheticUpdate,
    SyntheticUploadResponse,
)
from app.services.synthetic_service import SyntheticService
from app.services.router_service import RouterService

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=PaginatedResponse[List[SyntheticRead]])
async def list_draft_pool(
    category_l4: Optional[str] = Query(None, description="按四级类目筛选"),
    status: Optional[str] = Query(None, pattern="^(draft|confirmed|rejected)$", description="按状态筛选"),
    difficulty: Optional[str] = Query(None, pattern="^(low|medium|high|ultra)$", description="按难度筛选"),
    seed_id: Optional[str] = Query(None, description="按种子ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_data_engineer),
):
    """
    查询初创池（合成数据）列表。
    
    支持按类目、状态、难度、种子ID筛选，支持关键词搜索。
    """
    service = SyntheticService(db)
    filter_params = SyntheticFilter(
        category_l4=category_l4,
        status=status,
        difficulty=difficulty,
        seed_id=seed_id,
        keyword=keyword,
    )
    
    result = await service.get_list(
        filter_params=filter_params,
        page=pagination.page,
        size=pagination.size,
    )
    
    return PaginatedResponse(
        code=0,
        message="success",
        data=result["items"],
        pagination=result["pagination"],
    )


@router.get("/{synthetic_id}", response_model=ResponseModel[SyntheticRead])
async def get_synthetic(
    synthetic_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_data_engineer),
):
    """获取单条合成数据详情。"""
    service = SyntheticService(db)
    synthetic = await service.get_by_synthetic_id(synthetic_id)
    
    if not synthetic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Synthetic data not found",
        )
    
    return ResponseModel(code=0, message="success", data=synthetic)


@router.post("/upload", response_model=ResponseModel[SyntheticUploadResponse])
async def upload_synthetics(
    file: UploadFile = File(..., description="Excel或CSV文件"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_data_engineer),
):
    """
    批量上传合成数据。
    
    支持Excel (.xlsx, .xls) 或 CSV 格式。
    必填字段：input, gt, category_l4
    可选字段：category_path, difficulty
    
    会自动进行SHA256去重校验。
    """
    service = SyntheticService(db)
    
    # Validate file type
    if not file.filename or not (
        file.filename.endswith(".xlsx") 
        or file.filename.endswith(".csv")
        or file.filename.endswith(".xls")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel (.xlsx, .xls) or CSV files are supported",
        )
    
    result = await service.upload_from_excel(
        file=file.file,
        filename=file.filename,
        created_by=current_user.id,
    )
    
    logger.info(f"Synthetic upload: {result.success} created, {result.duplicated} duplicated")
    
    return ResponseModel(code=0, message="success", data=result)


@router.get("/export/download")
async def export_synthetics(
    category_l4: Optional[str] = Query(None, description="按类目筛选"),
    status: Optional[str] = Query(None, pattern="^(draft|confirmed|rejected)$"),
    difficulty: Optional[str] = Query(None, pattern="^(low|medium|high|ultra)$"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_data_engineer),
):
    """
    导出合成数据为Excel文件。
    
    支持按类目、状态、难度筛选后导出。
    """
    service = SyntheticService(db)
    filter_params = SyntheticFilter(
        category_l4=category_l4,
        status=status,
        difficulty=difficulty,
    )
    
    output = await service.export_to_excel(filter_params)
    
    filename = f"synthetic_data_{category_l4 or 'all'}.xlsx"
    
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.put("/{synthetic_id}", response_model=ResponseModel[SyntheticRead])
async def update_synthetic(
    synthetic_id: str,
    data: SyntheticUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_data_engineer),
):
    """
    编辑合成数据。
    
    注意：已确认(confirmed)或已拒绝(rejected)的数据不能编辑。
    """
    service = SyntheticService(db)
    
    try:
        synthetic = await service.update(synthetic_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    if not synthetic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Synthetic data not found",
        )
    
    logger.info(f"Synthetic updated: {synthetic_id} by user {current_user.username}")
    
    return ResponseModel(code=0, message="success", data=synthetic)


@router.post("/{synthetic_id}/confirm", response_model=ResponseModel[SyntheticConfirmResponse])
async def confirm_synthetic(
    synthetic_id: str,
    request: SyntheticConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """
    确认或拒绝单条合成数据。
    
    - confirm: 确认数据有效，确认后会自动执行5:5分流
    - reject: 拒绝数据，可填写拒绝原因
    
    **确认后自动分流逻辑：**
    1. 将合成数据状态改为 confirmed
    2. 调用5:5分流算法
    3. 按category_l4分组
    4. 每组随机打乱后5:5分割
    5. 分别写入训练池(含GT)和评测池(GT隐藏)
    """
    service = SyntheticService(db)
    router_service = RouterService(db)
    
    # 执行确认/拒绝
    result = await service.confirm(
        synthetic_id=synthetic_id,
        action=request.action,
        confirmed_by=current_user.id,
        reason=request.reason,
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )
    
    # 如果是确认操作，执行5:5分流
    if request.action == "confirm":
        route_result = await router_service.execute_5_5_routing(
            synthetic_ids=[synthetic_id]
        )
        result.route_result = route_result
        
        logger.info(
            f"Synthetic confirmed and routed: {synthetic_id}, "
            f"batch_id={route_result.get('batch_id')}, "
            f"train={route_result.get('training')}, "
            f"eval={route_result.get('evaluation')}"
        )
    else:
        logger.info(f"Synthetic rejected: {synthetic_id}, reason={request.reason}")
    
    return ResponseModel(code=0, message="success", data=result)


@router.post("/batch-confirm", response_model=ResponseModel[List[SyntheticConfirmResponse]])
async def batch_confirm_synthetics(
    synthetic_ids: List[str],
    request: SyntheticConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """
    批量确认或拒绝合成数据。
    
    确认后会自动执行5:5分流。
    """
    service = SyntheticService(db)
    router_service = RouterService(db)
    
    results = []
    confirmed_ids = []
    
    # 先处理所有确认/拒绝操作
    for synthetic_id in synthetic_ids:
        result = await service.confirm(
            synthetic_id=synthetic_id,
            action=request.action,
            confirmed_by=current_user.id,
            reason=request.reason,
        )
        results.append(result)
        
        if result.success and request.action == "confirm":
            confirmed_ids.append(synthetic_id)
    
    # 批量执行分流（如果是确认操作）
    if confirmed_ids and request.action == "confirm":
        route_result = await router_service.execute_5_5_routing(
            synthetic_ids=confirmed_ids
        )
        
        # 将分流结果添加到每个响应中
        for result in results:
            if result.success:
                result.route_result = route_result
        
        logger.info(
            f"Batch confirmed and routed: {len(confirmed_ids)} synthetics, "
            f"batch_id={route_result.get('batch_id')}"
        )
    
    return ResponseModel(code=0, message="success", data=results)


@router.delete("/{synthetic_id}", response_model=ResponseModel[dict])
async def delete_synthetic(
    synthetic_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """
    删除合成数据。
    
    注意：已确认(confirmed)的数据不能删除。
    """
    service = SyntheticService(db)
    
    try:
        success = await service.delete(synthetic_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Synthetic data not found",
        )
    
    logger.info(f"Synthetic deleted: {synthetic_id} by user {current_user.username}")
    
    return ResponseModel(code=0, message="success", data={"deleted": True})


# ========== 路由相关API ==========

@router.post("/route/preview", response_model=ResponseModel[dict])
async def preview_routing(
    synthetic_ids: Optional[List[str]] = None,
    category_l4: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    """
    预览5:5分流结果（不实际执行）。
    
    用于确认前查看分流效果。
    """
    router_service = RouterService(db)
    
    result = await router_service.preview_routing(
        synthetic_ids=synthetic_ids,
        category_l4=category_l4,
    )
    
    return ResponseModel(code=0, message="success", data=result)


@router.get("/route/batch/{batch_id}", response_model=ResponseModel[dict])
async def get_route_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """查询分流批次状态。"""
    router_service = RouterService(db)
    
    result = await router_service.get_batch_status(batch_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found",
        )
    
    return ResponseModel(code=0, message="success", data=result)



# ========== 测试用API（开发环境使用，不需要认证） ==========

@router.post("/test/upload", response_model=ResponseModel[SyntheticUploadResponse])
async def test_upload_synthetics(
    file: UploadFile = File(..., description="Excel或CSV文件"),
    db: AsyncSession = Depends(get_db),
):
    """
    【测试用】批量上传合成数据（无需认证）。
    
    支持Excel (.xlsx, .xls) 或 CSV 格式。
    必填字段：input, gt, category_l4
    可选字段：category_path, difficulty
    
    Excel示例格式：
    | input | gt | category_l4 | category_path | difficulty |
    | UPVC管 DN20 | {"材质":"UPVC"} | 管材 | 建材/管材 | medium |
    """
    service = SyntheticService(db)
    
    # Validate file type
    if not file.filename or not (
        file.filename.endswith(".xlsx") 
        or file.filename.endswith(".csv")
        or file.filename.endswith(".xls")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel (.xlsx, .xls) or CSV files are supported",
        )
    
    result = await service.upload_from_excel(
        file=file.file,
        filename=file.filename,
        created_by=1,  # 测试用户ID
    )
    
    logger.info(f"[TEST] Synthetic upload: {result.success} created, {result.duplicated} duplicated")
    
    return ResponseModel(code=0, message="success", data=result)


@router.get("/test/list", response_model=PaginatedResponse[List[SyntheticRead]])
async def test_list_draft_pool(
    category_l4: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """【测试用】查询初创池列表（无需认证）。"""
    service = SyntheticService(db)
    filter_params = SyntheticFilter(
        category_l4=category_l4,
        status=status,
    )
    
    result = await service.get_list(
        filter_params=filter_params,
        page=page,
        size=size,
    )
    
    return PaginatedResponse(
        code=0,
        message="success",
        data=result["items"],
        pagination=result["pagination"],
    )


@router.post("/test/{synthetic_id}/confirm", response_model=ResponseModel[SyntheticConfirmResponse])
async def test_confirm_synthetic(
    synthetic_id: str,
    request: SyntheticConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    【测试用】确认或拒绝合成数据（无需认证）。
    
    - confirm: 确认数据有效，确认后会自动执行5:5分流
    - reject: 拒绝数据
    """
    service = SyntheticService(db)
    router_service = RouterService(db)
    
    # 执行确认/拒绝
    result = await service.confirm(
        synthetic_id=synthetic_id,
        action=request.action,
        confirmed_by=1,  # 测试用户ID
        reason=request.reason,
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )
    
    # 如果是确认操作，执行5:5分流
    if request.action == "confirm":
        route_result = await router_service.execute_5_5_routing(
            synthetic_ids=[synthetic_id]
        )
        result.route_result = route_result
        
        logger.info(
            f"[TEST] Synthetic confirmed and routed: {synthetic_id}, "
            f"batch_id={route_result.get('batch_id')}"
        )
    
    return ResponseModel(code=0, message="success", data=result)


@router.delete("/test/{synthetic_id}", response_model=ResponseModel[dict])
async def test_delete_synthetic(
    synthetic_id: str,
    db: AsyncSession = Depends(get_db),
):
    """【测试用】删除合成数据（无需认证）。"""
    service = SyntheticService(db)
    
    try:
        success = await service.delete(synthetic_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Synthetic data not found",
        )
    
    logger.info(f"[TEST] Synthetic deleted: {synthetic_id}")
    
    return ResponseModel(code=0, message="success", data={"deleted": True})
