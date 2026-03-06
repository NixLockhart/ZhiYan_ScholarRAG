from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentInfo(BaseModel):
    """文档信息"""
    doc_id: str
    filename: str
    file_type: str
    page_count: int = 0
    chunk_count: int = 0
    status: str = "processing"  # processing / ready / error
    upload_time: str = ""
    metadata: dict = {}


class ChatRequest(BaseModel):
    """对话请求"""
    question: str
    doc_ids: Optional[list[str]] = None


class ChatResponse(BaseModel):
    """对话响应"""
    answer: str
    sources: list[dict] = []
    query_time_ms: int = 0


class RAGConfig(BaseModel):
    """RAG 配置"""
    use_multi_query: bool = True
    multi_query_count: int = 3
    retrieve_k: int = 10
    rerank_top_k: int = 5
    use_rerank: bool = True
    use_compression: bool = False


class StatsResponse(BaseModel):
    """知识库统计"""
    doc_count: int = 0
    total_pages: int = 0
    total_chunks: int = 0


class APIResponse(BaseModel):
    """统一 API 响应"""
    code: int = 200
    message: str = "success"
    data: Optional[dict | list | None] = None
