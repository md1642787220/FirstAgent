"""
RAG检索器单元测试
测试中文分词、BM25索引、向量检索、RRF融合、查询改写等核心功能
"""
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document

from src.agents.rag.retriever import (
    _tokenize_chinese,
    _expand_query,
    vector_search,
    keyword_search,
    _rrf_fusion,
    hybrid_search,
    hybrid_search_debug,
    _get_bm25,
    retrieve_knowledge,
)


class TestChineseTokenization:
    """中文分词功能测试"""

    def test_basic_chinese_tokenization(self):
        """基本中文分词：应返回词列表"""
        text = "焊接工艺参数推荐"
        tokens = _tokenize_chinese(text)
        assert isinstance(tokens, list), "应返回列表"
        assert len(tokens) > 0, "不应返回空列表"

    def test_mixed_chinese_english(self):
        """中英文混合文本分词"""
        text = "Q235钢材CO2焊接工艺"
        tokens = _tokenize_chinese(text)
        # 应包含英文和中文token
        has_chinese = any('\u4e00' <= c <= '\u9fff' for t in tokens for c in t)
        has_ascii = any(t.isascii() for t in tokens if len(t) > 1)
        assert has_chinese or has_ascii, "应正确处理中英文混合"

    def test_empty_text_fallback(self):
        """空文本或特殊字符应回退到字符级"""
        tokens = _tokenize_chinese("")
        assert isinstance(tokens, list), "空输入应返回列表"

    def test_jieba_installed(self):
        """jieba可用时应使用jieba分词（更精确）"""
        try:
            import jieba
            text = "焊接气孔缺陷诊断"
            tokens = _tokenize_chinese(text)
            # jieba应能识别"焊接"、"气孔"、"缺陷"、"诊断"等词汇
            assert len(tokens) >= 2, "jieba分词结果应包含多个词"
        except ImportError:
            pytest.skip("jieba未安装，跳过此测试")


class TestQueryExpansion:
    """查询语义扩展测试"""

    def test_expand_welding_term(self):
        """焊接术语应被扩展"""
        query = "焊接气孔缺陷"
        expanded = _expand_query(query)
        assert "焊接" in expanded or "熔接" in expanded, "焊接术语应被扩展"

    def test_expand_crack_synonyms(self):
        """裂纹同义词扩展"""
        query = "焊接裂纹原因"
        expanded = _expand_query(query)
        # 应包含原始查询和可能的同义词
        assert len(expanded) >= len(query), "扩展后长度不应缩短"

    def test_no_expansion_for_unknown(self):
        """无已知术语时不应改变原查询"""
        query = "某某某未知术语"
        expanded = _expand_query(query)
        # 至少应保留原始查询
        assert query in expanded, "原始查询应保留在扩展结果中"


class TestRRFFusion:
    """RRF融合排序测试"""

    def test_basic_fusion(self):
        """基本融合：两个列表的结果应合并"""
        doc1 = Document(page_content="向量检索结果A", metadata={"source": "vector"})
        doc2 = Document(page_content="关键词检索结果B", metadata={"source": "bm25"})
        fused = _rrf_fusion([doc1], [doc2])
        assert len(fused) == 2, "融合后应包含所有不重复文档"

    def test_deduplication(self):
        """去重：相同内容不应重复出现"""
        doc = Document(page_content="相同内容", metadata={"source": "test"})
        fused = _rrf_fusion([doc], [doc])
        assert len(fused) == 1, "重复文档应被去重"

    def test_rrf_score_in_metadata(self):
        """融合结果应包含_rrf_score元数据"""
        doc1 = Document(page_content="结果1", metadata={})
        doc2 = Document(page_content="结果2", metadata={})
        fused = _rrf_fusion([doc1, doc2], [])
        for doc in fused:
            assert "_rrf_score" in doc.metadata, "每个结果应有_rrf_score字段"
            assert isinstance(doc.metadata["_rrf_score"], float), "_rrf_score应为浮点数"

    def test_ranking_order(self):
        """排名靠前的文档应有更高的RRF分数"""
        doc_first = Document(page_content="排名第一的文档")
        doc_second = Document(page_content="排名第二的文档")
        fused = _rrf_fusion([doc_first, doc_second], [])
        if len(fused) >= 2:
            assert fused[0].metadata["_rrf_score"] >= fused[1].metadata["_rrf_score"], \
                "排名靠前的文档RRF分数应更高或相等"


class TestHybridSearch:
    """混合检索集成测试"""

    @patch('src.agents.rag.retriever.get_vector_store')
    def test_hybrid_search_with_mock_vector(self, mock_store):
        """模拟向量存储的混合检索"""
        # 模拟向量存储返回空（无真实ChromaDB）
        mock_store.return_value = None

        # 仅测试BM25部分（使用内置文档构建索引）
        results = hybrid_search("焊接参数", top_k=2)
        # 可能返回空（如果BM25也未初始化）或内置文档匹配结果
        assert isinstance(results, list), "应返回列表"

    @patch('src.agents.rag.retriever.get_vector_store')
    def test_hybrid_search_debug_structure(self, mock_store):
        """调试接口应返回完整结构"""
        mock_store.return_value = None
        debug_info = hybrid_search_debug("测试查询", top_k=2)

        assert "query" in debug_info, "缺少query字段"
        assert "vector_results" in debug_info, "缺少vector_results字段"
        assert "bm25_results" in debug_info, "缺少bm25_results字段"
        assert "fused_results" in debug_info, "缺少fused_results字段"
        assert "total_latency_ms" in debug_info, "缺少total_latency_ms字段"
        assert isinstance(debug_info["total_latency_ms"], float), "latency应为浮点数"

    def test_retrieve_knowledge_format(self):
        """retrieve_knowledge应返回格式化字符串"""
        context = retrieve_knowledge("焊接工艺", k=2)
        assert isinstance(context, str), "应返回字符串"
        # 可能为"未检索到相关焊接知识。"或实际内容
        assert len(context) > 0, "不应返回空字符串"


class TestBM25Index:
    """BM25索引构建与检索测试"""

    def test_bm25_index_builds_from_builtin(self):
        """BM25索引应能从内置文档构建"""
        # 清除缓存强制重建
        import src.agents.rag.retriever as retriever_module
        retriever_module._bm25_corpus = None
        retriever_module._bm25_docs = None

        bm25, docs = _get_bm25()
        if bm25 is not None:
            assert len(docs) > 0, "BM25索引构建后应有文档"
        else:
            pytest.skip("BM25索引构建失败（可能缺少依赖）")

    def test_keyword_search_returns_list(self):
        """关键词检索应返回Document列表"""
        results = keyword_search("焊接", k=3)
        assert isinstance(results, list), "应返回列表"
        for doc in results:
            assert isinstance(doc, Document), "每个结果应为Document对象"


class TestVectorSearch:
    """向量检索测试"""

    @patch('src.agents.rag.retriever.get_vector_store')
    def test_vector_search_no_store(self, mock_store):
        """无向量存储时应返回空列表"""
        mock_store.return_value = None
        results = vector_search("测试查询")
        assert results == [], "无向量存储时应返回空列表"

    @patch('src.agents.rag.retriever.get_vector_store')
    def test_vector_search_with_mock(self, mock_store):
        """模拟向量存储的检索"""
        mock_store_instance = MagicMock()
        mock_store_instance.similarity_search.return_value = [
            Document(page_content="模拟检索结果", metadata={"source": "mock"})
        ]
        mock_store.return_value = mock_store_instance

        results = vector_search("测试查询", k=2)
        assert len(results) == 1, "应返回模拟的结果"
        assert "模拟检索结果" in results[0].page_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
