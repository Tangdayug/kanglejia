# 2026-08-07 xiaozhi-server 智能体按名称路由到 SecondNature

## 目标

实现：当小智硬件连接 xiaozhi-server，且设备绑定的智能体名称为 `second-nature` 时，
自动把该 WebSocket 连接透明代理到 SecondNature 系统。

## 实现方式

通过补丁方式修改 xiaozhi-server，不改动其镜像：

1. 新增 `/opt/xiaozhi-server/data/secondnature_proxy.py`：查询 MySQL 获取设备绑定的智能体名称，若匹配则代理到 SecondNature。
2. 修改 `/opt/xiaozhi-server/core/connection.py`：在连接建立后、业务处理前，调用代理判断。
3. 通过 `docker-compose.override.yml` 把上述文件绑定挂载到 xiaozhi-server 容器。

## 文件位置

- `/opt/xiaozhi-server/data/secondnature_proxy.py`
- `/opt/xiaozhi-server/patches/connection.py`
- `/opt/xiaozhi-server/docker-compose.override.yml`

## 配置说明

在 `/opt/xiaozhi-server/docker-compose.override.yml` 中配置：

```yaml
services:
  xiaozhi-esp32-server:
    environment:
      - SECONDNATURE_HOST=host.docker.internal
      - SECONDNATURE_PORT=8006
      - SECONDNATURE_PATH=/api/ws/xiaozhi
      - SECONDNATURE_TOKEN=your-xiaozhi-system-token
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

- `SECONDNATURE_TOKEN` 必须和 SecondNature 的 `XIAOZHI_SYSTEM_TOKEN` 一致。
- `host.docker.internal` 用于 xiaozhi-server 容器访问宿主机的 SecondNature。

## 应用方式

```bash
cd /opt/xiaozhi-server
sudo docker compose -f docker-compose_all.yml -f docker-compose.override.yml up -d xiaozhi-esp32-server
```

## 验证结果

测试脚本：`backend/test_xiaozhi_server_proxy.py`

| 设备 | 绑定智能体 | 结果 |
|------|-----------|------|
| d4:05:92:8d:31:29 | second-nature | ✅ 代理到 SecondNature，返回 `session_ready` |
| d4:05:92:8d:20:1d | 其他 | ✅ 由 xiaozhi-server 本地处理 |

## 注意事项

- 当前正在运行的旧 `secondnature` 容器未设置 `XIAOZHI_AGENT_NAME`，处于兼容模式，代理可连通但不校验 agent_name/token。
- 生产环境请使用新的 SecondNature 容器并设置 `-e XIAOZHI_AGENT_NAME=second-nature -e XIAOZHI_SYSTEM_TOKEN=your-token`。

## 2026-08-07 更新：协议转换

小智硬件期望的首次响应是 `{"type":"hello", ...}`，但 SecondNature 返回的是 `{"type":"control","action":"session_ready"}`。

已增加 `_translate_secondnature_response` 函数，把 `session_ready` 转换为 `hello`，避免硬件“等待响应超时”。

转换示例：
- 收到：`{"type":"control","action":"session_ready","session_id":4}`
- 转发给硬件：`{"type":"hello","version":1,"transport":"websocket","session_id":4,"audio_params":{"format":"opus","sample_rate":24000,"channels":1,"frame_duration":60}}`

## 2026-08-07 更新：重启 SecondNature 容器

已按要求重启 SecondNature 容器，配置：
- 加入 `xiaozhi-server_default` Docker 网络
- `XIAOZHI_SERVER_URL=ws://xiaozhi-esp32-server:8000/xiaozhi`
- `XIAOZHI_AGENT_NAME=second-nature`
- `XIAOZHI_SYSTEM_TOKEN` 与 xiaozhi-server 代理端保持一致
- 保留原 SQLite 数据库文件

启动命令示例：
```bash
docker run -d --name secondnature \
  --network xiaozhi-server_default \
  -p 8006:7860 \
  -e DEEPSEEK_API_KEY=sk-your-key \
  -e JWT_SECRET_KEY=your-jwt-secret \
  -e XIAOZHI_AGENT_NAME=second-nature \
  -e XIAOZHI_SYSTEM_TOKEN=your-token \
  -e XIAOZHI_DEVICE_WHITELIST_ENABLED=true \
  -e XIAOZHI_SERVER_URL=ws://xiaozhi-esp32-server:8000/xiaozhi \
  -v /path/to/secondnature.db:/app/backend/data/secondnature.db \
  secondnature:latest
```

验证：
- SecondNature 日志显示 `[XiaoZhi] outbound connected to ws://xiaozhi-esp32-server:8000/xiaozhi`
- 代理测试显示 second-nature 设备收到标准 `hello` 响应
