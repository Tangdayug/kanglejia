# Stage 1: 构建前端
FROM node:20-alpine AS frontend-builder

# 使用 npm 镜像加速
RUN npm config set registry https://registry.npmmirror.com

WORKDIR /app/frontend
COPY frontend/package.json ./
# 不复制 package-lock.json：原 lock 中部分包锁定在腾讯云内网镜像，
# Docker 内无法解析；按 package.json 用 npmmirror 重新安装。
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# Stage 2: 后端运行时
FROM python:3.11-slim

# 使用阿里云 PyPI 镜像加速
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn

WORKDIR /app

# 使用阿里云 Debian 镜像加速 apt
RUN sed -i 's|http://deb.debian.org/debian|https://mirrors.aliyun.com/debian|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|http://deb.debian.org/debian-security|https://mirrors.aliyun.com/debian-security|g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y \
    nginx curl dos2unix gettext-base \
    && rm -rf /var/lib/apt/lists/*

# 复制后端代码
COPY backend/ ./backend/

# 安装 Python 依赖（排除 mysqlclient，使用 SQLite）
COPY backend/requirements.txt ./backend/

# 把容易在批量下载时卡住的大包拆成多组安装，降低单条 RUN 的网络/缓冲压力。
# torch/sentence-transformers 及其依赖若一次性安装会触发镜像连接异常，
# 因此按“大 wheel 单独装 + 运行时依赖小批量装”的方式分批处理。
ENV PIP_NO_CACHE_DIR=1
ENV PIP_PREFER_BINARY=1
ENV PIP_DEFAULT_TIMEOUT=180

# 第 1 组：numpy（torch 与 scikit-learn 共用，先固定 1.x 避免被依赖自动升到 2.x）
RUN pip install --timeout 180 --retries 5 numpy==1.26.4

# 第 2 组：PyTorch CPU-only（仅安装 torch 自身，依赖在下一组单独装）
RUN pip install --timeout 180 --retries 5 --no-deps \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.3.1+cpu

# 第 3 组：torch 运行时依赖（显式版本，避免 pip 拉取镜像上文件缺失的最新版）
RUN pip install --timeout 180 --retries 5 \
    filelock==3.32.3 typing_extensions==4.16.0 sympy==1.14.0 \
    networkx==3.6.1 jinja2==3.1.6 fsspec==2026.7.0 \
    MarkupSafe==3.0.3 mpmath==1.3.0

# 第 4 组：sentence-transformers（仅自身）
RUN pip install --timeout 180 --retries 5 --no-deps sentence-transformers==3.0.1

# 第 5 组：sentence-transformers / transformers 运行时依赖（含 numpy 固定）
RUN pip install --timeout 180 --retries 5 \
    numpy==1.26.4 transformers==4.41.2 huggingface-hub==0.23.4 \
    tokenizers==0.19.1 safetensors==0.4.3 scipy==1.13.1 \
    scikit-learn==1.5.0 Pillow==10.4.0 tqdm==4.66.4 regex==2024.5.15

# 第 6 组：向量检索
RUN pip install --timeout 180 --retries 5 faiss-cpu==1.13.2

# 第 7 组：Web 框架与核心依赖
RUN pip install --timeout 180 --retries 5 \
    fastapi[all]==0.128.0 uvicorn[standard]==0.40.0 python-dotenv==1.2.1 \
    starlette==0.50.0 pydantic==2.12.5 python-multipart==0.0.21

# 第 8 组：数据库、认证、安全
RUN pip install --timeout 180 --retries 5 \
    SQLAlchemy==2.0.23 pymysql==1.1.2 PyJWT==2.11.0 passlib==1.7.4 \
    bcrypt==4.0.1 cryptography==46.0.4

# 第 9 组：TTS、LLM、网络、工具
RUN pip install --timeout 180 --retries 5 \
    edge-tts==7.2.7 tabulate==0.9.0 openai==1.6.1 httpx==0.28.1 \
    websockets==13.1 requests==2.32.5 orjson==3.11.5 pytz==2025.2 \
    python-dateutil==2.9.0.post0 PyYAML==6.0.3 psutil==5.9.6

# 第 10 组：文档处理
RUN pip install --timeout 180 --retries 5 \
    PyPDF2==3.0.1 python-docx==0.8.11 markdown==3.7

# 最后再固定一次 numpy，防止前面某组因为依赖解析临时升级到 2.x
RUN pip install --timeout 60 --retries 3 numpy==1.26.4

# 创建数据目录
RUN mkdir -p /app/backend/data && chmod 777 /app/backend/data

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist/

# 复制配置文件
COPY nginx.conf /etc/nginx/nginx.conf
COPY start.sh /app/start.sh
RUN dos2unix /app/start.sh && chmod +x /app/start.sh

# 容器对外端口（默认 8006，与 README/xiaozhi-server-less 代理保持一致）
ENV PORT=8006
# FastAPI 内部监听端口（默认 8007）
ENV INTERNAL_PORT=8007

EXPOSE ${PORT}

ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV MYSQL_HOST=localhost

# 数据持久化卷
VOLUME ["/app/backend/data"]

CMD ["/app/start.sh"]
