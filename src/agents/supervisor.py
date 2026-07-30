"""
主控Agent (Supervisor)
基于意图识别实现任务路由、结果聚合
架构：1主控Agent + 5专业Agent（设备/生产/BOM/库存/工艺知识）
"""
import time
import re
from typing import Optional
from enum import Enum

from src.agents.trace import TraceLogger, TracePhase, create_trace
from src.agents.rag.retriever import retrieve_knowledge


class IntentType(str, Enum):
    """意图类型"""
    DEVICE = "设备监控"
    PRODUCTION = "生产进度"
    BOM = "BOM管理"
    INVENTORY = "库存分析"
    KNOWLEDGE = "工艺知识"
    COMPOSITE = "复合意图"


# 意图关键词映射
INTENT_KEYWORDS = {
    IntentType.DEVICE: ["电流", "电压", "焊速", "气体", "温度", "振动", "设备", "焊机", "参数", "异常", "告警", "DEV"],
    IntentType.PRODUCTION: ["工单", "进度", "工序", "生产", "滞后", "延迟", "完成", "排产", "WO"],
    IntentType.BOM: ["BOM", "物料清单", "版本", "对比", "齐套", "bom"],
    IntentType.INVENTORY: ["库存", "安全库存", "呆滞", "短缺", "缺货", "预警", "库位", "仓库"],
    IntentType.KNOWLEDGE: ["怎么焊", "焊接工艺", "参数推荐", "缺陷", "气孔", "裂纹", "标准", "材质", "Q235", "Q345", "不锈钢", "预热"],
}


def classify_intent(user_input: str) -> tuple[IntentType, list[IntentType]]:
    """基于关键词的意图识别，支持复合意图"""
    matched = set()
    text = user_input.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                matched.add(intent)
                break
    if len(matched) == 0:
        return IntentType.KNOWLEDGE, []
    elif len(matched) == 1:
        return list(matched)[0], []
    else:
        return IntentType.COMPOSITE, list(matched)


# ===== 专业Agent执行器 =====
def run_device_agent(query: str, trace: TraceLogger) -> dict:
    """设备监控Agent"""
    start = time.time()
    trace.add_step(agent="设备监控Agent", phase=TracePhase.ACTION,
                   thought="查询设备信息", action="device_tools")
    from src.simulators.welding_simulator import welding_simulator
    device_match = re.search(r'DEV-W\d+', query, re.IGNORECASE)
    if device_match:
        device_id = device_match.group().upper()
        result = welding_simulator.get_device_metrics(device_id)
    else:
        result = {"devices": welding_simulator.get_devices()}
    trace.add_step(agent="设备监控Agent", phase=TracePhase.OBSERVATION,
                   observation=str(result)[:200], duration_ms=int((time.time() - start) * 1000))
    return {"agent": "设备监控Agent", "data": result}


def run_production_agent(query: str, trace: TraceLogger) -> dict:
    """生产进度Agent"""
    start = time.time()
    trace.add_step(agent="生产进度Agent", phase=TracePhase.ACTION,
                   thought="查询生产进度", action="production_tools")
    from src.models.database import get_db_session
    from src.models.tables import WorkOrder, ProcessStep
    session = get_db_session()
    try:
        wo_match = re.search(r'WO-\d{4}-\d{3}', query, re.IGNORECASE)
        if wo_match:
            wo_id = wo_match.group().upper()
            wo = session.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
            steps = session.query(ProcessStep).filter(ProcessStep.work_order_id == wo_id).order_by(ProcessStep.step_order).all()
            result = {"work_order": wo.to_dict() if wo else None, "steps": [s.to_dict() for s in steps]}
        elif "滞后" in query or "延迟" in query:
            delayed = session.query(WorkOrder).filter(WorkOrder.delay_days > 0).all()
            result = {"delayed_orders": [wo.to_dict() for wo in delayed]}
        else:
            total = session.query(WorkOrder).count()
            in_prog = session.query(WorkOrder).filter(WorkOrder.status == "生产中").count()
            done = session.query(WorkOrder).filter(WorkOrder.status == "已完成").count()
            delayed = session.query(WorkOrder).filter(WorkOrder.delay_days > 0).count()
            urgent = session.query(WorkOrder).filter(WorkOrder.priority == "紧急").count()
            result = {"total": total, "in_progress": in_prog, "completed": done, "delayed": delayed, "urgent": urgent}
    finally:
        session.close()
    trace.add_step(agent="生产进度Agent", phase=TracePhase.OBSERVATION,
                   observation=str(result)[:200], duration_ms=int((time.time() - start) * 1000))
    return {"agent": "生产进度Agent", "data": result}


def run_bom_agent(query: str, trace: TraceLogger) -> dict:
    """BOM管理Agent"""
    start = time.time()
    trace.add_step(agent="BOM管理Agent", phase=TracePhase.ACTION,
                   thought="查询BOM信息", action="bom_tools")
    from src.models.database import get_db_session
    from src.models.tables import BOM, BOMItem, Inventory
    session = get_db_session()
    try:
        bom_match = re.search(r'BOM-\d{4}-\d{3}', query, re.IGNORECASE)
        bom_id = bom_match.group().upper() if bom_match else "BOM-2026-001"
        bom = session.query(BOM).filter(BOM.id == bom_id).first()
        items = session.query(BOMItem).filter(BOMItem.bom_id == bom_id).all()

        if "齐套" in query or "够不够" in query:
            avail_results = []
            shortage = 0
            for item in items:
                inv = session.query(Inventory).filter(Inventory.material_code == item.material_code).first()
                stock = inv.quantity if inv else 0
                is_short = stock < item.quantity
                if is_short:
                    shortage += 1
                avail_results.append({"material": item.material_name, "required": item.quantity, "stock": stock, "status": "缺货" if is_short else "充足"})
            result = {"bom_id": bom_id, "total": len(avail_results), "shortage": shortage, "items": avail_results}
        else:
            result = {"bom": bom.to_dict() if bom else None, "items": [i.to_dict() for i in items], "total_cost": sum(i.cost * i.quantity for i in items)}
    finally:
        session.close()
    trace.add_step(agent="BOM管理Agent", phase=TracePhase.OBSERVATION,
                   observation=str(result)[:200], duration_ms=int((time.time() - start) * 1000))
    return {"agent": "BOM管理Agent", "data": result}


def run_inventory_agent(query: str, trace: TraceLogger) -> dict:
    """库存分析Agent"""
    start = time.time()
    trace.add_step(agent="库存分析Agent", phase=TracePhase.ACTION,
                   thought="查询库存信息", action="inventory_tools")
    from src.models.database import get_db_session
    from src.models.tables import Inventory
    session = get_db_session()
    try:
        if "短缺" in query or "缺货" in query or "预警" in query:
            items = session.query(Inventory).filter(Inventory.status == "短缺").all()
            result = {"shortage_alerts": [{**i.to_dict(), "gap": round(i.safety_stock - i.quantity, 2)} for i in items]}
        elif "呆滞" in query:
            items = session.query(Inventory).filter(Inventory.turnover_days >= 180).all()
            result = {"obsolete_materials": [i.to_dict() for i in items]}
        else:
            total = session.query(Inventory).count()
            shortage = session.query(Inventory).filter(Inventory.status == "短缺").count()
            obsolete = session.query(Inventory).filter(Inventory.status == "呆滞").count()
            normal = session.query(Inventory).filter(Inventory.status == "正常").count()
            result = {"total": total, "shortage": shortage, "obsolete": obsolete, "normal": normal}
    finally:
        session.close()
    trace.add_step(agent="库存分析Agent", phase=TracePhase.OBSERVATION,
                   observation=str(result)[:200], duration_ms=int((time.time() - start) * 1000))
    return {"agent": "库存分析Agent", "data": result}


def run_knowledge_agent(query: str, trace: TraceLogger) -> dict:
    """工艺知识Agent（RAG）"""
    start = time.time()
    trace.add_step(agent="工艺知识Agent", phase=TracePhase.ACTION,
                   thought="RAG检索焊接知识库", action="rag_retrieval")
    context = retrieve_knowledge(query, k=3)
    result = {"rag_context": context}

    # 参数推荐
    mat_match = re.search(r'Q235|Q345|SUS304|304', query, re.IGNORECASE)
    thick_match = re.search(r'(\d+)mm', query)
    if mat_match and thick_match and ("怎么焊" in query or "参数" in query or "推荐" in query):
        from src.agents.tools.knowledge_tools import recommend_welding_parameters
        result["recommendation"] = recommend_welding_parameters.invoke({"material": mat_match.group().upper(), "thickness": thick_match.group()})

    # 缺陷诊断
    for defect in ["气孔", "夹渣", "未焊透", "裂纹", "咬边"]:
        if defect in query:
            from src.agents.tools.knowledge_tools import diagnose_welding_defect
            result["diagnosis"] = diagnose_welding_defect.invoke({"defect_type": defect})
            break

    trace.add_step(agent="工艺知识Agent", phase=TracePhase.OBSERVATION,
                   observation=context[:200], duration_ms=int((time.time() - start) * 1000))
    return {"agent": "工艺知识Agent", "data": result}


AGENT_ROUTERS = {
    IntentType.DEVICE: run_device_agent,
    IntentType.PRODUCTION: run_production_agent,
    IntentType.BOM: run_bom_agent,
    IntentType.INVENTORY: run_inventory_agent,
    IntentType.KNOWLEDGE: run_knowledge_agent,
}


def supervisor_chat(user_input: str, session_id: Optional[str] = None) -> dict:
    """主控Agent对话入口"""
    trace = create_trace(session_id)
    start_time = time.time()

    # 意图识别
    trace.add_step(agent="主控Agent", phase=TracePhase.ROUTING,
                   thought=f"分析用户输入: {user_input}", action="classify_intent")
    intent, sub_intents = classify_intent(user_input)
    routed_intents = sub_intents if sub_intents else [intent]
    trace.add_step(agent="主控Agent", phase=TracePhase.ROUTING,
                   thought=f"识别意图: {intent.value}, 子意图: {[i.value for i in routed_intents]}",
                   action="route_to_agents", action_input=[i.value for i in routed_intents],
                   observation=f"路由到 {len(routed_intents)} 个Agent")

    # 执行专业Agent
    all_results = []
    for it in routed_intents:
        agent_fn = AGENT_ROUTERS.get(it)
        if agent_fn:
            try:
                result = agent_fn(user_input, trace)
                all_results.append(result)
            except Exception as e:
                all_results.append({"agent": it.value, "error": str(e)})
                trace.add_step(agent=it.value, phase=TracePhase.OBSERVATION, observation=f"执行出错: {e}")

    # 生成回答
    answer = format_answer(user_input, intent, all_results)
    trace.add_step(agent="主控Agent", phase=TracePhase.ANSWER,
                   thought="聚合各Agent结果", action="generate_answer",
                   observation=answer[:200], duration_ms=int((time.time() - start_time) * 1000))

    return {
        "session_id": trace.session_id,
        "user_input": user_input,
        "intent": intent.value,
        "routed_agents": [r.get("agent", "") for r in all_results],
        "answer": answer,
        "results": all_results,
        "trace": trace.get_trace(),
    }


def format_answer(user_input: str, intent: IntentType, results: list) -> str:
    """格式化最终回答"""
    if not results:
        return "抱歉，未能处理您的请求。"
    parts = []
    for r in results:
        agent = r.get("agent", "")
        data = r.get("data", {})
        if "error" in r:
            parts.append(f"[{agent}] 执行出错: {r['error']}")
        else:
            parts.append(f"[{agent}] 查询结果:\n{format_data(data)}")
    answer = "\n\n".join(parts)
    if len(results) > 1:
        answer = f"您的问题涉及多个领域，已分别调用相关Agent处理：\n\n{answer}"
    return answer


def format_data(data: dict, indent: int = 0) -> str:
    """递归格式化数据为可读文本"""
    if not isinstance(data, dict):
        return str(data)
    lines = []
    prefix = "  " * indent
    for key, val in data.items():
        if isinstance(val, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(format_data(val, indent + 1))
        elif isinstance(val, list):
            lines.append(f"{prefix}{key}: ({len(val)}项)")
            for item in val[:3]:
                if isinstance(item, dict):
                    lines.append(format_data(item, indent + 1))
                else:
                    lines.append(f"{prefix}  - {item}")
            if len(val) > 3:
                lines.append(f"{prefix}  ... 等{len(val)}项")
        else:
            lines.append(f"{prefix}{key}: {val}")
    return "\n".join(lines)
