"""
库存分析Agent工具集
库存查询、短缺预警、呆滞料识别
"""
from langchain_core.tools import tool
from src.models.database import get_db_session
from src.models.tables import Inventory


@tool
def query_inventory(material_code: str = "", category: str = "", status: str = "") -> list:
    """查询库存物料。支持按物料编码、类别、状态筛选。

    Args:
        material_code: 物料编码（精确匹配），为空则不筛选
        category: 物料类别（原材料/外购件/自制件/标准件/辅料/半成品/成品）
        status: 库存状态（正常/短缺/呆滞/超储）
    """
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
        return [item.to_dict() for item in items]
    finally:
        session.close()


@tool
def get_low_stock_alerts() -> list:
    """获取低于安全库存的物料预警列表。返回所有短缺状态物料及其缺口。"""
    session = get_db_session()
    try:
        items = session.query(Inventory).filter(Inventory.status == "短缺").all()
        results = []
        for item in items:
            gap = item.safety_stock - item.quantity
            results.append({
                **item.to_dict(),
                "gap": round(gap, 2),
                "urgency": "紧急" if item.quantity < item.safety_stock * 0.3 else "警告",
            })
        return results
    finally:
        session.close()


@tool
def get_obsolete_materials(days: int = 180) -> list:
    """识别呆滞物料。返回周转天数超过指定阈值的物料。

    Args:
        days: 呆滞判定天数，默认180天
    """
    session = get_db_session()
    try:
        items = session.query(Inventory).filter(
            Inventory.turnover_days >= days
        ).all()
        return [
            {
                **item.to_dict(),
                "suggestion": "建议降价处理或报废" if item.status == "呆滞" else f"周转天数{item.turnover_days}天，建议关注",
            }
            for item in items
        ]
    finally:
        session.close()


@tool
def get_inventory_summary() -> dict:
    """获取库存汇总统计。返回总数、短缺数、呆滞数、超储数、正常数。"""
    session = get_db_session()
    try:
        total = session.query(Inventory).count()
        shortage = session.query(Inventory).filter(Inventory.status == "短缺").count()
        obsolete = session.query(Inventory).filter(Inventory.status == "呆滞").count()
        overstock = session.query(Inventory).filter(Inventory.status == "超储").count()
        normal = session.query(Inventory).filter(Inventory.status == "正常").count()
        return {
            "total": total,
            "shortage": shortage,
            "obsolete": obsolete,
            "overstock": overstock,
            "normal": normal,
        }
    finally:
        session.close()


INVENTORY_TOOLS = [query_inventory, get_low_stock_alerts, get_obsolete_materials, get_inventory_summary]
