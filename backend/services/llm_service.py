import os
from langchain_community.llms import Tongyi
from langchain_community.embeddings import DashScopeEmbeddings

from config import DASHSCOPE_API_KEY, LLM_MODEL, EMBEDDING_MODEL

# 设置 API Key 环境变量（DashScope SDK 读取此变量）
os.environ["DASHSCOPE_API_KEY"] = DASHSCOPE_API_KEY

# LLM 实例
_llm = None
# Embedding 实例
_embeddings = None


def get_llm():
    """获取通义千问 LLM 实例"""
    global _llm
    if _llm is None:
        _llm = Tongyi(model_name=LLM_MODEL, temperature=0.1)
    return _llm


def get_embeddings():
    """获取 DashScope Embedding 实例"""
    global _embeddings
    if _embeddings is None:
        _embeddings = DashScopeEmbeddings(model=EMBEDDING_MODEL)
    return _embeddings
