"""
Agent执行轨迹日志系统
记录每个Agent每一步的"思考-行动-观察"过程，支持结构化JSON存储与查询
"""
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from dataclasses import dataclass, field, asdict


class TracePhase(str, Enum):
    """轨迹阶段"""
    THINKING = "thinking"      # 思考
    ACTION = "action"          # 行动
    OBSERVATION = "observation"  # 观察
    ROUTING = "routing"        # 路由
    ANSWER = "answer"          # 最终回答


@dataclass
class TraceStep:
    """单个轨迹步骤"""
    step: int                                    # 步骤序号
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    agent: str = ""                              # Agent名称
    phase: str = ""                              # 阶段(thinking/action/observation/routing/answer)
    thought: str = ""                            # 思考内容
    action: str = ""                             # 执行动作
    action_input: Any = None                     # 动作输入
    observation: str = ""                        # 观察结果
    next_thought: str = ""                       # 下一步思考
    duration_ms: int = 0                         # 耗时(毫秒)
    token_usage: int = 0                         # Token消耗

    def to_dict(self) -> dict:
        return asdict(self)


class TraceLogger:
    """轨迹日志记录器"""

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or f"sess_{uuid.uuid4().hex[:8]}"
        self.steps: list[TraceStep] = []
        self._step_counter = 0
        self._start_time = datetime.now()

    def add_step(
        self,
        agent: str,
        phase: TracePhase,
        thought: str = "",
        action: str = "",
        action_input: Any = None,
        observation: str = "",
        next_thought: str = "",
        duration_ms: int = 0,
        token_usage: int = 0,
    ) -> TraceStep:
        """添加一个轨迹步骤"""
        self._step_counter += 1
        step = TraceStep(
            step=self._step_counter,
            agent=agent,
            phase=phase.value if isinstance(phase, TracePhase) else str(phase),
            thought=thought,
            action=action,
            action_input=action_input,
            observation=observation,
            next_thought=next_thought,
            duration_ms=duration_ms,
            token_usage=token_usage,
        )
        self.steps.append(step)
        return step

    def get_trace(self) -> dict:
        """获取完整轨迹"""
        total_duration = int((datetime.now() - self._start_time).total_seconds() * 1000)
        total_tokens = sum(s.token_usage for s in self.steps)
        return {
            "session_id": self.session_id,
            "start_time": self._start_time.isoformat(),
            "total_steps": len(self.steps),
            "total_duration_ms": total_duration,
            "total_token_usage": total_tokens,
            "steps": [s.to_dict() for s in self.steps],
        }

    def to_json(self) -> str:
        """序列化为JSON字符串"""
        return json.dumps(self.get_trace(), ensure_ascii=False, indent=2, default=str)

    def summary(self) -> str:
        """轨迹摘要"""
        return (
            f"会话 {self.session_id} | "
            f"步骤 {len(self.steps)} | "
            f"耗时 {int((datetime.now() - self._start_time).total_seconds() * 1000)}ms | "
            f"Token {sum(s.token_usage for s in self.steps)}"
        )


# 全局轨迹存储（内存，按session_id索引）
_trace_store: dict[str, TraceLogger] = {}


def create_trace(session_id: Optional[str] = None) -> TraceLogger:
    """创建新的轨迹记录器"""
    logger = TraceLogger(session_id)
    _trace_store[logger.session_id] = logger
    return logger


def get_trace(session_id: str) -> Optional[TraceLogger]:
    """获取已有的轨迹记录器"""
    return _trace_store.get(session_id)


def get_trace_data(session_id: str) -> Optional[dict]:
    """获取轨迹数据（字典格式）"""
    logger = _trace_store.get(session_id)
    return logger.get_trace() if logger else None
