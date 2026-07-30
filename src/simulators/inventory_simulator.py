"""
库存数据模拟器
模拟物料库存水位与预警数据，写入SQLite
"""
from datetime import datetime, date, timedelta
from src.models.database import get_db_session, init_db
from src.models.tables import Inventory


class InventorySimulator:
    """库存水位与预警数据模拟器"""

    MATERIAL_TEMPLATES = [
        ("MAT-001", "底板 Q235 10mm", "原材料", "宝钢", "kg", 500, 100, 800, 150, 2.8),
        ("MAT-002", "侧板 Q235 8mm", "原材料", "宝钢", "kg", 320, 80, 600, 120, 2.5),
        ("MAT-003", "加强筋 Q235 6mm", "原材料", "宝钢", "件", 120, 50, 300, 80, 0.8),
        ("MAT-010", "主梁槽钢 20#", "原材料", "马钢", "根", 15, 20, 50, 25, 8.5),
        ("MAT-011", "连接板", "自制件", "自制", "件", 85, 30, 200, 50, 1.2),
        ("MAT-012", "高强螺栓 M20", "标准件", "晋亿", "套", 480, 200, 1000, 300, 0.012),
        ("MAT-020", "箱体壳体", "自制件", "自制", "件", 25, 10, 50, 15, 1.5),
        ("MAT-021", "控制板 PCB", "外购件", "嘉立创", "块", 8, 10, 30, 12, 3.2),
        ("MAT-1001", "接触器 CJX2-12", "外购件", "施耐德", "件", 5, 20, 100, 30, 0.085),
        ("MAT-1002", "焊丝 1.2mm", "辅料", "金桥焊材", "kg", 50, 100, 300, 120, 0.035),
        ("MAT-1003", "保护镜片", "辅料", "宾采尔", "件", 3, 10, 50, 15, 0.065),
        ("MAT-1004", "导电嘴 1.2mm", "辅料", "宾采尔", "件", 120, 50, 300, 80, 0.015),
        ("MAT-1005", "气体 CO2", "辅料", "林德气体", "瓶", 8, 5, 20, 6, 0.045),
        ("MAT-1006", "防飞溅剂", "辅料", "国产", "瓶", 2, 10, 30, 12, 0.025),
        ("MAT-1007", "旧型号继电器", "外购件", "已停产", "件", 85, 0, 0, 0, 0.045),
    ]

    def generate_and_save(self):
        """生成库存数据并写入数据库"""
        init_db()
        session = get_db_session()
        try:
            session.query(Inventory).delete()
            session.commit()

            now = date.today()
            for tpl in self.MATERIAL_TEMPLATES:
                code, name, cat, supplier, unit, qty, safety, max_s, reorder, cost = tpl

                # 判断状态
                if safety == 0:
                    status = "呆滞"
                elif qty < safety:
                    status = "短缺"
                elif qty > max_s:
                    status = "超储"
                else:
                    status = "正常"

                inv = Inventory(
                    material_code=code,
                    material_name=name,
                    category=cat,
                    warehouse="1号仓库",
                    location=f"A-{code[-3:]}",
                    quantity=qty,
                    unit=unit,
                    safety_stock=safety,
                    max_stock=max_s,
                    reorder_point=reorder,
                    last_inbound=now - timedelta(days=random_days()),
                    last_outbound=now - timedelta(days=random_days()),
                    turnover_days=random_days(1, 365),
                    status=status,
                    supplier=supplier,
                    unit_cost=cost,
                )
                session.add(inv)

            session.commit()
            print(f"[InventorySimulator] 已生成 {len(self.MATERIAL_TEMPLATES)} 条库存数据")
        finally:
            session.close()

    def get_summary(self) -> dict:
        """获取库存汇总"""
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


def random_days(min_d: int = 1, max_d: int = 60) -> int:
    import random
    return random.randint(min_d, max_d)


inventory_simulator = InventorySimulator()
