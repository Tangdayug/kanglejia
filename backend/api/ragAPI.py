"""
RAG 管理 API - 支持热更新知识库，无需重启容器或重新构建镜像
"""
import os
import shutil
from pathlib import Path
from typing import List

from fastapi import Depends, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse

from api import app
from common.auth import auth_handler
from common.constant import RAG_KNOWLEDGE_BASE_PATH
from common.result import ResultModel, Result
from rag.retriever_faiss import get_rag_retriever


# 允许上传的知识库文件类型
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def _get_kb_path() -> Path:
    """获取知识库根目录"""
    return Path(os.getenv("RAG_KNOWLEDGE_BASE_PATH", RAG_KNOWLEDGE_BASE_PATH))


def _validate_filename(filename: str) -> str:
    """校验并清理文件名，防止路径遍历攻击"""
    if not filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 只取基本文件名，去掉路径
    basename = os.path.basename(filename)
    # 进一步清理危险字符
    basename = basename.replace('..', '').strip()
    if not basename:
        raise HTTPException(status_code=400, detail="文件名不合法")

    ext = Path(basename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}，仅允许 {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return basename


def _rebuild_after_change():
    """文件变更后触发向量库重建（在后台线程执行，避免阻塞 API 响应）"""
    import threading
    def _run():
        try:
            retriever = get_rag_retriever()
            result = retriever.rebuild_knowledge_base()
            print(f"[RAG API] 文件变更后重建完成: {result.get('status')}")
        except Exception as e:
            print(f"[RAG API] 文件变更后重建失败: {e}")
    threading.Thread(target=_run, daemon=True, name="rag-api-rebuild").start()


@app.post("/rag/rebuild", response_model=ResultModel)
async def rebuild_knowledge_base(
    user_id: int = Depends(auth_handler.auth_required)
):
    """
    重新加载知识库文档并重建向量索引。

    使用方式：
    1. 把新的 PDF/DOC/TXT 文档放到挂载的知识库目录（如 /app/backend/rag/data）
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


@app.get("/rag/files", response_model=ResultModel)
async def list_knowledge_base_files(
    user_id: int = Depends(auth_handler.auth_required)
):
    """列出知识库目录下所有支持的文档文件。"""
    kb_path = _get_kb_path()
    if not kb_path.exists():
        return Result.success(data={"files": [], "path": str(kb_path)})

    files: List[dict] = []
    for file_path in kb_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "relative_path": str(file_path.relative_to(kb_path)),
                "size": stat.st_size,
                "modified_at": stat.st_mtime,
                "extension": file_path.suffix.lower()
            })

    # 按修改时间倒序
    files.sort(key=lambda x: x["modified_at"], reverse=True)
    return Result.success(data={"files": files, "path": str(kb_path), "count": len(files)})


@app.post("/rag/files", response_model=ResultModel)
async def upload_knowledge_base_file(
    file: UploadFile = File(...),
    keep_filename: bool = Form(False),
    user_id: int = Depends(auth_handler.auth_required)
):
    """
    上传文件到知识库目录。

    Args:
        file: 上传的文件
        keep_filename: 是否保留原始文件名；False 时使用上传时的文件名
    """
    if not file.filename:
        return Result.error(msg="文件名不能为空")

    filename = _validate_filename(file.filename)
    kb_path = _get_kb_path()
    kb_path.mkdir(parents=True, exist_ok=True)
    target_path = kb_path / filename

    # 检查文件大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        return Result.error(msg=f"文件大小超过限制 {MAX_FILE_SIZE // 1024 // 1024}MB")

    # 如果文件已存在且不允许覆盖，返回错误（调用方应先删除或使用更新接口）
    if target_path.exists():
        return Result.error(msg=f"文件 {filename} 已存在，请先删除或使用更新接口")

    with open(target_path, 'wb') as f:
        f.write(content)

    _rebuild_after_change()

    return Result.success(data={
        "filename": filename,
        "path": str(target_path.relative_to(kb_path)),
        "size": len(content)
    })


@app.put("/rag/files/{filename:path}", response_model=ResultModel)
async def update_knowledge_base_file(
    filename: str,
    file: UploadFile = File(...),
    user_id: int = Depends(auth_handler.auth_required)
):
    """更新（覆盖）知识库中的指定文件。"""
    filename = _validate_filename(filename)
    kb_path = _get_kb_path()
    target_path = kb_path / filename

    if not target_path.exists():
        return Result.error(msg=f"文件 {filename} 不存在")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        return Result.error(msg=f"文件大小超过限制 {MAX_FILE_SIZE // 1024 // 1024}MB")

    # 备份旧文件（可选，保留 .bak 便于回滚）
    backup_path = target_path.with_suffix(target_path.suffix + '.bak')
    shutil.copy2(target_path, backup_path)

    with open(target_path, 'wb') as f:
        f.write(content)

    _rebuild_after_change()

    return Result.success(data={
        "filename": filename,
        "path": str(target_path.relative_to(kb_path)),
        "size": len(content),
        "backup": backup_path.name
    })


@app.delete("/rag/files/{filename:path}", response_model=ResultModel)
async def delete_knowledge_base_file(
    filename: str,
    user_id: int = Depends(auth_handler.auth_required)
):
    """删除知识库中的指定文件。"""
    filename = _validate_filename(filename)
    kb_path = _get_kb_path()
    target_path = kb_path / filename

    if not target_path.exists():
        return Result.error(msg=f"文件 {filename} 不存在")

    target_path.unlink()

    # 同时清理备份文件
    backup_path = target_path.with_suffix(target_path.suffix + '.bak')
    if backup_path.exists():
        backup_path.unlink()

    _rebuild_after_change()

    return Result.success(data={"deleted": filename})


@app.get("/rag/files/{filename:path}/download")
async def download_knowledge_base_file(
    filename: str,
    user_id: int = Depends(auth_handler.auth_required)
):
    """下载知识库中的指定文件。"""
    filename = _validate_filename(filename)
    kb_path = _get_kb_path()
    target_path = kb_path / filename

    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")

    return FileResponse(
        path=str(target_path),
        filename=filename,
        media_type='application/octet-stream'
    )
