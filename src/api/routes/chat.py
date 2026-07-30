"""对话接口 - SSE流式返回"""
import json
from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.agents.supervisor import supervisor_chat

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str = None


@router.post("/chat")
async def chat(req: ChatRequest):
    """对话接口 - SSE流式返回Agent执行过程与最终答案"""
    result = supervisor_chat(req.message, req.session_id)

    async def event_generator():
        # 流式推送轨迹步骤
        for step in result["trace"]["steps"]:
            yield {"event": "trace_step", "data": json.dumps(step, ensure_ascii=False, default=str)}
        # 推送最终答案
        yield {"event": "answer", "data": json.dumps({
            "session_id": result["session_id"],
            "intent": result["intent"],
            "answer": result["answer"],
        }, ensure_ascii=False, default=str)}
        yield {"event": "done", "data": "[DONE]"}

    return EventSourceResponse(event_generator())


@router.post("/chat/sync")
async def chat_sync(req: ChatRequest):
    """对话接口 - 同步返回完整结果"""
    result = supervisor_chat(req.message, req.session_id)
    return {
        "session_id": result["session_id"],
        "intent": result["intent"],
        "routed_agents": result["routed_agents"],
        "answer": result["answer"],
        "trace": result["trace"],
    }
