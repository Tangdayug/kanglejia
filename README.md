# SecondNature - 内在能力减退管理支持系统

## 环境变量配置

### 必需环境变量:
- `DEEPSEEK_API_KEY` - DeepSeek API 密钥
- `JWT_SECRET_KEY` - JWT 密钥 (至少32字符)

### 数据库配置 (可选):
系统默认使用 **SQLite**，无需额外配置。

如需使用 MySQL，配置以下环境变量：
- `MYSQL_HOST` - MySQL 主机地址
- `MYSQL_PORT` - MySQL 端口
- `MYSQL_USER` - MySQL 用户名
- `MYSQL_PASSWORD` - MySQL 密码
- `MYSQL_DATABASE` - 数据库名称

## 端口说明
- 应用前端端口: 8006
- 内部后端端口: 8007

## Docker 运行

### 1. 准备环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 DEEPSEEK_API_KEY 和 JWT_SECRET_KEY
```

### 2. 启动（生产模式，无热重载）

```bash
docker compose up --build -d
```

查看日志：

```bash
docker compose logs --tail 50 -f
```

访问：http://localhost:8006

### 3. 开发模式（前后端全部热更新，无需重启容器）

```bash
# 1. 准备本地密钥
 cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 DEEPSEEK_API_KEY 和 JWT_SECRET_KEY

# 2. 启动开发组合（backend 热重载 + frontend 自动构建）
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

开发时：
- 修改 `backend/` 下的 `.py` 文件 → uvicorn 自动重载后端。
- 修改 `frontend/src/` 下的 `.vue` / `.css` / `.scss` → `frontend` 服务自动重新构建 `dist/`，nginx 立即 serving 最新前端。
- 都不需要重启容器。

如果你习惯用 `docker-compose.override.yml`（已加入 `.gitignore`），也可以：

```bash
cp docker-compose.dev.yml docker-compose.override.yml
# 按需编辑，填入密钥等
docker compose up -d
```

### 4. 更新向量知识库（不重启服务）

向 `backend/rag/data/` 添加新的 PDF/Markdown 文档后，调用接口重建索引：

```bash
curl -X POST http://localhost:8006/api/rag/rebuild \
  -H "Authorization: Bearer <your_jwt_token>"
```

### 5. 停止

```bash
docker compose down
```

## 资源限制

`docker-compose.yml` 已为 4 核 / 8 GB 机器设置：
- CPU 限制：3 核
- 内存限制：7 GB（保留 2 GB）

## 语音问题
- 接入方言分类头，调用云端方言大模型，建立方言规则映射表，用对应方言的tts回复
- 建立提示词库，考虑老人交互的安全、自主性、主动性问题
- 选择轻量声纹识别器识别老人身份

## 桥接硬件
- 此功能为硬件功能，软件已实现
- 后端通过 WebSocket 桥接 `/opt/xiaozhi-server/` 里的小智智能体。
- 注意此智能体是本项目调整过的（如果此项目没智能体，则选用此项目的硬件交互逻辑：内在能力减退初筛测试和健康咨询对话系统，）
- 内在能力减退初筛测试的唤醒词为“我要测试”，进入测试，语音提示“您要独自回答还是他人协助”，如果回答“独自回答”，则进入独自回答，反之亦然，注意用正则表达式匹配选择逻辑，并用冗余备份，中途要退出可以说“我要退出”则退出内在能力减退初筛测试
- 健康咨询对话系统为开机自启，续期轮次	放宽到 10 轮以上	病情交流需要多轮追问
超时策略	加入"情感续期"	检测到哭声/急促呼吸 → 不超时，保持 session
打断敏感度	调高	老人可能随时补充症状，要允许随时插话
session 复用	当天内同一用户复用健康档案	不用每次重新问基础病史
- 精心设计面向续期轮次	放宽到 10 轮以上	病情交流需要多轮追问
超时策略	加入"情感续期"	检测到哭声/急促呼吸 → 不超时，保持 session
打断敏感度	调高	老人可能随时补充症状，要允许随时插话
session 复用	当天内同一用户复用健康档案	不用每次重新问基础病史
- 精心设计老人的会话逻辑

## 数据持久化
- SQLite 数据库存储在容器内 `/app/backend/data/secondnature.db`
- 已通过命名卷 `secondnature-data` 持久化

## 提交代码

仓库地址：`https://github.com/jiayusu/kanglejia.git`

本地提交与推送流程：

```bash
# 1. 查看改动
git status

# 2. 添加修改的文件（不要添加 .env 等密钥文件，它们已被 .gitignore 忽略）
git add <file1> <file2>
# 或一次性添加所有改动
git add .

# 3. 提交，写清楚本次改动
git commit -m "feat(scope): 简短描述

详细说明本次改动了什么、为什么改动、如何验证。"

# 4. 推送到 GitHub
# 使用 HTTPS + Personal Access Token
git push https://<username>:<token>@github.com/jiayusu/kanglejia.git master

# 或使用 SSH（推荐长期开发）
git push origin master
```

### 注意事项
- `.env`、`docker-compose.override.yml` 等含密钥的文件已加入 `.gitignore`，**不要**手动强制提交。
- 提交信息参考格式：`type(scope): subject`，例如：
  - `fix(rag): lazy-load embedding model to avoid blocking startup`
  - `feat(xiaozhi): allow hardware connection without voiceprint binding`
  - `docs(readme): add commit workflow`
- 提交前确保 Docker 服务还能正常启动，关键接口可 `curl http://localhost:8006/api/health` 验证。

## 沉淀文档
- 每次更新代码逻辑需要在本目录的子目录下新建md文档详细记录
- 注意记录主要功能的更新
