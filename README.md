# 焊接设备AI Agent综合管理平台

> 基于"1主控Agent + 5专业Agent"多智能体架构的焊接设备智能管理平台
>
> 支持 **Web浏览器** 和 **Qt桌面客户端** 双端访问

## 架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                         客户端层                                    │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐   │
│  │  React Web 前端     │    │  Qt 桌面客户端 (PySide6)        │   │
│  │  (Vite + Ant Design) │    │  (深色工业主题 / Qt Charts)     │   │
│  └──────────┬──────────┘    └──────────────┬──────────────────┘   │
└─────────────┼──────────────────────────────┼───────────────────────┘
              │ HTTP/SSE/WebSocket            │ HTTP/SSE/WebSocket
              └──────────────┬───────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI 后端服务                               │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    主控Agent (Supervisor)                     │  │
│  │              意图识别 → 任务路由 → LLM生成回答                 │  │
│  └─────────────────────────────────────────────────────────────┘  │
│         │         │         │         │         │                │
│  ┌──────▼───┐ ┌──▼──────┐ ┌▼───────┐ ┌▼──────┐ ┌▼───────────┐  │
│  │设备监控  │ │生产进度  │ │BOM管理 │ │库存分析│ │工艺知识(RAG)│  │
│  │  Agent   │ │  Agent   │ │ Agent  │ │ Agent  │ │   Agent     │  │
│  └──────┬───┘ └──┬──────┘ └┬───────┘ └┬──────┘ └┬───────────┘  │
│         │        │         │         │        │               │
│  ┌──────▼───┐ ┌──▼──────┐ ┌▼───────┐ ┌▼──────┐ ┌▼───────────┐  │
│  │WeldingSim│ │SQLite   │ │SQLite  │ │SQLite │ │Chroma+BM25  │  │
│  │imulator  │ │工单数据  │ │BOM数据 │ │库存数据│ │+本地Embedding│  │
│  └──────────┘ └─────────┘ └────────┘ └───────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   DeepSeek / 国产LLM  │
                    │  (OpenAI兼容接口)    │
                    └─────────────────────┘
```

## 技术栈

| 层 | 技术 | 说明 |
|---|------|------|
| **Web前端** | React 18, Vite, Ant Design, ECharts | 现代化单页应用 |
| **桌面客户端** | PySide6 (Qt6), Qt Charts | 深色工业主题 |
| **后端框架** | FastAPI, Uvicorn, SSE流式输出, WebSocket | 高性能异步服务 |
| **Agent引擎** | LangChain, LangGraph | 意图路由 + 多Agent协作 |
| **LLM模型** | DeepSeek-V3 / Qwen / GLM 等 | OpenAI兼容接口，支持国产模型 |
| **RAG检索** | Chroma向量库, BM25混合检索, sentence_transformers | 三级降级策略 |
| **数据库** | SQLite + SQLAlchemy | 5张ORM表 + 数据模拟器 |

## 快速启动

### 前置要求

- **Python >= 3.10**
- **Node.js >= 18** （如需运行Web前端）
- **UV 包管理器**

### 0. 安装 UV（首次）

```bash
# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 1. 同步 Python 依赖

```bash
cd e:/Code/FirstAgent
uv sync
```

可选组件按需安装：

```bash
uv sync --extra db-mysql        # MySQL/MariaDB
uv sync --extra db-postgres     # PostgreSQL
uv sync --extra db-sqlserver    # SQL Server (Windows)
uv sync --extra db-oracle       # Oracle (需 Oracle Instant Client)
uv sync --extra ocr             # OCR (需另装 Tesseract-OCR)
```

### 2. 配置 LLM 模型（必须）

复制或创建 `.env` 文件：

```bash
cp .env.example .env   # 或手动创建
```

编辑 `.env` 填入 API Key：

```bash
# ==================== LLM 模型配置 ====================
# 方案1：DeepSeek（推荐，性价比最高）
OPENAI_API_KEY=sk-your-deepseek-api-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
MODEL_NAME=deepseek-chat

# 方案2：通义千问 Qwen
# OPENAI_API_KEY=sk-your-dashscope-key
# OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# MODEL_NAME=qwen-plus

# 方案3：智谱 GLM（有免费额度）
# OPENAI_API_KEY=your-zhipu-key
# OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
# MODEL_NAME=glm-4-flash

# 方案4：Ollama 本地部署（离线环境）
# OPENAI_API_KEY=ollama
# OPENAI_BASE_URL=http://localhost:11434/v1
# MODEL_NAME=qwen2.5:14b

# ==================== 应用配置 ====================
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
```

> **获取 API Key：**
> - DeepSeek: https://platform.deepseek.com/
> - 通义千问: https://dashscope.console.aliyun.com/
> - 智谱 AI: https://open.bigmodel.cn/

### 3. 初始化模拟数据

```bash
uv run python -m src.init_data
```

### 4. 启动后端服务

```bash
uv run python -m uvicorn src.api.server:app --reload --port 8000
```

启动成功后：
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/health

### 5. 启动前端（二选一）

#### 方案 A：React Web 前端（推荐）

```bash
cd web
npm install
npm run dev
```

访问 http://localhost:5173

#### 方案 B：Qt 桌面客户端

```bash
uv run python -m src.client.main
```

---

## 功能模块

| 模块 | 功能 | API 路由 |
|------|------|----------|
| **实时监控** | 焊接参数仪表盘、实时曲线、异常告警 | `/api/devices` |
| **生产进度** | 工单看板、工序进度、滞后预警 | `/api/production` |
| **BOM管理** | 树形展示、版本对比、齐套分析 | `/api/bom` |
| **库存分析** | 水位看板、短缺预警、呆滞识别 | `/api/inventory` |
| **AI对话** | 自然语言问答、多Agent路由、LLM生成回答 | `/api/chat` |
| **知识库管理** | 文档上传、向量化、检索测试 | `/api/knowledge` |
| **轨迹追踪** | 思考-行动-观察全链路可视化 | `/api/sessions` |
| **实时推送** | WebSocket 设备数据实时推送 | `/ws` |

## 项目结构

```
FirstAgent/
├── .env                        # 环境变量配置（含LLM API Key）
├── .env.example                # 配置模板
├── pyproject.toml              # Python项目定义与依赖
├── README.md                   # 本文档
│
├── src/                        # 后端源码
│   ├── config.py               # 全局配置（读取.env）
│   ├── init_data.py            # 数据初始化脚本
│   │
│   ├── models/                 # ORM表定义 + 数据库引擎
│   ├── simulators/             # 4套数据模拟器（设备/生产/BOM/库存）
│   │
│   ├── agents/                 # Agent系统
│   │   ├── tools/              # 5个专业Agent工具集
│   │   ├── rag/                # RAG知识库
│   │   │   ├── vector_store.py # 向量存储（Chroma + 本地Embedding）
│   │   │   └── retriever.py    # 混合检索（向量+BM25+RRF融合）
│   │   ├── supervisor.py       # 主控Agent（意图识别+路由+LLM生成）
│   │   └── trace.py            # 执行轨迹日志系统
│   │
│   ├── api/                    # FastAPI接口层
│   │   ├── server.py           # 应用入口、CORS、生命周期
│   │   ├── websocket.py        # WebSocket实时推送
│   │   └── routes/             # 7组REST接口
│   │       ├── chat.py         # 对话接口（SSE流式响应）
│   │       ├── devices.py      # 设备监控
│   │       ├── production.py   # 生产进度
│   │       ├── bom.py          # BOM管理
│   │       ├── inventory.py    # 库存分析
│   │       ├── knowledge.py    # 知识库管理
│   │       └── trace.py        # 轨迹查询
│   │
│   └── client/                 # Qt桌面客户端
│       ├── main.py             # Qt应用入口
│       ├── widgets/            # 6大功能面板
│       ├── services/           # HTTP/WebSocket客户端
│       └── styles/             # 深色工业主题QSS
│
├── web/                        # React Web前端
│   ├── src/                    # 源码
│   ├── package.json            # 依赖配置
│   └── vite.config.js          # Vite构建配置
│
├── tests/                      # 测试用例
│   ├── test_rag_loader.py      # RAG加载器测试
│   ├── test_rag_retriever.py   # RAG检索器测试
│   ├── test_rag_vector_store.py# 向量存储测试
│   └── test_sentence_transformers.py  # Embedding模型测试
│
└── data/                       # 运行时数据（自动生成）
    ├── welding_agent.db        # SQLite数据库
    ├── chroma_db/              # 向量数据库持久化
    └── knowledge_docs/         # 焊接知识库文档
```

## Agent 意图路由

主控Agent (`supervisor.py`) 根据用户输入的关键词进行意图识别，路由到对应的专业Agent：

| 用户输入示例 | 识别意图 | 路由Agent | 数据来源 |
|-------------|---------|-----------|---------|
| 当前焊接电流是多少？ | 设备监控 | 设备监控Agent | WeldingSimulator |
| WO-2026-001做到哪了？ | 生产进度 | 生产进度Agent | SQLite(工单) |
| BOM-2026-001包含什么物料？ | BOM管理 | BOM管理Agent | SQLite(BOM) |
| 焊丝还有多少？ | 库存分析 | 库存分析Agent | SQLite(库存) |
| Q235 10mm怎么焊？ | 工艺知识 | 工艺知识Agent | RAG知识库 |
| 设备温度异常且工单滞后 | 复合意图 | 设备Agent + 生产Agent | 多源聚合 |

### LLM 回答生成流程

```
用户提问 → 意图识别 → Agent执行查询 → 结果聚合 → [DeepSeek LLM] → 自然语言回答
                                                        ↓ (失败)
                                                   [模板回复] → 降级输出
```

主控Agent的 `format_answer()` 函数会调用配置的LLM（默认DeepSeek）将各Agent的结构化查询结果转化为自然语言回答。若LLM调用失败，自动降级为模板格式输出。

## LLM 模型配置详解

### 支持的国产模型

| 模型 | 厂商 | MODEL_NAME | 特点 | 价格参考 |
|------|------|------------|------|---------|
| **DeepSeek-V3** | 深度求索 | `deepseek-chat` | 性价比之王，推荐首选 | ¥1/百万token |
| **DeepSeek-R1** | 深度求索 | `deepseek-reasoner` | 推理能力强 | ¥4/百万token |
| **Qwen-Plus** | 阿里云 | `qwen-plus` | 中文能力顶级 | ¥0.8/百万token |
| **GLM-4-Flash** | 智谱AI | `glm-4-flash` | **免费额度** | 免费 |
| **Doubao-Pro** | 字节跳动 | `doubao-pro-32k` | 长上下文 | ¥0.5/百万token |

### 本地部署方案（离线环境）

使用 Ollama 运行本地模型：

```bash
# 安装 Ollama
winget install Ollama.Ollama

# 下载中文模型
ollama pull qwen2.5:7b      # 7B参数，~4GB显存
ollama pull qwen2.5:14b     # 14B参数，~8GB显存（推荐）

# .env 配置
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
MODEL_NAME=qwen2.5:14b
```

### Embedding 模型

RAG向量检索需要Embedding模型，系统采用**三级降级策略**：

| 优先级 | 方案 | 适用场景 | 语义能力 |
|--------|------|----------|----------|
| **L1** | OpenAI API (text-embedding-3-small) | 云端部署 | ⭐⭐⭐⭐⭐ |
| **L2** | 本地 BGE 中文模型 (bge-small-zh-v1.5) | 内网/离线（推荐） | ⭐⭐⭐⭐ |
| **L3** | MD5 哈希 Fallback | 仅测试环境 | ⭐（无语义） |

可通过环境变量自定义：

```bash
LOCAL_EMBEDDING_MODEL=BAAI/bge-base-zh-v1.5   # 更大模型，质量更好
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-12-v2  # 重排序模型
```

## RAG 检索增强

### 混合检索架构

```
用户查询 → ┌─────────────┬─────────────┐
           │  向量检索    │  BM25检索   │
           │ (Chroma)    │ (关键词)    │
           └──────┬──────┴──────┬──────┘
                  │  RRF融合    │
                  ▼             ▼
           ┌──────────────────────┐
           │  Cross-Encoder重排序 │  (可选)
           └──────────┬───────────┘
                      ▼
                最终Top-K结果
```

### Cross-Encoder 重排序（可选）

在 RRF 融合后增加精排层，提升检索精度 10-15%：

```python
from src.agents.rag.retriever import hybrid_search, hybrid_search_debug

# 启用重排序
results = hybrid_search("焊接气孔缺陷", top_k=5, use_rerank=True)

# 调试模式查看详细分数
debug_info = hybrid_search_debug("焊接参数", use_rerank=True)
# debug_info["reranked_results"] 包含 _ce_score 分数
```

### 推荐Embedding模型选择

| 场景 | 模型 | 大小 | 推理速度 |
|------|------|------|----------|
| **资源受限** | BAAI/bge-small-zh-v1.5 | ~100MB | <10ms/doc |
| **质量优先** | BAAI/bge-base-zh-v1.5 | ~400MB | ~30ms/doc |
| **极致精度** | BAAI/bge-large-zh-v1.5 | ~1.2GB | ~80ms/doc |

## API 接口总览

启动服务后访问 http://localhost:8000/docs 查看完整交互式文档。

### 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | AI对话（支持SSE流式响应） |
| GET | `/api/devices` | 设备列表与状态 |
| GET | `/api/devices/{device_id}/metrics` | 设备实时参数 |
| GET | `/api/production` | 生产统计概览 |
| GET | `/api/production/{wo_id}` | 工单详情与工序 |
| GET | `/api/bom/{bom_id}` | BOM详情与物料清单 |
| GET | `/api/inventory` | 库存统计分析 |
| POST | `/api/knowledge/upload` | 上传知识库文档 |
| POST | `/api/knowledge/search` | 知识库检索测试 |
| GET | `/api/sessions/{session_id}/trace` | 查询执行轨迹 |
| WS | `/ws/devices` | WebSocket设备数据推送 |

## 测试

```bash
# 运行全部测试
uv run pytest tests/

# 运行指定测试文件
uv run pytest tests/test_rag_retriever.py -v

# 查看测试覆盖率
uv run pytest tests/ --cov=src --cov-report=term-missing
```

## 开发指南

### 添加新的依赖

```bash
uv add <包名>       # uv.lock 会自动更新
uv remove <包名>    # 移除依赖
```

### 调试模式

设置 `DEBUG=true`（默认），Uvicorn 会启用热重载：

```bash
uv run python -m uvicorn src.api.server:app --reload --port 8000
```

### LangSmith 追踪（可选）

用于可视化和调试Agent执行链路：

```bash
# .env 中启用
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=welding-agent-platform
```

然后访问 https://smith.langchain.com/ 查看追踪数据。

## 常见问题

### Q: LLM调用失败怎么办？

A: 检查 `.env` 中的 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL` 是否正确。系统会自动降级为模板回复，不会阻塞服务。

### Q: RAG知识库初始化失败？

A: 首次运行会自动下载Embedding模型（约100MB）。如果网络不通，系统会降级为MD5哈希模式（无语义检索）。

### Q: 如何切换LLM模型？

A: 只需修改 `.env` 中的三个变量：`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`MODEL_NAME`，重启服务即可。代码无需改动。

---

> **版本**: v0.1.0 | **Python**: >=3.10 | **License**: Internal Use
