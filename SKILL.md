---
name: feishu-automation-mcp
version: "0.3.0"
description: >
  飞书多维表格自动化 MCP：通过编程方式创建和管理多维表格的自动化工作流。
  支持定时消息、记录变化、表单提交、按钮点击等触发器，以及发消息、更新记录、发邮件、HTTP请求等动作。
  触发词：自动化工作流、定时提醒、自动通知、工作流管理、自动化MCP、
  创建提醒、定时消息、记录触发、飞书自动化、表单触发、按钮触发。
---

# 飞书多维表格自动化 MCP

通过逆向工程的飞书内部 API，实现多维表格自动化工作流的编程管理。

## 支持的触发器

| 类型 | 说明 |
|------|------|
| TimerTrigger | 定时触发（每日/每周/一次性） |
| RecordTrigger | 记录变化触发 |
| FormTrigger | 表单提交触发 |
| ButtonTrigger | 按钮点击触发 |

## 支持的动作

| 类型 | 说明 |
|------|------|
| LarkMessageAction | 发送飞书消息 |
| BitableAction | 更新记录字段 |
| SendEmailAction | 发送邮件 |
| HttpAction | HTTP 请求 |
| WebhookAction | Webhook 回调 |
| ConditionAction | 条件判断 |
| BitableAutomationAction | 自动化动作 |

## 工具（7个）

- `list_workflows` — 列出所有工作流
- `create_workflow` — 通用创建接口
- `create_daily_message` — 每日定时提醒
- `create_once_message` — 一次性提醒
- `create_record_trigger` — 记录变化触发
- `create_form_trigger` — 表单提交触发
- `create_button_trigger` — 按钮点击触发

## 文件位置

- MCP Server: `/root/.openclaw/skills/feishu-automation-mcp/server.py`
- 文档: `/root/.openclaw/skills/feishu-automation-mcp/README.md`
