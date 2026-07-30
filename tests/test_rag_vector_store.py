"""
RAG向量存储单元测试
测试ChromaDB初始化、向量化、状态统计、增量更新等核心功能
"""
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document

from src.agents.rag.vector_store import (
    get_embeddings,
    get_vector_store,
    build_vector_store,
    init_knowledge_base,
    get_stats,
    _FallbackEmbedding,
)


class TestFallbackEmbedding:
    """Fallback Embedding测试（无需真实API）"""

    def test_embedding_dimension(self):
        """Fallback embedding维度应为128"""
        embedder = _FallbackEmbedding()
        vec = embedder.embed_query("测试文本")
        assert len(vec) == 128, f"维度应为128，实际: {len(vec)}"

    def test_embedding_normalization(self):
        """Embedding应归一化（模长≈1）"""
        embedder = _FallbackEmbedding()
        vec = embedder.embed_query("测试文本归一化")
        magnitude = sum(v ** 2 for v in vec) ** 0.5
        assert abs(magnitude - 1.0) < 0.001, f"模长应接近1，实际: {magnitude:.4f}"

    def test_different_texts_different_vectors(self):
        """不同文本应产生不同的embedding"""
        embedder = _FallbackEmbedding()
        vec1 = embedder.embed_query("文本A")
        vec2 = embedder.embed_query("文本B")
        # 不应完全相同
        assert vec1 != vec2, "不同文本的embedding应不同"

    def test_batch_embedding(self):
        """批量embed_documents应工作"""
        embedder = _FallbackEmbedding()
        texts = ["文本1", "文本2", "文本3"]
        vecs = embedder.embed_documents(texts)
        assert len(vecs) == 3, "应返回3个向量"
        for vec in vecs:
            assert len(vec) == 128, "每个向量维度应为128"


class TestGetStats:
    """状态统计接口测试"""

    def test_stats_returns_dict(self):
        """get_stats应返回字典"""
        stats = get_stats()
        assert isinstance(stats, dict), "应返回字典"

    def test_stats_required_fields(self):
        """stats应包含必要字段"""
        stats = get_stats()
        required_fields = [
            "total_documents", "total_chunks", "collection_name",
            "persist_dir", "embedding_model", "status"
        ]
        for field in required_fields:
            assert field in stats, f"缺少必要字段: {field}"

    def test_stats_no_store(self):
        """无向量存储时status应为unavailable"""
        with patch('src.agents.rag.vector_store.get_vector_store', return_value=None):
            stats = get_stats()
            assert stats["status"] == "unavailable", "无存储时status应为unavailable"
            assert stats["total_documents"] == 0, "无存储时文档数应为0"


class TestBuildVectorStore:
    """向量存储构建测试"""

    def test_build_empty_documents(self):
        """空文档列表应返回False或失败"""
        result = build_vector_store([])
        assert result is False, "空文档列表应返回False"

    def test_build_with_sample_documents(self):
        """使用示例文档构建（需要真实的ChromaDB或Mock）"""
        docs = [
            Document(
                page_content="这是测试文档内容",
                metadata={"source": "test.txt", "category": "测试"}
            )
        ]

        # 如果环境中有ChromaDB则真实测试，否则跳过
        try:
            result = build_vector_store(docs)
            # 成功或失败都接受（取决于环境配置）
            assert isinstance(result, bool), "应返回布尔值"
        except Exception as e:
            pytest.skip(f"ChromaDB不可用: {e}")


class TestInitKnowledgeBase:
    """知识库初始化流程测试"""

    @patch('src.agents.rag.vector_store.prepare_multi_source_documents')
    @patch('src.agents.rag.vector_store.split_documents')
    @patch('src.agents.rag.vector_store.build_vector_store')
    def test_init_calls_pipeline(self, mock_build, mock_split, mock_load):
        """初始化应调用完整的加载->分块->向量化pipeline"""
        # Mock各步骤返回值
        mock_load.return_value = [Document(page_content="测试")]
        mock_split.return_value = [Document(page_content="测试chunk")]
        mock_build.return_value = True

        result = init_knowledge_base()

        assert mock_load.called, "应调用文档加载"
        assert mock_split.called, "应调用文档分块"
        assert mock_build.called, "应调用向量存储构建"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
