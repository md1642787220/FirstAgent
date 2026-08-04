"""
认证路由
简单的账号密码登录，签发 token（演示用，非生产级安全）
"""
import os
import base64
import json
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# 默认账号（可被环境变量 ADMIN_USER / ADMIN_PASSWORD 覆盖）
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# token 有效期（秒）：默认 12 小时
TOKEN_TTL = 12 * 3600


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    expires_at: float


def _make_token(username: str) -> str:
    """生成一个简单的 base64 token（payload 含用户名与过期时间）"""
    payload = {
        "username": username,
        "issued_at": int(time.time()),
        "expires_at": int(time.time()) + TOKEN_TTL,
    }
    raw = json.dumps(payload, ensure_ascii=False)
    return base64.b64encode(raw.encode("utf-8")).decode("ascii")


def verify_token(token: str) -> dict | None:
    """校验 token，返回 payload 或 None"""
    try:
        raw = base64.b64decode(token.encode("ascii")).decode("utf-8")
        payload = json.loads(raw)
        if payload.get("expires_at", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


@router.post("/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    if req.username != ADMIN_USER or req.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = _make_token(req.username)
    return LoginResponse(
        token=token,
        username=req.username,
        expires_at=int(time.time()) + TOKEN_TTL,
    )
