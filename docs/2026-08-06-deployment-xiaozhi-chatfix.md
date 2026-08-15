# 2026-08-06 部署、健康对话修复与小智硬件桥接实现记录

## 1. 部署情况

- 基于项目根目录 `Dockerfile` 构建镜像 `secondnature:latest`（约 886 MB）。
- 容器名称 `secondnature`，前端映射到主机端口 `8006`（README 写的前端端口），容器内部 nginx 监听 `7860`，后端监听 `7861`。
- 使用命名卷 `secondnature_data` 持久化 SQLite 数据库 `/app/backend/data/secondnature.db`。
- 环境变量：按 README.md 要求注入 `DEEPSEEK_API_KEY` 与 `JWT_SECRET_KEY`；`DASHSCOPE_API_KEY` 未在 README 中提供，留空。

## 2. 健康对话发送消息失败修复

### 问题现象

调用 `POST /api/chat/send` 返回 500：

```json
{"msg": "DASHSCOPE_API_KEY 环境变量未设置"}
```

### 根因

- `service/chatService.py` 原使用 `rag.retriever`（ChromaDB 版本），初始化时必须调用阿里云百炼嵌入模型，从而强制要求 `DASHSCOPE_API_KEY`。
- 项目 `requirements.txt` 与运行配置实际使用 FAISS 向量库，`start.sh` 也设置 `RAG_VECTOR_DB_PATH=./rag/data/faiss`。
- README.md 仅把 `DEEPSgit push -u origin master --force --no-verifyEEK_API_KEY` 与 `JWT_SECRET_KEY` 列为必需，`DASHSCOPE_API_KEY` 应可选。

### 修改内容

1. `backend/service/chatService.py`
   - 将 `from rag.retriever import get_rag_retriever` 改为 `from rag.retriever_faiss import get_rag_retriever`。
   - 引入 `CHAT_MAX_HISTORY_ROUNDS`，替换硬编码的 `10`/`6` 轮历史。
2. `backend/rag/retriever_faiss.py` / `backend/rag/retriever.py`
   - 新增 `NoOpRetriever` 降级检索器。
   - `get_rag_retriever()` 初始化失败时自动降级为无检索模式，确保聊天仍可用 DeepSeek 直接回复。
3. `backend/common/constant.py`
   - 默认 `RAG_VECTOR_DB_PATH` 改为 `./rag/data/faiss`。
   - 新增 `CHAT_MAX_HISTORY_ROUNDS=12`（可通过环境变量覆盖），满足 README “10 轮以上” 要求。
4. `backend/rag/vector_store.py`
   - 修复 `os.getenv(RAG_VECTOR_DB_PATH, ...)` 把路径值当成环境变量名的 bug。
5. `backend/requirements.txt`
   - 新增 `websockets==13.1` 以支持小智出站 WebSocket 桥接。

### 验证

```bash
curl -X POST http://localhost:8006/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"session_id":2,"message":"你好"}'
```

返回 200 与正常回复，`sources` 为 `null`（无 RAG 时正常）。

## 3. 小智（XiaoZhi）硬件 WebSocket 桥接实现

### 实现目标（对应 README.md 要求）

- 后端通过 WebSocket 桥接 `/opt/xiaozhi-server/` 里的小智智能体。
- 健康咨询对话系统开机自启，续期轮次放宽到 10 轮以上。
- 超时策略加入“情感续期”：检测到哭声/急促呼吸 → 不超时，保持 session。
- 打断敏感度调高：允许用户随时插话。
- session 复用：当天内同一声纹/用户复用健康档案，不重复问基础病史。
- ICOPE 初筛测试唤醒词“我要测试”，支持“独自回答/他人协助”选择（正则冗余匹配），中途“我要退出”退出测试。
- 轻量声纹识别、方言分类/TTS 映射 stub。

### 新增文件

1. `backend/model/xiaozhiSession.py`
   - `XiaozhiVoiceSession`：语音会话表，记录 session_type、state_json、last_active_at 等。
   - `XiaozhiVoiceprint`：声纹→用户映射表。
2. `backend/common/xiaozhi_prompts.py`
   - 老年人安全、自主、主动原则提示词。
   - ICOPE 筛查问题与提示、健康咨询开场白、情绪安抚话术、方言风格 stub。
3. `backend/service/xiaozhiService.py`
   - `XiaozhiWebSocketClient`：出站 WebSocket 客户端，连接 `XIAOZHI_SERVER_URL`（默认 `ws://localhost:8000/xiaozhi`，可被环境变量覆盖）。
   - `XiaozhiDialogueManager`：
     - 内存活跃会话管理 + 数据库持久化。
     - 唤醒词/退出词/情绪检测。
     - ICOPE 流程驱动。
     - 健康咨询流程，复用现有 `ChatService`。
     - 情感续期（`EMOTION_RENEWAL_SECONDS=600`）。
     - 高敏感打断处理。
     - 同一天同 voiceprint_id 复用会话与健康档案。
     - 轻量声纹识别 stub、方言映射 stub、EdgeTTS 语音合成。
4. `backend/api/xiaozhiAPI.py`
   - WebSocket 接入端 `/ws/xiaozhi`（JSON 协议：hello / stt / audio / interrupt / speak_done）。
   - REST 管理端：`/xiaozhi/status`、`/xiaozhi/sessions`、`/xiaozhi/session/{id}/reset`、`/xiaozhi/voiceprint/register`。

### 修改文件

- `backend/model/__init__.py`：导入 `xiaozhiSession` 以创建新表。
- `backend/api/__init__.py`：导入 `xiaozhiAPI` 注册路由。
- `nginx.conf`：增加 WebSocket Upgrade / Connection 头与长连接超时，确保外部 `ws://host:8006/api/ws/xiaozhi` 可正常透传。

### WebSocket 协议示例

```json
{"type": "hello", "voiceprint_id": "elder-001", "dialect_code": "mandarin"}
{"type": "stt", "text": "我要测试"}
{"type": "stt", "text": "独自回答"}
{"type": "interrupt", "text": "等等"}
{"type": "speak_done"}
```

### 验证

已使用容器内 Python 脚本连接 `ws://localhost:7861/ws/xiaozhi` 并完成：

1. hello → `session_ready`
2. “我要测试” → 进入 `icope_test` 模式并询问协助方式
3. “独自回答” → 开始 ICOPE 第一个问题

HTTP 健康检查全部 200：

- `GET /` → 200
- `GET /api/xiaozhi/status` → 200
- `GET /api/chat/sessions` → 200

## 4. Docker 启动命令（不重新构建镜像）

```bash
JWT_SECRET=$(openssl rand -hex 32)

docker run -d \
  --name secondnature \
  -p 8006:7860 \
  -e DEEPSEEK_API_KEY= \
  -e JWT_SECRET_KEY="$JWT_SECRET" \
  -e DASHSCOPE_API_KEY="" \
  -e XIAOZHI_SERVER_URL=ws://localhost:8000/xiaozhi \
  -v secondnature_data:/app/backend/data \
  --restart unless-stopped \
  secondnature:latest
```

说明：

- 使用已构建好的镜像 `secondnature:latest`，无需重新 `docker build`。
- 如需使用 RAG 知识库检索，需额外提供有效的 `DASHSCOPE_API_KEY`。
- 小智硬件代理服务器地址通过 `XIAOZHI_SERVER_URL` 配置；若实际代理不在 `localhost:8000`，请修改该变量。
- 数据持久化在 Docker 卷 `secondnature_data`，删除容器后数据不会丢失。


## 5. 小智接入鉴权（新增）

### 问题

此前任何能连到 `/ws/xiaozhi` 的客户端都会被当作本系统的小智设备处理，缺少“是否属于本系统”的判定逻辑。

### 实现方案

新增两层鉴权：

1. **系统级 Token**：环境变量 `XIAOZHI_SYSTEM_TOKEN`。
   - 未设置时保持兼容，不强制校验（开发/测试环境）。
   - 设置后，入站连接必须携带相同 token，否则返回 `rejected`。
2. **设备/声纹白名单**：环境变量 `XIAOZHI_DEVICE_WHITELIST_ENABLED=true` 开启。
   - 只有数据库 `xiaozhi_voiceprints` 中 `is_allowed=True` 的声纹才允许接入。
   - 未开启白名单时允许所有声纹（但 token 仍然校验）。

### 文件变更

- `backend/common/constant.py`：新增 `XIAOZHI_SYSTEM_TOKEN`、`XIAOZHI_DEVICE_WHITELIST_ENABLED`。
- `backend/model/xiaozhiSession.py`：`XiaozhiVoiceprint` 新增 `is_allowed`、`last_connected_at`。
- `backend/service/xiaozhiService.py`：
  - 新增 `validate_xiaozhi_token`、`is_voiceprint_allowed`、`record_voiceprint_connection`。
  - `get_or_create_voice_session` 接入前执行 token + 白名单校验。
  - 出站 `XiaozhiWebSocketClient` 自动把 token 拼到 URL 查询参数，供小智代理服务器校验。
- `backend/api/xiaozhiAPI.py`：
  - 从 WebSocket URL `?token=xxx` 或 hello 消息 `system_token` 获取 token。
  - 鉴权失败返回 `{"type":"error","action":"rejected","message":"..."}` 并断开连接。
  - 新增 REST 管理端点：`/xiaozhi/device/allow`、`/xiaozhi/devices`。

### 使用方式

1. 生成并配置系统 token：

```bash
XIAOZHI_TOKEN=$(openssl rand -hex 32)

docker run -d \
  --name secondnature \
  -p 8006:7860 \
  -e DEEPSEEK_API_KEY= \
  -e JWT_SECRET_KEY="$JWT_SECRET" \
  -e XIAOZHI_SYSTEM_TOKEN="$XIAOZHI_TOKEN" \
  -e XIAOZHI_DEVICE_WHITELIST_ENABLED=true \
  -e XIAOZHI_SERVER_URL=ws://localhost:8000/xiaozhi \
  -v secondnature_data:/app/backend/data \
  --restart unless-stopped \
  secondnature:latest
```

2. 注册允许的声纹：

```bash
curl -X POST http://localhost:8006/api/xiaozhi/voiceprint/register \
  -H "Content-Type: application/json" \
  -d '{"voiceprint_id":"elder-001","user_id":1}'
```

3. 硬件连接时携带 token：

```text
ws://<host>:8006/api/ws/xiaozhi?token=<XIAOZHI_TOKEN>
```

或在 hello 消息中携带：

```json
{"type":"hello","voiceprint_id":"elder-001","system_token":"<XIAOZHI_TOKEN>"}
```

4. 禁止某个设备：

```bash
curl -X POST http://localhost:8006/api/xiaozhi/device/allow \
  -H "Content-Type: application/json" \
  -d '{"voiceprint_id":"elder-001","is_allowed":false}'
```

### 验证

- 未配置 `XIAOZHI_SYSTEM_TOKEN` 时，普通 hello 仍可正常返回 `session_ready`。
- 单元验证脚本确认：
  - 正确 token → True，错误 token → False。
  - 白名单开启后：已注册且 `is_allowed=True` → True；已阻塞或未知声纹 → False。
