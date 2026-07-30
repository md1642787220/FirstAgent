"""
全局配置模块
读取 .env 环境变量，提供全局配置访问
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 .env 文件
load_dotenv(BASE_DIR / ".env")


class Settings:
    """应用全局配置"""

    # ===== LLM 模型配置 =====
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # ===== 应用配置 =====
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # ===== 数据库配置 =====
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", "data/welding_agent.db")
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / SQLITE_PATH}"

    # ===== 向量数据库配置 =====
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / os.getenv("CHROMA_PERSIST_DIR", "data/chroma_db"))
    KNOWLEDGE_DOCS_DIR: str = str(BASE_DIR / os.getenv("KNOWLEDGE_DOCS_DIR", "data/knowledge_docs"))

    # ===== RAG检索配置 =====
    VECTOR_TOP_K: int = int(os.getenv("VECTOR_TOP_K", "5"))          # 向量检索候选数
    BM25_TOP_K: int = int(os.getenv("BM25_TOP_K", "5"))             # BM25检索候选数
    FINAL_TOP_K: int = int(os.getenv("FINAL_TOP_K", "3"))           # RRF融合最终结果数
    RRF_K: int = int(os.getenv("RRF_K", "60"))                      # RRF平滑常数
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))            # 文本分块大小
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))       # 分块重叠大小

    # ===== 多源数据源配置 =====
    # 数据库数据源（JSON格式，环境变量配置）
    # 示例: DATA_SOURCE_DBS='[{"url":"mysql+pymysql://...", "tables":[{"name":"records"}]}]'
    DATA_SOURCE_DBS: str = os.getenv("DATA_SOURCE_DBS", "[]")

    # API数据源（JSON格式）
    DATA_SOURCE_APIS: str = os.getenv("DATA_SOURCE_APIS", "[]")

    # 数据源YAML配置文件路径（如果配置了此文件，将优先使用）
    DATA_SOURCES_CONFIG: str = os.getenv(
        "DATA_SOURCES_CONFIG",
        str(BASE_DIR / "data_sources.yml"),
    )

    # ===== LangSmith 追踪 =====
    LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "welding-agent-platform")

    # ===== 设备监控参数正常范围 =====
    DEVICE_METRICS_RANGE = {
        "current": {"min": 100, "max": 300, "unit": "A", "label": "焊接电流"},
        "voltage": {"min": 20, "max": 35, "unit": "V", "label": "焊接电压"},
        "speed": {"min": 300, "max": 800, "unit": "mm/min", "label": "焊接速度"},
        "wire_speed": {"min": 3, "max": 15, "unit": "m/min", "label": "送丝速度"},
        "gas_flow": {"min": 15, "max": 25, "unit": "L/min", "label": "气体流量"},
        "temperature": {"min": 0, "max": 85, "unit": "℃", "label": "设备温度"},
        "vibration": {"min": 0, "max": 0.5, "unit": "m/s²", "label": "设备振动"},
    }

    @property
    def llm_kwargs(self) -> dict:
        """LLM 调用参数"""
        return {
            "api_key": self.OPENAI_API_KEY,
            "base_url": self.OPENAI_BASE_URL,
            "model": self.MODEL_NAME,
        }


settings = Settings()

# 确保数据目录存在
os.makedirs(BASE_DIR / "data", exist_ok=True)
os.makedirs(BASE_DIR / "data" / "knowledge_docs", exist_ok=True)
os.makedirs(BASE_DIR / "data" / "chroma_db", exist_ok=True)
