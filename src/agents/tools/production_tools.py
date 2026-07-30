"""
生产进度Agent工具集
查询工单状态、工序进度、识别滞后风险
"""
from langchain_core.tools import tool
from src.models.database import get_db_session
from src.models.tables import WorkOrder, ProcessStep


@tool
def get_work_order(work_order_id: str) -> dict:
    """查询工单详细信息。返回工单的产品、数量、进度、状态、计划时间等。

    Args:
        work_order_id: 工单ID，例如 WO-2026-001
    """
    session = get_db_session()
    try:
        wo = session.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not wo:
            return {"error": f"工单 {work_order_id} 不存在"}
        return wo.to_dict()
    finally:
        session.close()


@tool
def get_process_progress(work_order_id: str) -> list:
    """查询工单各工序的详细进度。返回下料、焊接、打磨、检验、包装等工序的状态和耗时。

    Args:
        work_order_id: 工单ID
    """
    session = get_db_session()
    try:
        steps = session.query(ProcessStep).filter(
            ProcessStep.work_order_id == work_order_id
        ).order_by(ProcessStep.step_order).all()
        if not steps:
            return [{"error": f"工单 {work_order_id} 无工序数据"}]
        return [s.to_dict() for s in steps]
    finally:
        session.close()


@tool
def get_all_work_orders(status: str = "") -> list:
    """获取所有工单列表。可按状态筛选。

    Args:
        status: 工单状态筛选（待排产/生产中/已完成/已暂停），为空则返回全部
    """
    session = get_db_session()
    try:
        query = session.query(WorkOrder)
        if status:
            query = query.filter(WorkOrder.status == status)
        orders = query.order_by(WorkOrder.created_at.desc()).all()
        return [wo.to_dict() for wo in orders]
    finally:
        session.close()


@tool
def identify_delays() -> list:
    """识别所有滞后工单。返回delay_days大于0的工单列表及滞后原因分析。"""
    session = get_db_session()
    try:
        delayed = session.query(WorkOrder).filter(WorkOrder.delay_days > 0).all()
        results = []
        for wo in delayed:
            # 查找阻塞工序
            blocked_steps = session.query(ProcessStep).filter(
                ProcessStep.work_order_id == wo.id,
                ProcessStep.status == "阻塞"
            ).all()
            reasons = [s.notes for s in blocked_steps if s.notes]
            results.append({
                **wo.to_dict(),
                "delay_reasons": reasons if reasons else ["未明确记录原因"],
            })
        return results
    finally:
        session.close()


@tool
def get_today_production_summary() -> dict:
    """获取今日生产汇总。返回在制工单数、已完成数、滞后数、紧急工单数。"""
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


PRODUCTION_TOOLS = [get_work_order, get_process_progress, get_all_work_orders, identify_delays, get_today_production_summary]
