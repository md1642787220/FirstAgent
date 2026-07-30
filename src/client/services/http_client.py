"""
HTTP客户端 - 调用后端REST API
封装所有与FastAPI后端的HTTP通信
"""
import httpx
from typing import Optional


class ApiClient:
    """后端API客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=30.0)

    # ===== 对话 =====
    def chat_sync(self, message: str, session_id: Optional[str] = None) -> dict:
        """同步对话"""
        resp = self.client.post("/api/chat/sync", json={"message": message, "session_id": session_id})
        resp.raise_for_status()
        return resp.json()

    # ===== 设备 =====
    def get_devices(self) -> dict:
        resp = self.client.get("/api/devices")
        return resp.json()

    def get_device_metrics(self, device_id: str) -> dict:
        resp = self.client.get(f"/api/devices/{device_id}/metrics")
        return resp.json()

    def get_device_history(self, device_id: str, seconds: int = 60) -> dict:
        resp = self.client.get(f"/api/devices/{device_id}/history", params={"seconds": seconds})
        return resp.json()

    # ===== 生产 =====
    def get_production_orders(self, status: str = "") -> dict:
        resp = self.client.get("/api/production/orders", params={"status": status} if status else {})
        return resp.json()

    def get_order_detail(self, order_id: str) -> dict:
        resp = self.client.get(f"/api/production/orders/{order_id}")
        return resp.json()

    def get_delays(self) -> dict:
        resp = self.client.get("/api/production/delays")
        return resp.json()

    def get_production_summary(self) -> dict:
        resp = self.client.get("/api/production/summary")
        return resp.json()

    # ===== BOM =====
    def get_all_boms(self) -> dict:
        resp = self.client.get("/api/bom")
        return resp.json()

    def get_bom(self, bom_id: str) -> dict:
        resp = self.client.get(f"/api/bom/{bom_id}")
        return resp.json()

    def check_availability(self, bom_id: str, quantity: int = 1) -> dict:
        resp = self.client.post("/api/bom/availability", params={"bom_id": bom_id, "quantity": quantity})
        return resp.json()

    # ===== 库存 =====
    def get_inventory(self, status: str = "") -> dict:
        resp = self.client.get("/api/inventory", params={"status": status} if status else {})
        return resp.json()

    def get_inventory_alerts(self) -> dict:
        resp = self.client.get("/api/inventory/alerts")
        return resp.json()

    def get_inventory_obsolete(self, days: int = 180) -> dict:
        resp = self.client.get("/api/inventory/obsolete", params={"days": days})
        return resp.json()

    def get_inventory_summary(self) -> dict:
        resp = self.client.get("/api/inventory/summary")
        return resp.json()

    # ===== 轨迹 =====
    def get_trace(self, session_id: str) -> dict:
        resp = self.client.get(f"/api/sessions/{session_id}/trace")
        return resp.json()

    def close(self):
        self.client.close()


# 全局API客户端
api_client = ApiClient()
