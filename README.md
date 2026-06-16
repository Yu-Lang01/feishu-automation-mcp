# 飞书多维表格自动化 MCP

通过逆向工程的飞书内部 API，实现多维表格自动化工作流的编程管理。

## 支持的触发器（8种）

| 触发器 | triggerName | 说明 |
|--------|-------------|------|
| TimerTrigger | `cron` | 定时触发（每日/每周/一次性） |
| SetRecordTrigger | `setRecord` | 新增记录触发 |
| ChangeRecordTrigger | `changeRecord` | 记录满足条件触发 |
| ReminderTrigger | `datetimeField` | 到达记录中的时间触发 |
| LarkMessageTrigger | `larkMessage` | 接收到飞书消息触发 |
| WebhookTrigger | `webhook` | 接收到webhook触发 |
| FormTrigger | `form_submit` | 表单提交触发 |
| ButtonTrigger | `button_click` | 按钮点击触发 |

## 支持的动作（10种）

| 动作 | 说明 |
|------|------|
| LarkMessageAction | 发送飞书消息 |
| AddRecordAction | 新增记录 |
| SetRecordAction | 修改记录 |
| FindRecordAction | 查找记录 |
| GenerateAiTextAction | AI生成文本 |
| HTTPClientAction | 发送HTTP请求 |
| BitableAction | 更新字段 |
| SendEmailAction | 发送邮件 |
| WebhookAction | Webhook回调 |
| ConditionAction | 条件判断 |

## 工具列表（10个）

### list_workflows
列出多维表格的所有自动化工作流。
```json
{"app_token": "多维表格token"}
```

### create_daily_message
创建每日定时消息提醒。
```json
{
  "app_token": "多维表格token",
  "title": "每日提醒",
  "message": "今日待办...",
  "table_id": "tblxxx",
  "hour": 10, "minute": 0,
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

### create_new_record_notify
新增记录时发送通知。
```json
{
  "app_token": "多维表格token",
  "title": "新记录通知",
  "message": "有新记录创建",
  "table_id": "tblxxx",
  "receivers": ["ou_xxx"]
}
```

### create_change_record_notify
记录满足条件时发送通知。
```json
{
  "app_token": "多维表格token",
  "title": "条件触发通知",
  "message": "记录已满足条件",
  "table_id": "tblxxx",
  "field_id": "fldxxx",
  "receivers": ["ou_xxx"]
}
```

### create_time_reminder
到达记录中的时间时发送提醒。
```json
{
  "app_token": "多维表格token",
  "title": "时间提醒",
  "message": "时间到了",
  "table_id": "tblxxx",
  "field_id": "fldxxx",
  "hour": 9, "minute": 0,
  "receivers": ["ou_xxx"]
}
```

### create_lark_message_trigger
接收到飞书消息时触发。
```json
{
  "app_token": "多维表格token",
  "title": "消息触发通知",
  "message": "收到新消息",
  "scope": "at",
  "receivers": ["ou_xxx"]
}
```

### create_webhook_notify
接收到webhook时发送通知。
```json
{
  "app_token": "多维表格token",
  "title": "Webhook通知",
  "message": "收到webhook",
  "receivers": ["ou_xxx"]
}
```

### create_form_notify
表单提交时发送通知。
```json
{
  "app_token": "多维表格token",
  "title": "表单提交通知",
  "message": "有新表单提交",
  "table_id": "tblxxx",
  "receivers": ["ou_xxx"]
}
```

### create_button_notify
按钮点击时发送通知。
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

### ref_ 前缀系统

飞书内部 API 使用 `ref_` 前缀引用 table 和 field：
- 表ID：`ref_` + 真实table_id
- 字段ID：`ref_` + 真实table_id + `_` + 真实field_id

MCP 会自动处理前缀生成和 `extra.TableMap` 映射。

### ⚠️ 关键发现

**不要传 `flowSchema` 和 `nodeSchema`！** 服务器会根据 draft 自动生成这两个字段。

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/space/api/bitable/automation/create` | POST | 创建工作流 |
| `/space/api/bitable/{token}/automation/list` | GET | 列出工作流 |

## 版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.1.0 | 2026-06-16 | 初版，验证 API 可行性 |
| 0.2.0 | 2026-06-16 | 重构为通用 MCP |
| 0.3.0 | 2026-06-16 | 支持 TimerTrigger + LarkMessageAction |
| 0.4.0 | 2026-06-16 | 支持全部 8 种触发器 + 10 种动作 + ref_ 前缀系统 |
