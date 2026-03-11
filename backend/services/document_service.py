import os
import re
import uuid
from datetime import datetime

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import UPLOAD_DIR, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP


# 内存中的文档元数据存储（后续可迁移到 SQLite）
_documents_store: dict = {}


def save_upload_file(file_bytes: bytes, filename: str) -> str:
    """保存上传文件到磁盘，返回文件路径"""
    doc_id = uuid.uuid4().hex[:12]
    ext = os.path.splitext(filename)[1].lower()
    save_name = f"{doc_id}{ext}"
    save_path = os.path.join(UPLOAD_DIR, save_name)

    with open(save_path, "wb") as f:
        f.write(file_bytes)

    return doc_id, save_path, ext.lstrip(".")


def load_document(file_path: str, file_type: str):
    """加载文档，返回 LangChain Document 列表"""
    if file_type == "pdf":
        loader = PyPDFLoader(file_path)
    elif file_type in ("docx", "doc"):
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")

    pages = loader.load()
    return pages


def clean_text(text: str) -> str:
    """文本清洗：去除多余空白、页眉页脚噪声"""
    # 去除多余换行和空格
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    # 去除常见页眉页脚模式（如纯数字页码行）
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    return text.strip()


# 参考文献/附录标题的正则模式（匹配独占一行的标题）
_SECTION_STOP_PATTERNS = [
    re.compile(r"(?i)^\s*(\d+\s*\.?\s*)?references\s*$", re.MULTILINE),
    re.compile(r"(?i)^\s*(\d+\s*\.?\s*)?bibliography\s*$", re.MULTILINE),
    re.compile(r"^\s*(\d+\s*\.?\s*)?参考文献\s*$", re.MULTILINE),
    re.compile(r"(?i)^\s*(\d+\s*\.?\s*)?works\s+cited\s*$", re.MULTILINE),
    re.compile(r"(?i)^\s*appendix\b", re.MULTILINE),
    re.compile(r"^\s*附录\b", re.MULTILINE),
]


def _filter_reference_pages(pages):
    """
    过滤参考文献和附录区域。
    扫描每页的完整文本，一旦发现参考文献/附录标题行：
    - 保留该页中标题之前的正文内容
    - 丢弃标题之后的内容及所有后续页
    """
    filtered = []
    for page in pages:
        text = page.page_content
        earliest_pos = None
        for pattern in _SECTION_STOP_PATTERNS:
            m = pattern.search(text)
            if m and (earliest_pos is None or m.start() < earliest_pos):
                earliest_pos = m.start()

        if earliest_pos is not None:
            # 保留标题之前的正文（如果有实质内容）
            before = text[:earliest_pos].strip()
            if len(before) > 50:
                page.page_content = before
                filtered.append(page)
            break  # 丢弃后续所有页
        else:
            filtered.append(page)
    return filtered


def split_documents(pages, chunk_size=DEFAULT_CHUNK_SIZE, chunk_overlap=DEFAULT_CHUNK_OVERLAP):
    """将文档切分为文本块"""
    # 过滤参考文献页
    pages = _filter_reference_pages(pages)

    # 清洗每页文本
    for page in pages:
        page.page_content = clean_text(page.page_content)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "；", "，", " ", ""],
    )

    chunks = splitter.split_documents(pages)

    # 为每个 chunk 补充索引信息
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    return chunks


def process_document(file_bytes: bytes, filename: str) -> dict:
    """
    完整的文档处理流程：保存 → 加载 → 清洗 → 分块
    返回文档元信息和文本块列表
    """
    doc_id, file_path, file_type = save_upload_file(file_bytes, filename)

    pages = load_document(file_path, file_type)
    chunks = split_documents(pages)

    # 把原始文件名写入每个chunk的metadata，供引用来源展示
    for chunk in chunks:
        chunk.metadata["original_filename"] = filename

    doc_info = {
        "doc_id": doc_id,
        "filename": filename,
        "file_type": file_type,
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "status": "ready",
        "upload_time": datetime.now().isoformat(),
        "metadata": {
            "source": file_path,
            "size_bytes": len(file_bytes),
        },
    }

    # 存入内存
    _documents_store[doc_id] = doc_info

    return doc_info, chunks


def get_all_documents() -> list[dict]:
    """获取所有文档信息"""
    return list(_documents_store.values())


def get_document(doc_id: str) -> dict | None:
    """获取单个文档信息"""
    return _documents_store.get(doc_id)


def delete_document_record(doc_id: str) -> bool:
    """删除文档记录和文件"""
    doc = _documents_store.pop(doc_id, None)
    if doc is None:
        return False

    # 删除磁盘文件
    file_path = doc.get("metadata", {}).get("source", "")
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    return True


def get_stats() -> dict:
    """获取知识库统计信息"""
    docs = list(_documents_store.values())
    return {
        "doc_count": len(docs),
        "total_pages": sum(d.get("page_count", 0) for d in docs),
        "total_chunks": sum(d.get("chunk_count", 0) for d in docs),
    }
