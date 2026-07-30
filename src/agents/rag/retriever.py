"""
RAG混合检索器
向量语义检索 + BM25关键词检索(jieba中文分词) + RRF融合排序

原理：
  - 向量语义检索：理解语义，匹配近义词/同义词
  - BM25关键词检索：精确匹配术语，使用jieba中文分词提升召回率
  - RRF融合排序：综合两种检索分数，取长补短
  - 查询改写（可选）：同义词扩展 + 焊接术语标准化
"""
from typing import List, Optional, Dict
from langchain_core.documents import Document

from src.agents.rag.vector_store import get_vector_store
from src.config import settings


# ==================== 中文分词工具 ====================

def _tokenize_chinese(text: str) -> List[str]:
    """中文文本分词：jieba精确模式 + 英文原样保留 + 数字/单位保持

    Args:
        text: 待分词文本

    Returns:
        分词结果列表
    """
    try:
        import jieba
        # 使用jieba精确模式分词，过滤单字符（除非是数字/英文）
        tokens = []
        for word in jieba.lcut(text):
            if len(word) > 1 or word.isascii():  # 保留多字词和英文/数字
                tokens.append(word)
        return tokens if tokens else list(text)  # 空结果回退到字符级
    except ImportError:
        # jieba未安装时回退到空格+字符级混合
        return text.replace("\n", " ").split() or list(text[:200])


# ==================== 查询改写（可选） ====================

# 焊接领域常见同义词映射表
_WELDING_SYNONYMS: Dict[str, List[str]] = {
    "焊接": ["熔接", "钎焊"],
    "焊缝": ["焊道", "焊接接头"],
    "气孔": ["气泡", "气眼"],
    "裂纹": ["裂缝", "开裂"],
    "夹渣": ["夹杂物", "焊渣残留"],
    "未熔合": ["未融合", "结合不良"],
    "未焊透": ["未熔透", "根部缺陷"],
    "咬边": ["咬肉", "边缘切割"],
    "烧穿": ["过烧", "熔穿"],
    "变形": ["翘曲", "扭曲"],
    "电流": ["安培数", "焊接电流"],
    "电压": ["电弧电压", "弧压"],
    "速度": ["焊接速率", "行进速度"],
    "气体": ["保护气体", " shielding gas"],
    "钨极": ["钨棒", "非消耗电极"],
    "焊丝": ["填充金属", "焊料"],
    "不锈钢": ["304", "316", "奥氏体钢"],
    "铝合金": ["铝材", "5系铝", "6系铝"],
}


def _expand_query(query: str) -> str:
    """查询语义扩展：用同义词替换原始术语以扩大召回范围

    Args:
        query: 原始查询文本

    Returns:
        扩展后的查询文本（原始词 + 同义词拼接）
    """
    expanded_parts = [query]  # 始终保留原始查询
    for term, synonyms in _WELDING_SYNONYMS.items():
        if term in query:
            # 找到同义词并追加
            valid_synonyms = [s for s in synonyms if s not in query]
            if valid_synonyms:
                expanded_parts.append(" ".join(valid_synonyms))
    return " ".join(expanded_parts) if len(expanded_parts) > 1 else query

# 全局BM25索引缓存（构建后复用以提高性能）
_bm25_corpus = None
_bm25_docs = None

# 全局Cross-Encoder重排序模型缓存（懒加载）
_reranker = None


def _get_reranker():
    """获取或创建 Cross-Encoder 重排序模型实例（懒加载单例）

    Returns:
        CrossEncoder 实例，如果加载失败则返回 None
    """
    global _reranker
    if _reranker is not None:
        return _reranker

    try:
        from sentence_transformers import CrossEncoder

        # 支持通过环境变量自定义模型（默认使用 ms-marco-MiniLM-L-6-v2）
        model_name = getattr(settings, 'RERANKER_MODEL', None) or 'cross-encoder/ms-marco-MiniLM-L-6-v2'

        _reranker = CrossEncoder(model_name)
        print(f"[RAG] ✅ Cross-Encoder 重排序模型已加载: {model_name}")
        return _reranker
    except Exception as e:
        print(f"[RAG] ⚠️ Cross-Encoder 模型加载失败({e})，禁用重排序功能")
        _reranker = False  # 标记为已尝试加载但失败，避免重复尝试
        return None


def _get_bm25():
    """获取或构建BM25索引（懒加载，使用jieba中文分词构建）"""
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

        # 使用jieba中文分词构建BM25语料库
        corpus = [_tokenize_chinese(doc.page_content) for doc in _bm25_docs]
        _bm25_corpus = BM25Okapi(corpus)
        print(f"[RAG] BM25索引已构建（jieba分词），文档数: {len(_bm25_docs)}")
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
    """BM25关键词检索（使用jieba中文分词）

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
        tokens = _tokenize_chinese(query)  # 使用jieba中文分词
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
    """RRF (Reciprocal Rank Fusion) 融合排序（增强版，保留分数元数据）

    公式: RRF_score(d) = Σ_{rankings} 1 / (rrf_k + rank_i(d))

    Args:
        vector_docs: 向量检索结果（已按相似度排序）
        keyword_docs: BM25检索结果（已按分数排序）
        k: RRF平滑常数，默认使用全局配置 RRF_K

    Returns:
        融合排序后的Document列表（metadata中包含 _rrf_score 字段）
    """
    if k is None:
        k = settings.RRF_K

    scores: Dict[str, float] = {}
    doc_map: Dict[str, Document] = {}

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

    # 按RRF分数降序，并将分数写入metadata
    sorted_keys = sorted(scores, key=scores.get, reverse=True)
    result = []
    for key in sorted_keys:
        doc = doc_map[key].copy()
        # 将RRF分数写入metadata供调试使用
        doc.metadata["_rrf_score"] = round(scores[key], 6)
        result.append(doc)
    return result


def _rerank_with_cross_encoder(
    query: str,
    documents: List[Document],
    top_k: int = None,
) -> List[Document]:
    """使用 Cross-Encoder 对检索结果进行精细重排序

    Cross-Encoder 能同时看到 query 和 document，比 Bi-Encoder（向量检索）更擅长判断相关性。
    通常用于 RRF 融合后的精排阶段。

    Args:
        query: 原始查询文本
        documents: 待重排序的文档列表（通常是 RRF 融合后的 top-N 结果）
        top_k: 重排序后返回的文档数

    Returns:
        按 Cross-Encoder 分数降序排列的 Document 列表（metadata 中包含 _ce_score 字段）
    """
    if not documents:
        return []

    reranker = _get_reranker()
    if reranker is None:
        # 模型不可用，直接返回原结果
        return documents

    if top_k is None:
        top_k = len(documents)

    # 构造 (query, document) 对
    pairs = [(query, doc.page_content) for doc in documents]

    # 预测相关性分数
    try:
        import numpy as np
        scores = reranker.predict(pairs)

        # 如果分数是一维数组（单个分数），直接使用
        if len(scores.shape) == 1:
            scores = scores.tolist()
        else:
            # 如果是二维数组（有些模型返回 [not_relevant, relevant]），取第二列
            scores = scores[:, 1].tolist() if scores.shape[1] > 1 else scores[:, 0].tolist()

        # 按分数降序排列
        ranked = sorted(
            zip(scores, documents),
            key=lambda x: x[0],
            reverse=True
        )[:top_k]

        # 将 Cross-Encoder 分数写入 metadata
        result = []
        for score, doc in ranked:
            doc_with_score = doc.copy()
            doc_with_score.metadata["_ce_score"] = round(float(score), 4)
            result.append(doc_with_score)

        print(f"[RAG] 🎯 Cross-Encoder 重排序完成: {len(documents)} → {len(result)} 篇")
        return result

    except Exception as e:
        print(f"[RAG] ⚠️ Cross-Encoder 重排序失败({e})，返回原始顺序")
        return documents[:top_k]


def hybrid_search(
    query: str,
    top_k: int = None,
    vector_k: int = None,
    bm25_k: int = None,
    threshold: float = None,
    use_query_expansion: bool = False,
    use_rerank: bool = False,
) -> List[Document]:
    """混合检索：向量语义 + BM25关键词(jieba分词) + RRF融合 + 可选Cross-Encoder重排序

    Args:
        query: 查询文本
        top_k: 最终返回结果数，默认使用 FINAL_TOP_K
        vector_k: 向量检索候选数
        bm25_k: BM25检索候选数
        threshold: 相似度阈值，低于此值的结果丢弃
        use_query_expansion: 是否启用查询同义词扩展（默认关闭）
        use_rerank: 是否启用 Cross-Encoder 重排序（默认关闭，推荐开启以提升精度）

    Returns:
        融合排序后的Document列表（含_rrf_score元数据，如启用重排序则还包含_ce_score）
    """
    if top_k is None:
        top_k = settings.FINAL_TOP_K
    if threshold is None:
        threshold = settings.SIMILARITY_THRESHOLD

    # 可选：查询语义扩展
    search_query = _expand_query(query) if use_query_expansion else query

    vec_results = vector_search(search_query, k=vector_k)
    kw_results = keyword_search(search_query, k=bm25_k)

    merged = _rrf_fusion(vec_results, kw_results)

    # 可选：Cross-Encoder 精排（对 RRF 融合后的 top-2*top_k 候选进行重排序）
    if use_rerank:
        candidate_k = min(len(merged), top_k * 2)  # 取更多候选进行重排
        return _rerank_with_cross_encoder(query, merged[:candidate_k], top_k=top_k)

    return merged[:top_k]


def hybrid_search_debug(
    query: str,
    top_k: int = None,
    vector_k: int = None,
    bm25_k: int = None,
    use_query_expansion: bool = False,
    use_rerank: bool = False,
) -> Dict:
    """混合检索调试版本：返回三路中间结果及分数详情

    用于API调试接口 /api/knowledge/search-debug

    Args:
        query: 查询文本
        top_k: 最终返回数
        vector_k: 向量检索候选数
        bm25_k: BM25检索候选数
        use_query_expansion: 是否启用查询扩展
        use_rerank: 是否启用 Cross-Encoder 重排序

    Returns:
        包含 vector_results / bm25_results / fused_results / reranked_results(可选) / query_expanded 的字典
    """
    import time
    start_time = time.perf_counter()

    if top_k is None:
        top_k = settings.FINAL_TOP_K

    # 可选：查询扩展
    expanded_query = _expand_query(query) if use_query_expansion else query
    is_expanded = expanded_query != query

    # 三路检索
    vec_results = vector_search(expanded_query, k=vector_k)
    kw_results = keyword_search(expanded_query, k=bm25_k)

    # 为向量结果添加相似度占位（ChromaDB不直接返回分数，用排名代替）
    for rank, doc in enumerate(vec_results):
        doc.metadata["_vector_rank"] = rank + 1

    # 为BM25结果添加原始分数
    try:
        bm25, _ = _get_bm25()
        if bm25:
            tokens = _tokenize_chinese(expanded_query)
            raw_scores = bm25.get_scores(tokens)
            # 构建内容->分数映射
            score_map = {}
            for doc, score in zip(kw_results, [s for s in sorted(raw_scores, reverse=True)[:len(kw_results)]]):
                score_map[doc.page_content[:80]] = score
            for doc in kw_results:
                key = doc.page_content[:80]
                doc.metadata["_bm25_score"] = round(score_map.get(key, 0), 4)
    except Exception:
        pass

    # RRF融合
    fused_results = _rrf_fusion(vec_results, kw_results)[:top_k]

    # 可选：Cross-Encoder 重排序
    reranked_results = None
    if use_rerank:
        candidate_k = min(len(fused_results), top_k * 2)
        reranked_results = _rerank_with_cross_encoder(query, fused_results[:candidate_k], top_k=top_k)

    latency_ms = (time.perf_counter() - start_time) * 1000

    result = {
        "query": query,
        "expanded_query": expanded_query if is_expanded else None,
        "is_expanded": is_expanded,
        "vector_results": vec_results,
        "bm25_results": kw_results,
        "fused_results": fused_results,
        "total_latency_ms": round(latency_ms, 2),
    }

    # 如果启用了重排序，添加重排序结果
    if reranked_results is not None:
        result["reranked_results"] = reranked_results
        result["use_rerank"] = True

    return result


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
