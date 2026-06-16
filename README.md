# 飞书多维表格自动化 MCP

通过逆向工程的飞书内部 API，实现多维表格自动化工作流的编程管理。

## 支持的触发器类型

| 类型 | 说明 |
|------|------|
| TimerTrigger | 定时触发（每日/每周/一次性） |
| RecordTrigger | 记录变化触发（新增/修改/删除） |
| FormTrigger | 表单提交触发 |
| ButtonTrigger | 按钮点击触发 |

## 支持的动作类型

| 类型 | 说明 |
|------|------|
| LarkMessageAction | 发送飞书消息 |
| BitableAction | 更新记录字段 |
| SendEmailAction | 发送邮件 |
| HttpAction | HTTP 请求 |
| WebhookAction | Webhook 回调 |
| ConditionAction | 条件判断 |
| BitableAutomationAction | 自动化动作 |

## 工具列表

### list_workflows

列出多维表格的所有自动化工作流。

```json
{"app_token": "多维表格token"}
```

### create_workflow

通用工作流创建接口（支持所有触发器和动作类型）。

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

### create_form_trigger

创建表单提交触发消息。

```json
{
  "app_token": "多维表格token",
  "title": "表单提交通知",
  "message": "有新表单提交",
  "table_id": "tblxxx",
  "receivers": ["ou_xxx"]
}
```

### create_button_trigger

创建按钮点击触发消息。

```json
{
  "app_token": "多维表格token",
  "title": "按钮点击通知",
  "message": "按钮被点击",
  "table_id": "tblxxx",
  "field_id": "fldxxx",
  "receivers": ["ou_xxx"]
}
```

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

## 版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.1.0 | 2026-06-16 | 初版，验证 API 可行性 |
| 0.2.0 | 2026-06-16 | 重构为通用 MCP |
| 0.3.0 | 2026-06-16 | 支持 4 种触发器 + 7 种动作类型 |
