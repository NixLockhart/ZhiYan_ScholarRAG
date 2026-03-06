import os

# ========== 通义千问 DashScope 配置 ==========
# 请将下方替换为你自己的 API Key（从阿里云百炼平台获取）
# 获取地址：https://bailian.console.aliyun.com/ → API-KEY 管理
DASHSCOPE_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxx"

# LLM 模型
LLM_MODEL = "qwen3.5-plus"
# Embedding 模型
EMBEDDING_MODEL = "text-embedding-v2"

# ========== 向量数据库配置 ==========
QDRANT_PATH = os.path.join(os.path.dirname(__file__), "qdrant_data")
COLLECTION_NAME = "paper_chunks"

# ========== 文件上传配置 ==========
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# ========== RAG 默认参数 ==========
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
DEFAULT_RETRIEVE_K = 10
DEFAULT_RERANK_TOP_K = 5
DEFAULT_MULTI_QUERY_COUNT = 3

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(QDRANT_PATH, exist_ok=True)
