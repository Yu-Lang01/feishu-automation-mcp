#!/usr/bin/env python3
"""
飞书多维表格自动化 MCP Server v0.3.0
Feishu Bitable Automation MCP Server

支持的触发器类型：
- TimerTrigger: 定时触发（每日/每周/一次性）
- RecordTrigger: 记录变化触发（新增/修改/删除）
- FormTrigger: 表单提交触发
- ButtonTrigger: 按钮点击触发

支持的动作类型：
- LarkMessageAction: 发送飞书消息
- BitableAction: 更新记录字段
- SendEmailAction: 发送邮件
- HttpAction: HTTP 请求
- WebhookAction: Webhook 回调
- ConditionAction: 条件判断
- BitableAutomationAction: 自动化动作

使用方式：
  export FEISHU_SESSION="你的session"
  export FEISHU_CSRF_TOKEN="你的csrf_token"
  export FEISHU_PASSPORT_TOKEN="你的passport_app_access_token"
  python3 server.py --port 8067

版本: 0.3.0
"""

import json, os, sys, random, string, time, argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request

VERSION = "0.3.0"

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

# ========== Draft 构建器 ==========

TRIGGER_MAP = {
    "TimerTrigger": "cron",
    "RecordTrigger": "record_change",
    "FormTrigger": "form_submit",
    "ButtonTrigger": "button_click",
}

def build_draft(config):
    trig_id = f"trig{rand_id()}"
    now_ms = int(time.time() * 1000)

    trigger = config["trigger"]
    trig_type = trigger["type"]

    # 构建触发器
    if trig_type == "TimerTrigger":
        trigger_step = {
            "id": trig_id, "type": trig_type,
            "data": {
                "startTime": now_ms,
                "rule": trigger.get("rule", "DAILY"),
                "endTime": now_ms + 365 * 24 * 3600 * 1000,
                "isNeverEnd": False,
                "hour": trigger.get("hour", 10),
                "minute": trigger.get("minute", 0),
            },
            "stepTitle": "", "next": []
        }
    elif trig_type == "RecordTrigger":
        trigger_step = {
            "id": trig_id, "type": trig_type,
            "data": {
                "tableId": trigger["tableId"],
                "filter": trigger.get("filter", {"conjunction": "and", "conditions": []}),
                "eventType": trigger.get("eventType", "create")
            },
            "stepTitle": "", "next": []
        }
    elif trig_type == "FormTrigger":
        trigger_step = {
            "id": trig_id, "type": trig_type,
            "data": {
                "tableId": trigger["tableId"],
                "filter": trigger.get("filter", {"conjunction": "and", "conditions": []})
            },
            "stepTitle": "", "next": []
        }
    elif trig_type == "ButtonTrigger":
        trigger_step = {
            "id": trig_id, "type": trig_type,
            "data": {"tableId": trigger["tableId"], "fieldId": trigger.get("fieldId", "")},
            "stepTitle": "", "next": []
        }
    else:
        return None, f"不支持的触发器类型: {trig_type}"

    trigger_name = TRIGGER_MAP.get(trig_type, "cron")

    # 构建动作
    action_steps = []
    for action in config.get("actions", []):
        act_id = f"act{rand_id()}"
        act_type = action.get("type", "LarkMessageAction")

        if act_type == "LarkMessageAction":
            persons = [{"type": "ref", "id": r, "entityId": r, "value": "", "tagType": "user", "owner_type": 0, "department": ""} for r in action.get("receivers", [])]
            rich_text = [{"type": "paragraph", "lineMarkerList": [], "value": [{"type": "text", "text": action.get("content", ""), "extra": {}}]}]
            act_data = {
                "notifyIdentity": "mixed", "robotType": "baseApp",
                "persons": persons, "groups": [], "title": [],
                "titleTemplateColor": action.get("color", "purple"),
                "content": [], "btnList": [], "needBtn": False, "needTopBase": False,
                "needCompress": True, "sendMsgScene": "send", "senders": [],
                "senderType": 4, "attachments": [], "contentType": "rich_text",
                "richTextContent": rich_text,
                "buttonConfig": {"notRepeatClickMode": "AllUser", "mutualExclusion": False}
            }
        elif act_type == "BitableAction":
            act_data = {
                "tableId": action["tableId"],
                "fieldId": action.get("fieldId", ""),
                "action": action.get("updateAction", "setValue"),
                "value": action.get("value", ""),
            }
        elif act_type == "SendEmailAction":
            act_data = {"to": action["to"], "subject": action.get("subject", ""), "body": action.get("body", "")}
        elif act_type == "HttpAction":
            act_data = {"url": action["url"], "method": action.get("method", "GET"), "headers": action.get("headers", {}), "body": action.get("body", "")}
        elif act_type == "WebhookAction":
            act_data = {"url": action["url"]}
        elif act_type == "ConditionAction":
            act_data = {"conditions": action.get("conditions", [])}
        elif act_type == "BitableAutomationAction":
            act_data = action.get("data", {})
        else:
            act_data = action.get("data", {})

        action_steps.append({
            "id": act_id, "type": act_type, "data": act_data,
            "stepTitle": action.get("title", ""), "version": "1.1.0", "next": []
        })

    if action_steps:
        trigger_step["next"] = [{"ids": [action_steps[0]["id"]]}]

    draft = {"steps": [trigger_step] + action_steps, "title": config.get("title", "自动化工作流"), "tabldFieldMap": {}}
    return draft, trigger_name

# ========== MCP 工具 ==========

def tool_list_workflows(app_token):
    return api_call("GET", f"/space/api/bitable/{app_token}/automation/list")

def tool_create_workflow(app_token, config):
    draft, trigger_name = build_draft(config)
    if draft is None:
        return {"code": -1, "msg": trigger_name}
    body = {"token": app_token, "draft": json.dumps(draft, ensure_ascii=False),
            "extra": json.dumps({"TableMap": {}, "BlockMap": {}, "WorkflowMap": {}, "RelationInfo": {}}),
            "triggerName": trigger_name, "status": 0, "source": "mcp_create"}
    return api_call("POST", "/space/api/bitable/automation/create", body)

def tool_create_daily_message(app_token, title, message, hour=10, minute=0, receivers=None):
    return tool_create_workflow(app_token, {
        "title": title,
        "trigger": {"type": "TimerTrigger", "rule": "DAILY", "hour": hour, "minute": minute},
        "actions": [{"type": "LarkMessageAction", "title": title, "content": message, "receivers": receivers or [], "color": "purple"}]
    })

def tool_create_once_message(app_token, title, message, receivers=None):
    return tool_create_workflow(app_token, {
        "title": title,
        "trigger": {"type": "TimerTrigger", "rule": "NO_REPEAT"},
        "actions": [{"type": "LarkMessageAction", "title": title, "content": message, "receivers": receivers or [], "color": "blue"}]
    })

def tool_create_record_trigger(app_token, title, message, table_id, receivers=None):
    return tool_create_workflow(app_token, {
        "title": title,
        "trigger": {"type": "RecordTrigger", "tableId": table_id},
        "actions": [{"type": "LarkMessageAction", "title": title, "content": message, "receivers": receivers or [], "color": "green"}]
    })

def tool_create_form_trigger(app_token, title, message, table_id, receivers=None):
    return tool_create_workflow(app_token, {
        "title": title,
        "trigger": {"type": "FormTrigger", "tableId": table_id},
        "actions": [{"type": "LarkMessageAction", "title": title, "content": message, "receivers": receivers or [], "color": "orange"}]
    })

def tool_create_button_trigger(app_token, title, message, table_id, field_id=None, receivers=None):
    return tool_create_workflow(app_token, {
        "title": title,
        "trigger": {"type": "ButtonTrigger", "tableId": table_id, "fieldId": field_id or ""},
        "actions": [{"type": "LarkMessageAction", "title": title, "content": message, "receivers": receivers or [], "color": "red"}]
    })

# ========== MCP Server ==========

TOOLS = [
    {"name": "list_workflows", "description": "列出飞书多维表格的所有自动化工作流",
     "inputSchema": {"type": "object", "properties": {"app_token": {"type": "string"}}, "required": ["app_token"]}},

    {"name": "create_workflow", "description": "创建自动化工作流（通用接口，支持所有触发器和动作类型）",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "config": {"type": "object"}
     }, "required": ["app_token", "config"]}},

    {"name": "create_daily_message", "description": "创建每日定时消息提醒",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "title": {"type": "string"}, "message": {"type": "string"},
         "hour": {"type": "integer"}, "minute": {"type": "integer"},
         "receivers": {"type": "array", "items": {"type": "string"}}
     }, "required": ["app_token", "title", "message"]}},

    {"name": "create_once_message", "description": "创建一次性消息提醒",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "title": {"type": "string"}, "message": {"type": "string"},
         "receivers": {"type": "array", "items": {"type": "string"}}
     }, "required": ["app_token", "title", "message"]}},

    {"name": "create_record_trigger", "description": "创建记录变化触发（当记录新增/修改/删除时发消息）",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "title": {"type": "string"}, "message": {"type": "string"},
         "table_id": {"type": "string"}, "receivers": {"type": "array", "items": {"type": "string"}}
     }, "required": ["app_token", "title", "message", "table_id"]}},

    {"name": "create_form_trigger", "description": "创建表单提交触发（当用户提交表单时发消息）",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "title": {"type": "string"}, "message": {"type": "string"},
         "table_id": {"type": "string"}, "receivers": {"type": "array", "items": {"type": "string"}}
     }, "required": ["app_token", "title", "message", "table_id"]}},

    {"name": "create_button_trigger", "description": "创建按钮点击触发（当用户点击按钮时发消息）",
     "inputSchema": {"type": "object", "properties": {
         "app_token": {"type": "string"}, "title": {"type": "string"}, "message": {"type": "string"},
         "table_id": {"type": "string"}, "field_id": {"type": "string"},
         "receivers": {"type": "array", "items": {"type": "string"}}
     }, "required": ["app_token", "title", "message", "table_id"]}},
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
            elif name == "create_workflow": r = tool_create_workflow(args["app_token"], args["config"])
            elif name == "create_daily_message": r = tool_create_daily_message(args["app_token"], args["title"], args["message"], args.get("hour", 10), args.get("minute", 0), args.get("receivers"))
            elif name == "create_once_message": r = tool_create_once_message(args["app_token"], args["title"], args["message"], args.get("receivers"))
            elif name == "create_record_trigger": r = tool_create_record_trigger(args["app_token"], args["title"], args["message"], args["table_id"], args.get("receivers"))
            elif name == "create_form_trigger": r = tool_create_form_trigger(args["app_token"], args["title"], args["message"], args["table_id"], args.get("receivers"))
            elif name == "create_button_trigger": r = tool_create_button_trigger(args["app_token"], args["title"], args["message"], args["table_id"], args.get("field_id"), args.get("receivers"))
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
