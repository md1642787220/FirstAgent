"""
WebSocket客户端 - 接收实时推送事件
设备参数更新、库存预警、Agent轨迹步骤
"""
import json
import asyncio
from typing import Callable, Optional

try:
    from PySide6.QtCore import QObject, Signal, QThread
    import websockets
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False


if PYSIDE6_AVAILABLE:

    class WebSocketClient(QObject):
        """WebSocket客户端（PySide6信号驱动）"""
        metrics_received = Signal(dict)
        alert_received = Signal(dict)
        trace_received = Signal(dict)
        connected = Signal()
        disconnected = Signal()

        def __init__(self, url: str = "ws://localhost:8000/ws/realtime"):
            super().__init__()
            self.url = url
            self._running = False
            self._ws = None

        async def _connect(self):
            try:
                self._ws = await websockets.connect(self.url)
                self.connected.emit()
                self._running = True
                while self._running:
                    try:
                        msg = await self._ws.recv()
                        data = json.loads(msg)
                        event = data.get("event", "")
                        if event == "metrics:update":
                            self.metrics_received.emit(data.get("data", {}))
                        elif event == "inventory:alert":
                            self.alert_received.emit(data.get("data", {}))
                        elif event == "trace:step":
                            self.trace_received.emit(data.get("data", {}))
                    except Exception:
                        break
            except Exception as e:
                print(f"[WS] 连接失败: {e}")
            finally:
                self.disconnected.emit()

        def start(self):
            """在独立线程中启动WebSocket"""
            import threading
            def run():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._connect())
            t = threading.Thread(target=run, daemon=True)
            t.start()

        def stop(self):
            self._running = False
            if self._ws:
                asyncio.run(self._ws.close())

else:
    # PySide6不可用时的简易桩
    class WebSocketClient:
        def __init__(self, *args, **kwargs):
            pass
        def start(self):
            pass
        def stop(self):
            pass
