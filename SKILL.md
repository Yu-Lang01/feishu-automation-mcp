---
name: feishu-automation-mcp
version: "0.2.0"
description: >
  飞书多维表格自动化 MCP：通过编程方式创建和管理多维表格的自动化工作流。
  支持定时消息提醒、记录变化触发等功能。
  触发词：自动化工作流、定时提醒、自动通知、工作流管理、自动化MCP、
  创建提醒、定时消息、记录触发、飞书自动化。
---

# 飞书多维表格自动化 MCP

通过逆向工程的飞书内部 API，实现多维表格自动化工作流的编程管理。

## 能力

- 📋 列出多维表格的所有自动化工作流
- ➕ 创建定时消息提醒（每日/每周/一次性）
- 🔔 创建记录变化触发（当新增/修改记录时触发消息）
- 🛠️ 通用工作流创建接口

## 前置条件

### 环境变量

```bash
export FEISHU_SESSION="你的session值"
export FEISHU_CSRF_TOKEN="你的csrf_token"
export FEISHU_PASSPORT_TOKEN="你的passport_app_access_token"
```

### 启动 MCP Server

```bash
python3 /root/.openclaw/skills/feishu-automation-mcp/server.py --port 8067 &
```

## 工具调用

### 列出工作流

```bash
curl -X POST http://localhost:8067 -H 'Content-Type: application/json' -d '{
  "jsonrpc": "2.0", "id": 1, "method": "tools/call",
  "params": {"name": "list_workflows", "arguments": {"app_token": "多维表格token"}}
}'
```

### 创建每日提醒

```bash
curl -X POST http://localhost:8067 -H 'Content-Type: application/json' -d '{
  "jsonrpc": "2.0", "id": 1, "method": "tools/call",
  "params": {"name": "create_daily_message", "arguments": {
    "app_token": "多维表格token",
    "title": "每日提醒",
    "message": "今日待处理任务...",
    "hour": 10, "minute": 0
  }}
}'
```

### 创建记录触发

```bash
curl -X POST http://localhost:8067 -H 'Content-Type: application/json' -d '{
  "jsonrpc": "2.0", "id": 1, "method": "tools/call",
  "params": {"name": "create_record_trigger", "arguments": {
    "app_token": "多维表格token",
    "title": "新记录通知",
    "message": "有新记录创建",
    "table_id": "tblxxx"
  }}
}'
```

## ⚠️ 关键踩坑记录

1. **不要传 flowSchema 和 nodeSchema** — 服务器会根据 draft 自动生成，传了会导致 cron 验证失败
2. **Cookie 会过期** — 需要定期更新环境变量
3. **删除需要更高权限** — 目前 API 删除返回 403
4. **不同租户域名不同** — 通过 FEISHU_DOMAIN 环境变量配置

## 文件位置

- MCP Server: `/root/.openclaw/skills/feishu-automation-mcp/server.py`
- 文档: `/root/.openclaw/skills/feishu-automation-mcp/README.md`
