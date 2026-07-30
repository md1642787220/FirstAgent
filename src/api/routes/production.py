"""生产进度接口"""
from fastapi import APIRouter
from src.models.database import get_db_session
from src.models.tables import WorkOrder, ProcessStep

router = APIRouter()


@router.get("/orders")
async def get_orders(status: str = ""):
    """获取工单列表"""
    session = get_db_session()
    try:
        query = session.query(WorkOrder)
        if status:
            query = query.filter(WorkOrder.status == status)
        orders = query.order_by(WorkOrder.created_at.desc()).all()
        return {"orders": [wo.to_dict() for wo in orders], "count": len(orders)}
    finally:
        session.close()


@router.get("/orders/{order_id}")
async def get_order_detail(order_id: str):
    """获取工单详情+工序进度"""
    session = get_db_session()
    try:
        wo = session.query(WorkOrder).filter(WorkOrder.id == order_id).first()
        if not wo:
            return {"error": f"工单 {order_id} 不存在"}
        steps = session.query(ProcessStep).filter(
            ProcessStep.work_order_id == order_id
        ).order_by(ProcessStep.step_order).all()
        return {"work_order": wo.to_dict(), "steps": [s.to_dict() for s in steps]}
    finally:
        session.close()


@router.get("/delays")
async def get_delays():
    """获取滞后工单"""
    session = get_db_session()
    try:
        delayed = session.query(WorkOrder).filter(WorkOrder.delay_days > 0).all()
        return {"delayed_orders": [wo.to_dict() for wo in delayed], "count": len(delayed)}
    finally:
        session.close()


@router.get("/summary")
async def get_summary():
    """获取生产汇总"""
    session = get_db_session()
    try:
        total = session.query(WorkOrder).count()
        in_progress = session.query(WorkOrder).filter(WorkOrder.status == "生产中").count()
        completed = session.query(WorkOrder).filter(WorkOrder.status == "已完成").count()
        delayed = session.query(WorkOrder).filter(WorkOrder.delay_days > 0).count()
        urgent = session.query(WorkOrder).filter(WorkOrder.priority == "紧急").count()
        return {"total": total, "in_progress": in_progress, "completed": completed, "delayed": delayed, "urgent": urgent}
    finally:
        session.close()
