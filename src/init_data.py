"""
数据初始化脚本
一键生成所有模拟数据到SQLite数据库
用法: python -m src.init_data
"""
from src.models.database import init_db
from src.simulators.production_simulator import production_simulator
from src.simulators.bom_simulator import bom_simulator
from src.simulators.inventory_simulator import inventory_simulator


def init_all_data():
    """初始化全部模拟数据"""
    print("=" * 60)
    print("开始初始化模拟数据...")
    print("=" * 60)

    # 初始化数据库表结构
    init_db()
    print("[OK] 数据库表结构已创建")

    # 生成生产进度数据
    production_simulator.generate_and_save()
    print(f"[OK] 生产汇总: {production_simulator.get_today_summary()}")

    # 生成BOM数据
    bom_simulator.generate_and_save()
    print("[OK] BOM数据已生成")

    # 生成库存数据
    inventory_simulator.generate_and_save()
    print(f"[OK] 库存汇总: {inventory_simulator.get_summary()}")

    print("=" * 60)
    print("全部模拟数据初始化完成!")
    print("=" * 60)


if __name__ == "__main__":
    init_all_data()
