"""
Seed data API routes.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db, require_admin
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse, PaginationParams, ResponseModel
from app.schemas.seed import SeedCreate, SeedFilter, SeedRead, SeedUpdate, SeedUploadResponse
from app.services.seed_service import SeedService

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=PaginatedResponse[List[SeedRead]])
async def list_seeds(
    category_l4: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, pattern="^(draft|official)$"),
    keyword: Optional[str] = Query(None, description="Search keyword"),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> PaginatedResponse[List[SeedRead]]:
    """List seed data with filtering."""
    service = SeedService(db)
    filter_params = SeedFilter(
        category_l4=category_l4,
        status=status,
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


@router.get("/{seed_id}", response_model=ResponseModel[SeedRead])
async def get_seed(
    seed_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
) -> ResponseModel[SeedRead]:
    """Get seed by ID."""
    service = SeedService(db)
    seed = await service.get_by_seed_id(seed_id)
    
    if not seed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seed not found",
        )
    
    return ResponseModel(code=0, message="success", data=seed)


@router.post("/upload", response_model=ResponseModel[SeedUploadResponse])
async def upload_seeds(
    file: UploadFile = File(..., description="Excel or CSV file"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
) -> ResponseModel[SeedUploadResponse]:
    """Upload seed data from file."""
    service = SeedService(db)
    
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
    
    result = await service.upload_from_file(
        file=file.file,
        filename=file.filename,
        created_by=current_user.id,
    )
    
    logger.info(f"Seed upload: {result.success} created, {result.duplicated} duplicated")
    
    return ResponseModel(code=0, message="success", data=result)


@router.post("", response_model=ResponseModel[SeedRead])
async def create_seed(
    data: SeedCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
) -> ResponseModel[SeedRead]:
    """Create a single seed."""
    service = SeedService(db)
    seed = await service.create(data, created_by=current_user.id)
    
    return ResponseModel(code=0, message="success", data=seed)


@router.put("/{seed_id}", response_model=ResponseModel[SeedRead])
async def update_seed(
    seed_id: str,
    data: SeedUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
) -> ResponseModel[SeedRead]:
    """Update seed."""
    service = SeedService(db)
    seed = await service.update(seed_id, data)
    
    if not seed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seed not found",
        )
    
    return ResponseModel(code=0, message="success", data=seed)


@router.post("/{seed_id}/confirm", response_model=ResponseModel[SeedRead])
async def confirm_seed(
    seed_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
) -> ResponseModel[SeedRead]:
    """Confirm seed to official status."""
    service = SeedService(db)
    seed = await service.confirm(seed_id, confirmed_by=current_user.id)
    
    if not seed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seed not found",
        )
    
    logger.info(f"Seed confirmed: {seed_id} by user {current_user.username}")
    
    return ResponseModel(code=0, message="success", data=seed)


@router.delete("/{seed_id}", response_model=ResponseModel[dict])
async def delete_seed(
    seed_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
) -> ResponseModel[dict]:
    """Delete seed."""
    service = SeedService(db)
    success = await service.delete(seed_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seed not found",
        )
    
    logger.info(f"Seed deleted: {seed_id} by user {current_user.username}")
    
    return ResponseModel(code=0, message="success", data={"deleted": True})
