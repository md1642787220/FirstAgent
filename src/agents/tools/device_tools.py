"""
设备监控Agent工具集
查询焊接设备实时参数、历史数据、异常诊断
"""
from langchain_core.tools import tool
from src.simulators.welding_simulator import welding_simulator


@tool
def get_device_metrics(device_id: str) -> dict:
    """获取焊接设备实时参数。输入设备ID（如DEV-W001），返回电流、电压、焊速、气体流量等实时数据。

    Args:
        device_id: 设备ID，例如 DEV-W001、DEV-W002
    """
    return welding_simulator.get_device_metrics(device_id)


@tool
def get_device_history(device_id: str, seconds: int = 60) -> list:
    """获取设备历史参数数据。返回最近N秒的参数变化曲线数据。

    Args:
        device_id: 设备ID
        seconds: 查询最近多少秒的数据，默认60秒
    """
    return welding_simulator.get_device_history(device_id, seconds)


@tool
def get_all_devices() -> list:
    """获取所有焊接设备列表及其状态。"""
    return welding_simulator.get_devices()


@tool
def diagnose_anomaly(device_id: str, metric: str = "", value: float = 0) -> dict:
    """诊断设备参数异常，给出可能原因和处理建议。

    Args:
        device_id: 设备ID
        metric: 异常参数名（current/voltage/temperature/vibration）
        value: 异常值（可选，不传则自动获取最新值）
    """
    metrics = welding_simulator.get_device_metrics(device_id)
    if "error" in metrics:
        return metrics

    alerts = metrics.get("alerts", [])
    if not alerts and not metric:
        return {
            "device_id": device_id,
            "status": "正常",
            "diagnosis": "所有参数在正常范围内",
            "suggestion": "无需处理",
        }

    diagnosis_rules = {
        "current": {
            "high": "电流过高，可能原因：电弧长度过短、送丝速度过大、工件间隙过大",
            "low": "电流过低，可能原因：送丝不畅、导电嘴磨损、电源电压波动",
        },
        "voltage": {
            "high": "电压过高，可能原因：电弧长度过长、保护气体流量不足",
            "low": "电压过低，可能原因：回路接触不良、焊丝伸出长度过长",
        },
        "temperature": {
            "high": "设备温度过高，可能原因：冷却系统故障、连续工作时间过长、环境温度过高",
            "low": "温度正常",
        },
        "vibration": {
            "high": "设备振动异常，可能原因：送丝轮磨损、导轨松动、工件固定不牢",
            "low": "振动正常",
        },
    }

    results = []
    for alert in alerts:
        m = alert["metric"]
        level = alert["level"]
        rule = diagnosis_rules.get(m, {}).get(level, "未知异常，需人工检查")
        results.append({
            "metric": m,
            "label": alert["label"],
            "value": alert["value"],
            "level": level,
            "diagnosis": rule,
            "suggestion": "建议停机检查相关部件，确认后恢复生产" if level == "high" else "建议关注并记录趋势",
        })

    return {
        "device_id": device_id,
        "alert_count": len(results),
        "diagnoses": results,
    }


DEVICE_TOOLS = [get_device_metrics, get_device_history, get_all_devices, diagnose_anomaly]
