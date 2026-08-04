"""对话接口 - SSE流式返回（DeepSeek 真实 token 级流式）+ 历史记录"""
import json
import uuid
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.agents.supervisor import supervisor_chat, supervisor_chat_stream
from src.models.database import get_db_session
from src.models.tables import ChatSession, ChatMessage

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str = None
    # 用户角色：expert 专家 / beginner 新手 / user 普通用户（默认）
    # 用于动态生成系统提示词，让AI回答风格匹配用户角色
    user_role: str = "user"


@router.post("/chat")
async def chat(req: ChatRequest):
    """对话接口 - DeepSeek token 级 SSE 流式返回 + 自动持久化"""
    # 生成或复用 session_id
    actual_sid = req.session_id or f"sess_{uuid.uuid4().hex[:8]}"
    full_answer = ""

    # 规范化 user_role，防止传入非法值
    user_role = req.user_role if req.user_role in ("expert", "beginner", "user") else "user"

    async def event_generator():
        nonlocal full_answer

        # 保存用户消息
        _save_message(actual_sid, "user", req.message)

        # 流式生成回答
        for chunk in supervisor_chat_stream(req.message, actual_sid, user_role=user_role):
            event = chunk.get("event", "message")
            data = chunk.get("data", "")

            # 收集完整回答
            if event == "answer_chunk":
                full_answer += data if isinstance(data, str) else ""

            # 推送 session_id（第一条事件）
            if not hasattr(event_generator, '_sent_sid'):
                event_generator._sent_sid = True
                yield {
                    "event": "session",
                    "data": json.dumps({"session_id": actual_sid}, ensure_ascii=False),
                }

            if isinstance(data, dict):
                data = json.dumps(data, ensure_ascii=False, default=str)
            yield {"event": event, "data": data}

        # 保存AI回答
        if full_answer.strip():
            _save_message(actual_sid, "assistant", full_answer)

    return EventSourceResponse(event_generator())


@router.get("/chat/sessions")
async def list_sessions():
    """获取所有对话历史"""
    db = get_db_session()
    try:
        sessions = db.query(ChatSession).order_by(
            ChatSession.updated_at.desc()
        ).all()
        return [s.to_dict() for s in sessions]
    finally:
        db.close()


@router.get("/chat/sessions/{session_id}")
async def get_session(session_id: str):
    """获取指定会话的全部消息"""
    db = get_db_session()
    try:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).all()
        return {
            "session_id": session_id,
            "messages": [m.to_dict() for m in messages],
        }
    finally:
        db.close()


@router.delete("/chat/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除指定会话"""
    db = get_db_session()
    try:
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        db.query(ChatSession).filter(ChatSession.id == session_id).delete()
        db.commit()
        return {"ok": True}
    finally:
        db.close()


def _save_message(session_id: str, role: str, content: str):
    """保存一条消息到数据库"""
    db = get_db_session()
    try:
        # 确保 session 存在
        sess = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not sess:
            # 取用户消息前 20 字作为标题
            title = content.replace('\n', ' ')[:20].strip() or "新对话"
            sess = ChatSession(id=session_id, title=title)
            db.add(sess)
        else:
            sess.updated_at = datetime.now()

        # 保存消息
        msg = ChatMessage(session_id=session_id, role=role, content=content)
        db.add(msg)
        db.commit()
    except Exception as e:
        print(f"[Chat] 保存消息失败: {e}")
        db.rollback()
    finally:
        db.close()


@router.post("/chat/sync")
async def chat_sync(req: ChatRequest):
    """对话接口 - 同步返回完整结果"""
    user_role = req.user_role if req.user_role in ("expert", "beginner", "user") else "user"
    result = supervisor_chat(req.message, req.session_id, user_role=user_role)
    return {
        "session_id": result["session_id"],
        "intent": result["intent"],
        "routed_agents": result["routed_agents"],
        "answer": result["answer"],
        "trace": result["trace"],
    }
