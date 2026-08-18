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


def _warm_up_rag():
    """在后台线程预热 RAG：加载 embedding 模型并初始化向量库。

    避免首个聊天请求触发模型延迟加载，导致对话长时间无响应。
    若索引非空但维度与当前模型不匹配，自动清空重建。
    空索引由 RAG Watcher 负责初始化，避免与启动时重建任务重复。
    """
    import os
    # 模型已预下载，强制离线模式避免 HuggingFace 网络检查挂起
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

    try:
        print("🔥 后台预热 RAG 检索器（加载 embedding 模型 + 初始化知识库）...")
        from common.local_embedding import get_local_embedding
        from rag.vector_store_faiss import get_vector_store
        from rag.retriever_faiss import get_rag_retriever, _rag_rebuild_lock

        embedder = get_local_embedding()
        model_dim = embedder.get_dimension()
        print(f"✅ 本地嵌入模型加载完成，维度: {model_dim}")

        # 触发一次实际嵌入计算，确保模型完全加载到内存
        _ = embedder.embed_query("warmup")
        print("✅ embedding warmup 完成")

        vector_store = get_vector_store()
        index_dim = vector_store.embedding_dimension
        print(f"📊 当前向量索引维度: {index_dim}, 向量数: {vector_store.index.ntotal if vector_store.index else 0}")

        # 空索引由 RAG Watcher 在启动时初始化，避免重复重建
        if vector_store.is_empty():
            print("⏭️  向量库为空，跳过预热重建（RAG Watcher 将负责初始化）")
            return

        # 维度不匹配时自动重建索引，防止搜索报错
        if index_dim is not None and index_dim != model_dim:
            if not _rag_rebuild_lock.acquire(blocking=False):
                print("⏭️  已有重建任务在进行中，跳过预热重建")
                return
            try:
                print(f"⚠️  索引维度 ({index_dim}) 与模型维度 ({model_dim}) 不匹配，正在重建向量库...")
                retriever = get_rag_retriever()
                retriever.rebuild_knowledge_base()
                print(f"✅ 向量库重建完成，新维度: {vector_store.embedding_dimension}")
            finally:
                _rag_rebuild_lock.release()
        else:
            retriever = get_rag_retriever()
            info = retriever.initialize_knowledge_base()
            print(f"✅ RAG 预热完成: {info}")
    except Exception as e:
        print(f"⚠️  RAG 后台预热失败（不影响聊天）: {e}")
        import traceback
        traceback.print_exc()


# 启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    from model import init_db
    init_db()

    # 启动 RAG 知识库自动监听（热更新）
    from service.rag_watcher_service import start_rag_watcher
    start_rag_watcher()

    # 后台线程预热 embedding 模型与向量库，避免首条消息阻塞
    import threading
    threading.Thread(target=_warm_up_rag, daemon=True, name="rag-warmup").start()