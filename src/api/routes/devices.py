"""设备监控接口"""
from fastapi import APIRouter

from src.simulators.welding_simulator import welding_simulator

router = APIRouter()


@router.get("")
async def get_devices():
    """获取所有设备列表"""
    return {"devices": welding_simulator.get_devices()}


@router.post("/refresh")
async def refresh_devices():
    """刷新设备状态：重新探测设备在线/离线情况"""
    return {"devices": welding_simulator.refresh_devices()}


@router.get("/{device_id}/metrics")
async def get_device_metrics(device_id: str):
    """获取设备实时参数"""
    return welding_simulator.get_device_metrics(device_id)


@router.get("/{device_id}/history")
async def get_device_history(device_id: str, seconds: int = 60):
    """获取设备历史参数"""
    return {"history": welding_simulator.get_device_history(device_id, seconds)}


@router.post("/{device_id}/diagnose")
async def diagnose_device(device_id: str, metric: str = "", value: float = 0):
    """诊断设备异常"""
    from src.agents.tools.device_tools import diagnose_anomaly
    return diagnose_anomaly.invoke({"device_id": device_id, "metric": metric, "value": value})
