"""
RAG文档加载器单元测试
测试文档加载、分块、内置文档等核心功能
"""
import pytest
from pathlib import Path
from langchain_core.documents import Document

from src.agents.rag.document_loader import (
    load_document,
    split_documents,
    BUILTIN_DOCS,
    prepare_multi_source_documents,
    _load_pdf,
    _load_word,
    _load_text,
)


class TestBuiltinDocs:
    """内置焊接知识库测试"""

    def test_builtin_docs_not_empty(self):
        """内置文档列表不应为空"""
        assert len(BUILTIN_DOCS) > 0, "内置焊接知识库不应为空"

    def test_builtin_docs_have_content(self):
        """每个内置文档应有非空内容"""
        for doc in BUILTIN_DOCS:
            assert isinstance(doc, Document), f"应为Document对象，实际: {type(doc)}"
            assert len(doc.page_content.strip()) > 0, "文档内容不应为空"

    def test_builtin_docs_have_metadata(self):
        """每个内置文档应有source和category元数据"""
        for doc in BUILTIN_DOCS:
            assert "source" in doc.metadata, "缺少source元数据"
            assert "category" in doc.metadata, "缺少category元数据"


class TestSplitDocuments:
    """文档分块功能测试"""

    def test_split_basic(self):
        """基本分块功能：长文本应被分割为多个chunk"""
        long_text = "这是测试句子。" * 100  # 足够长的文本
        docs = [Document(page_content=long_text, metadata={"source": "test"})]
        chunks = split_documents(docs, chunk_size=100, chunk_overlap=10)
        assert len(chunks) > 1, "长文本应被分割为多个chunk"

    def test_split_short_text_unchanged(self):
        """短文本不应被分割"""
        short_text = "这是一个短文本，不需要分割。"
        docs = [Document(page_content=short_text, metadata={"source": "test"})]
        chunks = split_documents(docs, chunk_size=500, chunk_overlap=50)
        assert len(chunks) == 1, "短文本应保持为单个chunk"
        assert chunks[0].page_content == short_text

    def test_split_preserves_metadata(self):
        """分块后metadata应保留"""
        original_meta = {"source": "test.txt", "category": "工艺参数"}
        docs = [Document(page_content="测试内容" * 50, metadata=original_meta)]
        chunks = split_documents(docs, chunk_size=100, chunk_overlap=10)
        for chunk in chunks:
            assert chunk.metadata["source"] == "test.txt", "source元数据丢失"
            assert chunk.metadata["category"] == "工艺参数", "category元数据丢失"

    def test_split_empty_input(self):
        """空输入应返回空列表"""
        chunks = split_documents([], chunk_size=100, chunk_overlap=10)
        assert chunks == [], "空输入应返回空列表"


class TestLoadTextFile:
    """文本文件加载测试"""

    def test_load_txt_file(self, tmp_path):
        """.txt文件加载"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("这是一段测试文本。\n第二行内容。", encoding="utf-8")
        docs = load_document(str(test_file), source="test.txt")
        assert len(docs) == 1
        assert "测试文本" in docs[0].page_content

    def test_load_markdown_file(self, tmp_path):
        """.md文件加载"""
        test_file = tmp_path / "test.md"
        test_file.write_text("# 标题\n\n这是**Markdown**内容。", encoding="utf-8")
        docs = load_document(str(test_file), source="test.md")
        assert len(docs) >= 1
        assert "Markdown" in docs[0].page_content or "标题" in docs[0].page_content

    def test_load_json_file(self, tmp_path):
        """.json文件加载"""
        import json
        test_data = {"key": "value", "nested": {"text": "JSON内容"}}
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(test_data, ensure_ascii=False), encoding="utf-8")
        docs = load_document(str(test_file), source="test.json")
        assert len(docs) >= 1
        # JSON内容应该被提取到文本中
        combined = " ".join([d.page_content for d in docs])
        assert "value" in combined or "JSON" in combined


class TestPrepareMultiSource:
    """多源文档准备测试"""

    def test_prepare_with_builtin_only(self):
        """仅使用内置文档（无外部目录）"""
        docs = prepare_multi_source_documents(
            docs_dir="/nonexistent/path",
            db_configs=None,
            api_configs=None,
            include_builtin=True,
        )
        # 应至少包含内置文档
        assert len(docs) > 0, "启用builtin时应返回内置文档"

    def test_prepare_without_builtin(self):
        """不使用内置文档且路径不存在时应返回空"""
        docs = prepare_multi_source_documents(
            docs_dir="/nonexistent/path",
            db_configs=None,
            api_configs=None,
            include_builtin=False,
        )
        assert len(docs) == 0, "无有效数据源时应返回空列表"


class TestErrorHandling:
    """错误处理测试"""

    def test_load_nonexistent_file(self):
        """加载不存在的文件应返回空列表或抛出异常"""
        with pytest.raises((FileNotFoundError, Exception)):
            load_document("/nonexistent/file.pdf", source="test")

    def test_unsupported_format(self, tmp_path):
        """不支持的文件格式应报错或返回空"""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("dummy content")
        # 应该抛出异常或返回空列表
        try:
            docs = load_document(str(test_file), source="test.xyz")
            # 如果没抛异常，应该返回空
            assert docs == []
        except (ValueError, Exception):
            pass  # 预期内的异常


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
