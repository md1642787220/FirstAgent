"""端到端功能测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.supervisor import supervisor_chat, classify_intent, IntentType
from src.simulators.welding_simulator import welding_simulator
from src.models.database import get_db_session, init_db
from src.models.tables import WorkOrder, BOM, Inventory


def test_intent_classification():
    """测试意图识别"""
    assert classify_intent("电流是多少")[0] == IntentType.DEVICE
    assert classify_intent("WO-2026-001进度")[0] == IntentType.PRODUCTION
    assert classify_intent("BOM-2026-001物料")[0] == IntentType.BOM
    assert classify_intent("库存短缺")[0] == IntentType.INVENTORY
    assert classify_intent("Q235怎么焊")[0] == IntentType.KNOWLEDGE
    print("[PASS] test_intent_classification")


def test_welding_simulator():
    """测试焊接设备模拟器"""
    metrics = welding_simulator.get_device_metrics("DEV-W001")
    assert "current" in metrics
    assert "voltage" in metrics
    assert "alerts" in metrics
    devices = welding_simulator.get_devices()
    assert len(devices) == 4
    print("[PASS] test_welding_simulator")


def test_supervisor_chat_production():
    """测试生产进度对话"""
    result = supervisor_chat("WO-2026-001的进度怎么样")
    assert result["intent"] == "生产进度"
    assert "生产进度Agent" in result["routed_agents"]
    assert len(result["trace"]["steps"]) > 0
    print("[PASS] test_supervisor_chat_production")


def test_supervisor_chat_inventory():
    """测试库存对话"""
    result = supervisor_chat("库存短缺预警有哪些")
    assert result["intent"] == "库存分析"
    assert "库存分析Agent" in result["routed_agents"]
    print("[PASS] test_supervisor_chat_inventory")


def test_supervisor_chat_knowledge():
    """测试工艺知识对话"""
    result = supervisor_chat("Q235 10mm怎么焊")
    assert result["intent"] == "工艺知识"
    assert "工艺知识Agent" in result["routed_agents"]
    print("[PASS] test_supervisor_chat_knowledge")


def test_database_tables():
    """测试数据库表数据"""
    init_db()
    session = get_db_session()
    try:
        wo_count = session.query(WorkOrder).count()
        bom_count = session.query(BOM).count()
        inv_count = session.query(Inventory).count()
        assert wo_count > 0, "No work orders"
        assert bom_count > 0, "No BOMs"
        assert inv_count > 0, "No inventory"
        print(f"[PASS] test_database_tables (orders={wo_count}, boms={bom_count}, inventory={inv_count})")
    finally:
        session.close()


def test_trace_system():
    """测试轨迹系统"""
    from src.agents.trace import create_trace, TracePhase
    trace = create_trace("test_session")
    trace.add_step(agent="TestAgent", phase=TracePhase.ACTION, thought="test", action="test_action")
    data = trace.get_trace()
    assert data["session_id"] == "test_session"
    assert data["total_steps"] == 1
    print("[PASS] test_trace_system")


if __name__ == "__main__":
    print("=" * 50)
    print("Running tests...")
    print("=" * 50)
    test_intent_classification()
    test_welding_simulator()
    test_supervisor_chat_production()
    test_supervisor_chat_inventory()
    test_supervisor_chat_knowledge()
    test_database_tables()
    test_trace_system()
    print("=" * 50)
    print("All tests passed!")
    print("=" * 50)
