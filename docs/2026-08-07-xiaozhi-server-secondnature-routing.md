# 2026-08-07 xiaozhi-server 智能体按名称路由到 SecondNature

## 目标

当小智硬件连接 xiaozhi-server，且设备绑定的智能体名称为 `second-nature` 时，
自动把该 WebSocket 连接透明代理到 SecondNature 系统。

## 前置条件

- 已部署并启动 `xiaozhi-server`（本环境示例目录：`/home/ubuntu/xiaozhi-server-less`，生产环境常用 `/opt/xiaozhi-server`）。
- 已部署并启动 SecondNature（本环境端口 `8006`）。
- xiaozhi-server 容器能访问到 SecondNature 的 `/api/ws/xiaozhi`（这里使用 `host.docker.internal:8006`）。

## 实现方式

通过补丁方式修改 xiaozhi-server，不改动其镜像：

1. 新增 `data/secondnature_proxy.py`：查询 MySQL 获取设备绑定的智能体名称，若匹配则代理到 SecondNature。
2. 修改 `core/connection.py`：在连接建立后、业务处理前，调用代理判断。
3. 通过 `docker-compose.override.yml` 把上述文件绑定挂载到 xiaozhi-server 容器。

## 文件位置（相对于 xiaozhi-server 目录）

- `data/secondnature_proxy.py`
- `patches/connection.py`
- `docker-compose.override.yml`

SecondNature 仓库中保留了模板：

- `deploy/xiaozhi-server/docker-compose.override.yml.example`
- `docs/2026-08-07-xiaozhi-server-secondnature-routing.md`

## 配置说明

`docker-compose.override.yml` 示例：

```yaml
services:
  xiaozhi-esp32-server:
    environment:
      - SECONDNATURE_HOST=host.docker.internal
      - SECONDNATURE_PORT=8006
      - SECONDNATURE_PATH=/api/ws/xiaozhi
      # 若 SecondNature 设置了 XIAOZHI_SYSTEM_TOKEN，这里必须保持一致
      - SECONDNATURE_TOKEN=
      - SECONDNATURE_AGENT_NAME=second-nature
      - XIAOZHI_MYSQL_HOST=xiaozhi-esp32-server-db
      - XIAOZHI_MYSQL_PORT=3306
      - XIAOZHI_MYSQL_USER=root
      - XIAOZHI_MYSQL_PASSWORD=123456
      - XIAOZHI_MYSQL_DATABASE=xiaozhi_esp32_server
    volumes:
      - ./data/secondnature_proxy.py:/opt/xiaozhi-esp32-server/data/secondnature_proxy.py:ro
      - ./patches/connection.py:/opt/xiaozhi-esp32-server/core/connection.py:ro
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

注意：

- `SECONDNATURE_TOKEN` 必须和 SecondNature 的 `XIAOZHI_SYSTEM_TOKEN` 保持一致；未设置时留空即可。
- `host.docker.internal` 用于 xiaozhi-server 容器访问宿主机的 SecondNature。

## 应用方式

```bash
cd <xiaozhi-server-dir>
sudo docker-compose -f docker-compose_all.yml -f docker-compose.override.yml up -d xiaozhi-esp32-server
```

> 当前环境使用的是 `docker-compose` v1.29.2。如果用新镜像出现 `KeyError: 'ContainerConfig'`，说明 compose 版本与镜像元数据不兼容，可用以下任一方式绕过：
>
> 1. 用 `docker run` 手动创建/替换 `xiaozhi-esp32-server` 容器（保持相同网络、端口、卷挂载）。
> 2. 升级 Docker Compose 到 v2 以上。

## 小智服务端认证

xiaozhi-server 默认会从 manager-api 读取配置。如果返回的 `server.auth.enabled` 为 `true`，代理连接会因缺少有效 token 被认证拒绝。

测试时可在 manager-api 数据库关闭认证：

```bash
# 进入 xiaozhi-server DB 容器
mysql -uroot -p123456 xiaozhi_esp32_server
UPDATE sys_params SET param_value='false' WHERE param_code='server.auth.enabled';
# 清掉 redis 配置缓存
docker-compose exec xiaozhi-esp32-server-redis redis-cli DEL server:config
# 重启 xiaozhi-esp32-server
docker restart xiaozhi-esp32-server
```

生产环境应保留认证，并给代理连接提供有效 token。

## SecondNature 侧设置

SecondNature 默认智能体名称为 `second-nature`（`XIAOZHI_AGENT_NAME` 默认即此值）。

测试命令示例（关闭鉴权）：

```bash
docker run -d --name secondnature \
  -p 8006:8006 \
  -e DEEPSEEK_API_KEY=sk-your-key \
  -e JWT_SECRET_KEY=your-jwt-secret \
  -e XIAOZHI_AGENT_NAME=second-nature \
  -e XIAOZHI_SYSTEM_TOKEN=your-token \
  -e DISABLE_AUTH=true \
  -e XIAOZHI_DEVICE_WHITELIST_ENABLED=false \
  -v secondnature-data:/app/backend/data \
  second_nature_1_app
```

生产环境应去掉 `DISABLE_AUTH=true` 和 `XIAOZHI_DEVICE_WHITELIST_ENABLED=false`，并设置 `XIAOZHI_SYSTEM_TOKEN`。

## 验证

1. 在 xiaozhi-server DB 中确保设备绑定了 `second-nature` 智能体：

```sql
SELECT d.mac_address, a.agent_name
FROM ai_device d
LEFT JOIN ai_agent a ON d.agent_id = a.id
WHERE d.mac_address = 'd4:05:92:8d:31:29';
```

2. 用 Python 连接 xiaozhi-server WebSocket（建议用 URL 查询参数传 `device-id`）：

```python
import asyncio, websockets, json

async def test():
    uri = 'ws://localhost:8000/xiaozhi/v1/?device-id=d4:05:92:8d:31:29'
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "type": "hello",
            "version": 1,
            "transport": "websocket",
            "audio_params": {
                "format": "opus",
                "sample_rate": 24000,
                "channels": 1,
                "frame_duration": 60
            }
        }))
        msg = await asyncio.wait_for(ws.recv(), timeout=8)
        print(msg)

asyncio.run(test())
```

3. 期望收到已由 `session_ready` 转换后的标准 `hello`：

```json
{
  "type": "hello",
  "version": 1,
  "transport": "websocket",
  "session_id": 2,
  "audio_params": {
    "format": "opus",
    "sample_rate": 24000,
    "channels": 1,
    "frame_duration": 60
  }
}
```

## 注意事项

- 新版 websockets 客户端发送自定义 header 可能不被服务端识别，测试时建议用 `?device-id=...` 查询参数。
- 当前正在运行的旧 `secondnature` 容器未设置 `XIAOZHI_AGENT_NAME` 时，处于兼容模式，代理可连通但不校验 agent_name/token。
- 生产环境请配置 `XIAOZHI_AGENT_NAME=second-nature` 和 `XIAOZHI_SYSTEM_TOKEN`，并在 xiaozhi-server 侧保持一致。

## 协议转换

小智硬件期望的首次响应是 `{"type":"hello", ...}`，但 SecondNature 返回的是 `{"type":"control","action":"session_ready"}`。

`secondnature_proxy.py` 中的 `_translate_secondnature_response` 会把 `session_ready` 转换为 `hello`，避免硬件“等待响应超时”。

转换示例：

- 收到：`{"type":"control","action":"session_ready","session_id":4}`
- 转发给硬件：`{"type":"hello","version":1,"transport":"websocket","session_id":4,"audio_params":{"format":"opus","sample_rate":24000,"channels":1,"frame_duration":60}}`
