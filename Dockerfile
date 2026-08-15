# Stage 1: 构建前端
FROM node:18-alpine AS frontend-builder

# 使用 npm 镜像加速
RUN npm config set registry https://registry.npmmirror.com

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: 后端运行时
FROM python:3.11-slim

# 使用阿里云 PyPI 镜像加速
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set install.trusted-host mirrors.aliyun.com

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    nginx curl dos2unix \
    && rm -rf /var/lib/apt/lists/*

# 复制后端代码
COPY backend/ ./backend/

# 安装 Python 依赖（排除 mysqlclient，使用 SQLite）
COPY backend/requirements.txt ./backend/
RUN grep -v "mysqlclient" backend/requirements.txt > /tmp/requirements.txt && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# 创建数据目录
RUN mkdir -p /app/backend/data && chmod 777 /app/backend/data

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist/

# 复制配置文件
COPY nginx.conf /etc/nginx/nginx.conf
COPY start.sh /app/start.sh
RUN dos2unix /app/start.sh && chmod +x /app/start.sh

EXPOSE 7860

ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=7861
ENV MYSQL_HOST=localhost

# 数据持久化卷
VOLUME ["/app/backend/data"]

CMD ["/app/start.sh"]
