"""
Chroma向量存储管理
文档向量化、存储、持久化
"""
from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from src.config import settings


def get_embeddings() -> Embeddings:
    """获取Embedding模型实例。
    优先使用公司内网模型，失败则降级使用本地FakeEmbedding。
    """
    try:
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            model=settings.EMBEDDING_MODEL,
        )
    except Exception as e:
        print(f"[RAG] OpenAI Embedding不可用({e})，使用本地Fallback Embedding")
        return _FallbackEmbedding()


class _FallbackEmbedding(Embeddings):
    """本地兜底Embedding（基于关键词哈希，仅用于无网络环境测试）"""

    def _embed(self, text: str) -> list[float]:
        """简单关键词哈希嵌入（128维）"""
        import hashlib
        vec = [0.0] * 128
        words = text.replace("\n", " ").split()
        for word in words:
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            vec[h % 128] += 1.0
        # 归一化
        magnitude = sum(v * v for v in vec) ** 0.5
        if magnitude > 0:
            vec = [v / magnitude for v in vec]
        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)


# 全局向量存储实例
_vector_store = None


def get_vector_store() -> Optional[object]:
    """获取或创建Chroma向量存储（单例）"""
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    try:
        from langchain_chroma import Chroma
        embeddings = get_embeddings()
        _vector_store = Chroma(
            collection_name="welding_knowledge",
            embedding_function=embeddings,
            persist_directory=settings.CHROMA_PERSIST_DIR,
        )
        print(f"[RAG] Chroma向量存储已初始化: {settings.CHROMA_PERSIST_DIR}")
        return _vector_store
    except Exception as e:
        print(f"[RAG] Chroma初始化失败: {e}")
        return None


def build_vector_store(documents: List[Document]) -> bool:
    """构建向量存储（将文档写入Chroma）"""
    try:
        from langchain_chroma import Chroma
        embeddings = get_embeddings()
        store = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            collection_name="welding_knowledge",
            persist_directory=settings.CHROMA_PERSIST_DIR,
        )
        global _vector_store
        _vector_store = store
        print(f"[RAG] 向量存储构建完成，已索引 {len(documents)} 个文档块")
        return True
    except Exception as e:
        print(f"[RAG] 向量存储构建失败: {e}")
        return False


def init_knowledge_base():
    """初始化知识库（多源加载文档 -> 分块 -> 向量化存储）

    支持从文件系统、数据库、API 三源同时加载。
    如果配置了 data_sources.yml，优先使用配置文件。
    """
    import json
    import os

    # 优先使用YAML配置文件
    config_path = os.getenv("DATA_SOURCES_CONFIG", "")
    if config_path and os.path.exists(config_path):
        try:
            from src.agents.rag.document_loader import prepare_from_config
            documents = prepare_from_config(config_path)
            if documents:
                chunks = split_documents(documents)
                return build_vector_store(chunks)
        except Exception as e:
            print(f"[RAG] 从YAML配置加载失败: {e}，回退到默认模式")

    # 尝试使用多源加载（环境变量配置）
    from src.agents.rag.document_loader import prepare_multi_source_documents
    from src.config import settings

    try:
        import json
        db_configs = json.loads(settings.DATA_SOURCE_DBS) if settings.DATA_SOURCE_DBS else None
        api_configs = json.loads(settings.DATA_SOURCE_APIS) if settings.DATA_SOURCE_APIS else None
    except json.JSONDecodeError:
        db_configs = None
        api_configs = None

    documents = prepare_multi_source_documents(
        docs_dir=settings.KNOWLEDGE_DOCS_DIR,
        db_configs=db_configs,
        api_configs=api_configs,
        include_builtin=True,
    )

    # 分块
    from src.agents.rag.document_loader import split_documents
    chunks = split_documents(
        documents,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    return build_vector_store(chunks)
