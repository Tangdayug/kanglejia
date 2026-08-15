"""
RAG 管理 API - 支持热更新知识库，无需重启容器或重新构建镜像
"""
from fastapi import Depends

from api import app
from common.auth import auth_handler
from common.result import ResultModel, Result
from rag.retriever_faiss import get_rag_retriever


@app.post("/rag/rebuild", response_model=ResultModel)
async def rebuild_knowledge_base(
    user_id: int = Depends(auth_handler.auth_required)
):
    """
    重新加载知识库文档并重建向量索引。

    使用方式：
    1. 把新的 PDF/DOC 文档放到挂载的知识库目录（如 /app/backend/rag/data）
    2. 调用此接口
    3. 接口返回重建结果，无需重启容器
    """
    retriever = get_rag_retriever()
    result = retriever.rebuild_knowledge_base()

    if result.get('status') == 'error':
        return Result.error(msg=result.get('message', '知识库重建失败'), data=result)

    return Result.success(data=result)


@app.get("/rag/status", response_model=ResultModel)
async def get_knowledge_base_status(
    user_id: int = Depends(auth_handler.auth_required)
):
    """获取当前知识库/向量索引状态。"""
    retriever = get_rag_retriever()
    info = retriever.vector_store.get_collection_info()
    return Result.success(data={
        'status': 'ok',
        'vectorCount': info.get('count', 0),
        'dimension': info.get('dimension', 0),
        'persistDirectory': info.get('persist_directory', '')
    })
