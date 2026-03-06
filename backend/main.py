from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.document import router as document_router
from routers.chat import router as chat_router

app = FastAPI(
    title="知研 ScholarRAG",
    description="基于 RAG 的论文阅读助手后端 API",
    version="0.1.0",
)

# CORS 跨域配置（允许前端开发服务器访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(document_router)
app.include_router(chat_router)


@app.get("/api/health")
async def health_check():
    return {"code": 200, "message": "知研 ScholarRAG 服务运行中", "data": None}
