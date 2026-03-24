"""
Synthetic data service.
"""
import hashlib
import json
import re
import uuid
from io import BytesIO
from typing import List, Optional

import pandas as pd
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.synthetic import SyntheticData
from app.schemas.common import PaginationInfo
from app.schemas.synthetic import (
    SyntheticConfirmResponse,
    SyntheticCreate,
    SyntheticFilter,
    SyntheticUpdate,
    SyntheticUploadResponse,
)
from app.services.base import BaseService
from app.services.category_service import CategoryService


class SyntheticService(BaseService[SyntheticData]):
    """Synthetic data service."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, SyntheticData)
    
    @staticmethod
    def generate_synthetic_id() -> str:
        """Generate global unique synthetic ID."""
        return f"syn_{uuid.uuid4().hex[:16]}"
    
    @staticmethod
    def compute_hash(input_text: str, gt: dict) -> str:
        """Compute SHA256 hash for deduplication."""
        content = f"{input_text}:{json.dumps(gt, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    @staticmethod
    def infer_category_from_input(input_text: str) -> str:
        """Infer category from input text using keyword matching."""
        input_lower = input_text.lower()
        
        # 定义类目关键词映射
        category_keywords = {
            "管材": ["管", "pvc", "ppr", "pe", "钢管", "铸铁管", "波纹管"],
            "阀门": ["阀", "闸阀", "球阀", "蝶阀", "截止阀", "止回阀"],
            "管件": ["弯头", "三通", "法兰", "接头", "活接", "补芯"],
            "泵": ["泵", "水泵", "离心泵", "潜水泵", "管道泵"],
            "电线电缆": ["电缆", "电线", "线缆", "铜芯", "铝芯"],
            "开关插座": ["开关", "插座", "面板", "断路器"],
            "灯具": ["灯", "灯具", "照明", "灯泡", "灯管"],
            "五金工具": ["工具", "扳手", "螺丝刀", "钳子", "锤子"],
            "劳保用品": ["劳保", "手套", "口罩", "安全帽", "防护服"],
            "密封材料": ["密封", "垫片", "密封圈", "密封胶", "生料带"],
            "紧固件": ["螺栓", "螺母", "螺丝", "垫圈", "挡圈", "销"],
        }
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in input_lower:
                    return category
        
        return "其他"
    
    @staticmethod
    def parse_excel_smart(df: pd.DataFrame) -> List[dict]:
        """
        智能解析Excel数据，支持多种格式：
        
        格式1 (标准格式):
        | input | gt | category_l1 | category_l2 | category_l3 | category_l4 | ... |
        
        格式2 (简写格式 - 推荐):
        | 物料描述 | 材质 | 规格 | 压力等级 | 用途 | 一级类目 | 二级类目 | 三级类目 | 四级类目 |
        第一列作为input，其余列（除类目列外）合并为gt
        
        格式3 (单列表):
        | input |
        只有input列，gt为空对象
        """
        results = []
        columns = list(df.columns)
        
        # 标准化列名（去除空格）
        column_map = {col: col.strip() for col in columns}
        df.rename(columns=column_map, inplace=True)
        columns = list(df.columns)
        
        # 检测格式
        has_input_col = "input" in columns
        has_gt_col = "gt" in columns
        
        # 检测四级类目列（支持多种命名方式）
        category_cols = {
            "l1": None,
            "l2": None,
            "l3": None,
            "l4": None,
        }
        for col in columns:
            col_lower = col.lower()
            if col_lower in ["category_l1", "一级类目", "一级", "类目1", "cat1", "l1"]:
                category_cols["l1"] = col
            elif col_lower in ["category_l2", "二级类目", "二级", "类目2", "cat2", "l2"]:
                category_cols["l2"] = col
            elif col_lower in ["category_l3", "三级类目", "三级", "类目3", "cat3", "l3"]:
                category_cols["l3"] = col
            elif col_lower in ["category_l4", "四级类目", "四级", "类目4", "cat4", "l4", "category"]:
                category_cols["l4"] = col
        
        # 元数据列集合（需要跳过的列）
        metadata_cols = set()
        for col in columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ["category", "类目", "cat", "l1", "l2", "l3", "l4", "difficulty", "难度", "path", "路径"]):
                metadata_cols.add(col)
        
        for idx, row in df.iterrows():
            try:
                # 初始化数据
                input_text = None
                gt = {}
                category_l1 = None
                category_l2 = None
                category_l3 = None
                category_l4 = None
                category_path = None
                difficulty = "medium"
                
                # 情况1: 有标准input列
                if has_input_col:
                    input_text = str(row.get("input")) if pd.notna(row.get("input")) else None
                    
                    # 处理gt列
                    if has_gt_col and pd.notna(row.get("gt")):
                        gt_value = row.get("gt")
                        if isinstance(gt_value, str):
                            try:
                                gt = json.loads(gt_value)
                            except json.JSONDecodeError:
                                gt = {"value": gt_value}
                        elif isinstance(gt_value, dict):
                            gt = gt_value
                    
                    # 获取四级类目
                    if category_cols["l1"] and pd.notna(row.get(category_cols["l1"])):
                        category_l1 = str(row.get(category_cols["l1"]))
                    if category_cols["l2"] and pd.notna(row.get(category_cols["l2"])):
                        category_l2 = str(row.get(category_cols["l2"]))
                    if category_cols["l3"] and pd.notna(row.get(category_cols["l3"])):
                        category_l3 = str(row.get(category_cols["l3"]))
                    if category_cols["l4"] and pd.notna(row.get(category_cols["l4"])):
                        category_l4 = str(row.get(category_cols["l4"]))
                    
                    if "category_path" in columns and pd.notna(row.get("category_path")):
                        category_path = str(row.get("category_path"))
                    if "difficulty" in columns and pd.notna(row.get("difficulty")):
                        difficulty = str(row.get("difficulty"))
                
                # 情况2: 没有input列，使用第一列作为input
                else:
                    if len(columns) == 0:
                        raise ValueError("Excel file has no columns")
                    
                    # 第一列作为input
                    first_col = columns[0]
                    input_text = str(row.get(first_col)) if pd.notna(row.get(first_col)) else None
                    
                    # 其余列合并为gt（跳过元数据列）
                    other_cols = columns[1:]
                    gt = {}
                    for col in other_cols:
                        if col in metadata_cols:
                            continue
                        
                        value = row.get(col)
                        if pd.notna(value):
                            gt[col] = str(value)
                    
                    # 从元数据列获取四级类目
                    if category_cols["l1"] and pd.notna(row.get(category_cols["l1"])):
                        category_l1 = str(row.get(category_cols["l1"]))
                    if category_cols["l2"] and pd.notna(row.get(category_cols["l2"])):
                        category_l2 = str(row.get(category_cols["l2"]))
                    if category_cols["l3"] and pd.notna(row.get(category_cols["l3"])):
                        category_l3 = str(row.get(category_cols["l3"]))
                    if category_cols["l4"] and pd.notna(row.get(category_cols["l4"])):
                        category_l4 = str(row.get(category_cols["l4"]))
                    
                    if "category_path" in columns and pd.notna(row.get("category_path")):
                        category_path = str(row.get("category_path"))
                    if "difficulty" in columns and pd.notna(row.get("difficulty")):
                        difficulty = str(row.get("difficulty"))
                
                # 验证input
                if not input_text or input_text.strip() == "" or input_text.lower() == "nan":
                    results.append({
                        "row": idx + 1,
                        "status": "failed",
                        "reason": "Input is empty",
                    })
                    continue
                
                # 如果没有指定四级类目，尝试从input推断（仅作为category_l4）
                if not category_l1 and not category_l2 and not category_l3 and not category_l4:
                    category_l4 = SyntheticService.infer_category_from_input(input_text)
                
                # 如果没有category_path，根据四级类目自动生成
                if not category_path:
                    path_parts = [p for p in [category_l1, category_l2, category_l3, category_l4] if p]
                    if path_parts:
                        category_path = "/".join(path_parts)
                    else:
                        category_path = f"建材/{category_l4 or '其他'}"
                
                results.append({
                    "row": idx + 1,
                    "status": "success",
                    "data": {
                        "input": input_text.strip(),
                        "gt": gt,
                        "category_l1": category_l1,
                        "category_l2": category_l2,
                        "category_l3": category_l3,
                        "category_l4": category_l4,
                        "category_path": category_path,
                        "difficulty": difficulty,
                    }
                })
                
            except Exception as e:
                results.append({
                    "row": idx + 1,
                    "status": "failed",
                    "reason": str(e),
                })
        
        return results
    
    async def get_by_synthetic_id(self, synthetic_id: str) -> Optional[SyntheticData]:
        """Get synthetic data by synthetic_id."""
        result = await self.db.execute(
            select(SyntheticData).where(SyntheticData.synthetic_id == synthetic_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_hash(self, hash_value: str) -> Optional[SyntheticData]:
        """Get synthetic data by hash."""
        result = await self.db.execute(
            select(SyntheticData).where(SyntheticData.hash == hash_value)
        )
        return result.scalar_one_or_none()
    
    async def get_list(
        self,
        filter_params: SyntheticFilter,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        """Get synthetic data list with filtering."""
        query = select(SyntheticData)
        
        # Apply filters
        if filter_params.category_l4:
            query = query.where(SyntheticData.category_l4 == filter_params.category_l4)
        
        if filter_params.status:
            query = query.where(SyntheticData.status == filter_params.status)
        
        if filter_params.seed_id:
            query = query.where(SyntheticData.seed_id == filter_params.seed_id)
        
        if filter_params.keyword:
            keyword = f"%{filter_params.keyword}%"
            query = query.where(
                or_(
                    SyntheticData.input.ilike(keyword),
                    SyntheticData.category_l4.ilike(keyword),
                )
            )
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Pagination
        query = query.order_by(desc(SyntheticData.created_at))
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
        data: SyntheticCreate,
        created_by: Optional[int] = None,
    ) -> SyntheticData:
        """Create a new synthetic data."""
        # Compute hash
        hash_value = self.compute_hash(data.input, data.gt)
        
        # Check for duplicate
        existing = await self.get_by_hash(hash_value)
        if existing:
            raise ValueError(f"Duplicate synthetic data detected: {existing.synthetic_id}")
        
        synthetic_data = {
            "synthetic_id": data.synthetic_id or self.generate_synthetic_id(),
            "input": data.input,
            "gt": data.gt,
            "category_l1": data.category_l1,
            "category_l2": data.category_l2,
            "category_l3": data.category_l3,
            "category_l4": data.category_l4,
            "category_path": data.category_path,
            "status": "draft",
            "hash": hash_value,
            "version": "1.0",
            "seed_id": data.seed_id,
            "standard_id": data.standard_id,
            "skill_id": data.skill_id,
            "difficulty": data.difficulty,
            "synthesis_params": data.synthesis_params,
            "ai_check_result": data.ai_check_result,
            "ai_check_passed": data.ai_check_passed,
            "created_by": created_by,
        }
        
        return await super().create(**synthetic_data)
    
    async def update(
        self,
        synthetic_id: str,
        data: SyntheticUpdate,
    ) -> Optional[SyntheticData]:
        """Update synthetic data."""
        synthetic = await self.get_by_synthetic_id(synthetic_id)
        if not synthetic:
            return None
        
        # Cannot update confirmed data
        if synthetic.status == "confirmed":
            raise ValueError("Cannot update confirmed synthetic data")
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Recompute hash if input or gt changed
        if "input" in update_data or "gt" in update_data:
            new_input = update_data.get("input", synthetic.input)
            new_gt = update_data.get("gt", synthetic.gt)
            update_data["hash"] = self.compute_hash(new_input, new_gt)
        
        for key, value in update_data.items():
            setattr(synthetic, key, value)
        
        await self.db.commit()
        await self.db.refresh(synthetic)
        return synthetic
    
    async def upload_from_excel(
        self,
        file: BytesIO,
        filename: str,
        created_by: int,
    ) -> SyntheticUploadResponse:
        """
        Upload synthetic data from Excel/CSV file with smart column detection.
        
        支持格式：
        1. 标准格式: input, gt(JSON), category_l4, category_path, difficulty
        2. 简写格式: 第一列=input, 其余列合并为gt, 自动推断category
        3. 混合格式: 包含input列和部分gt列
        """
        # Read file
        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(file)
            elif filename.endswith(".xlsx"):
                df = pd.read_excel(file, engine='openpyxl')
            elif filename.endswith(".xls"):
                df = pd.read_excel(file, engine='xlrd')
            else:
                # Try to detect format
                content = file.read(1024)
                file.seek(0)
                if b'\x50\x4b\x03\x04' in content:  # ZIP signature (xlsx)
                    df = pd.read_excel(file, engine='openpyxl')
                else:
                    df = pd.read_csv(file)
        except Exception as e:
            raise ValueError(f"Cannot read file: {str(e)}. Please ensure the file is a valid Excel (.xlsx, .xls) or CSV file.")
        
        # 使用智能解析
        parsed_results = self.parse_excel_smart(df)
        
        total = len(parsed_results)
        success = 0
        duplicated = 0
        failed = 0
        details = []
        
        for result in parsed_results:
            row_num = result["row"]
            status = result["status"]
            
            if status == "failed":
                failed += 1
                details.append({
                    "row": row_num,
                    "status": "failed",
                    "reason": result.get("reason", "Unknown error"),
                })
                continue
            
            try:
                data = result["data"]
                
                # Create or get category if L4 is provided
                if data.get("category_l4"):
                    category_service = CategoryService(self.db)
                    l1 = data.get("category_l1") or "未分类"
                    l2 = data.get("category_l2") or "未分类"
                    l3 = data.get("category_l3") or "未分类"
                    l4 = data.get("category_l4")
                    
                    await category_service.get_or_create(
                        l1=l1,
                        l2=l2,
                        l3=l3,
                        l4=l4,
                        source="upload",
                    )
                
                # Create synthetic data with full category hierarchy
                synthetic_data = SyntheticCreate(
                    input=data["input"],
                    gt=data["gt"],
                    category_l1=data.get("category_l1"),
                    category_l2=data.get("category_l2"),
                    category_l3=data.get("category_l3"),
                    category_l4=data.get("category_l4"),
                    category_path=data["category_path"],
                    difficulty=data["difficulty"],
                )
                
                await self.create(synthetic_data, created_by=created_by)
                success += 1
                details.append({"row": row_num, "status": "success"})
                
            except ValueError as e:
                if "Duplicate" in str(e):
                    duplicated += 1
                    details.append({
                        "row": row_num,
                        "status": "duplicated",
                        "reason": str(e),
                    })
                else:
                    failed += 1
                    details.append({
                        "row": row_num,
                        "status": "failed",
                        "reason": str(e),
                    })
            except Exception as e:
                failed += 1
                details.append({
                    "row": row_num,
                    "status": "failed",
                    "reason": str(e),
                })
        
        return SyntheticUploadResponse(
            total=total,
            success=success,
            duplicated=duplicated,
            failed=failed,
            details=details,
        )
    
    async def export_to_excel(
        self,
        filter_params: SyntheticFilter,
    ) -> BytesIO:
        """Export synthetic data to Excel."""
        # Get all data (no pagination)
        query = select(SyntheticData)
        
        if filter_params.category_l4:
            query = query.where(SyntheticData.category_l4 == filter_params.category_l4)
        if filter_params.status:
            query = query.where(SyntheticData.status == filter_params.status)
        if filter_params.difficulty:
            query = query.where(SyntheticData.difficulty == filter_params.difficulty)
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        
        # Prepare data for export
        data = []
        for item in items:
            data.append({
                "synthetic_id": item.synthetic_id,
                "input": item.input,
                "gt": json.dumps(item.gt, ensure_ascii=False),
                "category_l4": item.category_l4,
                "category_path": item.category_path,
                "status": item.status,
                "difficulty": item.difficulty,
                "ai_check_passed": item.ai_check_passed,
                "seed_id": item.seed_id,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            })
        
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, sheet_name="Synthetic Data")
        output.seek(0)
        
        return output
    
    async def confirm(
        self,
        synthetic_id: str,
        action: str,
        confirmed_by: int,
        reason: Optional[str] = None,
    ) -> SyntheticConfirmResponse:
        """Confirm or reject synthetic data."""
        from datetime import datetime, timezone
        
        synthetic = await self.get_by_synthetic_id(synthetic_id)
        if not synthetic:
            return SyntheticConfirmResponse(
                success=False,
                synthetic_id=synthetic_id,
                action=action,
                message="Synthetic data not found",
            )
        
        if synthetic.status != "draft":
            return SyntheticConfirmResponse(
                success=False,
                synthetic_id=synthetic_id,
                action=action,
                message=f"Cannot {action} synthetic data with status: {synthetic.status}",
            )
        
        if action == "confirm":
            synthetic.status = "confirmed"
            synthetic.confirmed_by = confirmed_by
            synthetic.confirmed_at = datetime.now(timezone.utc)
            message = "Synthetic data confirmed successfully"
        else:  # reject
            synthetic.status = "rejected"
            synthetic.confirmed_by = confirmed_by
            synthetic.confirmed_at = datetime.now(timezone.utc)
            message = f"Synthetic data rejected. Reason: {reason}"
        
        await self.db.commit()
        await self.db.refresh(synthetic)
        
        return SyntheticConfirmResponse(
            success=True,
            synthetic_id=synthetic_id,
            action=action,
            message=message,
        )
    
    async def batch_confirm(
        self,
        synthetic_ids: List[str],
        action: str,
        confirmed_by: int,
    ) -> List[SyntheticConfirmResponse]:
        """Batch confirm/reject synthetic data."""
        results = []
        for synthetic_id in synthetic_ids:
            result = await self.confirm(synthetic_id, action, confirmed_by)
            results.append(result)
        return results
    
    async def delete(self, synthetic_id: str) -> bool:
        """Delete synthetic data."""
        synthetic = await self.get_by_synthetic_id(synthetic_id)
        if not synthetic:
            return False
        
        # Cannot delete confirmed data
        if synthetic.status == "confirmed":
            raise ValueError("Cannot delete confirmed synthetic data")
        
        await self.db.delete(synthetic)
        await self.db.commit()
        return True
