"""
生产进度模拟器
模拟工单与工序进度数据，写入SQLite
"""
import random
from datetime import datetime, timedelta
from typing import List

from src.models.database import get_db_session, init_db
from src.models.tables import WorkOrder, ProcessStep


PRODUCTS = [
    ("焊接底座", "PRD-001", 200),
    ("机架组件", "PRD-002", 150),
    ("控制箱体", "PRD-003", 80),
    ("变压器支架", "PRD-004", 300),
    ("散热器总成", "PRD-005", 100),
    ("法兰总成", "PRD-006", 250),
    ("支撑臂", "PRD-007", 120),
]

CUSTOMERS = ["中车集团", "三一重工", "徐工机械", "中联重科", "卡特彼勒"]

STEP_TEMPLATES = ["下料", "焊接", "打磨", "检验", "包装"]


class ProductionSimulator:
    """生产工单与工序进度数据模拟器"""

    def __init__(self, order_count: int = 20):
        self.order_count = order_count

    def generate_and_save(self):
        """生成模拟数据并写入数据库"""
        init_db()
        session = get_db_session()

        try:
            # 清空旧数据
            session.query(ProcessStep).delete()
            session.query(WorkOrder).delete()
            session.commit()

            now = datetime.now()
            orders_data = []

            for i in range(self.order_count):
                product = random.choice(PRODUCTS)
                progress = random.randint(0, 100)
                if progress == 100:
                    status = "已完成"
                elif progress > 0:
                    status = "生产中"
                else:
                    status = "待排产"

                planned_start = now - timedelta(days=random.randint(0, 10))
                planned_end = now + timedelta(days=random.randint(1, 10))
                delay_days = random.randint(1, 3) if (progress < 50 and random.random() > 0.5) else 0
                priority = random.choices(["紧急", "高", "中", "低"], weights=[1, 2, 4, 1])[0]

                wo = WorkOrder(
                    id=f"WO-2026-{i+1:03d}",
                    product_name=product[0],
                    product_code=product[1],
                    quantity=product[2],
                    priority=priority,
                    status=status,
                    planned_start=planned_start.date(),
                    planned_end=planned_end.date(),
                    actual_start=planned_start.date() if progress > 0 else None,
                    actual_end=planned_end.date() if progress == 100 else None,
                    customer=random.choice(CUSTOMERS),
                    progress=progress,
                    delay_days=delay_days,
                )
                session.add(wo)
                orders_data.append(wo)

                # 生成工序
                completed_steps = int(progress / 100 * len(STEP_TEMPLATES))
                for j, step_name in enumerate(STEP_TEMPLATES):
                    if j < completed_steps:
                        step_status = "已完成"
                        actual_dur = random.randint(2, 8)
                    elif j == completed_steps and progress > 0 and progress < 100:
                        step_status = "进行中"
                        actual_dur = random.randint(0, 4)
                    elif j == completed_steps and delay_days > 0:
                        step_status = "阻塞"
                        actual_dur = None
                    else:
                        step_status = "未开始"
                        actual_dur = None

                    step = ProcessStep(
                        work_order_id=wo.id,
                        step_name=step_name,
                        step_order=j + 1,
                        status=step_status,
                        planned_duration=random.randint(4, 10),
                        actual_duration=actual_dur,
                        start_time=planned_start + timedelta(days=j) if step_status != "未开始" else None,
                        end_time=planned_start + timedelta(days=j+1) if step_status == "已完成" else None,
                        device_id=f"DEV-W{random.randint(1, 4):03d}" if step_name == "焊接" else None,
                        operator=f"操作员{random.randint(1, 10):02d}",
                        notes=f"{step_name}工序" + ("，焊丝库存不足" if delay_days > 0 and step_name == "焊接" else ""),
                    )
                    session.add(step)

            session.commit()
            print(f"[ProductionSimulator] 已生成 {self.order_count} 个工单及工序数据")
            return orders_data

        finally:
            session.close()

    def get_today_summary(self) -> dict:
        """获取今日生产汇总"""
        session = get_db_session()
        try:
            total = session.query(WorkOrder).count()
            in_progress = session.query(WorkOrder).filter(WorkOrder.status == "生产中").count()
            completed = session.query(WorkOrder).filter(WorkOrder.status == "已完成").count()
            delayed = session.query(WorkOrder).filter(WorkOrder.delay_days > 0).count()
            urgent = session.query(WorkOrder).filter(WorkOrder.priority == "紧急").count()
            return {
                "total_orders": total,
                "in_progress": in_progress,
                "completed": completed,
                "delayed": delayed,
                "urgent": urgent,
            }
        finally:
            session.close()


# 单例
production_simulator = ProductionSimulator()
