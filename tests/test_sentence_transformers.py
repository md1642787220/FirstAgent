"""
sentence_transformers 集成测试
测试三级降级Embedding策略和Cross-Encoder重排序功能
"""
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document

# ==================== Embedding 三级降级策略测试 ====================


class TestEmbeddingFallbackStrategy:
    """测试 get_embeddings() 的三级降级策略"""

    @patch('src.agents.rag.vector_store.settings')
    def test_level1_openai_priority(self, mock_settings):
        """Level 1: OpenAI API 应优先使用（如果可用）"""
        # 模拟 OpenAI 可用
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.OPENAI_BASE_URL = "https://api.openai.com/v1"
        mock_settings.EMBEDDING_MODEL = "text-embedding-3-small"

        with patch('src.agents.rag.vector_store.OpenAIEmbeddings') as mock_openai:
            mock_instance = MagicMock()
            mock_openai.return_value = mock_instance

            from src.agents.rag.vector_store import get_embeddings
            result = get_embeddings()

            assert result == mock_instance, "应返回OpenAI Embedding实例"
            mock_openai.assert_called_once()

    @patch('src.agents.rag.vector_store.settings')
    def test_level2_local_model_fallback(self, mock_settings):
        """Level 2: OpenAI不可用时应尝试本地BGE模型"""
        mock_settings.OPENAI_API_KEY = "invalid"
        mock_settings.OPENAI_BASE_URL = "https://invalid"
        mock_settings.EMBEDDING_MODEL = "text-embedding-3-small"

        # 模拟 OpenAI 失败，本地模型成功
        with patch('src.agents.rag.vector_store.OpenAIEmbeddings', side_effect=Exception("API error")):
            with patch('src.agents.rag.vector_store.HuggingFaceEmbeddings') as mock_hf:
                mock_instance = MagicMock()
                mock_hf.return_value = mock_instance

                from src.agents.rag.vector_store import get_embeddings
                result = get_embeddings()

                assert result == mock_instance, "应返回HuggingFace Embedding实例"
                mock_hf.assert_called_once()

    @patch('src.agents.rag.vector_store.settings')
    def test_level3_md5_fallback(self, mock_settings):
        """Level 3: 所有模型都不可用时应降级到MD5 Fallback"""
        mock_settings.OPENAI_API_KEY = "invalid"
        mock_settings.OPENAI_BASE_URL = "https://invalid"
        mock_settings.EMBEDDING_MODEL = "text-embedding-3-small"

        # 模拟所有模型都失败
        with patch('src.agents.rag.vector_store.OpenAIEmbeddings', side_effect=Exception("API error")):
            with patch('src.agents.rag.vector_store.HuggingFaceEmbeddings', side_effect=Exception("Model error")):
                from src.agents.rag.vector_store import get_embeddings, _FallbackEmbedding
                result = get_embeddings()

                assert isinstance(result, _FallbackEmbedding), "应返回Fallback Embedding"

    def test_fallback_embedding_still_works(self):
        """Fallback Embedding 应仍能正常工作（向后兼容）"""
        from src.agents.rag.vector_store import _FallbackEmbedding

        embedder = _FallbackEmbedding()

        # 测试基本功能
        vec = embedder.embed_query("焊接工艺参数")
        assert len(vec) == 128, "维度应为128"
        assert all(isinstance(v, float) for v in vec), "所有值应为浮点数"

        # 测试批量嵌入
        texts = ["文本1", "文本2", "文本3"]
        vecs = embedder.embed_documents(texts)
        assert len(vecs) == 3, "应返回3个向量"


class TestLocalEmbeddingConfiguration:
    """测试本地Embedding模型的配置灵活性"""

    @patch('src.agents.rag.vector_store.settings')
    def test_custom_local_model_via_settings(self, mock_settings):
        """应支持通过 settings.LOCAL_EMBEDDING_MODEL 自定义模型"""
        # 模拟 OpenAI 不可用
        mock_settings.OPENAI_API_KEY = "invalid"
        mock_settings.OPENAI_BASE_URL = "https://invalid"
        mock_settings.EMBEDDING_MODEL = "text-embedding-3-small"
        # 设置自定义本地模型
        mock_settings.LOCAL_EMBEDDING_MODEL = "BAAI/bge-base-zh-v1.5"  # 更大的模型

        with patch('src.agents.rag.vector_store.OpenAIEmbeddings', side_effect=Exception("fail")):
            with patch('src.agents.rag.vector_store.HuggingFaceEmbeddings') as mock_hf:
                from src.agents.rag.vector_store import get_embeddings
                get_embeddings()

                # 验证使用了自定义模型名
                call_args = mock_hf.call_args
                assert call_args[1]['model_name'] == "BAAI/bge-base-zh-v1.5", \
                    f"应使用自定义模型名，实际: {call_args[1].get('model_name')}"

    @patch('src.agents.rag.vector_store.settings')
    def test_default_bge_small_model(self, mock_settings):
        """默认应使用 bge-small-zh-v1.5（轻量快速）"""
        mock_settings.OPENAI_API_KEY = "invalid"
        mock_settings.OPENAI_BASE_URL = "https://invalid"
        mock_settings.EMBEDDING_MODEL = "text-embedding-3-small"
        # 不设置 LOCAL_EMBEDDING_MODEL（使用默认值）

        with patch('src.agents.rag.vector_store.OpenAIEmbeddings', side_effect=Exception("fail")):
            with patch('src.agents.rag.vector_store.HuggingFaceEmbeddings') as mock_hf:
                from src.agents.rag.vector_store import get_embeddings
                get_embeddings()

                call_args = mock_hf.call_args
                assert call_args[1]['model_name'] == "BAAI/bge-small-zh-v1.5", \
                    "默认应使用 bge-small-zh-v1.5"


# ==================== Cross-Encoder 重排序功能测试 ====================


class TestCrossEncoderReranker:
    """测试 Cross-Encoder 重排序功能"""

    def setup_method(self):
        """每个测试前清除缓存"""
        import src.agents.rag.retriever as retriever_module
        retriever_module._reranker = None

    def test_reranker_lazy_loading(self):
        """Cross-Encoder 应懒加载（首次调用时才初始化）"""
        from src.agents.rag.retriever import _get_reranker, _reranker

        # 初始状态应为 None
        assert _reranker is None or _reranker is False, "初始状态应为未加载"

    @patch('src.agents.rag.retriever.settings')
    def test_reranker_loads_successfully(self, mock_settings):
        """Cross-Encoder 应能成功加载"""
        mock_settings.RERANKER_MODEL = None  # 使用默认模型

        with patch('src.agents.rag.retriever.CrossEncoder') as mock_ce:
            mock_instance = MagicMock()
            mock_ce.return_value = mock_instance

            from src.agents.rag.retriever import _get_reranker
            result = _get_reranker()

            assert result == mock_instance, "应返回CrossEncoder实例"
            mock_ce.assert_called_once_with('cross-encoder/ms-marco-MiniLM-L-6-v2')

    @patch('src.agents.rag.retriever.settings')
    def test_reranker_custom_model(self, mock_settings):
        """应支持通过 settings.RERANKER_MODEL 自定义重排序模型"""
        custom_model = 'cross-encoder/ms-marco-MiniLM-L-12-v2'
        mock_settings.RERANKER_MODEL = custom_model

        with patch('src.agents.rag.retriever.CrossEncoder') as mock_ce:
            mock_instance = MagicMock()
            mock_ce.return_value = mock_instance

            from src.agents.rag.retriever import _get_reranker
            _get_reranker()

            mock_ce.assert_called_once_with(custom_model)

    def test_reranker_handles_load_failure(self):
        """模型加载失败时应优雅降级（返回None）"""
        with patch('src.agents.rag.retriever.CrossEncoder', side_effect=Exception("Model not found")):
            from src.agents.rag.retriever import _get_reranker
            result = _get_reranker()

            assert result is None, "加载失败应返回None"

    def test_rerank_with_cross_encoder_basic(self):
        """基本重排序：应对文档列表重新排序"""
        # 准备测试文档
        docs = [
            Document(page_content="焊接气孔缺陷的预防措施", metadata={"source": "doc1"}),
            Document(page_content="气泡水制作方法", metadata={"source": "doc2"}),
            Document(page_content="焊接裂纹检测技术", metadata={"source": "doc3"}),
        ]

        # Mock Cross-Encoder 返回分数（让 doc1 和 doc3 排在前面）
        with patch('src.agents.rag.retriever._get_reranker') as mock_get_reranker:
            mock_reranker = MagicMock()
            # 返回分数：doc1最高，doc3次之，doc2最低
            mock_reranker.predict.return_value = [0.9, 0.1, 0.8]
            mock_get_reranker.return_value = mock_reranker

            from src.agents.rag.retriever import _rerank_with_cross_encoder
            results = _rerank_with_cross_encoder("焊接缺陷预防", docs, top_k=3)

            # 验证结果数量
            assert len(results) == 3, "应返回所有文档"

            # 验证排序顺序（按分数降序）
            assert results[0].page_content == "焊接气孔缺陷的预防措施", \
                "最高分文档应在第一位"
            assert results[2].page_content == "气泡水制作方法", \
                "最低分文档应在最后"

            # 验证 metadata 中包含 Cross-Encoder 分数
            for doc in results:
                assert "_ce_score" in doc.metadata, "每个文档应有_ce_score字段"

    def test_rerank_empty_documents(self):
        """空文档列表应返回空列表"""
        from src.agents.rag.retriever import _rerank_with_cross_encoder
        results = _rerank_with_cross_encoder("查询", [])
        assert results == [], "空输入应返回空列表"

    def test_rerank_no_reranker_available(self):
        """无可用重排序模型时应返回原始文档"""
        docs = [Document(page_content="测试文档", metadata={})]

        with patch('src.agents.rag.retriever._get_reranker', return_value=None):
            from src.agents.rag.retriever import _rerank_with_cross_encoder
            results = _rerank_with_cross_encoder("查询", docs)

            assert len(results) == 1, "应返回原始文档"
            assert results[0].page_content == "测试文档", "内容不应改变"

    def test_rerank_prediction_failure(self):
        """预测失败时应返回原始顺序"""
        docs = [
            Document(page_content="文档1", metadata={}),
            Document(page_content="文档2", metadata={}),
        ]

        mock_reranker = MagicMock()
        mock_reranker.predict.side_effect = Exception("Prediction failed")

        with patch('src.agents.rag.retriever._get_reranker', return_value=mock_reranker):
            from src.agents.rag.retriever import _rerank_with_cross_encoder
            results = _rerank_with_cross_encoder("查询", docs, top_k=2)

            assert len(results) <= 2, "失败时返回截断后的原始文档"


class TestHybridSearchWithReranking:
    """测试混合检索集成 Cross-Encoder 重排序"""

    def setup_method(self):
        """每个测试前清除缓存"""
        import src.agents.rag.retriever as retriever_module
        retriever_module._reranker = None
        retriever_module._bm25_corpus = None
        retriever_module._bm25_docs = None

    @patch('src.agents.rag.retriever.get_vector_store')
    def test_hybrid_search_with_rerank_enabled(self, mock_store):
        """启用重排序的混合检索"""
        mock_store.return_value = None

        # Mock 重排序
        with patch('src.agents.rag.retriever._rerank_with_cross_encoder') as mock_rerank:
            mock_rerank.return_value = [
                Document(page_content="重排后结果", metadata={"_ce_score": 0.95})
            ]

            from src.agents.rag.retriever import hybrid_search
            results = hybrid_search("焊接参数", top_k=5, use_rerank=True)

            mock_rerank.assert_called_once()
            assert len(results) == 1, "应返回重排序后的结果"

    @patch('src.agents.rag.retriever.get_vector_store')
    def test_hybrid_search_without_rerank(self, mock_store):
        """不启用重排序时的混合检索（默认行为）"""
        mock_store.return_value = None

        with patch('src.agents.rag.retriever._rerank_with_cross_encoder') as mock_rerank:
            from src.agents.rag.retriever import hybrid_search
            results = hybrid_search("焊接参数", top_k=5, use_rerank=False)

            mock_rerank.assert_not_called(), "不启用重排序时不应调用重排序函数"
            assert isinstance(results, list), "应返回列表"

    @patch('src.agents.rag.retriever.get_vector_store')
    def test_debug_interface_includes_rerank_results(self, mock_store):
        """调试接口应包含重排序结果（如果启用）"""
        mock_store.return_value = None

        with patch('src.agents.rag.retriever._rerank_with_cross_encoder') as mock_rerank:
            mock_rerank.return_value = [
                Document(page_content="重排结果", metadata={"_ce_score": 0.9})
            ]

            from src.agents.rag.retriever import hybrid_search_debug
            debug_info = hybrid_search_debug("测试", top_k=3, use_rerank=True)

            assert "reranked_results" in debug_info, "调试信息应包含重排序结果"
            assert debug_info["use_rerank"] is True, "应标记为已启用重排序"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
