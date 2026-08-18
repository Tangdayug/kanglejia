from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS FIRST, before registering routes
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Import routes AFTER CORS middleware is configured
from api import adminAPI, exceptionHandler, userAPI, healthRecordAPI, healthTestAPI, chatAPI, careAPI, interventionAPI, ttsAPI, healthEducationAPI, xiaozhiAPI, llmAPI, ragAPI


@app.get("/health")
async def health_check():
    """健康检查端点（经 nginx /api 代理后对外为 /api/health）。"""
    return {"status": "ok", "service": "second-nature"}


# 启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    from model import init_db
    init_db()

    # 启动 RAG 知识库自动监听（热更新）
    from service.rag_watcher_service import start_rag_watcher
    start_rag_watcher()