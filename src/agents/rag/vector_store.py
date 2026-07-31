"""
Chroma向量存储管理
文档向量化、存储、持久化
"""
from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from src.config import settings


def get_embeddings() -> Embeddings:
    """获取Embedding模型实例（三级降级策略）。

    策略优先级：
      1. OpenAI API（云端部署，需网络）
      2. 本地 BGE 中文模型（内网/离线环境，推荐）
      3. MD5 哈希 Fallback（仅测试用，无语义能力）

    Returns:
        可用的 Embeddings 实例
    """
    # ===== Level 1: 云端 Embedding API（阿里云百炼 / 其他 OpenAI 兼容接口）=====
    try:
        from langchain_openai import OpenAIEmbeddings
        print(f"[RAG] ✅ 使用云端 Embedding: {settings.EMBEDDING_MODEL} @ {settings.EMBEDDING_BASE_URL}")
        return OpenAIEmbeddings(
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_BASE_URL,
            model=settings.EMBEDDING_MODEL,
            check_embedding_ctx_length=False,  # 修复 DashScope 兼容接口 ctx 长度检查的非标格式报错
            chunk_size=10,                       # 阿里云百炼限制单批≤10条，分批发送
        )
    except Exception as e:
        print(f"[RAG] [WARN] 云端 Embedding 不可用({e})，尝试本地模型...")

    # ===== Level 2: 本地 BGE 中文模型（sentence_transformers）=====
    try:
        from langchain_huggingface import HuggingFaceEmbeddings

        # 支持通过环境变量自定义模型（默认使用 BGE-small-zh-v1.5）
        model_name = getattr(settings, 'LOCAL_EMBEDDING_MODEL', None) or "BAAI/bge-small-zh-v1.5"

        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},  # 可根据硬件改为 'cuda'
            encode_kwargs={'normalize_embeddings': True},
        )
        print(f"[RAG] ✅ 使用本地 Embedding 模型: {model_name}")
        return embeddings
    except Exception as e:
        print(f"[RAG] [WARN] 本地Embedding模型不可用({e})，降级到Fallback...")

    # ===== Level 3: MD5 哈希 Fallback（仅测试）=====
    print("[RAG] [ERROR] 使用 MD5 Fallback Embedding（无语义能力，仅适用于测试！）")
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
            collection_name=settings.COLLECTION_NAME,
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
            collection_name=settings.COLLECTION_NAME,
            persist_directory=settings.CHROMA_PERSIST_DIR,
        )
        global _vector_store
        _vector_store = store
        print(f"[RAG] 向量存储构建完成，已索引 {len(documents)} 个文档块")
        return True
    except Exception as e:
        print(f"[RAG] 向量存储构建失败: {e}")
        return False


def get_stats() -> dict:
    """获取向量存储统计信息（文档数、来源分布等）"""
    store = get_vector_store()
    if store is None:
        return {
            "total_documents": 0,
            "total_chunks": 0,
            "collection_name": settings.COLLECTION_NAME,
            "persist_dir": str(settings.CHROMA_PERSIST_DIR),
            "last_updated": None,
            "embedding_model": settings.EMBEDDING_MODEL,
            "status": "unavailable",
        }

    try:
        # 获取底层Chroma集合
        collection = store._collection
        total_chunks = collection.count()

        # 统计来源分布
        source_dist = {}
        if total_chunks > 0:
            # 获取所有文档的metadata中的source字段
            results = collection.get(include=["metadatas"])
            if results and results.get("metadatas"):
                for meta in results["metadatas"]:
                    source = meta.get("source", "unknown")
                    source_dist[source] = source_dist.get(source, 0) + 1

        return {
            "total_documents": len(source_dist),  # 不同source数量作为文档数近似
            "total_chunks": total_chunks,
            "collection_name": settings.COLLECTION_NAME,
            "persist_dir": str(settings.CHROMA_PERSIST_DIR),
            "last_updated": None,  # ChromaDB不直接提供最后更新时间
            "embedding_model": settings.EMBEDDING_MODEL,
            "status": "ready",
            "source_distribution": source_dist,
        }
    except Exception as e:
        return {
            "total_documents": 0,
            "total_chunks": 0,
            "collection_name": settings.COLLECTION_NAME,
            "persist_dir": str(settings.CHROMA_PERSIST_DIR),
            "last_updated": None,
            "embedding_model": settings.EMBEDDING_MODEL,
            "status": f"error: {e}",
        }


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
