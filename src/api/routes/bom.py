"""BOM管理接口"""
from fastapi import APIRouter
from src.models.database import get_db_session
from src.models.tables import BOM, BOMItem, Inventory

router = APIRouter()


@router.get("")
async def get_all_boms():
    """获取所有BOM列表"""
    session = get_db_session()
    try:
        boms = session.query(BOM).all()
        return {"boms": [b.to_dict() for b in boms], "count": len(boms)}
    finally:
        session.close()


@router.get("/{bom_id}")
async def get_bom(bom_id: str):
    """获取BOM完整结构"""
    session = get_db_session()
    try:
        bom = session.query(BOM).filter(BOM.id == bom_id).first()
        if not bom:
            return {"error": f"BOM {bom_id} 不存在"}
        items = session.query(BOMItem).filter(BOMItem.bom_id == bom_id).all()
        return {**bom.to_dict(), "items": [i.to_dict() for i in items], "total_cost": sum(i.cost * i.quantity for i in items)}
    finally:
        session.close()


@router.post("/compare")
async def compare_bom(bom_id: str, v1: str = "V1.0", v2: str = "V2.0"):
    """对比BOM版本"""
    from src.agents.tools.bom_tools import compare_bom_versions
    return compare_bom_versions.invoke({"bom_id": bom_id, "v1": v1, "v2": v2})


@router.post("/availability")
async def check_availability(bom_id: str, quantity: int = 1):
    """齐套性分析"""
    from src.agents.tools.bom_tools import check_material_availability
    return check_material_availability.invoke({"bom_id": bom_id, "quantity": quantity})
