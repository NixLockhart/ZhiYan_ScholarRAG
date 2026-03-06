from fastapi import APIRouter, UploadFile, File, HTTPException

from services.document_service import (
    process_document,
    get_all_documents,
    get_document,
    delete_document_record,
    get_stats,
)
from services.rag_service import add_documents_to_vectorstore, delete_documents_from_vectorstore
from config import MAX_FILE_SIZE

router = APIRouter(prefix="/api/documents", tags=["文档管理"])

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档：解析 → 分块 → 向量化"""
    # 校验文件类型
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        ext = (file.filename or "").rsplit(".", 1)[-1].lower()
        if ext not in ("pdf", "docx"):
            raise HTTPException(status_code=422, detail=f"不支持的文件类型: {content_type}")

    # 读取文件
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="文件过大，请上传小于50MB的文件")

    try:
        doc_info, chunks = process_document(file_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"文档解析失败: {str(e)}")

    # 向量化入库
    try:
        add_documents_to_vectorstore(chunks, doc_info["doc_id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"向量化失败: {str(e)}")

    return {"code": 200, "message": "success", "data": doc_info}


@router.get("")
async def list_documents():
    """获取文档列表"""
    docs = get_all_documents()
    return {"code": 200, "message": "success", "data": docs}


@router.get("/stats")
async def document_stats():
    """获取知识库统计"""
    stats = get_stats()
    return {"code": 200, "message": "success", "data": stats}


@router.get("/{doc_id}")
async def document_detail(doc_id: str):
    """获取单个文档详情"""
    doc = get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"code": 200, "message": "success", "data": doc}


@router.delete("/{doc_id}")
async def remove_document(doc_id: str):
    """删除文档"""
    # 从向量库删除
    delete_documents_from_vectorstore(doc_id)
    # 从记录和磁盘删除
    success = delete_document_record(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"code": 200, "message": "success", "data": None}
