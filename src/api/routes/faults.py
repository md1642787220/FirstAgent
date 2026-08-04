"""
故障库管理接口
提供故障记录的增删查改，用于日常积累常见故障供新人排查参考
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from src.models.database import get_db_session
from src.models.tables import FaultRecord

router = APIRouter()


# ============================================================
# 数据模型
# ============================================================

class FaultCreate(BaseModel):
    symptom: str
    category: str
    device_type: Optional[str] = None
    cause: Optional[str] = None
    solution: Optional[str] = None
    severity: str = "medium"          # high / medium / low
    recorder: Optional[str] = None


class FaultUpdate(BaseModel):
    symptom: Optional[str] = None
    category: Optional[str] = None
    device_type: Optional[str] = None
    cause: Optional[str] = None
    solution: Optional[str] = None
    severity: Optional[str] = None


# ============================================================
# 初始数据预置（首次启动时若表为空则灌入）
# ============================================================

INITIAL_FAULTS = [
    {"symptom": "难以引弧或频繁断弧", "category": "起弧异常", "cause": "电流设置过低 / 钨极氧化 / 接地不良", "solution": "检查电流设置、清理钨极、确认工件接地良好", "severity": "high", "recorder": "系统"},
    {"symptom": "焊缝表面出现气孔", "category": "焊缝缺陷", "cause": "保护气体不纯 / 工件表面油污锈迹 / 气流量过大或过小", "solution": "更换气体、检查气路、清理工件表面、调整流量至15-20L/min", "severity": "high", "recorder": "系统"},
    {"symptom": "焊缝有夹渣", "category": "焊缝缺陷", "cause": "层间清理不彻底 / 焊接电流过低 / 焊接速度过快", "solution": "加强层间打磨、提高电流、降低焊接速度", "severity": "medium", "recorder": "系统"},
    {"symptom": "送丝不均匀、有卡顿", "category": "送丝异常", "cause": "导电嘴磨损 / 送丝管堵塞 / 压轮压力不当", "solution": "更换导电嘴、清理送丝管、调整压轮压力", "severity": "medium", "recorder": "系统"},
    {"symptom": "焊缝出现咬边", "category": "焊缝缺陷", "cause": "焊接电流过大 / 焊接速度过快 / 运条角度不当", "solution": "适当降低电流、调整速度、保持正确运条角度", "severity": "low", "recorder": "系统"},
    {"symptom": "设备温度过高报警", "category": "温度报警", "cause": "长时间高负荷运行 / 散热风扇故障 / 环境温度过高", "solution": "停机降温、检查风扇、降低负载、改善通风", "severity": "high", "recorder": "系统"},
    {"symptom": "气体流量不稳定", "category": "气体保护", "cause": "气瓶压力低 / 减压阀故障 / 管路漏气", "solution": "更换气瓶、检查减压阀、检测管路密封", "severity": "medium", "recorder": "系统"},
    {"symptom": "电弧漂移、磁偏吹", "category": "起弧异常", "cause": "工件磁性 / 接地位置不对称 / 电缆走向不合理", "solution": "调整接地位置、改变电缆走向、分段焊接", "severity": "low", "recorder": "系统"},
]


def seed_faults_if_empty():
    """表为空时灌入初始故障数据"""
    session = get_db_session()
    try:
        if session.query(FaultRecord).count() == 0:
            for f in INITIAL_FAULTS:
                session.add(FaultRecord(**f))
            session.commit()
            print(f"[Faults] 已预置 {len(INITIAL_FAULTS)} 条初始故障记录")
    except Exception as e:
        session.rollback()
        print(f"[Faults] 预置初始数据失败: {e}")
    finally:
        session.close()


# ============================================================
# 接口
# ============================================================

@router.get("")
async def list_faults(category: Optional[str] = None, device_type: Optional[str] = None):
    """获取故障库列表，支持按类别/设备类型筛选"""
    session = get_db_session()
    try:
        q = session.query(FaultRecord)
        if category:
            q = q.filter(FaultRecord.category == category)
        if device_type:
            q = q.filter(FaultRecord.device_type == device_type)
        records = q.order_by(FaultRecord.created_at.desc()).all()
        return {"faults": [r.to_dict() for r in records], "count": len(records)}
    finally:
        session.close()


@router.post("")
async def create_fault(fault: FaultCreate):
    """新增故障记录"""
    if fault.severity not in ("high", "medium", "low"):
        raise HTTPException(status_code=400, detail="severity 必须为 high/medium/low")
    session = get_db_session()
    try:
        record = FaultRecord(
            symptom=fault.symptom.strip(),
            category=fault.category.strip(),
            device_type=fault.device_type,
            cause=fault.cause,
            solution=fault.solution,
            severity=fault.severity,
            recorder=fault.recorder or "匿名",
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return {"msg": "故障记录已新增", "fault": record.to_dict()}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"新增失败: {e}")
    finally:
        session.close()


@router.put("/{fault_id}")
async def update_fault(fault_id: int, fault: FaultUpdate):
    """更新故障记录"""
    session = get_db_session()
    try:
        record = session.query(FaultRecord).filter(FaultRecord.id == fault_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="故障记录不存在")
        updates = fault.model_dump(exclude_none=True)
        for k, v in updates.items():
            setattr(record, k, v)
        session.commit()
        session.refresh(record)
        return {"msg": "已更新", "fault": record.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {e}")
    finally:
        session.close()


@router.delete("/{fault_id}")
async def delete_fault(fault_id: int):
    """删除故障记录"""
    session = get_db_session()
    try:
        record = session.query(FaultRecord).filter(FaultRecord.id == fault_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="故障记录不存在")
        session.delete(record)
        session.commit()
        return {"msg": "已删除", "id": fault_id}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {e}")
    finally:
        session.close()
