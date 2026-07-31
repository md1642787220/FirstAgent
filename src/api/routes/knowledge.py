"""
知识库管理REST API
提供文档上传/删除/列表查询/索引重建/状态查看/检索调试等接口
"""
import json
import os
import time
from typing import Optional, List, AsyncGenerator, Dict

from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.agents.rag.vector_store import get_vector_store, get_stats, init_knowledge_base, build_vector_store
from src.agents.rag.document_loader import load_document, split_documents, BUILTIN_DOCS
from src.agents.rag.retriever import hybrid_search_debug, hybrid_search
from src.config import settings


router = APIRouter(prefix="/api/knowledge", tags=["知识库管理"])


# ==================== 请求/响应模型 ====================

class KnowledgeStatusResponse(BaseModel):
    """知识库状态响应"""
    total_documents: int = Field(description="不同来源的文档数量")
    total_chunks: int = Field(description="总文档块数")
    collection_name: str = Field(description="ChromaDB集合名称")
    persist_dir: str = Field(description="持久化目录路径")
    last_updated: Optional[str] = Field(default=None, description="最后更新时间")
    embedding_model: str = Field(description="当前使用的Embedding模型")
    status: str = Field(description="状态: ready/unavailable/error")
    source_distribution: dict = Field(default_factory=dict, description="来源分布")


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    success: bool = Field(description="是否成功")
    filename: str = Field(description="原始文件名")
    chunks_created: int = Field(description="生成的文档块数")
    message: str = Field(description="状态消息")


class DocumentItem(BaseModel):
    """文档列表项"""
    source: str = Field(description="文档来源标识")
    chunk_count: int = Field(description="该来源的块数")
    category: Optional[str] = Field(default=None, description="分类标签")
    summary: Optional[str] = Field(default=None, description="文档内容概要")


class DocumentListResponse(BaseModel):
    """文档列表响应（分页）"""
    total: int = Field(description="总文档数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
    items: List[DocumentItem] = Field(description="文档列表")


class SearchDebugRequest(BaseModel):
    """检索调试请求"""
    query: str = Field(..., description="查询文本", min_length=1)
    top_k: Optional[int] = Field(default=3, description="返回结果数")
    vector_k: Optional[int] = Field(default=5, description="向量检索候选数")
    bm25_k: Optional[int] = Field(default=5, description="BM25检索候选数")
    use_query_expansion: bool = Field(default=False, description="是否启用查询同义词扩展")


class SearchDebugResultItem(BaseModel):
    """检索结果项"""
    content: str = Field(description="文档内容片段")
    source: str = Field(description="来源")
    rrf_score: Optional[float] = Field(default=None, description="RRF融合分数")
    vector_rank: Optional[int] = Field(default=None, description="向量检索排名")
    bm25_score: Optional[float] = Field(default=None, description="BM25原始分数")


class SearchDebugResponse(BaseModel):
    """检索调试响应"""
    query: str = Field(description="原始查询")
    expanded_query: Optional[str] = Field(default=None, description="扩展后查询")
    is_expanded: bool = Field(description="是否进行了查询扩展")
    vector_result_count: int = Field(description="向量检索命中数")
    bm25_result_count: int = Field(description="BM25检索命中数")
    fused_results: List[SearchDebugResultItem] = Field(description="RRF融合后的最终结果")
    total_latency_ms: float = Field(description="总耗时(毫秒)")


class RebuildResponse(BaseModel):
    """索引重建响应"""
    success: bool = Field(description="是否成功")
    message: str = Field(description="状态消息")
    total_chunks: int = Field(description="重建后的总块数")
    latency_ms: float = Field(description="重建耗时(毫秒)")


# ==================== API端点实现 ====================

@router.get("/status", response_model=KnowledgeStatusResponse)
async def get_knowledge_status():
    """获取知识库状态信息（文档数、chunk数、来源分布、embedding模型等）"""
    return get_stats()


@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: Optional[str] = Form(default=None, description="文档分类"),
):
    """上传单个文档文件到知识库

    支持格式：PDF, Word(.docx), Excel(.xlsx/.xls), PPTX, CSV,
             JSON, XML, Markdown, HTML, EML, MSG, 图片(OCR)
    """
    # 验证文件扩展名
    allowed_extensions = {
        ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx",
        ".csv", ".json", ".xml", ".md", ".html", ".htm",
        ".eml", ".msg", ".png", ".jpg", ".jpeg", ".gif", ".bmp"
    }
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，允许的格式: {', '.join(sorted(allowed_extensions))}"
        )

    # 保存临时文件并加载
    temp_dir = settings.KNOWLEDGE_DOCS_DIR
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        # 写入临时文件
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 加载文档
        documents = load_document(temp_path, source=f"upload:{file.filename}")
        if not documents:
            return DocumentUploadResponse(
                success=False,
                filename=file.filename,
                chunks_created=0,
                message=f"未能从文件中提取文本内容，请检查文件是否损坏或为空"
            )

        # 分块
        chunks = split_documents(
            documents,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        # 添加category元数据
        if category:
            for chunk in chunks:
                chunk.metadata["category"] = category

        # 追加到现有向量存储（增量更新）
        store = get_vector_store()
        if store is None:
            return DocumentUploadResponse(
                success=False,
                filename=file.filename,
                chunks_created=0,
                message="向量存储不可用，请检查ChromaDB配置"
            )

        # 提取文本和metadata
        texts = [doc.page_content for doc in chunks]
        metadatas = [doc.metadata for doc in chunks]

        # 批量添加到集合
        store.add_texts(texts=texts, metadatas=metadatas)

        # 清理全局缓存（使BM25索引下次重建）
        from src.agents.rag.retriever import _get_bm25
        import src.agents.rag.retriever as retriever_module
        retriever_module._bm25_corpus = None
        retriever_module._bm25_docs = None

        return DocumentUploadResponse(
            success=True,
            filename=file.filename,
            chunks_created=len(chunks),
            message=f"文档已成功添加到知识库，生成 {len(chunks)} 个文档块"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")
    finally:
        # 清理临时文件（可选保留用于调试）
        if os.path.exists(temp_path):
            pass  # 保留文件以便后续重建时使用


@router.post("/documents/stream")
async def upload_document_stream(
    file: UploadFile = File(...),
    category: Optional[str] = Form(default=None, description="文档分类"),
):
    """流式上传文档，通过 SSE 逐步返回解析→分片→向量化→写入的进度

    事件格式: data: {"step":"parse|chunk|vectorize|done","status":"running|success|error","message":"...","detail":{...}}
    前端连接 SSE 后逐事件展示流水线进度。
    """

    allowed_extensions = {
        ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx",
        ".csv", ".json", ".xml", ".md", ".html", ".htm",
        ".eml", ".msg", ".png", ".jpg", ".jpeg", ".gif", ".bmp"
    }
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，允许的格式: {', '.join(sorted(allowed_extensions))}"
        )

    temp_dir = settings.KNOWLEDGE_DOCS_DIR
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)

    async def event_generator() -> AsyncGenerator[str, None]:
        def send(step: str, status: str, message: str, detail: dict = None):
            """构造一条 SSE data 行"""
            payload = {"step": step, "status": status, "message": message}
            if detail:
                payload["detail"] = detail
            return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        try:
            # ─── Step 0: 保存文件 ───
            content_bytes = await file.read()
            with open(temp_path, "wb") as f:
                f.write(content_bytes)
            yield send("receive", "success", f"已接收文件: {file.filename}", {"size": len(content_bytes)})

            # ─── Step 1: 解析 ───
            yield send("parse", "running", "正在解析文档...")
            documents = load_document(temp_path, source=f"upload:{file.filename}")
            if not documents:
                yield send("parse", "error", "未能从文件中提取文本内容，请检查文件是否损坏或为空")
                yield send("done", "done", "")
                return
            yield send("parse", "success", f"解析完成，共 {len(documents)} 页/段", {"pages": len(documents)})

            # ─── Step 2: 分片 ───
            yield send("chunk", "running", "正在分片...")
            chunks = split_documents(
                documents,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
            if not chunks:
                yield send("chunk", "error", "分片后无有效文本块，请检查文档内容")
                yield send("done", "done", "")
                return
            yield send("chunk", "success", f"分片完成，共 {len(chunks)} 个文档块", {"chunks": len(chunks)})

            # 添加 category 元数据
            if category:
                for chunk in chunks:
                    chunk.metadata["category"] = category

            # ─── Step 3: 向量化 + 写入向量库 ───
            yield send("vectorize", "running", f"正在向量化并写入 ({len(chunks)} 块)...")
            store = get_vector_store()
            if store is None:
                yield send("vectorize", "error", "向量存储不可用，请检查 ChromaDB 配置")
                yield send("done", "done", "")
                return

            texts = [doc.page_content for doc in chunks]
            metadatas = [doc.metadata for doc in chunks]
            store.add_texts(texts=texts, metadatas=metadatas)
            yield send("vectorize", "success", f"向量化并写入完成", {"chunks": len(chunks)})

            # ─── Step 4: 清理缓存 ───
            yield send("cleanup", "running", "正在刷新缓存...")
            import src.agents.rag.retriever as retriever_module
            retriever_module._bm25_corpus = None
            retriever_module._bm25_docs = None
            yield send("cleanup", "success", "缓存已刷新")

            # ─── 全部完成 ───
            yield send("done", "done", f"知识库新增 {len(chunks)} 条记录，文档可立即检索")

        except Exception as e:
            yield send("error", "error", f"处理异常: {str(e)}")
            yield send("done", "done", "")
        finally:
            # 保留临时文件用于后续重建
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页大小"),
    source_filter: Optional[str] = Query(default=None, description="按来源过滤"),
):
    """获取已加载的文档列表（分页，支持按source过滤）"""
    stats = get_stats()
    source_dist = stats.get("source_distribution", {})

    # 过滤
    if source_filter:
        source_dist = {k: v for k, v in source_dist.items() if source_filter in k}

    # 为每个文档生成概要（提取前2个chunk内容合并）
    store = get_vector_store()
    items = []
    for src, count in source_dist.items():
        summary = None
        if store and store._collection:
            try:
                results = store._collection.get(
                    where={"source": src},
                    limit=3,
                    include=["documents"],
                )
                if results and results.get("documents"):
                    # 合并前几个chunk内容，取前200字作为概要
                    content = " ".join(d for d in results["documents"] if d)
                    summary = content[:200].strip()
                    if len(content) > 200:
                        summary += "…"
            except Exception:
                pass

        items.append(DocumentItem(
            source=src,
            chunk_count=count,
            summary=summary,
        ))

    # 分页
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = items[start:end]

    return DocumentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=paginated_items,
    )


@router.delete("/documents/{source:path}")
async def delete_document(source: str):
    """删除指定来源的所有文档块

    Args:
        source: 文档来源标识（如 upload:manual.pdf 或 builtin:welding_params）
    """
    store = get_vector_store()
    if store is None:
        raise HTTPException(status_code=503, detail="向量存储不可用")

    try:
        collection = store._collection

        # 查询该source的所有记录
        results = collection.get(where={"source": source}, include=["ids"])
        if not results or not results.get("ids"):
            raise HTTPException(status_code=404, detail=f"未找到来源为 '{source}' 的文档")

        # 删除
        collection.delete(ids=results["ids"])

        # 清理BM25缓存
        import src.agents.rag.retriever as retriever_module
        retriever_module._bm25_corpus = None
        retriever_module._bm25_docs = None

        return {
            "success": True,
            "message": f"已删除来源 '{source}' 的 {len(results['ids'])} 个文档块",
            "deleted_count": len(results["ids"]),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/rebuild", response_model=RebuildResponse)
async def rebuild_knowledge_base():
    """全量重建知识库索引（清空ChromaDB后重新从data_sources.yml和内置文档加载）

    注意：此操作会清空所有已上传的自定义文档，仅保留内置+配置文件中的数据源。
    如需保留自定义文档，请重新上传。
    """
    start_time = time.perf_counter()

    try:
        # 重新初始化（会清空旧数据并重建）
        success = init_knowledge_base()
        latency_ms = (time.perf_counter() - start_time) * 1000

        if success:
            stats = get_stats()
            return RebuildResponse(
                success=True,
                message="知识库索引重建成功",
                total_chunks=stats.get("total_chunks", 0),
                latency_ms=round(latency_ms, 2),
            )
        else:
            return RebuildResponse(
                success=False,
                message="知识库索引重建失败，请检查日志获取详情",
                total_chunks=0,
                latency_ms=round(latency_ms, 2),
            )
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        raise HTTPException(
            status_code=500,
            detail=f"重建过程异常: {str(e)}",
        )


@router.post("/search", response_model=List[Dict])
async def search_documents(request: Dict):
    """语义检索（混合向量 + BM25 + RRF融合）

    Body:
        query: 用户查询
        top_k: 返回结果数（默认5）
        use_query_expansion: 是否启用同义词扩展
        use_rerank: 是否启用 Cross-Encoder 重排序
    """
    try:
        query = request.get("query", "").strip()
        if not query:
            raise HTTPException(status_code=400, detail="查询内容不能为空")
        top_k = request.get("top_k", 5)
        use_query_expansion = request.get("use_query_expansion", False)
        use_rerank = request.get("use_rerank", False)

        docs = hybrid_search(
            query=query,
            top_k=top_k,
            use_query_expansion=use_query_expansion,
            use_rerank=use_rerank,
        )
        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content[:500] + ("..." if len(doc.page_content) > 500 else ""),
                "source": doc.metadata.get("source", "unknown"),
                "score": doc.metadata.get("_rrf_score", 0.0),
                "metadata": {k: v for k, v in doc.metadata.items() if not k.startswith("_")},
            })
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")


@router.post("/search-debug", response_model=SearchDebugResponse)
async def search_debug(request: SearchDebugRequest):
    """检索调试接口：返回向量/BM25/RRF三路中间结果及分数详情

    用于调优检索参数和诊断检索质量问题。
    """
    try:
        debug_info = hybrid_search_debug(
            query=request.query,
            top_k=request.top_k,
            vector_k=request.vector_k,
            bm25_k=request.bm25_k,
            use_query_expansion=request.use_query_expansion,
        )

        # 转换为响应模型
        fused_items = []
        for doc in debug_info["fused_results"]:
            fused_items.append(SearchDebugResultItem(
                content=doc.page_content[:300] + ("..." if len(doc.page_content) > 300 else ""),
                source=doc.metadata.get("source", "unknown"),
                rrf_score=doc.metadata.get("_rrf_score"),
                vector_rank=doc.metadata.get("_vector_rank"),
                bm25_score=doc.metadata.get("_bm25_score"),
            ))

        return SearchDebugResponse(
            query=debug_info["query"],
            expanded_query=debug_info.get("expanded_query"),
            is_expanded=debug_info["is_expanded"],
            vector_result_count=len(debug_info["vector_results"]),
            bm25_result_count=len(debug_info["bm25_results"]),
            fused_results=fused_items,
            total_latency_ms=debug_info["total_latency_ms"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索调试失败: {str(e)}")
