# 知研 ScholarRAG

基于 RAG（检索增强生成）技术的学术论文阅读助手，支持上传 PDF / DOCX 格式的论文文档，通过智能问答快速获取论文核心内容。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Element Plus + Vite |
| 后端 | FastAPI + Uvicorn |
| LLM | 通义千问 qwen3.5-plus（DashScope API） |
| Embedding | DashScope text-embedding-v2 |
| 向量数据库 | Qdrant（本地模式） |
| RAG 框架 | LangChain |

## 项目结构

```
ZhiYan_ScholarRAG/
├── backend/
│   ├── main.py                 # FastAPI 应用入口
│   ├── config_example.py       # 配置文件模板
│   ├── requirements.txt        # Python 依赖
│   ├── models/
│   │   └── schemas.py          # Pydantic 数据模型
│   ├── routers/
│   │   ├── document.py         # 文档管理 API
│   │   └── chat.py             # 智能对话 API
│   └── services/
│       ├── llm_service.py      # LLM 和 Embedding 服务
│       ├── document_service.py # 文档解析与分块
│       └── rag_service.py      # RAG 检索问答核心
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js             # Vue 应用入口
│       ├── App.vue             # 主布局（侧边栏 + 路由）
│       ├── api/index.js        # Axios API 封装
│       ├── style.css           # 全局样式
│       ├── router/index.js     # 路由配置
│       └── views/
│           ├── HomeView.vue     # 首页
│           ├── UploadView.vue   # 上传文档
│           ├── LibraryView.vue  # 知识库管理
│           ├── ChatView.vue     # 智能对话
│           └── SettingsView.vue # RAG 参数设置
└── README.md
```

## 功能特性

- **文档管理**：支持 PDF / DOCX 上传，自动解析、文本清洗、智能分块
- **智能问答**：基于 RAG 的流式对话，支持引用来源定位（PDF 标注页码，DOCX 标注段落）
- **多文档检索**：支持全部文档问答或指定文档范围检索
- **对话历史**：对话记录持久化存储，页面刷新后自动恢复
- **RAG 参数可调**：
  - 多查询检索（MultiQueryRetriever）— 自动改写问题提高召回率
  - 长上下文重排序（LongContextReorder）— 缓解"中间丢失"问题
  - 上下文压缩（ContextualCompression）— LLM 过滤无关段落

## 快速开始

### 1. 后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置 API Key
cp config_example.py config.py
# 编辑 config.py，填入你的 DashScope API Key

# 启动服务
uvicorn main:app --reload --port 8000
```

### 2. 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

启动后访问 http://localhost:5173 即可使用。

## 使用流程

1. 在「上传文档」页面上传 PDF 或 DOCX 论文
2. 在「知识库」页面查看已上传的文档状态
3. 在「智能对话」页面提问，系统会检索相关文献并生成回答
4. 在「设置」页面调整 RAG 检索策略参数

## 配置说明

复制 `backend/config_example.py` 为 `backend/config.py`，修改以下配置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DASHSCOPE_API_KEY` | 通义千问 API Key | 需自行填写 |
| `LLM_MODEL` | LLM 模型名称 | qwen3.5-plus |
| `EMBEDDING_MODEL` | Embedding 模型 | text-embedding-v2 |
| `DEFAULT_CHUNK_SIZE` | 文本分块大小 | 500 |
| `DEFAULT_CHUNK_OVERLAP` | 分块重叠长度 | 50 |
| `DEFAULT_RETRIEVE_K` | 检索文档数量 | 10 |
