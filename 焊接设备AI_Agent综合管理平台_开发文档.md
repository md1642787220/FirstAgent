# 焊接设备AI Agent综合管理平台 —— 完整项目开发文档


## 一、项目概述

### 1.1 项目背景

焊接是制造业的核心工艺环节，长期以来面临三大痛点：

| 痛点领域 | 具体问题 |
|----------|----------|
| **工艺依赖经验** | 参数调优靠"手感"，优秀焊工培养周期长，工艺知识难以沉淀 |
| **质量追溯困难** | 焊接过程数据散落在不同系统，异常发生时已产生批量不良 |
| **生产协同不畅** | 生产进度靠电话追问，BOM变更后采购信息不同步，库存信息滞后影响排产 |

当前行业趋势是"AI+工业"的深度融合。博清科技推出国内首个工业焊接垂类大模型"际銮"，树根科技"焊接Agent"实现工艺自适应进化，海尔智家通过智能体平台实现"查订单、看库存"一站式入口，首钢股份《热轧生产AI智能体解决方案》入选行业标杆。

本项目旨在为公司构建一个**焊接设备AI Agent综合管理平台**，以桌面客户端为载体，将大模型推理能力与**设备实时监控、生产进度跟踪、BOM智能管理、库存动态分析**深度融合，打造覆盖"设备-工艺-物料-进度"全链路的智能决策中枢。

### 1.2 项目目标

| 目标 | 描述 | 量化指标 |
|------|------|----------|
| **设备实时监控** | 采集并展示焊接设备关键参数，实现异常告警 | 响应延迟<500ms |
| **智能工艺诊断** | Agent自动分析参数异常，给出优化建议 | 诊断准确率>85% |
| **生产进度管理** | 跟踪工单工序状态，自动识别滞后风险 | 进度透明度100% |
| **BOM智能管理** | BOM自然语言查询、版本对比、变更影响分析 | 查询响应<2s |
| **库存动态分析** | 实时查询库存水位，自动识别呆滞料风险 | 预警准确率>90% |
| **工艺知识问答** | 基于焊接知识库回答工艺参数、缺陷处理等问题 | 检索命中率>80% |
| **轨迹可视化** | 展示Agent"思考-行动"全链路 | 步骤100%可追溯 |

### 1.3 项目范围

- **包含**：Qt桌面客户端、Agent后端服务（FastAPI）、RAG知识库、设备数据模拟/采集接口、生产进度模拟数据、BOM与库存模拟数据
- **不包含**：真实ERP/MES系统的数据库直连、硬件改造、PLC底层驱动

### 1.4 项目定位

本项目属于 **"RAG + 结构化数据查询 + 多工具调用"** 的混合架构企业级智能体：

- **RAG部分**：焊接工艺知识（非结构化文档）的向量检索与生成
- **结构化部分**：生产进度、BOM层级、库存数量的SQL/API查询
- **整体定位**：基于大模型的企业级综合智能体，解决真实业务中**非结构化知识与结构化数据并存**的痛点


## 二、系统架构（自顶向下）

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              用户层 (UI Layer)                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                    Qt桌面客户端 (PySide6 / Qt6)                          │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │  │
│  │  │实时监控  │ │生产进度  │ │BOM管理  │ │库存看板  │ │对话交互      │ │  │
│  │  │仪表盘    │ │看板      │ │面板      │ │          │ │窗口          │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │  │
│  │  ┌──────────────────────────────────────────────────────────────────────┐ │  │
│  │  │              Agent执行轨迹追踪面板（全模块统一）                    │ │  │
│  │  └──────────────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │ HTTP/WebSocket                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                             服务层 (Service Layer)                             │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │              Agent后端服务 (Python / FastAPI / LangGraph)                │  │
│  │  ┌──────────────────────────────────────────────────────────────────────┐ │  │
│  │  │                      主控Agent (Supervisor)                         │ │  │
│  │  │         意图识别 → 任务路由 → 结果聚合                              │ │  │
│  │  └──────────┬──────────┬──────────┬──────────┬────────────────────────┘ │  │
│  │             │          │          │          │                          │  │
│  │  ┌──────────┴──┐ ┌────┴────┐ ┌───┴────┐ ┌──┴────────┐ ┌─────────────┐ │  │
│  │  │ 设备监控Agent│ │生产进度 │ │BOM管理 │ │库存分析   │ │工艺知识     │ │  │
│  │  │ (LangChain) │ │Agent    │ │Agent   │ │Agent      │ │Agent (RAG)  │ │  │
│  │  └─────────────┘ └─────────┘ └────────┘ └───────────┘ └─────────────┘ │  │
│  │  ┌──────────────────────────────────────────────────────────────────────┐ │  │
│  │  │                    工具注册中心 (Tool Registry)                     │ │  │
│  │  │  查设备参数 | 查工单进度 | 查BOM | 查库存 | 生成报告 | 缺陷诊断   │ │  │
│  │  └──────────────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                             数据层 (Data Layer)                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │  向量数据库   │ │  关系数据库  │ │  时序数据库  │ │  多源文档    │        │
│  │  (Chroma)    │ │  (SQLite)   │ │  (SQLite/   │ │  PDF/Word/   │        │
│  │              │ │  工单/BOM/   │ │   InfluxDB) │ │  Excel/PPTX  │        │
│  │              │ │   库存       │ │  设备参数   │ │  CSV/JSON/   │        │
│  │              │ │              │ │              │ │  DB/API/OCR  │        │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**技术架构图（Mermaid）：**

```mermaid
graph TB
    subgraph UI["🖥️ 用户层 (UI Layer)"]
        direction LR
        A1["实时监控仪表盘"]
        A2["生产进度看板"]
        A3["BOM管理面板"]
        A4["库存分析看板"]
        A5["对话交互窗口"]
        A6["轨迹追踪面板"]
    end

    subgraph Service["⚙️ 服务层 (Service Layer) - FastAPI + LangGraph"]
        B0["主控Agent<br/>Supervisor<br/>意图识别 → 路由 → 聚合"]
        B1["设备监控<br/>Agent"]
        B2["生产进度<br/>Agent"]
        B3["BOM管理<br/>Agent"]
        B4["库存分析<br/>Agent"]
        B5["工艺知识<br/>Agent<br/>(RAG)"]
        B0 --> B1
        B0 --> B2
        B0 --> B3
        B0 --> B4
        B0 --> B5
    end

    subgraph Data["💾 数据层 (Data Layer)"]
        direction LR
        C1[("Chroma<br/>向量数据库")]
        C2[("SQLite<br/>关系数据库<br/>工单/BOM/库存")]
        C3[("时序数据<br/>设备参数")]
        C4[("文档存储<br/>PDF/Word/Excel<br/>工艺手册")]
    end

    UI -->|"HTTP/REST + WebSocket"| Service
    Service -->|"SQLAlchemy + ChromaDB"| Data
    B1 --> C3
    B2 --> C2
    B3 --> C1
    B3 --> C2
    B4 --> C2
    B5 --> C1
    B5 --> C4

    classDef uiStyle fill:#1a1a2e,stroke:#e94560,color:#eee
    classDef svcStyle fill:#16213e,stroke:#0f3460,color:#eee
    classDef dataStyle fill:#0f3460,stroke:#533483,color:#eee
    class A1,A2,A3,A4,A5,A6 uiStyle
    class B0,B1,B2,B3,B4,B5 svcStyle
    class C1,C2,C3,C4 dataStyle
```

### 2.2 多Agent协作架构

本项目采用 **"1个主控Agent + 5个专业Agent"** 的多智能体协作架构：

| Agent | 职责 | 技术实现 |
|-------|------|----------|
| **主控Agent (Supervisor)** | 识别用户意图，路由到对应专业Agent，聚合结果返回 | LangGraph + 意图分类 |
| **设备监控Agent** | 查询设备实时参数、历史数据、异常诊断 | LangChain + Function Calling |
| **生产进度Agent** | 查询工单状态、工序进度、识别滞后风险 | LangChain + SQL查询 |
| **BOM管理Agent** | BOM查询、版本对比、变更影响分析 | LangChain + RAG + 结构化查询 |
| **库存分析Agent** | 库存查询、呆滞料预警、齐套分析 | LangChain + SQL查询 + 规则引擎 |
| **工艺知识Agent** | 焊接工艺参数推荐、缺陷诊断、标准查询 | RAG (Chroma + Embedding) |

### 2.3 数据流

1. **设备数据流**：焊接设备（或模拟器）→ 数据采集接口 → 设备监控Agent → Qt客户端实时展示
2. **生产数据流**：工单/工序数据（模拟或MES接口）→ 生产进度Agent → Qt客户端看板展示
3. **BOM数据流**：BOM数据（Excel/数据库）→ BOM管理Agent（向量化+结构化）→ Qt客户端查询展示
4. **库存数据流**：库存数据（模拟或ERP接口）→ 库存分析Agent → Qt客户端看板展示
5. **对话数据流**：用户提问 → Qt客户端 → 主控Agent（路由）→ 专业Agent → 流式返回
6. **轨迹数据流**：每个Agent的每一步执行 → 结构化日志 → Qt客户端轨迹面板实时更新

**数据流架构图（Mermaid）：**

```mermaid
graph TB
    subgraph Source["📥 数据源"]
        direction LR
        S1["焊接设备<br/>（模拟器）"]
        S2["MES/ERP<br/>（模拟接口）"]
        S3["BOM文档<br/>（Excel/DB）"]
        S4["库存系统<br/>（模拟接口）"]
        S5["工艺手册<br/>（PDF/Word）"]
    end

    subgraph Agent["🤖 Agent处理层"]
        direction LR
        AG1["设备监控Agent"]
        AG2["生产进度Agent"]
        AG3["BOM管理Agent"]
        AG4["库存分析Agent"]
        AG5["工艺知识Agent<br/>(RAG)"]
    end

    subgraph UI["🖥️ 客户端展示"]
        direction LR
        U1["实时监控<br/>仪表盘"]
        U2["生产进度<br/>看板"]
        U3["BOM管理<br/>面板"]
        U4["库存分析<br/>看板"]
        U5["轨迹追踪<br/>面板"]
    end

    User["👤 用户提问"] -->|"对话SSE"| Supervisor["主控Agent<br/>Supervisor"]
    Supervisor -->|"意图路由"| Agent
    S1 -->|"实时采集"| AG1
    S2 -->|"工单同步"| AG2
    S3 -->|"BOM导入"| AG3
    S4 -->|"库存快照"| AG4
    S5 -->|"文档加载"| AG5
    AG1 -->|"设备指标"| U1
    AG2 -->|"工单进度"| U2
    AG3 -->|"BOM树+齐套"| U3
    AG4 -->|"库存预警"| U4
    Supervisor -->|"思维轨迹"| U5
    AG1 -.->|"执行日志"| U5
    AG2 -.->|"执行日志"| U5
    AG3 -.->|"执行日志"| U5
    AG4 -.->|"执行日志"| U5
    AG5 -.->|"执行日志"| U5

    classDef srcStyle fill:#1a1a2e,stroke:#e94560,color:#eee
    classDef agtStyle fill:#16213e,stroke:#0f3460,color:#eee
    classDef uiStyle fill:#0f3460,stroke:#533483,color:#eee
    class S1,S2,S3,S4,S5 srcStyle
    class AG1,AG2,AG3,AG4,AG5,Supervisor agtStyle
    class U1,U2,U3,U4,U5,User uiStyle
```

### 2.4 多Agent协作时序图

以下时序图展示用户发起一次复杂查询时，主控Agent与5个专业Agent之间的完整协作过程：

```mermaid
sequenceDiagram
    actor User as 👤 用户
    participant Qt as 🖥️ Qt客户端
    participant Sup as 🧠 主控Agent<br/>Supervisor
    participant Dev as 🔧 设备监控Agent
    participant Prod as 📊 生产进度Agent
    participant BOM as 📋 BOM管理Agent
    participant Inv as 📦 库存分析Agent
    participant KNW as 📚 工艺知识Agent
    participant Tool as 🛠️ 工具层
    participant DB as 💾 数据库

    User->>Qt: "WO-001焊接工序滞后，焊丝库存够吗？"
    Qt->>Sup: POST /chat/sync (流式请求)

    Note over Sup: 意图分类 + 多意图识别
    Sup->>Sup: 识别意图: 生产+库存 [置信度0.95]

    par 并行路由
        Sup->>Prod: 路由: 查询工单WO-001
        Prod->>Tool: get_work_order("WO-001")
        Tool->>DB: SELECT * FROM work_orders...
        DB-->>Tool: 工单数据
        Tool-->>Prod: 返回结果
        Prod->>Tool: identify_delays()
        Tool->>DB: 滞后分析查询
        DB-->>Tool: 滞后数据
        Tool-->>Prod: 滞后报告
        Prod-->>Sup: 生产分析结果
    and
        Sup->>Inv: 路由: 查询焊丝库存
        Inv->>Tool: check_shortage()
        Tool->>DB: SELECT * FROM inventory...
        DB-->>Tool: 库存数据
        Tool-->>Inv: 短缺清单
        Inv->>Tool: analyze_stock("焊丝")
        Tool-->>Inv: 库存分析
        Inv-->>Sup: 库存分析结果
    end

    Sup->>Sup: 结果聚合 + LLM生成总结
    Sup-->>Qt: SSE流式返回回答
    Qt-->>User: 显示完整回答+思维轨迹
```

### 2.5 意图路由决策流程

主控Agent根据用户输入执行意图识别与路由的全流程：

```mermaid
flowchart TD
    A["👤 用户输入自然语言"] --> B{"🔍 关键词匹配<br/>+ 语义分析"}
    
    B -->|"关键词: 设备/电流/电压/异常"| C["路由: 设备监控Agent"]
    B -->|"关键词: 工单/工序/进度/滞后"| D["路由: 生产进度Agent"]
    B -->|"关键词: BOM/物料清单/版本"| E["路由: BOM管理Agent"]
    B -->|"关键词: 库存/短缺/呆滞/超储"| F["路由: 库存分析Agent"]
    B -->|"关键词: 焊接参数/缺陷/工艺"| G["路由: 工艺知识Agent (RAG)"]
    B -->|"多意图/复杂查询"| H{"🔀 多路由决策"}
    
    H -->|"生产+库存"| I["并行路由<br/>Production + Inventory"]
    H -->|"BOM+库存"| J["并行路由<br/>BOM + Inventory"]
    H -->|"设备+工艺"| K["并行路由<br/>Device + Knowledge"]
    H -->|"通用/闲聊"| L["直接回复<br/>无需Agent"]

    C --> M{"📊 结果聚合"}
    D --> M
    E --> M
    F --> M
    G --> M
    I --> M
    J --> M
    K --> M
    L --> M

    M --> N["✍️ LLM生成最终回答"]
    N --> O["📝 记录执行轨迹"]
    O --> P["📤 返回用户 (SSE流式)"]

    classDef inputStyle fill:#1a1a2e,stroke:#e94560,color:#eee
    classDef decStyle fill:#16213e,stroke:#0f3460,color:#eee
    classDef routeStyle fill:#0f3460,stroke:#533483,color:#eee
    classDef outStyle fill:#1a1a2e,stroke:#00b4d8,color:#eee
    class A inputStyle
    class B,H decStyle
    class C,D,E,F,G,I,J,K,L routeStyle
    class M,N,O,P outStyle
```


## 三、技术栈

### 3.1 Qt桌面客户端

| 组件 | 选型 | 说明 |
|------|------|------|
| **框架** | PySide6 (Qt6 for Python) | 跨平台、工业级稳定性 |
| **UI构建** | Qt Widgets + QML混合 | 仪表盘用QML（流畅动画），主界面用Widgets |
| **图表** | Qt Charts | 实时曲线图、仪表盘、甘特图 |
| **表格** | Qt TableView + 自定义Delegate | BOM展示、库存列表 |
| **网络** | Qt Network | HTTP客户端 + WebSocket |
| **JSON解析** | Qt Core (QJsonDocument) | 与后端API通信 |

### 3.2 Agent后端服务

| 组件 | 选型 | 说明 |
|------|------|------|
| **语言** | Python 3.10+ | |
| **Web框架** | FastAPI | 高性能异步API服务 |
| **Agent框架** | LangChain 1.0+ + LangGraph 1.0+ | 核心Agent编排 + 多Agent协作 |
| **LLM接口** | langchain-openai (OpenAI兼容协议) | 开发阶段直接调用API，部署时切换内网模型地址 |
| **Embedding** | text-embedding-3-small / 部署时可切换本地模型 | 文档向量化，通过 API 调用 |
| **向量数据库** | Chroma (本地持久化) | 工艺文档、BOM文档检索 |
| **关系数据库** | SQLite + SQLAlchemy | 工单、BOM结构化数据、库存 |
| **异步任务** | asyncio + uvicorn | |
| **数据验证** | Pydantic v2 | |

### 3.3 数据存储

| 数据 | 方案 | 说明 |
|------|------|------|
| **工艺知识向量** | Chroma (persist_directory) | 焊接工艺手册、操作规程、缺陷库 |
| **BOM文档向量** | Chroma | BOM说明文档、变更记录 |
| **工单/进度** | SQLite | 生产工单、工序状态、完成时间 |
| **BOM结构化数据** | SQLite | 物料清单、层级关系、用量 |
| **库存数据** | SQLite | 物料库存、库位、安全库存 |
| **设备时序数据** | SQLite / 内存缓存 | 近期设备参数 |
| **Agent执行轨迹** | 结构化JSON日志 | 每一步的思考-行动-观察 |


## 四、Python依赖包完整清单

### 4.1 按功能分类

| 类别 | 包名 | 版本建议 | 用途说明 |
|------|------|----------|----------|
| **核心框架** | `langchain` | >=1.0,<2.0 | LangChain核心库，Agent/Chain/Retriever |
| | `langchain-core` | >=1.0,<2.0 | 核心类型与接口定义 |
| | `langgraph` | >=1.0,<2.0 | 多Agent编排框架，状态图工作流 |
| | `langsmith` | >=0.3.0 | 运行追踪、评估与可观测性 |
| **模型接口** | `langchain-openai` | >=0.1.17 | OpenAI兼容接口（外网开发直连API，部署切换内网地址） |
| | `langchain-community` | >=0.2.10 | 社区集成包 |
| **向量检索** | `chromadb` | 最新稳定版 | 向量数据库，存储知识文档向量 |
| | `faiss-cpu` | 最新稳定版 | Facebook向量检索库 |
| | `rank_bm25` | 最新稳定版 | BM25关键词检索，混合检索 |
| | `tiktoken` | 最新稳定版 | Token计数器 |
| **Web服务** | `fastapi` | 最新稳定版 | Web框架，REST API + SSE流式输出 |
| | `uvicorn` | >=0.26.0 | ASGI服务器 |
| | `sse-starlette` | >=2.1.3,<3.4.0 | Server-Sent Events支持 |
| | `python-multipart` | 最新稳定版 | 文件上传处理 |
| **数据处理** | `sqlalchemy` | 最新稳定版 | ORM框架，操作SQLite |
| | `pandas` | 最新稳定版 | 数据处理与分析 |
| | `numpy` | 最新稳定版 | 数值计算 |
| **文档加载** | `pypdf` | 最新稳定版 | PDF文档加载 |
| | `pymupdf` | 最新稳定版 | 增强PDF处理 |
| | `python-docx` | 最新稳定版 | Word文档加载 |
| | `openpyxl` | 最新稳定版 | Excel文档加载 |
| **Qt界面** | `PySide6` | >=6.0 | Qt for Python，桌面客户端UI框架 |
| | `pyside6-essentials` | >=6.0 | PySide6基本Qt模块（实际安装此包） |
| **工具库** | `python-dotenv` | >=1.0.0 | 环境变量管理 |
| | `requests` | 最新稳定版 | HTTP请求 |
| | `httpx` | >=0.25.0 | 异步HTTP客户端 |
| | `tenacity` | >=8.0.0 | 重试机制 |
| | `orjson` | >=3.9.7 | 高性能JSON序列化 |
| | `pydantic` | >=2.0 | 数据验证 |

### 4.2 完整 requirements.txt

```txt
# ==================== 核心框架 ====================
langchain>=1.0,<2.0
langchain-core>=1.0,<2.0
langgraph>=1.0,<2.0
langsmith>=0.3.0

# ==================== 模型接口 ====================
langchain-openai>=0.1.17
langchain-community>=0.2.10

# ==================== 向量数据库与检索 ====================
chromadb
faiss-cpu
rank_bm25
tiktoken

# ==================== Web服务 ====================
fastapi
uvicorn>=0.26.0
sse-starlette>=2.1.3,<3.4.0
python-multipart

# ==================== 数据处理 ====================
sqlalchemy
pandas
numpy

# ==================== 文档加载 ====================
pypdf
pymupdf
python-docx
openpyxl

# ==================== Qt界面 ====================
PySide6>=6.0
# 注意：从6.3.0开始，实际需要安装 pyside6-essentials
# 但 pip install PySide6 会自动依赖它

# ==================== 工具库 ====================
python-dotenv>=1.0.0
requests
httpx>=0.25.0
tenacity>=8.0.0
orjson>=3.9.7
pydantic>=2.0
```

### 4.3 安装指南

> **开发模式（外网环境，推荐）**：直接 `pip install -r requirements.txt` 即可，所有依赖均可从 PyPI 在线拉取。LLM 和 Embedding 使用 API Key 直连调用，无需本地部署模型。

> **部署模式（内网环境）**：开发完成后部署到内网服务器时，按以下步骤准备离线包。

**Step 1：在外网开发机准备离线包**

```bash
# 创建下载目录
mkdir offline_packages

# 下载所有包及其依赖（适配当前Python环境）
pip download -r requirements.txt -d ./offline_packages

# 如需指定Python版本和操作系统（例如Windows + Python 3.10）
pip download -r requirements.txt -d ./offline_packages \
  --platform win_amd64 \
  --python-version 3.10 \
  --only-binary=:all:
```

**Step 2：拷贝到内网服务器安装**

```bash
# 将 offline_packages 文件夹通过U盘/内网共享拷贝到内网机器
# 修改 .env 中的 OPENAI_BASE_URL 指向内网模型网关
# 在内网机器上执行：
pip install --no-index --find-links=./offline_packages -r requirements.txt
```

**⚠️ PySide6特别提醒**：
- 从PySide6 6.3.0开始，`pyside6`主包几乎为空，实际需要安装 `pyside6-essentials`
- 下载时请确认 `.whl` 文件的Python版本（cp37/cp38/cp39/cp310/cp311）和操作系统架构（win_amd64）
- 如无法自动下载，可手动从 https://download.qt.io/official_releases/QtForPython/ 下载对应 `.whl` 文件

**⚠️ 版本建议**：
- Python版本：**3.10+**
- LangChain：建议 **1.0+**（LTS长期支持版本）
- 生产环境建议锁定具体版本号


## 五、核心功能模块详细设计

### 5.1 模块一：实时监控仪表盘

**功能描述**：以工业仪表盘形式，实时展示焊接设备关键参数。

**焊接设备核心参数**（行业标准参考）：

| 参数类别 | 参数名称 | 单位 | 正常范围 |
|----------|----------|------|----------|
| 电参数 | 焊接电流 | A | 100-300 |
| | 焊接电压 | V | 20-35 |
| 运动参数 | 焊接速度 | mm/min | 300-800 |
| | 送丝速度 | m/min | 3-15 |
| 气体参数 | 气体流量 | L/min | 15-25 |
| 状态参数 | 设备温度 | ℃ | <85 |
| | 设备振动 | m/s² | <0.5 |

**UI设计示意**：

```
┌─────────────────────────────────────────────────────────────┐
│  🔥 焊接设备监控面板                   2026-07-29 14:32:05 │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  电流     │  │  电压     │  │  焊速    │  │  气体    │ │
│  │  ╭──╮    │  │  ╭──╮    │  │  ╭──╮   │  │  ╭──╮   │ │
│  │  │245│ A  │  │  │28.5│ V │  │  │520│   │  │  │22│ L │ │
│  │  ╰──╯    │  │  ╰──╯    │  │  ╰──╯   │  │  ╰──╯   │ │
│  │  ██████░  │  │  ██████░  │  │  █████░  │  │  █████░ │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  实时曲线 (最近60秒)                                  │ │
│  │  电流 ── 电压 ── 焊速 ──                             │ │
│  └────────────────────────────────────────────────────────┘ │
│  ⚠️ 告警: 电流波动异常 (+/- 15A)  建议检查送丝机构        │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 模块二：生产进度管理看板

**核心数据模型**：

```sql
-- 工单表
CREATE TABLE work_orders (
    id TEXT PRIMARY KEY,
    product_name TEXT,
    product_code TEXT,
    quantity INTEGER,
    priority TEXT,                      -- 紧急/高/中/低
    status TEXT,                        -- 待排产/生产中/已完成/已暂停
    planned_start DATE,
    planned_end DATE,
    actual_start DATE,
    actual_end DATE,
    customer TEXT,
    created_at TIMESTAMP
);

-- 工序进度表
CREATE TABLE process_steps (
    id INTEGER PRIMARY KEY,
    work_order_id TEXT,
    step_name TEXT,                     -- 下料/焊接/打磨/检验/包装
    step_order INTEGER,
    status TEXT,                        -- 未开始/进行中/已完成/阻塞
    planned_duration INTEGER,           -- 计划时长(小时)
    actual_duration INTEGER,            -- 实际时长(小时)
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    device_id TEXT,
    operator TEXT,
    notes TEXT,
    FOREIGN KEY (work_order_id) REFERENCES work_orders(id)
);
```

**UI设计示意**：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📋 生产进度看板                         2026-07-29 14:32:05              │
├─────────────────────────────────────────────────────────────────────────────┤
│  统计: 在制工单 12 | 今日完成 3 | 滞后 2 ⚠️ | 紧急 1 🔴                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  WO-2026-07-001  |  焊接底座  |  200件  |  🔴紧急  |  进度 65%      │ │
│  │  ████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ │
│  │  下料 ✅  |  焊接 ⏳ 65%  |  打磨 ⏸️  |  检验 ⬜  |  包装 ⬜        │ │
│  │  计划: 07-20 ~ 07-30  |  当前: 07-29  |  状态: 进行中  |  滞后 2天 ⚠️│ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  🤖 Agent洞察: 工单WO-2026-07-001焊接工序进度滞后，建议增加夜班或调配    │
│     焊接设备支援。阻塞原因: 焊丝库存不足，已自动生成采购建议              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 模块三：BOM智能管理

**功能描述**：支持BOM（物料清单）的自然语言查询、版本对比、变更影响分析。

**核心数据模型**：

```sql
-- BOM表头
CREATE TABLE boms (
    id TEXT PRIMARY KEY,
    product_code TEXT,
    product_name TEXT,
    version TEXT,
    status TEXT,                        -- 草稿/已发布/已废弃
    effective_date DATE,
    created_by TEXT,
    created_at TIMESTAMP,
    description TEXT
);

-- BOM明细（父子层级）
CREATE TABLE bom_items (
    id INTEGER PRIMARY KEY,
    bom_id TEXT,
    parent_item_id INTEGER,             -- NULL表示顶层
    material_code TEXT,
    material_name TEXT,
    specification TEXT,
    quantity REAL,
    unit TEXT,                          -- 件/米/公斤
    material_type TEXT,                 -- 原材料/外购件/自制件/标准件
    source_supplier TEXT,
    cost REAL,
    lead_time INTEGER,                  -- 采购提前期(天)
    remark TEXT
);
```

**典型对话场景**：

| 用户提问 | Agent行为 |
|----------|-----------|
| "BOM-2026-001包含哪些物料？" | 查询BOM明细，树形结构展示全部层级 |
| "BOM V1.0和V1.1有什么区别？" | 对比两个版本，高亮新增/删除/变更物料 |
| "这个BOM的物料齐套吗？" | 检查所有物料当前库存，标记缺货物料 |

**BOM混合存储架构图：**

BOM管理Agent采用 **结构化查询(SQLite) + 向量检索(Chroma)** 双路径架构，兼顾精确字段查询和语义模糊匹配：

```mermaid
graph LR
    subgraph Input["📥 BOM数据导入"]
        direction TB
        I1["Excel/CSV<br/>BOM文件"]
        I2["数据库<br/>BOM表同步"]
    end

    subgraph Split["🔀 双路径存储"]
        S1["结构化路径<br/>SQLite"]
        S2["向量化路径<br/>Chroma"]
    end

    subgraph Struct["📊 结构化存储 (SQLite)"]
        direction TB
        ST1[("boms 表<br/>BOM头信息")]
        ST2[("bom_items 表<br/>BOM物料明细")]
        ST3[("版本对比<br/>V1.0 ↔ V1.1")]
        ST1 --> ST2
        ST1 --> ST3
    end

    subgraph Vector["🔍 向量存储 (Chroma)"]
        direction TB
        V1["文档分块<br/>LangChain Splitter"]
        V2["Embedding<br/>向量化编码"]
        V3[("Chroma<br/>向量索引")]
        V1 --> V2 --> V3
    end

    subgraph Query["🔎 查询层"]
        direction TB
        Q1["精确字段查询<br/>物料编码/版本/层级"]
        Q2["语义模糊搜索<br/>相似BOM/替代物料"]
        Q3["混合检索<br/>BM25 + 向量"]
    end

    subgraph Analysis["📋 分析输出"]
        direction TB
        A1["树形BOM结构"]
        A2["版本Diff对比"]
        A3["齐套性分析"]
    end

    Input --> Split
    Split --> Struct
    Split --> Vector
    Struct --> Q1
    Vector --> Q2
    Q1 --> Q3
    Q2 --> Q3
    Q3 --> Analysis

    classDef inStyle fill:#1a1a2e,stroke:#e94560,color:#eee
    classDef splitStyle fill:#16213e,stroke:#0f3460,color:#eee
    classDef storeStyle fill:#0f3460,stroke:#533483,color:#eee
    classDef queryStyle fill:#1a1a2e,stroke:#00b4d8,color:#eee
    classDef outStyle fill:#16213e,stroke:#e94560,color:#eee
    class I1,I2 inStyle
    class S1,S2 splitStyle
    class ST1,ST2,ST3,V1,V2,V3 storeStyle
    class Q1,Q2,Q3 queryStyle
    class A1,A2,A3 outStyle
```

### 5.4 模块四：库存动态分析看板

**核心数据模型**：

```sql
CREATE TABLE inventory (
    id INTEGER PRIMARY KEY,
    material_code TEXT UNIQUE,
    material_name TEXT,
    category TEXT,                      -- 原材料/半成品/成品/辅料
    warehouse TEXT,
    location TEXT,
    quantity REAL,
    unit TEXT,
    safety_stock REAL,
    max_stock REAL,
    reorder_point REAL,
    last_inbound DATE,
    last_outbound DATE,
    turnover_days INTEGER,
    status TEXT,                        -- 正常/短缺/呆滞/超储
    supplier TEXT,
    unit_cost REAL
);
```

**UI设计示意**：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📊 库存分析看板                         2026-07-29 14:32:05              │
├─────────────────────────────────────────────────────────────────────────────┤
│  总物料: 1,234  |  短缺: 23 🔴  |  呆滞: 45 🟡  |  超储: 12 🟠          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ⚠️ 短缺预警 (23项)                                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 物料编码  │ 物料名称    │ 当前库存 │ 安全库存 │ 缺口  │ 状态       │ │
│  │ MAT-1001  │ 接触器      │ 5        │ 20       │ 15    │ 🔴 紧急    │ │
│  │ MAT-1002  │ 焊丝 1.2mm │ 50kg     │ 100kg    │ 50kg  │ 🟠 警告    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  🤖 Agent建议: 接触器MAT-1001已连续3周低于安全库存，建议立即采购200件    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.5 模块五：Agent对话交互

**意图路由设计**：

| 用户输入示例 | 意图 | 路由目标 |
|-------------|------|----------|
| "当前焊接电流是多少？" | 设备查询 | 设备监控Agent |
| "WO-001现在做到哪了？" | 进度查询 | 生产进度Agent |
| "BOM-001包含什么物料？" | BOM查询 | BOM管理Agent |
| "焊丝还有多少？" | 库存查询 | 库存分析Agent |
| "Q235 10mm怎么焊？" | 工艺咨询 | 工艺知识Agent |
| "WO-001为什么滞后了？" | 进度诊断 | 生产进度Agent + 设备监控Agent |

### 5.6 模块六：Agent执行轨迹追踪面板

**核心功能**：实时展示Agent每一步"思考-行动-观察"过程，让AI决策完全透明。

**轨迹数据结构**：

```json
{
  "session_id": "sess_001",
  "step": 3,
  "timestamp": "2026-07-29T14:30:25Z",
  "agent": "生产进度Agent",
  "phase": "action",
  "content": {
    "thought": "用户询问工单WO-001的进度，需要查询数据库",
    "action": "query_database",
    "action_input": {"sql": "SELECT * FROM work_orders WHERE id='WO-001'"},
    "observation": "工单进度65%，当前工序为焊接",
    "next_thought": "进一步分析是否滞后"
  }
}
```

**轨迹面板UI示意**：

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  🔍 Agent执行轨迹                    会话: sess_001                          │
├────────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │  🤖 Step 1 (14:30:22.103)  主控Agent - 意图识别                        │ │
│  │     用户输入: "WO-001现在做到哪了？生产进度怎么样？"                     │ │
│  │     识别意图: 生产进度查询 [置信度: 0.96]                               │ │
│  │     路由目标: 生产进度Agent                                             │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │  📋 Step 2 (14:30:22.456)  生产进度Agent - 查询工单                    │ │
│  │     Query: SELECT * FROM work_orders WHERE id = 'WO-001'               │ │
│  │     查询结果: 工单WO-001，进度65%，当前工序: 焊接                      │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │  📋 Step 3 (14:30:22.891)  生产进度Agent - 分析滞后原因                │ │
│  │     诊断: 焊接工序进度滞后2天                                           │ │
│  │     原因: 焊丝库存不足导致停工待料                                     │ │
│  │     建议: 已通知采购部门，预计明日到货                                 │ │
│  ├────────────────────────────────────────────────────────────────────────────┤ │
│  │  💬 Step 4 (14:30:23.567)  主控Agent - 生成回答                        │ │
│  │     调用LLM生成最终回复                                                │ │
│  │     Token消耗: 1,234  |  总耗时: 1.46s                                │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────┘
```

**轨迹日志系统流程图：**

轨迹日志遵循 **"思考→行动→观察"** 的 ReAct 范式，完整记录每个Agent的执行全链路：

```mermaid
flowchart LR
    subgraph Agent["🤖 Agent执行循环"]
        direction LR
        A["用户提问"] --> B["🧠 意图识别<br/>Thought"]
        B --> C["🎯 路由决策<br/>Action"]
        C --> D["🔧 调用工具<br/>Tool Call"]
        D --> E["📊 获取结果<br/>Observation"]
        E --> F{"是否需要<br/>更多信息?"}
        F -->|"是"| B
        F -->|"否"| G["✍️ LLM生成回答"]
    end

    subgraph Trace["📝 轨迹记录 (实时)"]
        direction TB
        T1["Step ID + 时间戳"]
        T2["Agent名称 + 角色"]
        T3["输入/输出/Prompt"]
        T4["Token消耗 + 耗时"]
        T5["工具调用参数/结果"]
        T6["中间推理过程"]
    end

    subgraph Store["💾 轨迹存储"]
        direction TB
        ST1[("内存<br/>最近100条")]
        ST2[("SQLite<br/>trace_log表<br/>持久化归档")]
    end

    subgraph Display["🖥️ 轨迹面板展示"]
        direction TB
        D1["时间线视图<br/>Step 1 → 2 → 3 → 4"]
        D2["展开详情<br/>Prompt全文/查询SQL"]
        D3["统计汇总<br/>耗时/Token/步骤数"]
    end

    G --> Trace
    Trace --> Store
    Store --> Display

    classDef agtStyle fill:#1a1a2e,stroke:#e94560,color:#eee
    classDef traceStyle fill:#16213e,stroke:#0f3460,color:#eee
    classDef storeStyle fill:#0f3460,stroke:#533483,color:#eee
    classDef dispStyle fill:#1a1a2e,stroke:#00b4d8,color:#eee
    class A,B,C,D,E,F,G agtStyle
    class T1,T2,T3,T4,T5,T6 traceStyle
    class ST1,ST2 storeStyle
    class D1,D2,D3 dispStyle
```

### 5.7 RAG知识库构建流程（深度原理说明）

工艺知识Agent的核心依赖是RAG（Retrieval-Augmented Generation，检索增强生成）。以下从**原理层面**和**工程实现层面**两个维度，完整解析数据如何传递给模型、模型如何接收和分析的全链路过程。

#### 5.7.1 核心原理：数据不进入模型训练，而是通过"检索-注入-生成"三阶段

> **关键认知**：知识库中的数据**不会被"喂给"模型进行训练或微调**。模型本身从未"见过"这些私有数据，而是在每次问答时，动态地从向量数据库中检索最相关的片段，注入到Prompt的上下文窗口中，让模型基于这些临时上下文来生成回答。

**五阶段数据流转全景：**

```
用户原始文档              ──→  模型最终回答
     │                              ▲
     ▼                              │
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ ① 加载  │──→│ ② 分块  │──→│ ③ 向量化│──→│ ④ 存储  │──→│ ⑤ 检索  │
│ 文档    │   │ Chunking│   │Embedding│   │ Vector  │   │ + 生成  │
│         │   │         │   │         │   │ Store   │   │         │
└─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
   离线构建阶段（Build-time）               │   在线推理阶段（Query-time）
                                            │        │
                                    ┌───────┘        └────────┐
                                    ▼                          ▼
                            ┌─────────────┐          ┌─────────────┐
                            │ ChromaDB    │          │ Prompt注入   │
                            │ 向量数据库   │          │ + LLM生成    │
                            │ 持久化磁盘   │          │ + 来源引用   │
                            └─────────────┘          └─────────────┘
```

---

#### 5.7.2 阶段一：文档加载（Document Loading）—— 多源异构数据统一入口

数据来源涵盖企业内部多种格式，具体实现详见 [5.9节 多源数据加载器](#59-多源数据加载器企业级设计)：

| 数据源类别 | 支持格式 | 典型场景 |
|-----------|---------|---------|
| **办公文档** | PDF, Word(.docx), Excel(.xlsx), PowerPoint(.pptx), TXT | 工艺手册、操作规范、WPS、参数表 |
| **结构化文本** | CSV, JSON, JSONL, XML, Markdown, HTML | 设备日志导出、标准结构化数据 |
| **关系数据库** | MySQL, Oracle, SQL Server, PostgreSQL, SQLite | MES工单、ERP BOM、QMS检验数据 |
| **REST API** | HTTP/HTTPS接口（JSON响应） | 企业内部数据中台、实时数据源 |
| **内置知识字典** | Python dict 常量 | 焊接工艺参数库、缺陷诊断库（兜底数据） |
| **扩展数据源** | 图片OCR(PNG/JPG/TIFF)、邮件(EML/MSG)、日志文件(LOG) | 焊缝影像、往来邮件、设备日志 |

**加载后的统一数据格式——LangChain Document对象：**

每个文档加载后统一为 `Document(page_content="...", metadata={...})` 对象，其中：
- `page_content`：文档的原始文本内容
- `metadata`：包含 `source`（来源路径/表名/URL）、`data_type`（文件/数据库/API）、`category`（工艺/设备/生产）、`chunk_id` 等标注信息

```python
# 示例：统一后的Document对象
Document(
    page_content="Q235钢10mm板CO2气体保护焊，电流220-280A，电压28-32V...",
    metadata={
        "source": "data/knowledge_docs/焊接工艺手册.pdf",
        "data_type": "file",
        "category": "工艺参数",
        "page": 23,
        "material": "Q235",
    }
)
```

---

#### 5.7.3 阶段二：文档分块（Text Chunking）—— 检索精度的关键

分块策略直接影响检索质量，是本系统最核心的调优环节之一：

| 参数 | 默认值 | 作用 | 调优方向 |
|------|--------|------|----------|
| `chunk_size` | **500字符** | 每个文本块的大小 | 太小→信息碎片化，太大→检索精度下降 |
| `chunk_overlap` | **50字符** | 相邻块的重叠量 | 防止关键信息被切断在边界处 |
| `separators` | `["\n\n", "\n", "。", ".", " ", ""]` | 分割符优先级 | 优先在段落/句子边界分割，保证语义完整性 |

**分块算法**：`RecursiveCharacterTextSplitter`（递归字符分割器）

```
原始文档（3000字）
    │
    ▼ RecursiveCharacterTextSplitter
    ├── Chunk 1 (0-500):     "第一章 焊接工艺参数...（500字）"
    ├── Chunk 2 (450-950):   "...接上页重叠50字...（500字）"  ← overlap=50
    ├── Chunk 3 (900-1400):  "...接上页重叠50字...（500字）"
    ├── Chunk 4 (1350-1850): "...接上页重叠50字...（500字）"
    ├── Chunk 5 (1800-2300): "...接上页重叠50字...（500字）"
    └── Chunk 6 (2250-3000): "...最后500字"
```

**分块策略选择依据：**

| 文档类型 | 推荐chunk_size | 推荐overlap | 原因 |
|----------|---------------|-------------|------|
| 工艺手册/技术文档 | 500-800 | 10% | 段落适中，需保留上下文 |
| WPS焊接工艺规程 | 300-500 | 15% | 表格密集，参数需要完整 |
| 标准规范文档 | 600-1000 | 8% | 条款较长，需保留完整条款 |
| 设备日志 | 200-400 | 5% | 单条日志短，按行分割即可 |

---

#### 5.7.4 阶段三：向量化（Embedding）—— 将文本转化为机器可计算的"语义坐标"

这是RAG中最关键的技术环节：将自然语言文本转换为高维空间中的向量（一系列浮点数），使得语义相近的文本在向量空间中距离更近。

**向量化过程：**

```
文本: "Q235钢CO2气体保护焊电流220A"
        │
        ▼ Embedding模型（text-embedding-3-small）
        │
向量: [-0.023, 0.145, -0.089, ..., 0.067]  ← 1536维浮点数数组
```

**本系统配置：**

| 配置项 | 值 | 说明 |
|--------|-----|------|
| Embedding模型 | `text-embedding-3-small` | OpenAI Embedding模型 |
| 向量维度 | **1536维** | 每个文本块映射为1536个浮点数 |
| API端点 | `OPENAI_BASE_URL/embeddings` | 开发时直连API，部署时改为内网模型地址 |

**Embedding模型的语义理解能力示例：**

```
查询: "Q235 10mm板用什么焊接方法？"
        │
        ▼ Embedding → 向量Q
        │
        ▼ 在ChromaDB中搜索与Q余弦相似度最高的向量
        │
匹配结果（按相似度排序）：
  1. "Q235钢10mm板推荐采用CO2气体保护焊(GMAW)..."  ← 相似度 0.92
  2. "Q345低合金钢焊接方法选择..."                    ← 相似度 0.78
  3. "不锈钢SUS304 TIG焊工艺参数..."                   ← 相似度 0.65
```

---

#### 5.7.5 阶段四：向量存储（Vector Store）—— ChromaDB持久化

所有文本块经过Embedding后，以 `(向量, 文本, 元数据)` 三元组的形式存入ChromaDB：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 向量数据库 | **ChromaDB** | 轻量级，支持本地持久化，Python原生 |
| 存储路径 | `./data/chroma_db/` | 本地文件系统，随项目分发 |
| 索引结构 | **HNSW**（分层可导航小世界图） | 近似最近邻搜索，权衡速度与精度 |
| 距离度量 | **余弦相似度**（Cosine Similarity） | 对语义相似度衡量最有效 |
| 元数据字段 | `source`, `data_type`, `category`, `chunk_id` | 支持元数据过滤检索 |

**为什么选择ChromaDB而非其他向量数据库：**

| 对比维度 | ChromaDB | FAISS | Milvus | Pinecone |
|----------|----------|-------|--------|----------|
| 部署复杂度 | ⭐ 极简（pip install） | ⭐ 极简 | ⭐⭐⭐ 需Docker | ⭐⭐⭐⭐ 云服务 |
| 持久化 | ✅ 本地文件 | ❌ 仅内存（需手动持久化） | ✅ 分布式 | ✅ 云端 |
| 元数据过滤 | ✅ 内置 | ❌ 需自建 | ✅ 丰富 | ✅ 丰富 |
| 适用场景 | 中小规模（<100万条） | 大规模（亿级） | 企业级（千万级） | 企业级SaaS |
| **本项目选择** | **✅ 适合本地/内网部署** | 备选 | 过度设计 | 云服务（非必需） |

---

#### 5.7.6 阶段五：混合检索与生成（Hybrid Retrieval & Generation）—— 在线推理核心

这是RAG的**在线推理阶段**，用户每次提问都会实时执行以下流程：

**5.7.6.1 混合检索策略—— 向量语义 + 关键词双重保障**

```
用户提问: "Q235钢焊接出现气孔怎么办？"
        │
        ├──→ 向量语义检索（Vector Similarity Search）
        │    │
        │    ├─ 查询向量化 → Embedding(用户提问) → 1536维向量
        │    ├─ ChromaDB检索 → 余弦相似度 Top-K=5 候选
        │    └─ 结果: 语义相关段落（如"保护气体流量...气孔成因..."）
        │
        ├──→ BM25关键词检索（Sparse Retrieval）
        │    │
        │    ├─ 分词 → ["Q235", "钢", "焊接", "气孔", "怎么办"]
        │    ├─ 关键词匹配 → TF-IDF加权评分
        │    └─ 结果: 精确词匹配段落（如"Q235气孔缺陷...气体保护..."）
        │
        └──→ RRF融合排序（Reciprocal Rank Fusion）
             │
             ├─ 公式: RRF_score = Σ 1/(k + rank_i)  (k=60)
             ├─ 综合向量分数和关键词分数，重排序
             └─ 最终 Top-3 结果 → 注入Prompt
```

**为什么需要混合检索：**

| 检索方式 | 优势 | 劣势 | 适用场景 |
|----------|------|------|----------|
| 向量语义检索 | 理解语义，同义词/近义词可匹配 | 对精确术语/编码匹配弱 | "如何解决焊接质量问题" |
| BM25关键词检索 | 精确匹配术语、编号、标准号 | 不理解语义，同义词无法泛化 | "GB/T 985.1-2008 坡口标准" |
| **混合检索（本项目）** | 兼顾语义理解和精确匹配 | 计算开销稍高 | 企业场景全覆盖 |

**5.7.6.2 Prompt注入与生成（Augmented Generation）**

检索到的相关文档片段被注入到精心设计的Prompt模板中，指导LLM基于这些检索结果来生成回答：

```
┌─────────────────────────────────────────────────────────┐
│                    System Prompt（角色设定）              │
│  "你是一位资深的焊接工艺专家，拥有20年焊接工程经验。     │
│   请基于以下参考资料回答用户问题。"                       │
├─────────────────────────────────────────────────────────┤
│                    Context（检索注入的上下文）             │
│  [相关文档1] (来源: 焊接工艺手册.pdf, 相似度: 0.92)      │
│  "Q235钢CO2气体保护焊时，气孔主要由以下原因引起：        │
│   1. 保护气体流量不足（应保持15-20L/min）               │
│   2. 焊丝受潮..."                                       │
│                                                         │
│  [相关文档2] (来源: 缺陷诊断手册.docx, 相似度: 0.85)     │
│  "气孔缺陷的解决方案包括：调整气体流量至15-25L/min、     │
│   使用前烘干焊丝、焊前清理工件表面..."                    │
│                                                         │
│  [相关文档3] (来源: 内置知识库, 相似度: 0.81)            │
│  "DEFECT_DIAGNOSIS['气孔'].solutions:                   │
│   ['调整气体流量', '烘干焊丝', '清理表面', '防风屏障']"  │
├─────────────────────────────────────────────────────────┤
│                    User Question（用户问题）              │
│  "Q235钢焊接出现气孔怎么办？"                            │
├─────────────────────────────────────────────────────────┤
│                    LLM 生成回答                           │
│  "根据焊接工艺手册和缺陷诊断手册，Q235钢焊接出现气孔      │
│   的常见原因及解决方案如下：                              │
│                                                         │
│   **原因分析：**                                        │
│   1. 保护气体流量不足或过大 → 建议调整至15-25L/min       │
│   2. 焊丝受潮 → 使用前在250-300℃烘干1-2小时             │
│   ...                                                   │
│                                                         │
│   **参考来源：**                                        │
│   - 焊接工艺手册.pdf (第3章)                             │
│   - 缺陷诊断手册.docx                                   │
│   - 内置焊接知识库"                                     │
└─────────────────────────────────────────────────────────┘
```

**5.7.6.3 完整的检索配置参数表**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `vector_top_k` | **5** | 向量检索返回的候选数 |
| `bm25_top_k` | **5** | BM25检索返回的候选数 |
| `final_top_k` | **3** | RRF融合后的最终结果数 |
| `rrf_k` | **60** | RRF平滑常数 |
| `similarity_threshold` | **0.7** | 相似度阈值，低于此值的结果丢弃 |
| `max_tokens_context` | **3000** | 注入上下文的最大Token数 |

---

#### 5.7.7 总结：RAG数据传递全链路一览

```
                       【离线构建阶段】Build-time
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 多源数据  │───→│ 文档分块  │───→│ 向量化   │───→│ ChromaDB │
│ 加载器    │    │ chunk=500│    │ 1536维   │    │ 持久化   │
│ 20+格式   │    │ overlap=50│   │ Embedding│    │ 向量存储  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                               │
                      【在线推理阶段】Query-time  │
                                               ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ LLM生成  │←───│ Prompt   │←───│ RRF融合  │←───│ 混合检索  │
│ 回答+    │    │ 注入     │    │ 重排序   │    │ 向量+BM25│
│ 引用来源  │    │ 上下文   │    │ Top-3    │    │ Top-5各  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

**核心结论：**

1. **模型不直接读取知识库**——知识库数据通过向量检索 → Prompt注入 → LLM读取，而非训练或微调
2. **检索是瓶颈环节**——检索质量决定RAG上限；分块策略、Embedding模型、混合检索参数是三大调优杠杆
3. **向量数据库是"记忆中枢"**——ChromaDB充当长期记忆，所有焊接知识以向量形式存储，按需检索
4. **混合检索保障精度**——向量检索解决语义泛化，BM25解决精确匹配，RRF融合取长补短
5. **上下文窗口是硬约束**——注入Prompt的检索结果受Token限制，需控制retrieval_top_k和chunk_size的乘积

---

#### 5.7.8 RAG构建流程总览图

```mermaid
flowchart LR
    subgraph Load["📥 1. 文档加载 (Document Loader)"]
        direction TB
        L1["PDF 工艺手册"]
        L2["Word 操作规范"]
        L3["Excel 参数表"]
        L4["数据库 MES/ERP"]
        L5["REST API 接口"]
        L6["内置知识字典"]
    end

    subgraph Split["✂️ 2. 文档分块 (Text Splitter)"]
        direction TB
        SP1["递归字符分割<br/>RecursiveCharacterTextSplitter"]
        SP2["chunk_size=500<br/>chunk_overlap=50<br/>separators优先级分割"]
    end

    subgraph Embed["🧮 3. 向量化 (Embedding)"]
        direction TB
        EM1["文本 → 1536维向量<br/>OpenAI Embedding API<br/>text-embedding-3-small"]
        EM2["BM25 关键词索引<br/>TF-IDF稀疏向量<br/>(混合检索备用)"]
    end

    subgraph Store["💾 4. 向量存储 (Vector Store)"]
        direction TB
        VS1[("ChromaDB<br/>HNSW索引<br/>余弦相似度")]
        VS2["本地持久化<br/>./data/chroma_db/<br/>元数据过滤支持"]
    end

    subgraph Retrieve["🔍 5. 混合检索 (Hybrid Retrieval)"]
        direction TB
        RT1["向量语义检索<br/>Top-K=5 相似匹配"]
        RT2["BM25 关键词检索<br/>Top-K=5 词匹配"]
        RT3["🔀 RRF融合排序<br/>k=60, 最终Top-3"]
        RT1 --> RT3
        RT2 --> RT3
    end

    subgraph Generate["✍️ 6. RAG生成 (Augmented Generation)"]
        direction TB
        G1["构建Prompt<br/>System+Context+Question"]
        G2["LLM 生成回答<br/>含引用来源溯源"]
    end

    Load --> Split --> Embed --> Store --> Retrieve --> Generate

    classDef loadStyle fill:#1a1a2e,stroke:#e94560,color:#eee
    classDef procStyle fill:#16213e,stroke:#0f3460,color:#eee
    classDef storeStyle fill:#0f3460,stroke:#533483,color:#eee
    classDef retStyle fill:#1a1a2e,stroke:#00b4d8,color:#eee
    classDef genStyle fill:#16213e,stroke:#e94560,color:#eee
    class L1,L2,L3,L4,L5,L6 loadStyle
    class SP1,SP2,EM1,EM2 procStyle
    class VS1,VS2 storeStyle
    class RT1,RT2,RT3 retStyle
    class G1,G2 genStyle
```

### 5.8 Agent构建与编排流程（LangGraph）

下面展示从工具定义到多Agent编排的完整构建过程，基于 LangGraph 的 StateGraph 实现：

```mermaid
flowchart TD
    subgraph Phase1["🔨 阶段一: 定义工具 (Tool Definition)"]
        direction TB
        T1["@tool 装饰器<br/>定义Python函数签名"]
        T2["Pydantic Schema<br/>参数类型校验"]
        T3["工具注册表<br/>Tool Registry统一管理"]
        T1 --> T2 --> T3
    end

    subgraph Phase2["🏗️ 阶段二: 构建Agent (Agent Creation)"]
        direction TB
        AG1["create_react_agent<br/>绑定LLM + Tools"]
        AG2["System Prompt<br/>角色定义 + 领域知识"]
        AG3["5个专业Agent<br/>设备/生产/BOM/库存/工艺"]
        AG1 --> AG2 --> AG3
    end

    subgraph Phase3["🧩 阶段三: 编排主控 (Supervisor Graph)"]
        direction TB
        SV1["StateGraph 定义<br/>AgentState类型"]
        SV2["supervisor_node<br/>意图识别 + 路由决策"]
        SV3["5个agent_node<br/>专业Agent执行节点"]
        SV4["finish_node<br/>结果聚合 + LLM总结"]
        SV1 --> SV2
        SV2 -->|"conditional edge"| SV3
        SV3 -->|"返回"| SV2
        SV2 -->|"FINISH"| SV4
    end

    subgraph Phase4["🚀 阶段四: 运行时执行 (Runtime)"]
        direction TB
        R1["用户输入"]
        R2["graph.invoke()<br/>启动执行图"]
        R3["逐节点执行<br/>流式输出"]
        R4["轨迹日志<br/>实时记录"]
        R1 --> R2 --> R3 --> R4
    end

    Phase1 --> Phase2 --> Phase3 --> Phase4

    classDef p1 fill:#1a1a2e,stroke:#e94560,color:#eee
    classDef p2 fill:#16213e,stroke:#0f3460,color:#eee
    classDef p3 fill:#0f3460,stroke:#533483,color:#eee
    classDef p4 fill:#1a1a2e,stroke:#00b4d8,color:#eee
    class T1,T2,T3 p1
    class AG1,AG2,AG3 p2
    class SV1,SV2,SV3,SV4 p3
    class R1,R2,R3,R4 p4
```


### 5.9 多源数据加载器（企业级设计）

企业内部知识分布在多种异构数据源中，仅支持 PDF/Word/Excel 远远不够。本节设计了 **统一多源知识加载器（UnifiedKnowledgeLoader）**，实现从文件系统、关系数据库、REST API 三大类数据源中自动识别、加载、解析数据，统一输出为 LangChain Document 对象。

#### 5.9.1 架构总览

```
┌──────────────────────────────────────────────────────────────────────┐
│              UnifiedKnowledgeLoader（统一知识加载入口）               │
│                                                                      │
│  prepare_multi_source_documents(docs_dir, db_configs, api_configs)   │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│FileDocumentLoader│ │DB Document   │ │API Document      │
│                  │ │Loader        │ │Loader            │
│ 文件系统加载器    │ │ 数据库加载器  │ │ API加载器         │
├──────────────────┤ ├──────────────┤ ├──────────────────┤
│ PDF/Word/Excel   │ │ MySQL        │ │ REST API         │
│ PPTX/TXT/CSV     │ │ PostgreSQL   │ │ JSONPath提取     │
│ JSON/JSONL/XML   │ │ SQL Server   │ │ 模板渲染         │
│ Markdown/HTML    │ │ Oracle       │ │ 缓存机制         │
│ LOG/EML/MSG      │ │ SQLite       │ │ 认证支持         │
│ PNG/JPG/TIFF(OCR)│ │              │ │                  │
└──────────────────┘ └──────────────┘ └──────────────────┘
```

#### 5.9.2 FileDocumentLoader —— 20+文件格式统一加载

**设计思路**：通过扩展名映射表自动匹配对应的加载方法，新增格式只需添加映射条目。

| 类别 | 格式 | 加载库 | 方法 |
|------|------|--------|------|
| **PDF系列** | `.pdf` | PyMuPDF / PyPDF | 按页提取文本 |
| **Word** | `.docx` | python-docx | 按段落提取 |
| **Excel** | `.xlsx`, `.xls` | openpyxl / xlrd | 按行展开，保留表头 |
| **PPT** | `.pptx` | python-pptx | 按幻灯片提取 |
| **纯文本** | `.txt`, `.md`, `.log` | 原生open | 直接读取 |
| **CSV** | `.csv` | pandas | DataFrame→行文本 |
| **JSON** | `.json`, `.jsonl` | json | 序列化为文本，保留层级 |
| **XML** | `.xml` | lxml / xml.etree | 提取文本节点 |
| **Markdown** | `.md` | 原生open | 保留标题层级 |
| **HTML** | `.html`, `.htm` | BeautifulSoup4 | 去标签提取纯文本 |
| **邮件** | `.eml`, `.msg` | email / extract_msg | 提取主题+正文+附件文本 |
| **图片OCR** | `.png`, `.jpg`, `.jpeg`, `.tiff` | pytesseract + Pillow | OCR识别文字 |

**核心实现模式**：

```python
class FileDocumentLoader:
    """支持20+文件格式的文档加载器"""

    LOADERS: Dict[str, Callable] = {
        ".pdf":  "_load_pdf",
        ".docx": "_load_docx",
        ".xlsx": "_load_xlsx",
        ".xls":  "_load_xlsx",
        ".pptx": "_load_pptx",
        ".txt":  "_load_text",
        ".csv":  "_load_csv",
        ".json": "_load_json",
        ".jsonl":"_load_jsonl",
        ".xml":  "_load_xml",
        ".md":   "_load_markdown",
        ".html": "_load_html",
        ".htm":  "_load_html",
        ".log":  "_load_text",
        ".eml":  "_load_email",
        ".msg":  "_load_msg",
        ".png":  "_load_image_ocr",
        ".jpg":  "_load_image_ocr",
        ".jpeg": "_load_image_ocr",
        ".tiff": "_load_image_ocr",
    }

    def load_directory(self, dir_path: str) -> List[Document]:
        """递归扫描目录，自动识别并加载所有支持的文件"""
        documents = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in self.LOADERS:
                    loader_method = getattr(self, self.LOADERS[ext])
                    docs = loader_method(os.path.join(root, file))
                    documents.extend(docs)
        return documents
```

**OCR识别（图片→文字）**：

```python
def _load_image_ocr(self, file_path: str) -> List[Document]:
    """通过OCR从图片中提取文本（用于焊缝检测报告、手写记录等）"""
    from PIL import Image
    import pytesseract
    img = Image.open(file_path)
    text = pytesseract.image_to_string(img, lang="chi_sim+eng")
    if text.strip():
        return [Document(page_content=text.strip(), metadata={
            "source": file_path,
            "data_type": "image_ocr",
            "category": "图片识别",
        })]
    return []
```

#### 5.9.3 DatabaseDocumentLoader —— 关系数据库数据抽取

**设计思路**：通过SQLAlchemy连接多种数据库，支持两种抽取模式：
- **表导出模式**：将整张表的数据转换为自然语言描述文本
- **自定义SQL模式**：通过SQL查询精确提取所需知识

**支持的数据库及连接串模板：**

| 数据库 | 连接字符串模板 | 使用场景 |
|--------|---------------|----------|
| MySQL | `mysql+pymysql://user:pass@host:port/db` | 企业MES生产数据 |
| PostgreSQL | `postgresql+psycopg2://user:pass@host:port/db` | ERP系统 |
| SQL Server | `mssql+pyodbc://user:pass@host:port/db?driver=ODBC+Driver+17` | 企业OA/WMS |
| Oracle | `oracle+cx_oracle://user:pass@host:port/service_name` | 老系统遗留数据 |
| SQLite | `sqlite:///path/to/database.db` | 本地/嵌入式数据库 |

**核心实现：**

```python
class DatabaseDocumentLoader:
    """从关系数据库加载知识数据"""

    def __init__(self):
        self.engine = None

    def connect(self, db_url: str):
        """建立数据库连接（支持所有SQLAlchemy兼容的数据库）"""
        from sqlalchemy import create_engine
        self.engine = create_engine(db_url)

    def load_table(self, table_name: str, description: str = "",
                   limit: int = 10000) -> List[Document]:
        """读取整张表，每行转为一条Document

        转换逻辑：
        1. 读取表结构（列名和类型）
        2. 将每行的 列名:列值 拼接为自然语言文本
        3. 示例: "id=001, material=Q235, thickness=10mm, current=250A, status=OK"
        """
        import pandas as pd
        df = pd.read_sql(f"SELECT * FROM {table_name}", self.engine)
        if len(df) > limit:
            df = df.sample(n=limit)  # 超限时采样
        documents = []
        for idx, row in df.iterrows():
            content = f"[{table_name}] " + ", ".join(
                f"{col}={val}" for col, val in row.items()
            )
            documents.append(Document(
                page_content=content,
                metadata={
                    "source": f"db://{table_name}",
                    "data_type": "database",
                    "category": description or table_name,
                    "row_id": idx,
                }
            ))
        return documents

    def load_query(self, sql: str, description: str = "") -> List[Document]:
        """执行自定义SQL查询，结果转为Document"""
        import pandas as pd
        df = pd.read_sql(sql, self.engine)
        documents = []
        for idx, row in df.iterrows():
            content = ", ".join(f"{col}={val}" for col, val in row.items())
            documents.append(Document(
                page_content=content,
                metadata={
                    "source": "db://custom_query",
                    "data_type": "database",
                    "category": description or "SQL查询",
                    "sql": sql,
                }
            ))
        return documents
```

**典型企业场景的数据库配置示例：**

```yaml
# data_sources.yml - 数据源配置文件
database:
  # MES生产数据库
  mes_db:
    type: mysql
    host: 192.168.1.100
    port: 3306
    database: welding_mes
    user: mes_reader
    password: ${MES_DB_PASSWORD}  # 环境变量注入
    tables:
      - name: welding_records
        description: "焊接生产记录"
        limit: 5000
      - name: process_parameters
        description: "工艺参数历史"
        columns: ["material", "thickness", "current", "voltage", "speed"]

  # ERP物料数据库
  erp_db:
    type: postgresql
    host: 192.168.1.101
    port: 5432
    database: erp_production
    user: erp_reader
    queries:
      - sql: "SELECT material_code, material_name, spec FROM materials WHERE category='welding'"
        description: "焊接相关物料清单"
```

#### 5.9.4 APIDocumentLoader —— REST API数据接入

**设计思路**：支持对接企业内部数据中台、知识库接口等REST API，通过JSONPath路径提取、模板渲染、内存缓存实现灵活的数据接入。

```python
class APIDocumentLoader:
    """通过REST API加载知识数据"""

    def __init__(self):
        self._cache: Dict[str, List[Document]] = {}

    def load_from_api(
        self,
        url: str,
        method: str = "GET",
        headers: dict = None,
        params: dict = None,
        json_body: dict = None,
        json_path: str = "$",        # JSONPath提取路径，如 $.data[*]
        template: str = None,         # 可选的内容格式化模板
        description: str = "",        # 数据描述
        cache_key: str = None,        # 缓存键
    ) -> List[Document]:
        """调用REST API并解析响应为Document

        JSONPath说明:
        - "$"        : 整个响应
        - "$.data[*]": 取data数组中的每个元素
        - "$.results[0:10]": 取前10条结果

        模板说明 (Jinja2语法):
        - "{{ item.title }}: {{ item.content }}"  : 提取title和content字段
        - 不指定时，将整个item序列化为JSON文本
        """
        import requests
        from jsonpath_ng import parse as jsonpath_parse

        # 检查缓存
        if cache_key and cache_key in self._cache:
            return self._cache[cache_key]

        # 发送请求
        resp = requests.request(
            method=method, url=url,
            headers=headers or {},
            params=params or {},
            json=json_body or {},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        # JSONPath提取
        matches = jsonpath_parse(json_path).find(data)
        items = [m.value for m in matches]

        # 模板渲染或JSON序列化
        documents = []
        if template:
            from jinja2 import Template
            tmpl = Template(template)
            for item in items:
                content = tmpl.render(item=item)
                documents.append(Document(
                    page_content=content,
                    metadata={
                        "source": url,
                        "data_type": "api",
                        "category": description or "API数据",
                    }
                ))
        else:
            import json
            for item in items:
                documents.append(Document(
                    page_content=json.dumps(item, ensure_ascii=False, indent=2),
                    metadata={
                        "source": url,
                        "data_type": "api",
                        "category": description or "API数据",
                    }
                ))

        # 更新缓存
        if cache_key:
            self._cache[cache_key] = documents
        return documents
```

#### 5.9.5 UnifiedKnowledgeLoader —— 统一入口与编排

整合三大加载器，提供一行代码级别的调用体验：

```python
class UnifiedKnowledgeLoader:
    """统一知识加载器——多源数据一站式入口"""

    def __init__(self):
        self.file_loader = FileDocumentLoader()
        self.db_loader = DatabaseDocumentLoader()
        self.api_loader = APIDocumentLoader()

    def load_all(
        self,
        docs_dir: Optional[str] = None,      # 文件目录路径
        db_configs: Optional[List[dict]] = None,  # 数据库配置列表
        api_configs: Optional[List[dict]] = None, # API配置列表
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> List[Document]:
        """一次性从所有数据源加载知识，统一分块后返回

        典型调用示例:
            loader = UnifiedKnowledgeLoader()
            documents = loader.load_all(
                docs_dir="./data/knowledge_docs",
                db_configs=[
                    {
                        "url": "mysql+pymysql://reader:pass@192.168.1.100:3306/welding_mes",
                        "tables": [
                            {"name": "welding_records", "description": "焊接生产记录", "limit": 5000},
                        ],
                    },
                ],
                api_configs=[
                    {
                        "url": "http://internal-api/welding/standards",
                        "json_path": "$.data[*]",
                        "template": "标准号 {{ item.code }}: {{ item.name }}",
                        "description": "焊接标准规范",
                    },
                ],
            )
            # 返回统一的 Document[] 列表，可直接传入 split_documents()
        """
        all_docs = []

        # 1. 文件加载
        if docs_dir:
            file_docs = self.file_loader.load_directory(docs_dir)
            all_docs.extend(file_docs)

        # 2. 数据库加载
        if db_configs:
            for db_cfg in db_configs:
                self.db_loader.connect(db_cfg["url"])
                for table_cfg in db_cfg.get("tables", []):
                    docs = self.db_loader.load_table(
                        table_cfg["name"],
                        description=table_cfg.get("description", ""),
                        limit=table_cfg.get("limit", 10000),
                    )
                    all_docs.extend(docs)
                for query_cfg in db_cfg.get("queries", []):
                    docs = self.db_loader.load_query(
                        query_cfg["sql"],
                        description=query_cfg.get("description", ""),
                    )
                    all_docs.extend(docs)

        # 3. API加载
        if api_configs:
            for api_cfg in api_configs:
                docs = self.api_loader.load_from_api(**api_cfg)
                all_docs.extend(docs)

        return all_docs


# 公共接口（保持向后兼容）
def prepare_multi_source_documents(
    docs_dir: Optional[str] = None,
    db_configs: Optional[List[dict]] = None,
    api_configs: Optional[List[dict]] = None,
) -> List[Document]:
    """从多源加载知识文档

    向后兼容 prepare_documents() 和 load_documents() 接口。
    在不传 db_configs 和 api_configs 时，行为与原始 prepare_documents() 完全一致。
    """
    loader = UnifiedKnowledgeLoader()
    return loader.load_all(
        docs_dir=docs_dir,
        db_configs=db_configs,
        api_configs=api_configs,
    )
```

#### 5.9.6 数据源配置结构（data_sources.yml）

通过YAML配置文件统一管理所有数据源，实现配置与代码分离：

```yaml
# ==================== 知识文档目录 ====================
docs_dir: "./data/knowledge_docs"

# ==================== 数据库数据源 ====================
databases:
  # MES焊接生产数据库
  - id: mes_welding
    url: "mysql+pymysql://reader:${MES_PASSWORD}@192.168.1.100:3306/welding_mes"
    enabled: false  # 生产环境启用，开发环境使用SQLite模拟
    tables:
      - name: welding_records
        description: "焊接生产记录"
        limit: 5000
      - name: process_parameters
        description: "焊接工艺参数历史"
        limit: 3000

  # ERP物料信息
  - id: erp_materials
    url: "postgresql+psycopg2://reader:${ERP_PASSWORD}@192.168.1.101:5432/erp"
    enabled: false
    queries:
      - sql: >
          SELECT m.code, m.name, m.spec, m.category
          FROM materials m
          WHERE m.category IN ('焊接材料', '焊丝', '保护气体')
        description: "焊接相关物料清单"

  # QMS质量检验数据
  - id: qms_inspection
    url: "mssql+pyodbc://reader:${QMS_PASSWORD}@192.168.1.102:1433/qms?driver=ODBC+Driver+17+for+SQL+Server"
    enabled: false
    tables:
      - name: weld_inspections
        description: "焊缝质量检验记录"
        limit: 3000

# ==================== API数据源 ====================
apis:
  # 企业内部焊接标准API
  - id: welding_standards
    url: "http://internal-api.example.com/v1/welding/standards"
    method: GET
    headers:
      Authorization: "Bearer ${API_TOKEN}"
    json_path: "$.data[*]"
    template: "标准 {{ item.code }}: {{ item.name }} - {{ item.description }}"
    description: "焊接标准规范库"

  # 缺陷案例库API
  - id: defect_cases
    url: "http://internal-api.example.com/v1/welding/defect-cases"
    method: GET
    json_path: "$.results[*]"
    template: |
      [缺陷案例] 缺陷类型: {{ item.type }}
      材料: {{ item.material }}, 厚度: {{ item.thickness }}
      原因: {{ item.cause }}
      解决方案: {{ item.solution }}
    description: "焊接缺陷案例库"
    cache_key: "defect_cases"  # 缓存，避免重复请求

# ==================== 分块配置 ====================
chunking:
  chunk_size: 500
  chunk_overlap: 50
  separators: ["\n\n", "\n", "。", ".", " ", ""]
```

#### 5.9.7 实施优先级矩阵

| 优先级 | 数据源 | 理由 | 实施复杂度 |
|--------|--------|------|-----------|
| **P0（必须）** | 文件系统（已有格式+PPT/CSV/JSON/MD/HTML） | 企业文档以文件为主 | ⭐ |
| **P0（必须）** | 关系数据库（SQLite→MySQL→PG→MSSQL→Oracle） | 结构化数据最核心的来源 | ⭐⭐ |
| **P0（必须）** | REST API | 企业内部数据中台标配 | ⭐⭐ |
| **P1（推荐）** | 邮件(EML/MSG)、日志(LOG) | 操作记录和沟通记录有价值 | ⭐ |
| **P2（可选）** | 图片OCR | 特殊场景（焊缝影像报告） | ⭐⭐⭐ |

#### 5.9.8 依赖补充

多源加载器需要以下新依赖（已同步更新到 `requirements.txt`）：

```txt
# ==================== 多源数据加载（新增） ====================
python-pptx>=0.6.21          # PowerPoint文档解析
xlrd>=2.0.1                  # 老版Excel(.xls)支持
beautifulsoup4>=4.12.0       # HTML文本提取
lxml>=4.9.0                  # XML解析加速
extract-msg>=0.47.0          # Outlook .msg 邮件解析
Jinja2>=3.1.2                # API响应模板渲染
jsonpath-ng>=1.6.0           # JSON数据路径提取

# ==================== 数据库驱动（按需安装） ====================
pymysql>=1.1.0               # MySQL/MariaDB 驱动
psycopg2-binary>=2.9.9       # PostgreSQL 驱动
pyodbc>=5.0.0                # SQL Server 驱动 (Windows)
cx-Oracle>=8.3.0             # Oracle 驱动（需Oracle Instant Client）

# ==================== OCR支持（可选） ====================
pytesseract>=0.3.10          # OCR文字识别（需安装Tesseract-OCR）
Pillow>=10.0.0               # 图片处理
```


## 六、Agent工具设计

### 6.1 设备监控工具

```python
@tool
def get_device_metrics(device_id: str) -> dict:
    """获取焊接设备实时参数"""

@tool
def get_device_history(device_id: str, start: str, end: str) -> list:
    """获取设备历史参数"""

@tool
def diagnose_anomaly(device_id: str, metric: str, value: float) -> dict:
    """诊断设备参数异常"""
```

### 6.2 生产进度工具

```python
@tool
def get_work_order(work_order_id: str) -> dict:
    """查询工单详细信息"""

@tool
def get_process_progress(work_order_id: str) -> list:
    """查询工单各工序进度"""

@tool
def identify_delays() -> list:
    """识别所有滞后工单"""

@tool
def get_today_production_summary() -> dict:
    """获取今日生产汇总"""
```

### 6.3 BOM管理工具

```python
@tool
def get_bom(bom_id: str) -> dict:
    """查询BOM完整结构（树形）"""

@tool
def compare_bom_versions(bom_id: str, v1: str, v2: str) -> dict:
    """对比两个BOM版本的差异"""

@tool
def check_material_availability(bom_id: str, quantity: int) -> dict:
    """检查BOM物料的齐套性"""
```

### 6.4 库存分析工具

```python
@tool
def query_inventory(material_code: str = None, category: str = None) -> list:
    """查询库存"""

@tool
def get_low_stock_alerts() -> list:
    """获取低于安全库存的物料列表"""

@tool
def get_obsolete_materials(days: int = 180) -> list:
    """识别呆滞物料"""
```


## 七、API接口设计

### 7.1 REST API

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **对话** | POST | `/api/chat` | 发送消息，SSE流式返回 |
| **设备** | GET | `/api/devices/{id}/metrics` | 获取设备实时参数 |
| **设备** | GET | `/api/devices/{id}/history` | 获取历史时序数据 |
| **生产** | GET | `/api/production/orders` | 获取工单列表 |
| **生产** | GET | `/api/production/orders/{id}` | 获取工单详情+进度 |
| **生产** | GET | `/api/production/delays` | 获取滞后工单 |
| **生产** | GET | `/api/production/summary` | 获取生产汇总 |
| **BOM** | GET | `/api/bom/{id}` | 获取BOM完整结构 |
| **BOM** | POST | `/api/bom/compare` | 对比BOM版本 |
| **BOM** | POST | `/api/bom/availability` | 齐套性分析 |
| **库存** | GET | `/api/inventory` | 查询库存 |
| **库存** | GET | `/api/inventory/alerts` | 获取预警列表 |
| **库存** | GET | `/api/inventory/obsolete` | 获取呆滞物料 |
| **轨迹** | GET | `/api/sessions/{id}/trace` | 获取执行轨迹 |
| **报告** | POST | `/api/report/generate` | 生成综合报告 |

### 7.2 WebSocket事件

| 事件 | 方向 | 说明 |
|------|------|------|
| `metrics:update` | Server → Client | 设备参数实时推送 |
| `production:update` | Server → Client | 工单进度实时推送 |
| `inventory:alert` | Server → Client | 库存预警推送 |
| `trace:step` | Server → Client | Agent执行步骤推送 |


## 八、数据模拟方案

### 8.1 生产进度模拟器

```python
import random
from datetime import datetime, timedelta

class ProductionSimulator:
    """生产进度数据模拟器"""
    
    def __init__(self):
        self.orders = self._generate_orders(20)
    
    def _generate_orders(self, count):
        orders = []
        products = [
            ("焊接底座", "PRD-001", 200),
            ("机架组件", "PRD-002", 150),
            ("控制箱体", "PRD-003", 80),
            ("变压器支架", "PRD-004", 300),
            ("散热器总成", "PRD-005", 100),
        ]
        for i in range(count):
            product = random.choice(products)
            progress = random.randint(0, 100)
            status = "已完成" if progress == 100 else "进行中" if progress > 0 else "待排产"
            orders.append({
                "id": f"WO-2026-{i+1:03d}",
                "product_name": product[0],
                "product_code": product[1],
                "quantity": product[2],
                "progress": progress,
                "status": status,
                "planned_end": datetime.now() + timedelta(days=random.randint(1, 10)),
                "delay_days": random.randint(0, 3) if progress < 50 else 0
            })
        return orders
```

### 8.2 BOM数据模拟器

```python
class BOMSimulator:
    def get_bom(self, bom_id):
        return {
            "id": bom_id,
            "product_name": "焊接底座",
            "version": "V2.0",
            "items": [
                {"level": 1, "name": "底板 Q235 10mm", "qty": 1, "stock": 45, "status": "充足"},
                {"level": 1, "name": "侧板 Q235 8mm", "qty": 2, "stock": 32, "status": "充足"},
                {"level": 2, "name": "接触器 CJX2-12", "qty": 2, "stock": 5, "status": "缺货"},
            ]
        }
```

### 8.3 库存模拟器

```python
class InventorySimulator:
    def get_inventory(self):
        return [
            {"code": "MAT-1001", "name": "接触器", "qty": 5, "safety": 20, "status": "短缺"},
            {"code": "MAT-1002", "name": "焊丝 1.2mm", "qty": 50, "safety": 100, "status": "短缺"},
            {"code": "MAT-1003", "name": "保护镜片", "qty": 3, "safety": 10, "status": "短缺"},
        ]
```


## 九、开发计划

### 9.1 总体排期（5周）

```
Week 1: 后端核心（RAG + 基础Agent）    ████████████████████████████████████████
Week 2: 多Agent扩展（生产+BOM+库存）    ████████████████████████████████████████
Week 3: Qt客户端基础（监控+对话+轨迹）  ████████████████████████████████████████
Week 4: 功能集成（生产看板+BOM+库存）    ████████████████████████████████████████
Week 5: 测试、打磨与交付                ████████████████████████████████████████
```

### 9.2 详细任务拆解

#### 第一周：后端核心 + RAG（Day 1-7）

| 天数 | 任务 | 产出 |
|------|------|------|
| Day 1 | 环境搭建、LLM接口测试 | 模型调用成功 |
| Day 2 | 焊接知识文档收集（工艺手册、WPS等） | 知识库文档 |
| Day 3 | RAG检索链实现 | 基础RAG可用 |
| Day 4 | 主控Agent（意图识别 + 路由） | 多意图识别 |
| Day 5 | FastAPI服务 + 对话接口（SSE） | API可调用 |
| Day 6 | 设备数据模拟器 + 设备监控Agent | 设备模块可用 |
| Day 7 | 轨迹日志系统 | 轨迹可追溯 |

#### 第二周：多Agent扩展（Day 8-14）

| 天数 | 任务 | 产出 |
|------|------|------|
| Day 8 | 数据库设计（工单/BOM/库存表） | SQLite schema |
| Day 9 | 生产数据模拟 + 生产进度Agent | 进度查询可用 |
| Day 10 | BOM数据模拟 + BOM管理Agent | BOM查询可用 |
| Day 11 | 库存数据模拟 + 库存分析Agent | 库存查询可用 |
| Day 12 | 各Agent工具注册与测试 | 所有工具可用 |
| Day 13 | 多Agent协作编排（LangGraph） | 完整路由链路 |
| Day 14 | API接口扩展（生产/BOM/库存） | 全部API就绪 |

#### 第三周：Qt客户端基础（Day 15-21）

| 天数 | 任务 | 产出 |
|------|------|------|
| Day 15 | Qt项目初始化、主窗口框架 | 界面框架 |
| Day 16 | 监控仪表盘（参数卡片+曲线） | 设备监控UI |
| Day 17 | 对话交互界面 | 对话UI |
| Day 18 | 轨迹追踪面板 | 轨迹UI |
| Day 19 | HTTP客户端 + WebSocket | 通信打通 |
| Day 20 | 生产进度看板UI | 进度看板 |
| Day 21 | BOM管理面板UI | BOM面板 |

#### 第四周：功能集成（Day 22-28）

| 天数 | 任务 | 产出 |
|------|------|------|
| Day 22 | 库存分析看板UI | 库存看板 |
| Day 23 | 前后端全功能联调 | 端到端打通 |
| Day 24 | 多模块切换 + 统一导航 | 完整应用 |
| Day 25 | 告警推送 + 实时更新 | 实时能力 |
| Day 26 | 报告导出（PDF/Excel） | 报告功能 |
| Day 27 | UI/UX优化 | 视觉提升 |
| Day 28 | 性能优化 | 响应提速 |

#### 第五周：测试与交付（Day 29-35）

| 天数 | 任务 | 产出 |
|------|------|------|
| Day 29 | 全功能测试 | 测试报告 |
| Day 30 | 边缘情况处理 | 容错完善 |
| Day 31 | 文档编写（README + 架构文档） | 项目文档 |
| Day 32 | 录制演示视频 | 演示素材 |
| Day 33 | 代码审查与重构 | 代码质量 |
| Day 34 | 打包部署（exe + Docker） | 可交付产物 |
| Day 35 | 最终验收 + 面试准备 | 项目交付 |

### 9.3 里程碑

| 里程碑 | 时间 | 验收标准 |
|--------|------|----------|
| M1: RAG + 主控Agent | Day 7 | 能识别意图并路由到对应Agent |
| M2: 全功能Agent | Day 14 | 五个专业Agent全部可用 |
| M3: Qt原型 | Day 21 | 界面布局完成，能展示模拟数据 |
| M4: 端到端打通 | Day 28 | 全功能从界面到后端完整链路 |
| M5: 项目交付 | Day 35 | 完整系统 + 文档 + 视频 |


## 十、关键技术点与风险应对

### 10.1 多Agent协作的意图识别精度

**挑战**：用户提问可能涉及多个领域（如"WO-001的BOM物料库存够吗？"同时涉及生产、BOM、库存）

**应对**：
- 主控Agent采用**分层意图识别**：先识别主意图（生产/BOM/库存/设备/工艺），再识别子意图
- 支持**多意图并行处理**：对于复合问题，同时路由到多个Agent，聚合结果后返回
- 构建**焊接领域意图分类数据集**，持续优化分类器

### 10.2 BOM数据的结构化与向量化结合

**挑战**：BOM既有严格的层级结构（树形），又有非结构化的描述文本

**应对**：
- **结构化存储**：BOM的层级关系、用量、编码存SQLite，支持精确查询
- **向量化检索**：BOM的描述字段（物料名称、规格、备注）向量化存入Chroma
- **混合查询**：结构化问题走SQL，语义问题走向量检索

### 10.3 数据实时性与一致性

**挑战**：设备数据、生产进度、库存数据来自不同系统，存在时间差

**应对**：
- 统一采用**事件驱动**的数据更新机制
- 设置数据**时间戳**，在UI上明确标注数据时效
- 对关键决策采用**保守估计**（宁可误报缺货，不可漏报）

### 10.4 安全与权限

- **操作审计**：所有Agent操作记录完整的执行轨迹，可追溯
- **敏感操作确认**：涉及BOM修改、采购建议等操作，需人工二次确认
- **数据隔离**：不同产品线/车间的数据相互隔离


## 十一、面试展示要点

### 11.1 演示流程（7分钟）

| 环节 | 时长 | 内容 |
|------|------|------|
| 开场 | 30秒 | 介绍项目背景——焊接车间的设备监控+生产管理+物料协同痛点 |
| 设备监控 | 1分钟 | 展示实时仪表盘，参数动态更新，异常告警 |
| 生产进度 | 1.5分钟 | 展示工单看板，进度条、滞后预警，Agent自动分析滞后原因 |
| BOM管理 | 1.5分钟 | 展示BOM树形结构，版本对比，齐套性分析 |
| 库存分析 | 1分钟 | 展示库存看板，短缺预警，呆滞料识别 |
| 对话交互 | 1分钟 | 提问复合问题（如"WO-001的物料够不够？"），展示多Agent协作 |
| 轨迹追踪 | 30秒 | 展开轨迹面板，展示完整推理链条 |

### 11.2 常见面试问题准备

| 问题 | 回答要点 |
|------|----------|
| 为什么设计成多Agent架构？ | 单Agent难以同时处理设备、生产、BOM、库存多领域任务，多Agent实现专业化分工 |
| 各Agent之间怎么通信？ | 主控Agent负责路由和聚合，子Agent通过共享的State进行数据交换 |
| BOM的检索怎么做的？ | 结构化数据走SQL精确查询，描述文本走向量检索，两者结合 |
| 如何保证数据安全？ | 所有操作有审计日志，敏感操作需人工确认，数据按权限隔离 |
| 与真实MES/ERP怎么集成？ | 通过API对接，本项目先用模拟数据验证逻辑，实际部署时替换为真实数据源 |
| 这个项目还是RAG吗？ | RAG是核心组件之一，整体是"RAG+结构化查询+多工具调用"的混合架构 |


## 十二、项目交付物清单

- [ ] 源代码（Qt客户端 + Python后端，GitHub仓库）
- [ ] README.md（项目介绍、架构图、快速启动指南）
- [ ] 技术设计文档（本文档）
- [ ] API接口文档（OpenAPI/Swagger）
- [ ] 数据库Schema文档
- [ ] 8分钟演示视频（覆盖全部5大模块）
- [ ] 可执行文件（Windows exe + Docker Compose一键部署）
- [ ] 模拟数据集（工单/BOM/库存/设备参数）
- [ ] 面试问答准备稿
- [ ] 内网部署离线包（offline_packages/ 目录）


## 附录：环境配置与启动指南

### A.1 环境准备

**开发环境（外网，有API Key）：**

```bash
# 1. 安装Python 3.10+
# 2. 直接在线安装依赖
pip install -r requirements.txt

# 3. 配置环境变量（.env文件）
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1       # 或其他兼容API地址
MODEL_NAME=gpt-4o                                # 或 deepseek-chat 等
EMBEDDING_MODEL=text-embedding-3-small
```

**内网部署环境（切换模型地址）：**

```bash
# 1. 安装Python 3.10+
# 2. 使用离线包安装依赖
pip install --no-index --find-links=./offline_packages -r requirements.txt

# 3. 配置环境变量（.env文件）—— 仅改两行
OPENAI_API_KEY=your-internal-api-key
OPENAI_BASE_URL=http://内网模型网关地址/v1       # 改为公司内网地址
MODEL_NAME=公司部署的模型名称                      # 改为内网可用模型
EMBEDDING_MODEL=公司部署的Embedding模型名称
```

### A.2 启动服务

```bash
# 启动后端服务（开发/部署均可）
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

# 启动Qt客户端
python src/client/main.py
```

### A.3 外网开发 → 内网部署流程

本项目的开发和部署采用**完全分离**的模式：

```
┌─────────────────────────────────────────────────────────────────┐
│                     开发阶段（外网环境）                          │
│                                                                 │
│  pip install 直接拉取依赖  │  API Key 直连调用 LLM/Embedding    │
│  PyCharm/VS Code + Codex   │  GitHub 版本管理                   │
│  PyPI 实时获取最新包        │  OpenAI/GPT/DeepSeek API           │
└──────────────────────────────┬──────────────────────────────────┘
                               │ 开发完成
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   部署阶段（内网环境）                            │
│                                                                 │
│  pip download 准备离线包    │  .env 改 OPENAI_BASE_URL          │
│  PyInstaller 打包 exe       │  指向内网模型网关                  │
│  U盘/共享拷贝到内网服务器    │  数据不出企业内网                  │
└─────────────────────────────────────────────────────────────────┘
```

**核心要点**：整个项目代码完全一致，**仅需修改 `.env` 中的两行配置**即可在开发环境（外网API）和部署环境（内网模型）之间切换。

### A.4 系统部署架构

```mermaid
graph TB
    subgraph Client["🖥️ 客户端层 (Windows)"]
        direction LR
        CL1["Qt桌面客户端<br/>PySide6 GUI"]
        CL2["HTTP Client<br/>API调用"]
        CL3["WebSocket Client<br/>实时推送"]
    end

    subgraph Gateway["🌐 接入层"]
        GW1["Nginx / 直连<br/>反向代理(可选)"]
    end

    subgraph Backend["⚙️ 后端服务层 (FastAPI)"]
        direction LR
        SV1["REST API<br/>对话/设备/生产/BOM/库存/轨迹"]
        SV2["WebSocket Server<br/>metrics/alert/trace"]
        SV3["Agent服务<br/>LangGraph Supervisor"]
        SV4["RAG服务<br/>Chroma + BM25"]
    end

    subgraph Model["🧠 模型层"]
        MT1["LLM API<br/>OpenAI兼容接口<br/>外网开发直连/内网部署切换"]
        MT2["Embedding API<br/>向量化编码"]
    end

    subgraph Store["💾 数据存储层"]
        direction LR
        ST1[("SQLite<br/>业务数据<br/>工单/BOM/库存")]
        ST2[("ChromaDB<br/>向量索引<br/>工艺知识库")]
        ST3[("文件系统<br/>原始文档<br/>PDF/Word/Excel")]
    end

    subgraph Ops["🔧 运维与交付"]
        direction LR
        OP1["PyInstaller<br/>Windows exe打包"]
        OP2["pip download<br/>内网离线部署包"]
        OP3["外网开发 → 内网部署<br/>仅改 .env 两行配置"]
    end

    Client -->|"HTTP :8000"| Gateway
    Gateway --> Backend
    SV3 -->|"API Key"| Model
    SV4 -->|"API Key"| MT2
    SV1 -->|"SQLAlchemy"| ST1
    SV4 -->|"ChromaDB Client"| ST2
    SV4 -->|"文档读取"| ST3
    SV2 -->|"原生WS"| CL3

    classDef cliStyle fill:#1a1a2e,stroke:#e94560,color:#eee
    classDef gwStyle fill:#16213e,stroke:#0f3460,color:#eee
    classDef svcStyle fill:#0f3460,stroke:#533483,color:#eee
    classDef modelStyle fill:#1a1a2e,stroke:#00b4d8,color:#eee
    classDef dataStyle fill:#16213e,stroke:#e94560,color:#eee
    classDef opsStyle fill:#0f3460,stroke:#00b4d8,color:#eee
    class CL1,CL2,CL3 cliStyle
    class GW1 gwStyle
    class SV1,SV2,SV3,SV4 svcStyle
    class MT1,MT2 modelStyle
    class ST1,ST2,ST3 dataStyle
    class OP1,OP2,OP3 opsStyle
```

---

> **文档状态**：✅ 完整版，包含全部功能模块、技术选型、Python包清单、开发计划和面试准备
>
> **下一步**：确认文档后，可从 **第一周Day 1** 开始——搭建Python环境、安装依赖、测试LLM接口连通性。
