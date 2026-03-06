import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from models.schemas import ChatRequest, RAGConfig
from services.rag_service import (
    query,
    query_stream,
    get_chat_history,
    clear_chat_history,
    get_rag_config,
    update_rag_config,
)

router = APIRouter(prefix="/api", tags=["智能对话"])


@router.post("/chat")
async def chat(req: ChatRequest):
    """发送问题，获取 AI 回答（完整响应）"""
    result = query(req.question, req.doc_ids)
    return {"code": 200, "message": "success", "data": result}


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """发送问题，流式返回 AI 回答（SSE）"""

    def event_generator():
        for event_type, data in query_stream(req.question, req.doc_ids):
            payload = json.dumps({"type": event_type, "data": data}, ensure_ascii=False)
            yield f"data: {payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chat/history")
async def chat_history():
    """获取对话历史"""
    history = get_chat_history()
    return {"code": 200, "message": "success", "data": history}


@router.delete("/chat/history")
async def clear_history():
    """清空对话历史"""
    clear_chat_history()
    return {"code": 200, "message": "success", "data": None}


@router.get("/settings")
async def get_settings():
    """获取 RAG 配置"""
    config = get_rag_config()
    return {"code": 200, "message": "success", "data": config}


@router.put("/settings")
async def save_settings(config: RAGConfig):
    """更新 RAG 配置"""
    update_rag_config(config.model_dump())
    return {"code": 200, "message": "success", "data": config.model_dump()}
