"""
FastAPI应用入口
注册所有路由，配置CORS，启动时初始化数据库与知识库
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.init_data import init_all_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库、模拟数据与知识库"""
    print("[Startup] 初始化数据库与模拟数据...")
    init_all_data()

    # 初始化RAG知识库（失败不阻塞服务启动）
    print("[Startup] 初始化RAG知识库...")
    try:
        from src.agents.rag.vector_store import init_knowledge_base
        success = init_knowledge_base()
        if success:
            print("[Startup] RAG知识库初始化成功")
        else:
            print("[Startup] RAG知识库初始化失败，将使用降级模式")
    except Exception as e:
        print(f"[Startup] RAG知识库初始化异常: {e}，将使用降级模式")

    print("[Startup] 服务已就绪")
    yield
    print("[Shutdown] 服务已停止")


app = FastAPI(
    title="焊接设备AI Agent综合管理平台",
    description="1主控Agent + 5专业Agent多智能体系统API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.api.routes import chat, devices, production, bom, inventory, trace, knowledge

app.include_router(chat.router, prefix="/api", tags=["对话"])
app.include_router(devices.router, prefix="/api/devices", tags=["设备监控"])
app.include_router(production.router, prefix="/api/production", tags=["生产进度"])
app.include_router(bom.router, prefix="/api/bom", tags=["BOM管理"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["库存分析"])
app.include_router(trace.router, prefix="/api/sessions", tags=["执行轨迹"])
app.include_router(knowledge.router, tags=["知识库管理"])  # 前缀已在路由文件中定义为 /api/knowledge

from src.api.websocket import router as ws_router
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])


@app.get("/")
async def root():
    return {"service": "焊接设备AI Agent综合管理平台", "version": "1.0.0", "status": "running", "docs": "/docs"}


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "welding-agent-platform"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.server:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=settings.DEBUG)
