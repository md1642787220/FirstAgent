"""
BOM管理Agent工具集
BOM查询、版本对比、变更影响分析
"""
from langchain_core.tools import tool
from src.models.database import get_db_session
from src.models.tables import BOM, BOMItem, Inventory


@tool
def get_bom(bom_id: str) -> dict:
    """查询BOM完整结构（树形）。返回BOM表头和所有物料明细。

    Args:
        bom_id: BOM ID，例如 BOM-2026-001
    """
    session = get_db_session()
    try:
        bom = session.query(BOM).filter(BOM.id == bom_id).first()
        if not bom:
            return {"error": f"BOM {bom_id} 不存在"}
        items = session.query(BOMItem).filter(BOMItem.bom_id == bom_id).all()
        return {
            **bom.to_dict(),
            "items": [item.to_dict() for item in items],
            "total_cost": sum(i.cost * i.quantity for i in items),
            "item_count": len(items),
        }
    finally:
        session.close()


@tool
def get_all_boms() -> list:
    """获取所有BOM列表。"""
    session = get_db_session()
    try:
        boms = session.query(BOM).all()
        return [bom.to_dict() for bom in boms]
    finally:
        session.close()


@tool
def compare_bom_versions(bom_id: str, v1: str = "V1.0", v2: str = "V2.0") -> dict:
    """对比两个BOM版本的差异。返回新增、删除、变更的物料。

    Args:
        bom_id: BOM ID
        v1: 旧版本号
        v2: 新版本号
    """
    # 模拟V1.0数据
    v1_items = {
        "MAT-001": {"material_name": "底板 Q235 8mm", "specification": "1000x800x8", "quantity": 1, "cost": 260},
        "MAT-002": {"material_name": "侧板 Q235 6mm", "specification": "800x600x6", "quantity": 2, "cost": 140},
        "MAT-1001": {"material_name": "接触器 CJX2-12", "specification": "AC220V 12A", "quantity": 2, "cost": 85},
    }

    session = get_db_session()
    try:
        current_bom = session.query(BOM).filter(BOM.id == bom_id).first()
        if not current_bom:
            return {"error": f"BOM {bom_id} 不存在"}

        v2_items_list = session.query(BOMItem).filter(BOMItem.bom_id == bom_id).all()
        v2_items = {item.material_code: item.to_dict() for item in v2_items_list}

        added, removed, changed = [], [], []
        all_codes = set(v1_items.keys()) | set(v2_items.keys())
        for code in all_codes:
            if code not in v1_items:
                added.append(v2_items[code])
            elif code not in v2_items:
                removed.append(v1_items[code])
            else:
                i1, i2 = v1_items[code], v2_items[code]
                diffs = []
                if i1.get("quantity") != i2.get("quantity"):
                    diffs.append(f"用量: {i1['quantity']} -> {i2['quantity']}")
                if i1.get("specification") != i2.get("specification"):
                    diffs.append(f"规格: {i1['specification']} -> {i2['specification']}")
                if diffs:
                    changed.append({"material_code": code, "material_name": i2.get("material_name"), "changes": diffs})

        return {
            "bom_id": bom_id,
            "product_name": current_bom.product_name,
            "v1": v1,
            "v2": v2,
            "added": added,
            "removed": removed,
            "changed": changed,
            "summary": f"新增{len(added)}项, 删除{len(removed)}项, 变更{len(changed)}项",
        }
    finally:
        session.close()


@tool
def check_material_availability(bom_id: str, quantity: int = 1) -> dict:
    """检查BOM物料的齐套性。对比各物料库存与需求，标记缺货物料。

    Args:
        bom_id: BOM ID
        quantity: 生产数量，默认1
    """
    session = get_db_session()
    try:
        items = session.query(BOMItem).filter(BOMItem.bom_id == bom_id).all()
        if not items:
            return {"error": f"BOM {bom_id} 无物料"}

        results = []
        shortage_count = 0
        for item in items:
            inv = session.query(Inventory).filter(
                Inventory.material_code == item.material_code
            ).first()

            required = item.quantity * quantity
            stock = inv.quantity if inv else 0
            is_shortage = stock < required
            if is_shortage:
                shortage_count += 1

            results.append({
                "material_code": item.material_code,
                "material_name": item.material_name,
                "required": required,
                "unit": item.unit,
                "stock": stock,
                "gap": round(required - stock, 2) if is_shortage else 0,
                "status": "缺货" if is_shortage else "充足",
            })

        return {
            "bom_id": bom_id,
            "production_quantity": quantity,
            "total_items": len(results),
            "shortage_items": shortage_count,
            "availability_rate": round((len(results) - shortage_count) / len(results) * 100, 1),
            "items": results,
        }
    finally:
        session.close()


BOM_TOOLS = [get_bom, get_all_boms, compare_bom_versions, check_material_availability]
