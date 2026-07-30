"""执行轨迹接口"""
from fastapi import APIRouter
from src.agents.trace import get_trace_data, _trace_store

router = APIRouter()


@router.get("/{session_id}/trace")
async def get_trace(session_id: str):
    """获取会话执行轨迹"""
    data = get_trace_data(session_id)
    if data is None:
        return {"error": f"会话 {session_id} 不存在"}
    return data


@router.get("/")
async def list_sessions():
    """获取所有会话列表"""
    sessions = []
    for sid, logger in _trace_store.items():
        sessions.append({
            "session_id": sid,
            "total_steps": len(logger.steps),
            "summary": logger.summary(),
        })
    return {"sessions": sessions, "count": len(sessions)}
