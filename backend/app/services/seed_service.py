"""
Seed data service.
"""
import hashlib
import json
import uuid
from io import BytesIO
from typing import List, Optional

import pandas as pd
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.seed import Seed
from app.schemas.common import PaginationInfo
from app.schemas.seed import SeedCreate, SeedFilter, SeedUpdate, SeedUploadResponse
from app.services.base import BaseService


class SeedService(BaseService[Seed]):
    """Seed data service."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Seed)
    
    @staticmethod
    def compute_hash(input_text: str, gt: dict) -> str:
        """Compute SHA256 hash for deduplication."""
        content = f"{input_text}:{json.dumps(gt, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def get_by_seed_id(self, seed_id: str) -> Optional[Seed]:
        """Get seed by seed_id."""
        result = await self.db.execute(
            select(Seed).where(Seed.seed_id == seed_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_hash(self, hash_value: str) -> Optional[Seed]:
        """Get seed by hash."""
        result = await self.db.execute(
            select(Seed).where(Seed.hash == hash_value)
        )
        return result.scalar_one_or_none()
    
    async def get_list(
        self,
        filter_params: SeedFilter,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        """Get seed list with filtering."""
        query = select(Seed)
        
        # Apply filters
        if filter_params.category_l4:
            query = query.where(Seed.category_l4 == filter_params.category_l4)
        
        if filter_params.status:
            query = query.where(Seed.status == filter_params.status)
        
        if filter_params.keyword:
            keyword = f"%{filter_params.keyword}%"
            query = query.where(
                or_(
                    Seed.input.ilike(keyword),
                    Seed.category_l4.ilike(keyword),
                )
            )
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Pagination
        query = query.order_by(desc(Seed.created_at))
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        pages = (total + size - 1) // size
        
        return {
            "items": list(items),
            "pagination": PaginationInfo(
                page=page,
                size=size,
                total=total,
                pages=pages,
            ),
        }
    
    async def create(
        self,
        data: SeedCreate,
        created_by: Optional[int] = None,
    ) -> Seed:
        """Create a new seed."""
        # Compute hash
        hash_value = self.compute_hash(data.input, data.gt)
        
        # Check for duplicate
        existing = await self.get_by_hash(hash_value)
        if existing:
            raise ValueError(f"Duplicate seed detected: {existing.seed_id}")
        
        seed_data = {
            "seed_id": data.seed_id or f"seed_{uuid.uuid4().hex[:12]}",
            "input": data.input,
            "gt": data.gt,
            "category_l4": data.category_l4,
            "category_path": data.category_path,
            "status": "draft",
            "hash": hash_value,
            "created_by": created_by,
        }
        
        return await super().create(**seed_data)
    
    async def update(
        self,
        seed_id: str,
        data: SeedUpdate,
    ) -> Optional[Seed]:
        """Update seed."""
        seed = await self.get_by_seed_id(seed_id)
        if not seed:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Recompute hash if input or gt changed
        if "input" in update_data or "gt" in update_data:
            new_input = update_data.get("input", seed.input)
            new_gt = update_data.get("gt", seed.gt)
            update_data["hash"] = self.compute_hash(new_input, new_gt)
        
        for key, value in update_data.items():
            setattr(seed, key, value)
        
        await self.db.commit()
        await self.db.refresh(seed)
        return seed
    
    async def confirm(self, seed_id: str, confirmed_by: int) -> Optional[Seed]:
        """Confirm seed to official status."""
        seed = await self.get_by_seed_id(seed_id)
        if not seed:
            return None
        
        from datetime import datetime, timezone
        
        seed.status = "official"
        seed.confirmed_by = confirmed_by
        seed.confirmed_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(seed)
        return seed
    
    async def delete(self, seed_id: str) -> bool:
        """Delete seed."""
        seed = await self.get_by_seed_id(seed_id)
        if not seed:
            return False
        
        await self.db.delete(seed)
        await self.db.commit()
        return True
    
    async def upload_from_file(
        self,
        file: BytesIO,
        filename: str,
        created_by: int,
    ) -> SeedUploadResponse:
        """Upload seeds from Excel/CSV file."""
        # Read file
        if filename.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        total = len(df)
        success = 0
        duplicated = 0
        failed = 0
        details = []
        
        for idx, row in df.iterrows():
            try:
                # Validate required fields
                if pd.isna(row.get("input")) or pd.isna(row.get("gt")):
                    failed += 1
                    details.append({
                        "row": idx + 1,
                        "status": "failed",
                        "reason": "Missing required fields: input or gt",
                    })
                    continue
                
                # Parse gt (JSON string or dict)
                gt = row.get("gt")
                if isinstance(gt, str):
                    gt = json.loads(gt)
                
                # Create seed
                seed_data = SeedCreate(
                    input=str(row.get("input")),
                    gt=gt,
                    category_l4=str(row.get("category_l4", "default")),
                    category_path=row.get("category_path"),
                )
                
                await self.create(seed_data, created_by=created_by)
                success += 1
                details.append({"row": idx + 1, "status": "success"})
                
            except ValueError as e:
                if "Duplicate" in str(e):
                    duplicated += 1
                    details.append({
                        "row": idx + 1,
                        "status": "duplicated",
                        "reason": str(e),
                    })
                else:
                    failed += 1
                    details.append({
                        "row": idx + 1,
                        "status": "failed",
                        "reason": str(e),
                    })
            except Exception as e:
                failed += 1
                details.append({
                    "row": idx + 1,
                    "status": "failed",
                    "reason": str(e),
                })
        
        return SeedUploadResponse(
            total=total,
            success=success,
            duplicated=duplicated,
            failed=failed,
            details=details,
        )
