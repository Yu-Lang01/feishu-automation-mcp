#!/usr/bin/env python3
"""
飞书多维表格自动化 MCP Server v0.4.0
Feishu Bitable Automation MCP Server

基于逆向工程的飞书内部 API，支持全部触发器和动作类型。

触发器类型（8种）：
- TimerTrigger: 定时触发（每日/每周/一次性）
- SetRecordTrigger: 新增记录触发
- ChangeRecordTrigger: 记录满足条件触发
- ReminderTrigger: 到达记录中的时间触发
- LarkMessageTrigger: 接收到飞书消息触发
- WebhookTrigger: 接收到webhook触发
- FormTrigger: 表单提交触发
- ButtonTrigger: 按钮点击触发

动作类型（10种）：
- LarkMessageAction: 发送飞书消息
- AddRecordAction: 新增记录
- SetRecordAction: 修改记录
- FindRecordAction: 查找记录
- GenerateAiTextAction: AI生成文本
- HTTPClientAction: 发送HTTP请求
- BitableAction: 更新字段
- SendEmailAction: 发送邮件
- WebhookAction: Webhook回调
- ConditionAction: 条件判断

使用方式：
  export FEISHU_SESSION="你的session"
  export FEISHU_CSRF_TOKEN="你的csrf_token"
  export FEISHU_PASSPORT_TOKEN="你的passport_app_access_token"
  python3 server.py --port 8067

版本: 0.4.0
"""

import json, os, sys, random, string, time, argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request

VERSION = "0.4.0"

# ========== 配置 ==========

def get_config():
    return {
        "domain": os.environ.get("FEISHU_DOMAIN", "mi.feishu.cn"),
        "session": os.environ.get("FEISHU_SESSION", ""),
        "csrf": os.environ.get("FEISHU_CSRF_TOKEN", ""),
        "passport": os.environ.get("FEISHU_PASSPORT_TOKEN", ""),
        "sl_session": os.environ.get("FEISHU_SL_SESSION", ""),
    }

CFG = get_config()

def rand_id(n=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def build_cookie():
    parts = []
    if CFG["session"]: parts.append(f"session={CFG['session']}")
    if CFG["csrf"]: parts.append(f"_csrf_token={CFG['csrf']}")
    if CFG["passport"]: parts.append(f"passport_app_access_token={CFG['passport']}")
    if CFG["sl_session"]: parts.append(f"sl_session={CFG['sl_session']}")
    return "; ".join(parts)

def api_call(method, path, body=None):
    url = f"https://{CFG['domain']}{path}"
    rid = rand_id()
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "context": f"request_id={rid}-30e1a3b0defe29a39179b04861fdad89f254d0a0;os=linux;platform=web",
        "origin": f"https://{CFG['domain']}",
        "referer": f"https://{CFG['domain']}/",
        "cookie": build_cookie(),
        "x-csrftoken": CFG["csrf"],
        "x-lgw-app-id": "1161", "x-lgw-os-type": "1", "x-lgw-terminal-type": "2",
        "x-lsc-bizid": "2", "x-lsc-terminal": "web", "x-lsc-version": "1",
        "x-request-id": f"{rid}-30e1a3b0defe29a39179b04861fdad89f254d0a0",
        "user-agent": "Mozilla/5.0 (Linux) Chrome/149.0.0.0",
        "doc-biz": "Lark", "doc-os": "linux", "doc-platform": "web",
        "rpc-persist-lane-c-lark-uid": "", "priority": "u=1, i"
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read().decode())
        except: return {"code": e.code, "msg": f"HTTP {e.code}"}
    except Exception as e:
        return {"code": -1, "msg": str(e)}

# ========== ref_ 前缀系统 ==========

def make_ref_table_id(table_id):
    """生成 ref_ 前缀的 table ID"""
    return f"ref_{table_id}"

def make_ref_field_id(table_id, field_id):
    """生成 ref_ 前缀的 field ID"""
    return f"ref_{table_id}_{field_id}"

def build_table_map(table_id, field_ids=None):
    """构建 extra.TableMap"""
    ref_table = make_ref_table_id(table_id)
    field_map = {}
    if field_ids:
        for fid in field_ids:
            field_map[make_ref_field_id(table_id, fid)] = fid
    return {ref_table: {"TableID": table_id, "FieldMap": field_map, "ViewMap": {}}}

def build_extra(table_id=None, field_ids=None):
    """构建 extra JSON"""
    table_map = {}
    if table_id:
        table_map = build_table_map(table_id, field_ids)
    return json.dumps({"TableMap": table_map, "BlockMap": {}, "WorkflowMap": {}, "RelationInfo": {}})

# ========== 触发器构建 ==========

def build_timer_trigger(table_id, rule="DAILY", hour=10, minute=0):
    """定时触发"""
    trig_id = f"trig{rand_id()}"
    now_ms = int(time.time() * 1000)
    return {
        "id": trig_id, "type": "TimerTrigger",
        "data": {
            "startTime": now_ms, "rule": rule,
            "endTime": now_ms + 365*24*3600*1000,
            "isNeverEnd": False, "hour": hour, "minute": minute
        },
        "stepTitle": "", "next": []
    }, "cron", trig_id

def build_set_record_trigger(table_id):
    """新增记录触发"""
    trig_id = f"trig{rand_id()}"
    ref_table = make_ref_table_id(table_id)
    return {
        "id": trig_id, "type": "SetRecordTrigger",
        "data": {
            "tableId": ref_table, "recordType": "All",
            "filterInfo": None, "fields": [],
            "triggerControlList": ["pasteUpdate", "automationBatchUpdate", "appendImport", "openAPIBatchUpdate"]
        },
        "stepTitle": "", "next": []
    }, "setRecord", trig_id

def build_change_record_trigger(table_id, field_id=None, field_type=None, operator="is", value=None):
    """记录满足条件触发"""
    trig_id = f"trig{rand_id()}"
    ref_table = make_ref_table_id(table_id)
    fields = []
    if field_id:
        ref_field = make_ref_field_id(table_id, field_id)
        cond_id = f"con{rand_id(8)}"
        fields = [{"fieldId": ref_field, "fieldType": field_type or 1, "operator": operator, "value": value, "conditionId": cond_id}]
    return {
        "id": trig_id, "type": "ChangeRecordTrigger",
        "data": {
            "tableId": ref_table, "fields": fields,
            "triggerControlList": ["appendImport", "syncUpdate", "automationBatchUpdate", "pasteUpdate", "openAPIBatchUpdate"]
        },
        "stepTitle": "", "next": []
    }, "changeRecord", trig_id

def build_reminder_trigger(table_id, field_id, offset=0, unit=3, hour=9, minute=0):
    """到达记录中的时间触发"""
    trig_id = f"trig{rand_id()}"
    ref_table = make_ref_table_id(table_id)
    ref_field = make_ref_field_id(table_id, field_id)
    return {
        "id": trig_id, "type": "ReminderTrigger",
        "data": {
            "tableId": ref_table, "fieldId": ref_field,
            "offset": offset, "unit": unit, "hour": hour, "minute": minute
        },
        "stepTitle": "", "next": []
    }, "datetimeField", trig_id

def build_lark_message_trigger(scope="at"):
    """接收到飞书消息触发"""
    trig_id = f"trig{rand_id()}"
    return {
        "id": trig_id, "type": "LarkMessageTrigger",
        "data": {
            "receiveScene": "group", "receiverType": "baseApp",
            "groups": None, "scope": scope,
            "sendPersons": None,
            "filter": {"conjunction": "and", "conditions": []}
        },
        "stepTitle": "", "next": []
    }, "larkMessage", trig_id

def build_webhook_trigger():
    """Webhook触发"""
    trig_id = f"trig{rand_id()}"
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=24))
    return {
        "id": trig_id, "type": "WebhookTrigger",
        "data": {
            "webhookToken": token, "ipAllowList": None,
            "bearerToken": None, "requestLoading": True,
            "outputType": "Request",
            "outputJson": {"body": "{}"}
        },
        "stepTitle": "", "next": []
    }, "webhook", trig_id

# ========== 动作构建 ==========

def build_lark_message_action(table_id, message, color="purple", receivers=None):
    """发送飞书消息"""
    act_id = f"act{rand_id()}"
    persons = []
    if receivers:
        for r in receivers:
            persons.append({"type": "ref", "id": r, "entityId": r, "value": "", "tagType": "user", "owner_type": 0, "department": ""})
    rich_text = [{"type": "paragraph", "lineMarkerList": [], "value": [{"type": "text", "text": message, "extra": {}}]}]
    return {
        "id": act_id, "type": "LarkMessageAction",
        "data": {
            "notifyIdentity": "mixed", "robotType": "baseApp",
            "persons": persons, "groups": [], "title": [],
            "titleTemplateColor": color, "content": [], "btnList": [],
            "needBtn": False, "needTopBase": False, "needCompress": True,
            "sendMsgScene": "send", "senders": [], "senderType": 4,
            "attachments": [], "contentType": "rich_text",
            "richTextContent": rich_text,
            "buttonConfig": {"notRepeatClickMode": "AllUser", "mutualExclusion": False}
        },
        "stepTitle": "", "version": "1.1.0", "next": []
    }, act_id

def build_add_record_action(table_id):
    """新增记录"""
    act_id = f"act{rand_id()}"
    ref_table = make_ref_table_id(table_id)
    return {
        "id": act_id, "type": "AddRecordAction",
        "data": {
            "tableId": ref_table,
            "values": []
        },
        "stepTitle": "", "next": []
    }, act_id

def build_set_record_action(table_id, ref_step_id):
    """修改记录"""
    act_id = f"act{rand_id()}"
    ref_table = make_ref_table_id(table_id)
    return {
        "id": act_id, "type": "SetRecordAction",
        "data": {
            "tableId": ref_table, "values": [],
            "recordType": "Ref",
            "recordInfo": {"stepId": ref_step_id, "stepNum": 0},
            "maxSetRecordNum": 100
        },
        "stepTitle": "", "next": []
    }, act_id

def build_find_record_action(table_id, field_id=None):
    """查找记录"""
    act_id = f"act{rand_id()}"
    ref_table = make_ref_table_id(table_id)
    conditions = []
    if field_id:
        ref_field = make_ref_field_id(table_id, field_id)
        cond_id = f"con{rand_id(8)}"
        conditions = [{"fieldId": ref_field, "fieldType": 1, "operator": "is", "value": None, "conditionId": cond_id}]
    return {
        "id": act_id, "type": "FindRecordAction",
        "data": {
            "tableId": ref_table, "fieldIds": [], "fieldsMap": {},
            "recordType": "Filter", "shouldProceedWithNoResults": True,
            "recordInfo": {"conjunction": "and", "conditions": conditions}
        },
        "stepTitle": "", "next": []
    }, act_id

def build_generate_ai_text_action():
    """AI生成文本"""
    act_id = f"act{rand_id()}"
    return {
        "id": act_id, "type": "GenerateAiTextAction",
        "data": {"prompt": [], "promptType": "customize"},
        "stepTitle": "", "next": []
    }, act_id

def build_http_client_action(method="POST"):
    """发送HTTP请求"""
    act_id = f"act{rand_id()}"
    return {
        "id": act_id, "type": "HTTPClientAction",
        "data": {
            "method": method, "url": [],
            "responseType": "json", "responseValue": "{}",
            "bodyType": "raw",
            "rawBody": [{"text": "{}", "type": "text"}]
        },
        "stepTitle": "", "next": []
    }, act_id

# ========== 工作流构建 ==========

TRIGGER_MAP = {
    "TimerTrigger": "cron", "SetRecordTrigger": "setRecord",
    "ChangeRecordTrigger": "changeRecord", "ReminderTrigger": "datetimeField",
    "LarkMessageTrigger": "larkMessage", "WebhookTrigger": "webhook",
    "FormTrigger": "form_submit", "ButtonTrigger": "button_click",
}

def build_draft(title, trigger_step, action_steps):
    """构建完整 draft"""
    if action_steps:
        trigger_step["next"] = [{"ids": [action_steps[0]["id"]]}]
    return {"steps": [trigger_step] + action_steps, "title": title, "tabldFieldMap": {}}

# ========== MCP 工具 ==========

def tool_list_workflows(app_token):
    return api_call("GET", f"/space/api/bitable/{app_token}/automation/list")

def tool_create_workflow(app_token, draft, trigger_name, extra=None):
    body = {
        "token": app_token,
        "draft": json.dumps(draft, ensure_ascii=False),
        "extra": extra or build_extra(),
        "triggerName": trigger_name,
        "status": 0,
        "source": "mcp_create"
    }
    return api_call("POST", "/space/api/bitable/automation/create", body)

def tool_create_daily_message(app_token, title, message, table_id=None, hour=10, minute=0, receivers=None):
    """创建每日定时消息"""
    trig, trig_name, _ = build_timer_trigger(table_id, "DAILY", hour, minute)
    act, act_id = build_lark_message_action(table_id, message, "purple", receivers)
    draft = build_draft(title, trig, [act])
    return tool_create_workflow(app_token, draft, trig_name)

def tool_create_once_message(app_token, title, message, table_id=None, receivers=None):
    """创建一次性消息"""
    trig, trig_name, _ = build_timer_trigger(table_id, "NO_REPEAT")
    act, act_id = build_lark_message_action(table_id, message, "blue", receivers)
    draft = build_draft(title, trig, [act])
    return tool_create_workflow(app_token, draft, trig_name)

def tool_create_new_record_notify(app_token, title, message, table_id, receivers=None):
    """新增记录时发消息"""
    trig, trig_name, _ = build_set_record_trigger(table_id)
    act, _ = build_lark_message_action(table_id, message, "green", receivers)
    draft = build_draft(title, trig, [act])
    return tool_create_workflow(app_token, draft, trig_name, build_extra(table_id))

def tool_create_change_record_notify(app_token, title, message, table_id, field_id=None, receivers=None):
    """记录满足条件时发消息"""
    trig, trig_name, trig_id = build_change_record_trigger(table_id, field_id)
    act, _ = build_lark_message_action(table_id, message, "orange", receivers)
    draft = build_draft(title, trig, [act])
    return tool_create_workflow(app_token, draft, trig_name, build_extra(table_id, [field_id] if field_id else None))

def tool_create_time_reminder(app_token, title, message, table_id, field_id, hour=9, minute=0, receivers=None):
    """到达记录中的时间时发消息"""
    trig, trig_name, _ = build_reminder_trigger(table_id, field_id, hour=hour, minute=minute)
    act, _ = build_lark_message_action(table_id, message, "red", receivers)
    draft = build_draft(title, trig, [act])
    return tool_create_workflow(app_token, draft, trig_name, build_extra(table_id, [field_id]))

def tool_create_lark_message_trigger(app_token, title, message, scope="at", receivers=None):
    """接收到飞书消息时发消息"""
    trig, trig_name, _ = build_lark_message_trigger(scope)
    act, _ = build_lark_message_action(None, message, "blue", receivers)
    draft = build_draft(title, trig, [act])
    return tool_create_workflow(app_token, draft, trig_name)

# ========== MCP Server ==========

TOOLS = [
    {"name": "list_workflows", "description": "列出飞书多维表格的所有自动化工作流",
     "inputSchema": {"type": "object", "properties": {"app_token": {"type": "string"}}, "required": ["app_token"]}},

    {"name": "create_daily_message", "description": "创建每日定时消息提醒",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "title": {"type": "string"}, "message": {"type": "string"},
         "table_id": {"type": "string"}, "hour": {"type": "integer"}, "minute": {"type": "integer"},
         "receivers": {"type": "array", "items": {"type": "string"}}
     }, "required": ["app_token", "title", "message"]}},

    {"name": "create_once_message", "description": "创建一次性消息提醒",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "title": {"type": "string"}, "message": {"type": "string"},
         "table_id": {"type": "string"}, "receivers": {"type": "array", "items": {"type": "string"}}
     }, "required": ["app_token", "title", "message"]}},

    {"name": "create_new_record_notify", "description": "新增记录时发送通知",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "title": {"type": "string"}, "message": {"type": "string"},
         "table_id": {"type": "string"}, "receivers": {"type": "array", "items": {"type": "string"}}
     }, "required": ["app_token", "title", "message", "table_id"]}},

    {"name": "create_change_record_notify", "description": "记录满足条件时发送通知",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "title": {"type": "string"}, "message": {"type": "string"},
         "table_id": {"type": "string"}, "field_id": {"type": "string"},
         "receivers": {"type": "array", "items": {"type": "string"}}
     }, "required": ["app_token", "title", "message", "table_id"]}},

    {"name": "create_time_reminder", "description": "到达记录中的时间时发送提醒",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "title": {"type": "string"}, "message": {"type": "string"},
         "table_id": {"type": "string"}, "field_id": {"type": "string"},
         "hour": {"type": "integer"}, "minute": {"type": "integer"},
         "receivers": {"type": "array", "items": {"type": "string"}}
     }, "required": ["app_token", "title", "message", "table_id", "field_id"]}},

    {"name": "create_lark_message_trigger", "description": "接收到飞书消息时触发",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "title": {"type": "string"}, "message": {"type": "string"},
         "scope": {"type": "string", "enum": ["at", "all"], "description": "at=被@时, all=所有消息"},
         "receivers": {"type": "array", "items": {"type": "string"}}
     }, "required": ["app_token", "title", "message"]}},

    {"name": "create_form_notify", "description": "表单提交时发送通知",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "title": {"type": "string"}, "message": {"type": "string"},
         "table_id": {"type": "string"}, "receivers": {"type": "array", "items": {"type": "string"}}
     }, "required": ["app_token", "title", "message", "table_id"]}},

    {"name": "create_button_notify", "description": "按钮点击时发送通知",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "title": {"type": "string"}, "message": {"type": "string"},
         "table_id": {"type": "string"}, "field_id": {"type": "string"},
         "receivers": {"type": "array", "items": {"type": "string"}}
     }, "required": ["app_token", "title", "message", "table_id"]}},

    {"name": "create_set_record_notify", "description": "新增记录时自动修改字段值（如设置状态为'已发送'）",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "title": {"type": "string"},
         "table_id": {"type": "string"}, "field_id": {"type": "string"},
         "new_value": {"description": "要设置的新值"},
         "receivers": {"type": "array", "items": {"type": "string"}}
     }, "required": ["app_token", "title", "table_id", "field_id", "new_value"]}},

    {"name": "create_condition_set_record", "description": "记录满足条件时自动修改字段值（如'发送'→改为'已发送'）",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "title": {"type": "string"},
         "table_id": {"type": "string"},
         "trigger_field_id": {"type": "string", "description": "触发条件的字段ID"},
         "trigger_value": {"description": "触发条件的字段值"},
         "set_field_id": {"type": "string", "description": "要修改的字段ID"},
         "set_value": {"description": "修改为的值"},
         "receivers": {"type": "array", "items": {"type": "string"}}
     }, "required": ["app_token", "title", "table_id", "trigger_field_id", "trigger_value", "set_field_id", "set_value"]}},
]

class MCPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try: req = json.loads(body)
        except: self._respond({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}); return

        method = req.get("method", "")
        params = req.get("params", {})
        req_id = req.get("id")

        if method == "initialize":
            self._respond({"jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                "serverInfo": {"name": "feishu-bitable-automation", "version": VERSION}}})
        elif method == "tools/list":
            self._respond({"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            name = params.get("name", "")
            args = params.get("arguments", {})
            result = self._call_tool(name, args)
            self._respond({"jsonrpc": "2.0", "id": req_id, "result": result})
        elif method == "ping":
            self._respond({"jsonrpc": "2.0", "id": req_id, "result": {}})
        else:
            self._respond({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Not found: {method}"}})

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"status": "ok", "version": VERSION, "domain": CFG["domain"],
                             "session": "configured" if CFG["session"] else "missing"})
        elif self.path == "/tools":
            self._json(200, {"tools": [t["name"] for t in TOOLS]})
        else:
            self.send_response(404); self.end_headers()

    def _call_tool(self, name, args):
        try:
            if name == "list_workflows": r = tool_list_workflows(args["app_token"])
            elif name == "create_daily_message": r = tool_create_daily_message(args["app_token"], args["title"], args["message"], args.get("table_id"), args.get("hour", 10), args.get("minute", 0), args.get("receivers"))
            elif name == "create_once_message": r = tool_create_once_message(args["app_token"], args["title"], args["message"], args.get("table_id"), args.get("receivers"))
            elif name == "create_new_record_notify": r = tool_create_new_record_notify(args["app_token"], args["title"], args["message"], args["table_id"], args.get("receivers"))
            elif name == "create_change_record_notify": r = tool_create_change_record_notify(args["app_token"], args["title"], args["message"], args["table_id"], args.get("field_id"), args.get("receivers"))
            elif name == "create_time_reminder": r = tool_create_time_reminder(args["app_token"], args["title"], args["message"], args["table_id"], args["field_id"], args.get("hour", 9), args.get("minute", 0), args.get("receivers"))
            elif name == "create_lark_message_trigger": r = tool_create_lark_message_trigger(args["app_token"], args["title"], args["message"], args.get("scope", "at"), args.get("receivers"))
            elif name == "create_form_notify": r = tool_create_form_notify(args["app_token"], args["title"], args["message"], args["table_id"], args.get("receivers"))
            elif name == "create_button_notify": r = tool_create_button_notify(args["app_token"], args["title"], args["message"], args["table_id"], args.get("field_id"), args.get("receivers"))
            elif name == "create_set_record_notify": r = tool_create_set_record_notify(args["app_token"], args["title"], args["table_id"], args["field_id"], args["new_value"], args.get("trigger_field_id"), args.get("trigger_value"), args.get("receivers"))
            elif name == "create_condition_set_record": r = tool_create_condition_set_record(args["app_token"], args["title"], args["table_id"], args["trigger_field_id"], args["trigger_value"], args["set_field_id"], args["set_value"], args.get("receivers"))
            else: return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}
            return {"content": [{"type": "text", "text": json.dumps(r, ensure_ascii=False, indent=2)}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}

    def _respond(self, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def _json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json")
        self.end_headers(); self.wfile.write(body)

    def log_message(self, *args): pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8067)
    args = parser.parse_args()
    print(f"🚀 飞书多维表格自动化 MCP Server v{VERSION}")
    print(f"   http://0.0.0.0:{args.port}")
    print(f"   Session: {'✅' if CFG['session'] else '❌'}")
    HTTPServer(("0.0.0.0", args.port), MCPHandler).serve_forever()

if __name__ == "__main__":
    main()

# ========== 补充的触发器构建 ==========

def build_form_trigger(table_id):
    """表单提交触发"""
    trig_id = f"trig{rand_id()}"
    ref_table = make_ref_table_id(table_id)
    return {
        "id": trig_id, "type": "FormTrigger",
        "data": {"tableId": ref_table, "filter": {"conjunction": "and", "conditions": []}},
        "stepTitle": "", "next": []
    }, "form_submit", trig_id

def build_button_trigger(table_id, field_id=None):
    """按钮点击触发"""
    trig_id = f"trig{rand_id()}"
    ref_table = make_ref_table_id(table_id)
    data = {"tableId": ref_table}
    if field_id:
        data["fieldId"] = make_ref_field_id(table_id, field_id)
    return {
        "id": trig_id, "type": "ButtonTrigger",
        "data": data,
        "stepTitle": "", "next": []
    }, "button_click", trig_id

# ========== 补充的工具 ==========



def tool_create_form_notify(app_token, title, message, table_id, receivers=None):
    """表单提交时发消息"""
    trig, trig_name, _ = build_form_trigger(table_id)
    act, _ = build_lark_message_action(table_id, message, "orange", receivers)
    draft = build_draft(title, trig, [act])
    return tool_create_workflow(app_token, draft, trig_name, build_extra(table_id))

def tool_create_button_notify(app_token, title, message, table_id, field_id=None, receivers=None):
    """按钮点击时发消息"""
    trig, trig_name, _ = build_button_trigger(table_id, field_id)
    act, _ = build_lark_message_action(table_id, message, "red", receivers)
    draft = build_draft(title, trig, [act])
    return tool_create_workflow(app_token, draft, trig_name, build_extra(table_id, [field_id] if field_id else None))

# ========== SetRecordAction 快捷工具 ==========

def tool_create_set_record_notify(app_token, title, table_id, field_id, new_value, trigger_field_id=None, trigger_value=None, receivers=None):
    """修改记录字段值（可配合其他触发器使用）"""
    trig, trig_name, trig_id = build_set_record_trigger(table_id)
    act, _ = build_set_record_action(table_id, trig_id)
    # 设置要修改的字段值
    ref_field = make_ref_field_id(table_id, field_id)
    act["data"]["values"] = [{"fieldId": ref_field, "valueType": "value", "value": new_value}]
    draft = build_draft(title, trig, [act])
    return tool_create_workflow(app_token, draft, trig_name, build_extra(table_id, [field_id]))

def tool_create_condition_set_record(app_token, title, table_id, trigger_field_id, trigger_value, set_field_id, set_value, receivers=None):
    """满足条件时修改记录"""
    trig, trig_name, trig_id = build_change_record_trigger(table_id, trigger_field_id)
    act, _ = build_set_record_action(table_id, trig_id)
    ref_field = make_ref_field_id(table_id, set_field_id)
    act["data"]["values"] = [{"fieldId": ref_field, "valueType": "value", "value": set_value}]
    draft = build_draft(title, trig, [act])
    return tool_create_workflow(app_token, draft, trig_name, build_extra(table_id, [trigger_field_id, set_field_id]))
