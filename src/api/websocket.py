"""
WebSocket实时推送
设备参数更新、库存预警、Agent轨迹步骤实时推送
"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# 活跃WebSocket连接
_active_connections: list[WebSocket] = []


@router.websocket("/realtime")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket实时推送端点"""
    await ws.accept()
    _active_connections.append(ws)
    try:
        await ws.send_json({"event": "connected", "msg": "WebSocket已连接"})

        # 启动设备参数推送任务
        async def push_metrics():
            from src.simulators.welding_simulator import welding_simulator
            while True:
                for dev in welding_simulator.DEVICES:
                    if dev["status"] == "运行中":
                        metrics = welding_simulator.get_device_metrics(dev["id"])
                        await ws.send_json({"event": "metrics:update", "data": metrics})
                await asyncio.sleep(2)

        task = asyncio.create_task(push_metrics())
        # 保持连接，接收客户端消息
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            # 处理客户端消息（如订阅特定事件）
            await ws.send_json({"event": "ack", "msg": f"已收到: {msg}"})

    except WebSocketDisconnect:
        _active_connections.remove(ws)
        task.cancel()


async def broadcast(event: str, data: dict):
    """向所有活跃连接广播消息"""
    for ws in _active_connections:
        try:
            await ws.send_json({"event": event, "data": data})
        except Exception:
            _active_connections.remove(ws)
