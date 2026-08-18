# xiaozhi-server 外部接入说明

本目录**不包含** `xiaozhi-server` 本身的代码。`xiaozhi-server` 应作为独立项目部署（本环境示例目录为 `/home/ubuntu/xiaozhi-server-less`，生产环境常用 `/opt/xiaozhi-server`），本仓库只提供与其对接所需的模板和文档。

## 目录内容

- `docker-compose.override.yml.example`：用于把 SecondNature 接入 xiaozhi-server 的 Docker Compose override 模板。

## 部署步骤

1. 在服务器上独立部署 `xiaozhi-server`。
2. 根据 `docs/2026-08-07-xiaozhi-server-secondnature-routing.md` 在 xiaozhi-server 目录中添加代理脚本与补丁：
   - `data/secondnature_proxy.py`
   - `patches/connection.py`
3. 把本目录的 `docker-compose.override.yml.example` 复制到 xiaozhi-server 目录下，命名为 `docker-compose.override.yml`，并填入真实配置。
4. 确保 SecondNature 的 `XIAOZHI_SYSTEM_TOKEN` 与本文件中的 `SECONDNATURE_TOKEN` 一致（未设置时两者都留空）。
5. 如果 xiaozhi-server 从 manager-api 读取到的 `server.auth.enabled` 为 `true`，代理连接会被认证拒绝；测试时可在 DB 中将其设为 `false` 并清空 Redis 缓存，生产环境请保留认证并提供有效 token。
6. 在 xiaozhi-server 目录重启 xiaozhi-server 容器：

```bash
cd <xiaozhi-server-dir>
sudo docker-compose -f docker-compose_all.yml -f docker-compose.override.yml up -d xiaozhi-esp32-server
```

> 注意：当前环境的 `docker-compose` v1.29.2 在重新创建容器时可能报错 `KeyError: 'ContainerConfig'`。此时可改用 `docker run` 手动重建 `xiaozhi-esp32-server` 容器，或升级 Docker Compose。

## 验证

参考 `docs/2026-08-07-xiaozhi-server-secondnature-routing.md` 中的“验证”章节，连接 `ws://localhost:8000/xiaozhi/v1/?device-id=<设备MAC>`，应收到转换后的 `hello` 响应。

## 为什么不把 xiaozhi-server 迁进本仓库

- `xiaozhi-server` 是独立维护的硬件接入网关，有自己的版本、数据库和网络。
- SecondNature 只通过 WebSocket/REST 与其对接，保持解耦便于各自升级。
