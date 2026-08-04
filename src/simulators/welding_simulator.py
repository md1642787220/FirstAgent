"""
焊接设备参数模拟器
模拟焊接设备的实时参数数据（电流/电压/焊速/气体流量/温度/振动）
支持父子设备结构（A-391/A-392 系列下挂 LT-100/LT-200 子设备）
"""
import random
import time
import math
from datetime import datetime
from typing import Optional


class WeldingSimulator:
    """焊接设备参数模拟器，生成带波动趋势的实时数据"""

    # 设备列表（含父子结构）
    # parent_id 为 None 表示顶级设备；非 None 表示是某系列的子设备
    DEVICES = [
        # === A-391 系列 ===
        {"id": "A-391", "name": "A-391 焊接系统", "type": "MIG焊机", "status": "offline", "parent_id": None},
        {"id": "A-391-LT-100", "name": "LT-100 焊枪头", "type": "MIG焊枪头", "status": "offline", "parent_id": "A-391"},
        {"id": "A-391-LT-200", "name": "LT-200 焊枪头", "type": "MIG焊枪头", "status": "offline", "parent_id": "A-391"},
        # === A-392 系列 ===
        {"id": "A-392", "name": "A-392 焊接系统", "type": "TIG焊机", "status": "offline", "parent_id": None},
        {"id": "A-392-LT-100", "name": "LT-100 焊枪头", "type": "TIG焊枪头", "status": "offline", "parent_id": "A-392"},
        {"id": "A-392-LT-200", "name": "LT-200 焊枪头", "type": "TIG焊枪头", "status": "offline", "parent_id": "A-392"},
        # === A-500 ===
        {"id": "A-500", "name": "A-500 多功能焊机", "type": "MAG焊机", "status": "offline", "parent_id": None},
        # === A-1000i ===
        {"id": "A-1000i", "name": "A-1000i 机器人焊接站", "type": "机器人焊机", "status": "offline", "parent_id": None},
    ]

    def __init__(self):
        self._tick = 0
        self._device_states = {}
        for dev in self.DEVICES:
            # 离线设备不生成实时数据（值为 None）
            if dev["status"] == "offline":
                self._device_states[dev["id"]] = None
            else:
                self._device_states[dev["id"]] = {
                    "current": 245.0,
                    "voltage": 28.5,
                    "speed": 520.0,
                    "wire_speed": 8.5,
                    "gas_flow": 22.0,
                    "temperature": 55.0,
                    "vibration": 0.12,
                }

    def get_devices(self) -> list:
        """获取设备列表（含父子结构）"""
        return self.DEVICES

    def refresh_devices(self) -> list:
        """刷新设备状态：模拟重新探测设备在线情况。

        刷新后大部分设备恢复在线（模拟探测成功），少数随机离线，
        并返回刷新后的最新设备列表。
        """
        for dev in self.DEVICES:
            # 90% 概率在线，模拟探测成功；其余保持/恢复为离线
            online = random.random() < 0.9
            dev["status"] = "online" if online else "offline"
            if online:
                self._device_states[dev["id"]] = {
                    "current": 245.0,
                    "voltage": 28.5,
                    "speed": 520.0,
                    "wire_speed": 8.5,
                    "gas_flow": 22.0,
                    "temperature": 55.0,
                    "vibration": 0.12,
                }
            else:
                self._device_states[dev["id"]] = None
        return self.DEVICES

    def get_device_metrics(self, device_id: str) -> dict:
        """获取设备实时参数（带波动）。离线设备返回离线状态。"""
        if device_id not in self._device_states:
            return {"error": f"设备 {device_id} 不存在"}

        # 离线设备
        if self._device_states[device_id] is None:
            return {
                "device_id": device_id,
                "timestamp": datetime.now().isoformat(),
                "status": "offline",
                "metrics": None,
                "alerts": [],
            }

        state = self._device_states[device_id]
        self._tick += 1

        # 生成带正弦波趋势的波动数据
        t = self._tick * 0.1
        metrics = {
            "current": round(state["current"] + math.sin(t) * 8 + random.uniform(-3, 3), 1),
            "voltage": round(state["voltage"] + math.sin(t * 1.2) * 1.5 + random.uniform(-0.5, 0.5), 2),
            "speed": round(state["speed"] + math.sin(t * 0.8) * 20 + random.uniform(-10, 10), 1),
            "wire_speed": round(state["wire_speed"] + math.sin(t * 1.5) * 0.8 + random.uniform(-0.3, 0.3), 2),
            "gas_flow": round(state["gas_flow"] + math.sin(t * 0.5) * 1.2 + random.uniform(-0.5, 0.5), 1),
            "temperature": round(state["temperature"] + math.sin(t * 0.3) * 3 + random.uniform(-1, 1), 1),
            "vibration": round(state["vibration"] + abs(math.sin(t * 2)) * 0.1 + random.uniform(-0.02, 0.02), 3),
        }

        # 判断是否异常
        alerts = self._check_alerts(metrics)
        return {
            "device_id": device_id,
            "timestamp": datetime.now().isoformat(),
            "status": "online",
            "metrics": metrics,
            "alerts": alerts,
        }

    def get_device_history(self, device_id: str, seconds: int = 60) -> list:
        """获取设备历史参数（最近N秒）。离线设备返回空。"""
        if device_id not in self._device_states or self._device_states[device_id] is None:
            return []

        history = []
        for i in range(seconds):
            t = (self._tick - seconds + i) * 0.1
            history.append({
                "timestamp": datetime.now().isoformat(),
                "current": round(245 + math.sin(t) * 8 + random.uniform(-2, 2), 1),
                "voltage": round(28.5 + math.sin(t * 1.2) * 1.5 + random.uniform(-0.3, 0.3), 2),
                "speed": round(520 + math.sin(t * 0.8) * 20 + random.uniform(-5, 5), 1),
                "gas_flow": round(22 + math.sin(t * 0.5) * 1.2 + random.uniform(-0.3, 0.3), 1),
            })
        return history

    def _check_alerts(self, metrics: dict) -> list:
        """检查参数是否超出正常范围"""
        alerts = []
        ranges = {
            "current": (100, 300, "电流"),
            "voltage": (20, 35, "电压"),
            "temperature": (0, 85, "温度"),
            "vibration": (0, 0.5, "振动"),
        }
        for key, (low, high, label) in ranges.items():
            val = metrics.get(key, 0)
            if val > high:
                alerts.append({"metric": key, "label": label, "level": "high", "value": val, "msg": f"{label}过高({val})"})
            elif val < low:
                alerts.append({"metric": key, "label": label, "level": "low", "value": val, "msg": f"{label}过低({val})"})
        return alerts

    def inject_anomaly(self, device_id: str, metric: str, value: float):
        """注入异常值（用于测试）"""
        if device_id in self._device_states and self._device_states[device_id] is not None:
            self._device_states[device_id][metric] = value
            return {"msg": f"已注入异常: {device_id} {metric}={value}"}
        return {"error": f"设备 {device_id} 不存在或离线"}


# 单例
welding_simulator = WeldingSimulator()
