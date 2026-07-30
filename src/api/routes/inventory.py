"""库存分析接口"""
from fastapi import APIRouter
from src.models.database import get_db_session
from src.models.tables import Inventory

router = APIRouter()


@router.get("")
async def query_inventory(material_code: str = "", category: str = "", status: str = ""):
    """查询库存"""
    session = get_db_session()
    try:
        query = session.query(Inventory)
        if material_code:
            query = query.filter(Inventory.material_code == material_code)
        if category:
            query = query.filter(Inventory.category == category)
        if status:
            query = query.filter(Inventory.status == status)
        items = query.all()
        return {"inventory": [i.to_dict() for i in items], "count": len(items)}
    finally:
        session.close()


@router.get("/alerts")
async def get_alerts():
    """获取短缺预警"""
    session = get_db_session()
    try:
        items = session.query(Inventory).filter(Inventory.status == "短缺").all()
        return {"alerts": [{**i.to_dict(), "gap": round(i.safety_stock - i.quantity, 2)} for i in items], "count": len(items)}
    finally:
        session.close()


@router.get("/obsolete")
async def get_obsolete(days: int = 180):
    """获取呆滞物料"""
    session = get_db_session()
    try:
        items = session.query(Inventory).filter(Inventory.turnover_days >= days).all()
        return {"obsolete": [i.to_dict() for i in items], "count": len(items)}
    finally:
        session.close()


@router.get("/summary")
async def get_summary():
    """库存汇总"""
    session = get_db_session()
    try:
        total = session.query(Inventory).count()
        shortage = session.query(Inventory).filter(Inventory.status == "短缺").count()
        obsolete = session.query(Inventory).filter(Inventory.status == "呆滞").count()
        overstock = session.query(Inventory).filter(Inventory.status == "超储").count()
        normal = session.query(Inventory).filter(Inventory.status == "正常").count()
        return {"total": total, "shortage": shortage, "obsolete": obsolete, "overstock": overstock, "normal": normal}
    finally:
        session.close()
