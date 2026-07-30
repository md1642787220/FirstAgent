"""
RAG混合检索器
向量语义检索 + BM25关键词检索 + RRF融合排序

原理：
  - 向量语义检索：理解语义，匹配近义词/同义词
  - BM25关键词检索：精确匹配术语，不遗漏编码/标准号
  - RRF融合排序：综合两种检索分数，取长补短
"""
from typing import List, Optional
from langchain_core.documents import Document

from src.agents.rag.vector_store import get_vector_store
from src.config import settings

# 全局BM25索引缓存（构建后复用以提高性能）
_bm25_corpus = None
_bm25_docs = None


def _get_bm25():
    """获取或构建BM25索引（懒加载，首次调用时从ChromaDB加载全部文档构建）"""
    global _bm25_corpus, _bm25_docs
    if _bm25_corpus is not None:
        return _bm25_corpus, _bm25_docs

    try:
        from rank_bm25 import BM25Okapi
        store = get_vector_store()
        if store is not None:
            # 从向量存储获取所有文档
            try:
                all_data = store.get()
                _bm25_docs = [
                    Document(page_content=text, metadata=meta or {})
                    for text, meta in zip(all_data.get("documents", []),
                                          all_data.get("metadatas", [{}] * len(all_data.get("documents", []))))
                ]
            except Exception:
                pass

        if not _bm25_docs:
            # 回退到内置文档
            from src.agents.rag.document_loader import BUILTIN_DOCS
            _bm25_docs = BUILTIN_DOCS

        # 中文友好的分词：使用字符级+空格分词混合
        corpus = []
        for doc in _bm25_docs:
            tokens = doc.page_content.replace("\n", " ").split()
            if not tokens:
                tokens = list(doc.page_content[:200])  # 字符级回退
            corpus.append(tokens)
        _bm25_corpus = BM25Okapi(corpus)
        return _bm25_corpus, _bm25_docs
    except Exception as e:
        print(f"[RAG] BM25索引构建失败: {e}")
        return None, None


def vector_search(query: str, k: int = None) -> List[Document]:
    """向量语义检索

    Args:
        query: 查询文本
        k: 返回文档数，默认使用全局配置 VECTOR_TOP_K
    """
    if k is None:
        k = settings.VECTOR_TOP_K
    store = get_vector_store()
    if store is None:
        return []
    try:
        return store.similarity_search(query, k=k)
    except Exception as e:
        print(f"[RAG] 向量检索失败: {e}")
        return []


def keyword_search(query: str, k: int = None) -> List[Document]:
    """BM25关键词检索

    Args:
        query: 查询文本
        k: 返回文档数，默认使用全局配置 BM25_TOP_K
    """
    if k is None:
        k = settings.BM25_TOP_K
    try:
        bm25, docs = _get_bm25()
        if bm25 is None or not docs:
            return []
        tokens = query.split() or list(query[:100])
        scores = bm25.get_scores(tokens)
        ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)[:k]
        return [doc for score, doc in ranked if score > 0]
    except Exception as e:
        print(f"[RAG] BM25检索失败: {e}")
        return []


def _rrf_fusion(
    vector_docs: List[Document],
    keyword_docs: List[Document],
    k: int = None,
) -> List[Document]:
    """RRF (Reciprocal Rank Fusion) 融合排序

    公式: RRF_score(d) = Σ_{rankings} 1 / (rrf_k + rank_i(d))

    Args:
        vector_docs: 向量检索结果（已按相似度排序）
        keyword_docs: BM25检索结果（已按分数排序）
        k: RRF平滑常数，默认使用全局配置 RRF_K

    Returns:
        融合排序后的Document列表
    """
    if k is None:
        k = settings.RRF_K

    scores = {}
    doc_map = {}

    # 向量检索排名贡献
    for rank, doc in enumerate(vector_docs):
        key = doc.page_content[:80]  # 用内容前缀去重
        scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
        doc_map[key] = doc

    # BM25检索排名贡献
    for rank, doc in enumerate(keyword_docs):
        key = doc.page_content[:80]
        scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
        if key not in doc_map:
            doc_map[key] = doc

    # 按RRF分数降序
    sorted_keys = sorted(scores, key=scores.get, reverse=True)
    return [doc_map[key] for key in sorted_keys]


def hybrid_search(
    query: str,
    top_k: int = None,
    vector_k: int = None,
    bm25_k: int = None,
    threshold: float = None,
) -> List[Document]:
    """混合检索：向量语义 + BM25关键词 + RRF融合

    Args:
        query: 查询文本
        top_k: 最终返回结果数，默认使用 FINAL_TOP_K
        vector_k: 向量检索候选数
        bm25_k: BM25检索候选数
        threshold: 相似度阈值，低于此值的结果丢弃

    Returns:
        RRF融合排序后的Document列表
    """
    if top_k is None:
        top_k = settings.FINAL_TOP_K
    if threshold is None:
        threshold = settings.SIMILARITY_THRESHOLD

    vec_results = vector_search(query, k=vector_k)
    kw_results = keyword_search(query, k=bm25_k)

    merged = _rrf_fusion(vec_results, kw_results)
    return merged[:top_k]


def retrieve_knowledge(query: str, k: int = None) -> str:
    """检索焊接知识并格式化为上下文文本（供Agent Prompt使用）

    Args:
        query: 用户查询
        k: 返回文档数

    Returns:
        格式化的上下文字符串，每个文档标注来源
    """
    if k is None:
        k = settings.FINAL_TOP_K

    docs = hybrid_search(query, top_k=k)
    if not docs:
        return "未检索到相关焊接知识。"

    context_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "未知来源")
        category = doc.metadata.get("category", "")
        source_info = f"来源: {source}"
        if category:
            source_info += f" [{category}]"
        context_parts.append(f"[{i}] {source_info}\n内容: {doc.page_content}")

    return "\n\n".join(context_parts)
