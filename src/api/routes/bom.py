"""BOM管理接口"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from src.models.database import get_db_session
from src.models.tables import BOM, BOMItem, Inventory

router = APIRouter()


# ---- Pydantic models ----

class BOMItemCreate(BaseModel):
    material_code: str
    material_name: str
    specification: Optional[str] = None
    quantity: float
    unit: Optional[str] = None
    material_type: Optional[str] = "component"
    source_supplier: Optional[str] = None
    cost: Optional[float] = 0.0
    lead_time: Optional[int] = 0
    remark: Optional[str] = None


class BOMItemUpdate(BaseModel):
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    specification: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    material_type: Optional[str] = None
    source_supplier: Optional[str] = None
    cost: Optional[float] = None
    lead_time: Optional[int] = None
    remark: Optional[str] = None


class BOMHeaderUpdate(BaseModel):
    product_name: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


# ---- BOM 列表 ----

@router.get("")
async def get_all_boms():
    """获取所有BOM列表"""
    session = get_db_session()
    try:
        boms = session.query(BOM).all()
        return {"boms": [b.to_dict() for b in boms], "count": len(boms)}
    finally:
        session.close()


# ---- BOM 详情 + 物料清单 ----

@router.get("/{bom_id}")
async def get_bom(bom_id: str):
    """获取BOM完整结构"""
    session = get_db_session()
    try:
        bom = session.query(BOM).filter(BOM.id == bom_id).first()
        if not bom:
            raise HTTPException(status_code=404, detail=f"BOM {bom_id} 不存在")
        items = session.query(BOMItem).filter(BOMItem.bom_id == bom_id).all()
        return {**bom.to_dict(), "items": [i.to_dict() for i in items],
                "total_cost": sum((i.cost or 0) * i.quantity for i in items)}
    finally:
        session.close()


# ---- 更新 BOM 头 ----

@router.put("/{bom_id}")
async def update_bom_header(bom_id: str, data: BOMHeaderUpdate):
    """更新BOM产品信息（名称、版本等）"""
    session = get_db_session()
    try:
        bom = session.query(BOM).filter(BOM.id == bom_id).first()
        if not bom:
            raise HTTPException(status_code=404, detail=f"BOM {bom_id} 不存在")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(bom, field, value)
        session.commit()
        return {"ok": True, "bom": bom.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# ---- 新增物料 ----

@router.post("/{bom_id}/items")
async def add_bom_item(bom_id: str, data: BOMItemCreate):
    """向BOM添加一条物料"""
    session = get_db_session()
    try:
        bom = session.query(BOM).filter(BOM.id == bom_id).first()
        if not bom:
            raise HTTPException(status_code=404, detail=f"BOM {bom_id} 不存在")
        item = BOMItem(
            bom_id=bom_id,
            material_code=data.material_code,
            material_name=data.material_name,
            specification=data.specification,
            quantity=data.quantity,
            unit=data.unit,
            material_type=data.material_type,
            source_supplier=data.source_supplier,
            cost=data.cost,
            lead_time=data.lead_time,
            remark=data.remark,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        return {"ok": True, "item": item.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# ---- 修改单个物料 ----

@router.put("/{bom_id}/items/{item_id}")
async def update_bom_item(bom_id: str, item_id: int, data: BOMItemUpdate):
    """修改BOM中某条物料的属性"""
    session = get_db_session()
    try:
        item = session.query(BOMItem).filter(
            BOMItem.id == item_id, BOMItem.bom_id == bom_id
        ).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"物料 {item_id} 不存在")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        session.commit()
        session.refresh(item)
        return {"ok": True, "item": item.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# ---- 删除物料 ----

@router.delete("/{bom_id}/items/{item_id}")
async def delete_bom_item(bom_id: str, item_id: int):
    """删除BOM中的某条物料"""
    session = get_db_session()
    try:
        item = session.query(BOMItem).filter(
            BOMItem.id == item_id, BOMItem.bom_id == bom_id
        ).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"物料 {item_id} 不存在")
        session.delete(item)
        session.commit()
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# ---- 版本对比 ----

@router.post("/compare")
async def compare_bom(bom_id: str, v1: str = "V1.0", v2: str = "V2.0"):
    """对比BOM版本"""
    from src.agents.tools.bom_tools import compare_bom_versions
    return compare_bom_versions.invoke({"bom_id": bom_id, "v1": v1, "v2": v2})


# ---- 齐套性分析 ----

@router.post("/availability")
async def check_availability(bom_id: str, quantity: int = 1):
    """齐套性分析"""
    from src.agents.tools.bom_tools import check_material_availability
    return check_material_availability.invoke({"bom_id": bom_id, "quantity": quantity})
