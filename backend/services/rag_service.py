import time

from langchain_qdrant import QdrantVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, MatchValue, FilterSelector

from config import QDRANT_PATH, COLLECTION_NAME, DEFAULT_RETRIEVE_K
from services.llm_service import get_llm, get_embeddings

# 向量存储实例
_vectorstore = None
# Qdrant 客户端实例
_qdrant_client = None

# 对话历史（内存存储，后续可迁移到数据库）
_chat_history: list[dict] = []

# RAG 配置（运行时状态）
_rag_config = {
    "use_multi_query": True,
    "multi_query_count": 3,
    "retrieve_k": DEFAULT_RETRIEVE_K,
    "rerank_top_k": 5,
    "use_rerank": True,
    "use_compression": False,
}

# 学术论文助手 Prompt
QA_PROMPT = ChatPromptTemplate.from_template(
    """你是专业的学术论文阅读助手「知研」。基于以下检索到的文献内容回答问题。

文献内容：
{context}

问题：{question}

要求：
1. 如果文献中有明确答案，直接引用并标注来源（文件名和页码）
2. 如果涉及多个文献，请综合对比分析
3. 如果文献中无相关信息，明确说明"在已上传的文献中未找到相关内容"
4. 保持学术严谨性，不臆测，使用中文回答
5. 适当使用 Markdown 格式使回答更清晰

回答："""
)


def _get_client():
    """获取 Qdrant 客户端"""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(path=QDRANT_PATH)
    return _qdrant_client


def _collection_exists():
    """检查集合是否已存在"""
    client = _get_client()
    try:
        collections = client.get_collections().collections
        return any(c.name == COLLECTION_NAME for c in collections)
    except Exception:
        return False


def get_vectorstore():
    """获取或创建向量存储实例"""
    global _vectorstore
    if _vectorstore is None and _collection_exists():
        _vectorstore = QdrantVectorStore(
            client=_get_client(),
            collection_name=COLLECTION_NAME,
            embedding=get_embeddings(),
        )
    return _vectorstore


def add_documents_to_vectorstore(chunks, doc_id: str):
    """将文档块添加到向量数据库"""
    global _vectorstore

    for chunk in chunks:
        chunk.metadata["doc_id"] = doc_id

    embeddings = get_embeddings()

    if _vectorstore is None:
        _vectorstore = QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            path=QDRANT_PATH,
            collection_name=COLLECTION_NAME,
        )
        # 同步客户端引用
        global _qdrant_client
        _qdrant_client = _vectorstore.client
    else:
        _vectorstore.add_documents(chunks)


def delete_documents_from_vectorstore(doc_id: str):
    """从向量数据库中删除指定文档的所有块"""
    if not _collection_exists():
        return

    try:
        client = _get_client()
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[FieldCondition(
                        key="metadata.doc_id",
                        match=MatchValue(value=doc_id),
                    )]
                )
            ),
        )
    except Exception:
        pass


def _format_docs(docs):
    """将检索到的文档格式化为文本"""
    return "\n\n".join(doc.page_content for doc in docs)


def _build_retriever_and_docs(question: str, doc_ids: list[str] | None = None):
    """构建检索器并返回检索到的文档，供普通问答和流式问答共用"""
    vs = get_vectorstore()
    if vs is None:
        return None, []

    k = _rag_config.get("retrieve_k", DEFAULT_RETRIEVE_K)
    search_kwargs = {"k": k}
    if doc_ids:
        from qdrant_client.models import MatchAny
        search_kwargs["filter"] = Filter(
            must=[FieldCondition(key="metadata.doc_id", match=MatchAny(any=doc_ids))]
        )

    retriever = vs.as_retriever(search_kwargs=search_kwargs)
    retrieved_docs = retriever.invoke(question)
    return vs, retrieved_docs


def _extract_sources(retrieved_docs):
    """从检索文档中提取来源信息"""
    sources = []
    seen = set()
    for doc in retrieved_docs:
        meta = doc.metadata
        key = f"{meta.get('source', '')}_{meta.get('page', 0)}"
        if key not in seen:
            seen.add(key)
            sources.append({
                "doc_id": meta.get("doc_id", ""),
                "filename": meta.get("source", "").split("/")[-1].split("\\")[-1],
                "page": meta.get("page", 0) + 1,
                "content": doc.page_content[:300],
            })
    return sources


def query(question: str, doc_ids: list[str] | None = None) -> dict:
    """
    执行 RAG 问答（完整响应）
    返回 { answer, sources, query_time_ms }
    """
    start = time.time()

    vs, retrieved_docs = _build_retriever_and_docs(question, doc_ids)
    if vs is None:
        return {
            "answer": "知识库为空，请先上传论文文档。",
            "sources": [],
            "query_time_ms": 0,
        }

    chain = (
        {"context": lambda _: _format_docs(retrieved_docs), "question": RunnablePassthrough()}
        | QA_PROMPT
        | get_llm()
        | StrOutputParser()
    )

    answer = chain.invoke(question)
    sources = _extract_sources(retrieved_docs)
    elapsed_ms = int((time.time() - start) * 1000)

    _chat_history.append({"role": "user", "content": question})
    _chat_history.append({
        "role": "ai",
        "content": answer,
        "sources": sources,
        "query_time_ms": elapsed_ms,
    })

    return {
        "answer": answer,
        "sources": sources,
        "query_time_ms": elapsed_ms,
    }


def query_stream(question: str, doc_ids: list[str] | None = None):
    """
    流式 RAG 问答生成器，逐个 token 返回
    yields: (event_type, data) 元组
      - ("token", str)     逐个 token
      - ("sources", list)  引用来源
      - ("done", dict)     结束信号，包含耗时
    """
    import json
    start = time.time()

    vs, retrieved_docs = _build_retriever_and_docs(question, doc_ids)
    if vs is None:
        yield ("token", "知识库为空，请先上传论文文档。")
        yield ("done", {"query_time_ms": 0})
        return

    chain = (
        {"context": lambda _: _format_docs(retrieved_docs), "question": RunnablePassthrough()}
        | QA_PROMPT
        | get_llm()
        | StrOutputParser()
    )

    # 使用 chain.stream() 逐 token 生成
    full_answer = ""
    for token in chain.stream(question):
        full_answer += token
        yield ("token", token)

    sources = _extract_sources(retrieved_docs)
    elapsed_ms = int((time.time() - start) * 1000)

    yield ("sources", sources)
    yield ("done", {"query_time_ms": elapsed_ms})

    # 记录到对话历史
    _chat_history.append({"role": "user", "content": question})
    _chat_history.append({
        "role": "ai",
        "content": full_answer,
        "sources": sources,
        "query_time_ms": elapsed_ms,
    })


# ========== 对话历史管理 ==========

def get_chat_history() -> list[dict]:
    return _chat_history


def clear_chat_history():
    _chat_history.clear()


# ========== RAG 配置管理 ==========

def get_rag_config() -> dict:
    return dict(_rag_config)


def update_rag_config(new_config: dict):
    _rag_config.update(new_config)
