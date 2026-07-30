# 焊接设备AI Agent综合管理平台

> 基于"1主控Agent + 5专业Agent"多智能体架构的焊接设备智能管理桌面应用

## 架构概览

```
Qt桌面客户端 (PySide6)  <--HTTP/SSE/WebSocket-->  FastAPI后端  -->  主控Agent (意图路由)
                                                        |
                    +-------------------+----------------+--------+----------+
                    |                   |                |        |          |
              设备监控Agent        生产进度Agent    BOM管理Agent 库存Agent  工艺知识Agent(RAG)
                    |                   |                |        |          |
                WeldingSimulator    SQLite(work_orders)  SQLite   SQLite    Chroma+BM25
```

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | PySide6 (Qt6), Qt Charts, 深色工业主题 |
| 后端 | FastAPI, uvicorn, SSE流式输出, WebSocket |
| Agent | LangChain, LangGraph, 意图路由, 5个专业Agent |
| RAG | Chroma向量库, BM25混合检索, 内置焊接知识库 |
| 数据 | SQLite + SQLAlchemy, 5张ORM表, 4套数据模拟器 |

## 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化模拟数据

```bash
python -m src.init_data
```

### 3. 启动后端服务

```bash
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

### 4. 启动Qt客户端

```bash
python -m src.client.main
```

### 5. 访问API文档

浏览器打开 http://localhost:8000/docs

## 功能模块

| 模块 | 功能 | API |
|------|------|-----|
| 实时监控 | 焊接参数仪表盘、实时曲线、异常告警 | /api/devices |
| 生产进度 | 工单看板、工序进度、滞后预警 | /api/production |
| BOM管理 | 树形展示、版本对比、齐套分析 | /api/bom |
| 库存分析 | 水位看板、短缺预警、呆滞识别 | /api/inventory |
| AI对话 | 自然语言问答、多Agent路由 | /api/chat |
| 轨迹追踪 | 思考-行动-观察全链路可视化 | /api/sessions |

## 项目结构

```
src/
  config.py              # 全局配置
  init_data.py           # 数据初始化脚本
  models/                # ORM表定义 + 数据库引擎
  simulators/            # 4套数据模拟器
  agents/
    tools/               # 5个专业Agent工具集
    rag/                 # RAG知识库(向量存储+混合检索)
    supervisor.py        # 主控Agent(意图识别+路由)
    trace.py             # 轨迹日志系统
  api/
    server.py            # FastAPI入口
    routes/              # 6组REST接口
    websocket.py         # WebSocket实时推送
  client/
    main.py              # Qt应用入口
    widgets/             # 6大功能面板
    services/            # HTTP/WebSocket客户端
    styles/              # 深色工业主题
```

## Agent意图路由

| 用户输入示例 | 识别意图 | 路由Agent |
|---|---|---|
| 当前焊接电流是多少？ | 设备监控 | 设备监控Agent |
| WO-2026-001做到哪了？ | 生产进度 | 生产进度Agent |
| BOM-2026-001包含什么物料？ | BOM管理 | BOM管理Agent |
| 焊丝还有多少？ | 库存分析 | 库存分析Agent |
| Q235 10mm怎么焊？ | 工艺知识 | 工艺知识Agent(RAG) |

## 测试

```bash
python -m pytest tests/
```
