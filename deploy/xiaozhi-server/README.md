# xiaozhi-server 外部接入说明

本目录**不包含** `xiaozhi-server` 本身的代码。`/opt/xiaozhi-server` 或 `/opt/xiaozhi-esp32-server` 应作为独立项目部署，本仓库只提供与其对接所需的模板和文档。

## 目录内容

- `docker-compose.override.yml.example`：用于把 SecondNature 接入 xiaozhi-server 的 Docker Compose override 模板。

## 部署步骤

1. 在服务器上独立部署 `xiaozhi-server`（通常位于 `/opt/xiaozhi-server`）。
2. 根据 `docs/2026-08-07-xiaozhi-server-secondnature-routing.md` 在 `/opt/xiaozhi-server` 中添加代理脚本与补丁。
3. 把本目录的 `docker-compose.override.yml.example` 复制到 `/opt/xiaozhi-server/docker-compose.override.yml` 并填入真实配置。
4. 确保 SecondNature 的 `XIAOZHI_SYSTEM_TOKEN` 与本文件中的 `SECONDNATURE_TOKEN` 一致。
5. 在 `/opt/xiaozhi-server` 目录重启 xiaozhi-server 容器。

## 为什么不把 xiaozhi-server 迁进本仓库

- `xiaozhi-server` 是独立维护的硬件接入网关，有自己的版本、数据库和网络。
- SecondNature 只通过 WebSocket/REST 与其对接，保持解耦便于各自升级。
