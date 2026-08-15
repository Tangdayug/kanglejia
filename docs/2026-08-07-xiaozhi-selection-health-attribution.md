# 2026-08-07 小智接入判定与健康归属最小可用设计

## 变更目标

1. 解决“凡是连上这台机器的小智都会自动进入 SecondNature”的问题：增加基于**智能体名称**的接入判定。
2. 改善声纹白名单体验：新设备不再被直接拒绝，而是自动登记为 `pending` 状态。
3. 实现最小可用设计的**健康归属**：A 描述 B 时，健康观察记录在 B 身上。

## 核心改动

### 1. 系统与硬件的选择代码

新增环境变量：

- `XIAOZHI_AGENT_NAME`：本系统在小智生态中的智能体名称，默认 `second-nature`。
- `XIAOZHI_SYSTEM_TOKEN`：系统级接入令牌（可选，但生产建议开启）。
- `XIAOZHI_DEVICE_WHITELIST_ENABLED`：声纹白名单开关，默认 `false`。

接入判定顺序（`backend/service/xiaozhiService.py`）：

1. 校验 `system_token`（若配置）。
2. 校验 `agent_name` 是否匹配 `XIAOZHI_AGENT_NAME`（若配置）。
3. 校验声纹白名单：
   - 未开启：允许所有声纹。
   - 开启后：
     - 已存在且 `blocked`：拒绝。
     - 已存在且 `allowed/pending`：允许。
     - 不存在：自动登记为 `pending` 并允许接入。

硬件端在 WebSocket URL 或 `hello` 消息中携带：

```json
{
  "type": "hello",
  "voiceprint_id": "vp_xxx",
  "agent_name": "second-nature",
  "system_token": "your-token",
  "dialect_code": "mandarin"
}
```

URL 示例：

```
ws://your-host:8006/api/ws/xiaozhi?agent_name=second-nature&token=your-token
```

### 2. 最小可用健康归属

新增表 `health_observations`：

- `observer_voiceprint_id`：说话人（谁说的）。
- `subject_voiceprint_id`：被描述对象（说的是谁）。
- `content`：观察内容。
- `category`：观察类别（sleep/emotion/symptom/general）。
- `source_session_id`：来源会话。

归属规则（`backend/service/xiaozhiService.py`）：

1. 优先匹配文本中提到的其他已注册声纹 `display_name`。
2. 若未提到别人，默认归属说话人自己。
3. 健康上下文（`ChatService.generate_chat_response` 的 `subject_user_id`）使用被描述对象的档案。
4. 聊天记录仍归属说话人，保证对话连续性。

声纹模型 `xiaozhi_voiceprints` 新增字段：

- `display_name`：用于文本中匹配被描述对象。
- `verification_status`：`pending` / `allowed` / `blocked`。

### 3. 自动迁移

`start.sh` 启动时会执行：

```bash
python scripts/migrate_xiaozhi_20260807.py
```

该迁移脚本会：

- 为已存在的 `xiaozhi_voiceprints` 表添加 `display_name`、`verification_status` 字段。
- 创建 `health_observations` 表。
- 将旧数据 `verification_status` 兼容为 `allowed`。

## 测试

已通过的测试：

- `backend/test_xiaozhi_selection_attribution.py`：单元测试，覆盖 agent_name 校验、软白名单、健康归属、观察记录。
- `backend/test_xiaozhi_ws_live.py`：在线 WebSocket 测试，覆盖正确/错误 agent_name 与 token 的组合。

测试结果：

```text
✅ 所有 WebSocket 选择测试通过
✅ 所有测试通过
```

## Docker 启动命令

```bash
docker run -d --name secondnature-v2 \
  -p 8006:7860 \
  -e DEEPSEEK_API_KEY=sk-your-deepseek-key \
  -e JWT_SECRET_KEY=your-secret-key-must-be-at-least-32-characters-long \
  -e XIAOZHI_AGENT_NAME=second-nature \
  -e XIAOZHI_SYSTEM_TOKEN=your-xiaozhi-system-token \
  -e XIAOZHI_DEVICE_WHITELIST_ENABLED=true \
  -v secondnature-data:/app/backend/data \
  secondnature:latest
```

说明：

- 该命令启动一个新容器，不重启已有容器。
- 如需替换旧容器，先 `docker stop secondnature && docker rm secondnature`，再执行上述命令。
- 建议挂载卷以持久化 SQLite 数据。

## 硬件配置说明

小智硬件/固件需要配置：

1. 目标智能体名称：`second-nature`（与 `XIAOZHI_AGENT_NAME` 一致）。
2. 系统接入令牌：与 `XIAOZHI_SYSTEM_TOKEN` 一致。
3. WebSocket 地址：`ws://<服务器IP>:8006/api/ws/xiaozhi?agent_name=second-nature&token=<your-token>`。

只有同时满足“智能体名称匹配”和“令牌正确”的硬件，才会被路由到 SecondNature 系统。
