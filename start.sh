#!/bin/bash
set -e  # 遇到错误立即退出

cd /app/backend

echo "=========================================="
echo "Starting SecondNature Backend"
echo "=========================================="

# 1. 创建必要的目录
echo "Creating directories..."
mkdir -p ./rag/indices/faiss
mkdir -p ./data
mkdir -p ./logs

# 2. 检查知识库文件
echo "Checking knowledge base files..."
PDF_COUNT=$(find ./rag/data -name "*.pdf" 2>/dev/null | wc -l)
echo "Found $PDF_COUNT PDF files in knowledge base"

# 3. 设置环境变量
export RAG_VECTOR_DB_PATH="./rag/indices/faiss"
export RAG_KNOWLEDGE_BASE_PATH="./rag/data"
export SKIP_RAG_INIT="true"
# 账号隔离需要认证生效，不再强制关闭；可通过 .env 控制 DISABLE_AUTH
export PYTHONUNBUFFERED="1"

echo "Configuration:"
echo "  RAG_VECTOR_DB_PATH: $RAG_VECTOR_DB_PATH"
echo "  RAG_KNOWLEDGE_BASE_PATH: $RAG_KNOWLEDGE_BASE_PATH"
echo "  SKIP_RAG_INIT: $SKIP_RAG_INIT"
echo "  DISABLE_AUTH: $DISABLE_AUTH"

# 4. 测试 Python 导入
echo "Testing Python imports..."
python -c "from api import app; print('✓ API module loaded successfully')" || {
    echo "❌ Failed to import API module"
    exit 1
}

# 5. 运行数据库迁移（新增表/字段）
echo "Running database migrations..."
python scripts/migrate_xiaozhi_20260807.py || {
    echo "❌ Database migration failed"
    exit 1
}

python scripts/migrate_account_isolation_20260810.py || {
    echo "❌ Account isolation migration failed"
    exit 1
}

# 6. 启动 nginx
echo "Starting nginx on port 7860..."
nginx -g "daemon off;" &
NGINX_PID=$!
echo "Nginx PID: $NGINX_PID"

# 7. 等待 nginx 启动
sleep 2

# 8. 启动 FastAPI 后端
echo "Starting FastAPI backend on port 7861..."
python main.py &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# 8. 等待进程启动
sleep 3

# 9. 检查进程状态
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start!"
    tail -50 ./logs/*.log 2>/dev/null || echo "No logs found"
    exit 1
fi

if ! kill -0 $NGINX_PID 2>/dev/null; then
    echo "❌ Nginx failed to start!"
    exit 1
fi

echo "=========================================="
echo "✓ Application started successfully!"
echo "  Frontend: http://0.0.0.0:7860"
echo "  Backend:  http://0.0.0.0:7861"
echo "=========================================="

# 10. 保持容器运行并监控进程
while true; do
    # 检查后端进程
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend process died!"
        exit 1
    fi

    # 检查 nginx 进程
    if ! kill -0 $NGINX_PID 2>/dev/null; then
        echo "❌ Nginx process died!"
        exit 1
    fi

    sleep 5
done
