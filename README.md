# 飞书多维表格自动化 MCP

通过逆向工程的飞书内部 API，实现多维表格自动化工作流的编程管理。

## 能力

- 📋 列出多维表格的所有自动化工作流
- ➕ 创建定时消息提醒（每日/每周/一次性）
- 🔔 创建记录变化触发（当新增/修改记录时触发消息）
- 🛠️ 通用工作流创建接口

## 前置条件

### 1. 获取 Cookie

1. 浏览器登录飞书（mi.feishu.cn）
2. F12 → 应用程序 → Cookie → mi.feishu.cn
3. 复制以下三个值：

| Cookie 名 | 说明 |
|-----------|------|
| `session` | 用户会话 |
| `_csrf_token` | CSRF 令牌 |
| `passport_app_access_token` | 应用访问令牌 |

### 2. 设置环境变量

```bash
export FEISHU_SESSION="你的session值"
export FEISHU_CSRF_TOKEN="你的csrf_token"
export FEISHU_PASSPORT_TOKEN="你的passport_app_access_token"
```

### 3. 启动服务

```bash
python3 server.py --port 8067
```

## 工具列表

### list_workflows

列出多维表格的所有自动化工作流。

```json
{"app_token": "多维表格token"}
```

### create_workflow

通用工作流创建接口。

```json
{
  "app_token": "多维表格token",
  "config": {
    "title": "工作流标题",
    "trigger": {
      "type": "TimerTrigger",
      "rule": "DAILY",
      "hour": 10,
      "minute": 0
    },
    "actions": [{
      "type": "LarkMessageAction",
      "title": "提醒标题",
      "content": "提醒内容",
      "receivers": ["ou_xxx"],
      "color": "purple"
    }]
  }
}
```

### create_daily_message

创建每日定时消息提醒（快捷方式）。

```json
{
  "app_token": "多维表格token",
  "title": "每日提醒",
  "message": "今日待办...",
  "hour": 10,
  "minute": 0,
  "receivers": ["ou_xxx"]
}
```

### create_once_message

创建一次性消息提醒。

```json
{
  "app_token": "多维表格token",
  "title": "一次性提醒",
  "message": "提醒内容",
  "receivers": ["ou_xxx"]
}
```

### create_record_trigger

创建记录变化触发消息。

```json
{
  "app_token": "多维表格token",
  "title": "新记录通知",
  "message": "有新记录创建",
  "table_id": "tblxxx",
  "receivers": ["ou_xxx"]
}
```

## 技术细节

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/space/api/bitable/automation/create` | POST | 创建工作流 |
| `/space/api/bitable/{token}/automation/list` | GET | 列出工作流 |

### 认证方式

Cookie 认证（非 App Token），需要用户登录态。

### ⚠️ 关键发现

**不要传 `flowSchema` 和 `nodeSchema`！** 服务器会根据 draft 自动生成这两个字段。如果传了，会导致 cron 验证失败。

### 支持的触发器类型

| 类型 | triggerName | 说明 |
|------|-------------|------|
| TimerTrigger | cron | 定时触发 |
| RecordTrigger | record_change | 记录变化触发 |

### 支持的动作类型

| 类型 | 说明 |
|------|------|
| LarkMessageAction | 发送飞书消息 |

## 限制

- Cookie 会过期，需要定期更新
- 删除工作流需要更高权限（目前 403）
- 不同租户的域名不同（mi.feishu.cn vs feishu.cn）
- 高级权限多维表格需要 owner 身份

## 版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.1.0 | 2026-06-16 | 初版，验证 API 可行性 |
| 0.2.0 | 2026-06-16 | 重构为通用 MCP，支持多种触发器和动作 |
