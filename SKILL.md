---
name: feishu-automation-mcp
version: "0.4.0"
description: >
  飞书多维表格自动化 MCP：通过编程方式创建和管理多维表格的自动化工作流。
  支持 8 种触发器（定时、新增记录、条件触发、时间提醒、飞书消息、webhook、表单、按钮）
  和 10 种动作（发消息、新增/修改/查找记录、AI生成文本、HTTP请求等）。
  触发词：自动化工作流、定时提醒、自动通知、工作流管理、自动化MCP、
  创建提醒、定时消息、记录触发、飞书自动化、表单触发、按钮触发、webhook触发。
---

# 飞书多维表格自动化 MCP

通过逆向工程的飞书内部 API，实现多维表格自动化工作流的编程管理。

## 8 种触发器

| 类型 | 说明 |
|------|------|
| TimerTrigger | 定时触发 |
| SetRecordTrigger | 新增记录触发 |
| ChangeRecordTrigger | 条件触发 |
| ReminderTrigger | 记录时间触发 |
| LarkMessageTrigger | 飞书消息触发 |
| WebhookTrigger | Webhook触发 |
| FormTrigger | 表单提交触发 |
| ButtonTrigger | 按钮点击触发 |

## 10 个工具

- `list_workflows` — 列出所有工作流
- `create_daily_message` — 每日定时提醒
- `create_once_message` — 一次性提醒
- `create_new_record_notify` — 新增记录通知
- `create_change_record_notify` — 条件触发通知
- `create_time_reminder` — 时间提醒
- `create_lark_message_trigger` — 飞书消息触发
- `create_webhook_notify` — Webhook通知
- `create_form_notify` — 表单提交通知
- `create_button_notify` — 按钮点击通知

## 文件位置

- MCP Server: `/root/.openclaw/skills/feishu-automation-mcp/server.py`
- 文档: `/root/.openclaw/skills/feishu-automation-mcp/README.md`
