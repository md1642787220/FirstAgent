"""
BOM数据模拟器
模拟BOM树形结构数据，写入SQLite
"""
from datetime import datetime, date
from src.models.database import get_db_session, init_db
from src.models.tables import BOM, BOMItem


class BOMSimulator:
    """BOM树形结构数据模拟器"""

    BOM_TEMPLATES = [
        {
            "bom_id": "BOM-2026-001",
            "product_code": "PRD-001",
            "product_name": "焊接底座",
            "version": "V2.0",
            "items": [
                {"code": "MAT-001", "name": "底板 Q235 10mm", "spec": "1000x800x10", "qty": 1, "unit": "件", "type": "原材料", "supplier": "宝钢", "cost": 320, "lead_time": 7},
                {"code": "MAT-002", "name": "侧板 Q235 8mm", "spec": "800x600x8", "qty": 2, "unit": "件", "type": "原材料", "supplier": "宝钢", "cost": 180, "lead_time": 7},
                {"code": "MAT-003", "name": "加强筋 Q235 6mm", "spec": "300x50x6", "qty": 4, "unit": "件", "type": "原材料", "supplier": "宝钢", "cost": 45, "lead_time": 5},
                {"code": "MAT-1001", "name": "接触器 CJX2-12", "spec": "AC220V 12A", "qty": 2, "unit": "件", "type": "外购件", "supplier": "施耐德", "cost": 85, "lead_time": 14},
                {"code": "MAT-1002", "name": "焊丝 1.2mm", "spec": "ER70S-6 1.2mm", "qty": 5, "unit": "kg", "type": "辅料", "supplier": "金桥焊材", "cost": 35, "lead_time": 3},
            ],
        },
        {
            "bom_id": "BOM-2026-002",
            "product_code": "PRD-002",
            "product_name": "机架组件",
            "version": "V1.5",
            "items": [
                {"code": "MAT-010", "name": "主梁槽钢", "spec": "20# 200x75x9", "qty": 2, "unit": "根", "type": "原材料", "supplier": "马钢", "cost": 450, "lead_time": 10},
                {"code": "MAT-011", "name": "连接板", "spec": "500x300x12", "qty": 4, "unit": "件", "type": "自制件", "supplier": "自制", "cost": 120, "lead_time": 2},
                {"code": "MAT-012", "name": "高强螺栓 M20", "spec": "10.9级 M20x60", "qty": 24, "unit": "套", "type": "标准件", "supplier": "晋亿", "cost": 8.5, "lead_time": 5},
                {"code": "MAT-1003", "name": "保护镜片", "spec": "D52x3.5", "qty": 4, "unit": "件", "type": "辅料", "supplier": "宾采尔", "cost": 65, "lead_time": 7},
            ],
        },
        {
            "bom_id": "BOM-2026-003",
            "product_code": "PRD-003",
            "product_name": "控制箱体",
            "version": "V1.0",
            "items": [
                {"code": "MAT-020", "name": "箱体壳体", "spec": "600x400x300", "qty": 1, "unit": "件", "type": "自制件", "supplier": "自制", "cost": 280, "lead_time": 3},
                {"code": "MAT-021", "name": "控制板 PCB", "spec": "4层板", "qty": 1, "unit": "块", "type": "外购件", "supplier": "嘉立创", "cost": 350, "lead_time": 15},
                {"code": "MAT-1001", "name": "接触器 CJX2-12", "spec": "AC220V 12A", "qty": 3, "unit": "件", "type": "外购件", "supplier": "施耐德", "cost": 85, "lead_time": 14},
            ],
        },
    ]

    # V1.0旧版本（用于版本对比）
    BOM_V1_ITEMS = [
        {"code": "MAT-001", "name": "底板 Q235 8mm", "spec": "1000x800x8", "qty": 1, "unit": "件", "type": "原材料", "supplier": "宝钢", "cost": 260, "lead_time": 7},
        {"code": "MAT-002", "name": "侧板 Q235 6mm", "spec": "800x600x6", "qty": 2, "unit": "件", "type": "原材料", "supplier": "宝钢", "cost": 140, "lead_time": 7},
        {"code": "MAT-1001", "name": "接触器 CJX2-12", "spec": "AC220V 12A", "qty": 2, "unit": "件", "type": "外购件", "supplier": "施耐德", "cost": 85, "lead_time": 14},
    ]

    def generate_and_save(self):
        """生成BOM数据并写入数据库"""
        init_db()
        session = get_db_session()
        try:
            session.query(BOMItem).delete()
            session.query(BOM).delete()
            session.commit()

            for template in self.BOM_TEMPLATES:
                bom = BOM(
                    id=template["bom_id"],
                    product_code=template["product_code"],
                    product_name=template["product_name"],
                    version=template["version"],
                    status="已发布",
                    effective_date=date(2026, 1, 1),
                    created_by="工艺部",
                    description=f"{template['product_name']}物料清单",
                )
                session.add(bom)

                for i, item in enumerate(template["items"]):
                    bom_item = BOMItem(
                        bom_id=bom.id,
                        parent_item_id=None,
                        material_code=item["code"],
                        material_name=item["name"],
                        specification=item["spec"],
                        quantity=item["qty"],
                        unit=item["unit"],
                        material_type=item["type"],
                        source_supplier=item["supplier"],
                        cost=item["cost"],
                        lead_time=item["lead_time"],
                    )
                    session.add(bom_item)

            session.commit()
            print(f"[BOMSimulator] 已生成 {len(self.BOM_TEMPLATES)} 个BOM")
        finally:
            session.close()

    def get_bom_tree(self, bom_id: str) -> dict:
        """获取BOM树形结构"""
        session = get_db_session()
        try:
            bom = session.query(BOM).filter(BOM.id == bom_id).first()
            if not bom:
                return {"error": f"BOM {bom_id} 不存在"}

            items = session.query(BOMItem).filter(BOMItem.bom_id == bom_id).all()
            return {
                "id": bom.id,
                "product_name": bom.product_name,
                "product_code": bom.product_code,
                "version": bom.version,
                "status": bom.status,
                "items": [item.to_dict() for item in items],
                "total_cost": sum(i.cost * i.quantity for i in items),
                "item_count": len(items),
            }
        finally:
            session.close()

    def compare_versions(self, bom_id: str, v1: str, v2: str) -> dict:
        """对比两个BOM版本（模拟）"""
        current = self.get_bom_tree(bom_id)
        if "error" in current:
            return current

        # 模拟V1.0数据
        v1_items = {item["material_code"]: item for item in [
            {"material_code": "MAT-001", "material_name": "底板 Q235 8mm", "specification": "1000x800x8", "quantity": 1, "cost": 260},
            {"material_code": "MAT-002", "material_name": "侧板 Q235 6mm", "specification": "800x600x6", "quantity": 2, "cost": 140},
            {"material_code": "MAT-1001", "material_name": "接触器 CJX2-12", "specification": "AC220V 12A", "quantity": 2, "cost": 85},
        ]}

        v2_items = {item["material_code"]: item for item in current["items"]}

        added, removed, changed = [], [], []
        all_codes = set(v1_items.keys()) | set(v2_items.keys())
        for code in all_codes:
            if code not in v1_items:
                added.append(v2_items[code])
            elif code not in v2_items:
                removed.append(v1_items[code])
            else:
                i1, i2 = v1_items[code], v2_items[code]
                if i1.get("quantity") != i2.get("quantity") or i1.get("specification") != i2.get("specification"):
                    changed.append({"code": code, "v1": i1, "v2": i2})

        return {
            "bom_id": bom_id,
            "v1": v1,
            "v2": v2,
            "added": added,
            "removed": removed,
            "changed": changed,
            "summary": f"新增{len(added)}项, 删除{len(removed)}项, 变更{len(changed)}项",
        }


bom_simulator = BOMSimulator()
