"""
WebSocket实时推送
设备参数更新、库存预警、Agent轨迹步骤实时推送
"""
import asyncio
import json
from datetime import datetime
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
                    # 离线设备也推送状态（让前端显示离线），但不生成指标
                    if dev["status"] == "offline":
                        await ws.send_json({
                            "type": "metrics:update",
                            "device_id": dev["id"],
                            "status": "offline",
                            "metrics": None,
                            "updated_at": datetime.now().isoformat(),
                        })
                    else:
                        result = welding_simulator.get_device_metrics(dev["id"])
                        await ws.send_json({
                            "type": "metrics:update",
                            "device_id": dev["id"],
                            "status": result.get("status", "online"),
                            "metrics": result.get("metrics", {}),
                            "alerts": result.get("alerts", []),
                            "updated_at": result.get("timestamp", datetime.now().isoformat()),
                        })
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
