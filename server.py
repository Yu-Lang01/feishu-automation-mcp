#!/usr/bin/env python3
"""
飞书多维表格自动化 MCP Server
Feishu Bitable Automation MCP Server

通过逆向工程的飞书内部 API，实现多维表格自动化工作流的编程管理。
任何虾都可以用这个 MCP 来创建、管理多维表格的自动化工作流。

已验证端点：
- POST /space/api/bitable/automation/create
- GET  /space/api/bitable/{token}/automation/list

使用方式：
  export FEISHU_SESSION="你的session"
  export FEISHU_CSRF_TOKEN="你的csrf_token"
  export FEISHU_PASSPORT_TOKEN="你的passport_app_access_token"
  python3 feishu-automation-mcp.py --port 8067

版本: 0.2.0
"""

import json
import os
import sys
import random
import string
import time
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request

VERSION = "0.2.0"

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

# ========== 工具函数 ==========

def rand_id(n=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))


def build_cookie():
    parts = []
    if CFG["session"]:
        parts.append(f"session={CFG['session']}")
    if CFG["csrf"]:
        parts.append(f"_csrf_token={CFG['csrf']}")
    if CFG["passport"]:
        parts.append(f"passport_app_access_token={CFG['passport']}")
    if CFG["sl_session"]:
        parts.append(f"sl_session={CFG['sl_session']}")
    return "; ".join(parts)


def api_call(method, path, body=None):
    """调用飞书内部 API"""
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
        "x-lgw-app-id": "1161",
        "x-lgw-os-type": "1",
        "x-lgw-terminal-type": "2",
        "x-lsc-bizid": "2",
        "x-lsc-terminal": "web",
        "x-lsc-version": "1",
        "x-request-id": f"{rid}-30e1a3b0defe29a39179b04861fdad89f254d0a0",
        "user-agent": "Mozilla/5.0 (Linux) Chrome/149.0.0.0",
        "doc-biz": "Lark",
        "doc-os": "linux",
        "doc-platform": "web",
        "rpc-persist-lane-c-lark-uid": "",
        "priority": "u=1, i"
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except:
            return {"code": e.code, "msg": f"HTTP {e.code}"}
    except Exception as e:
        return {"code": -1, "msg": str(e)}


# ========== Draft 构建器 ==========

def build_draft(config):
    """
    通用 draft 构建器
    
    config = {
        "title": "工作流标题",
        "trigger": {
            "type": "TimerTrigger" | "RecordTrigger",
            # TimerTrigger 参数:
            "rule": "DAILY" | "NO_REPEAT" | "WEEKLY",
            "hour": 10, "minute": 0,
            # RecordTrigger 参数:
            "tableId": "tblxxx",
        },
        "actions": [{
            "type": "LarkMessageAction",
            "title": "动作标题",
            "content": "消息内容",
            "receivers": ["ou_xxx"],  # 可选，不填则发给所有人
            "color": "purple",  # 可选
        }]
    }
    """
    trig_id = f"trig{rand_id()}"
    now_ms = int(time.time() * 1000)

    # 构建触发器
    trigger = config["trigger"]
    if trigger["type"] == "TimerTrigger":
        trigger_step = {
            "id": trig_id,
            "type": "TimerTrigger",
            "data": {
                "startTime": now_ms,
                "rule": trigger.get("rule", "DAILY"),
                "endTime": now_ms + 365 * 24 * 3600 * 1000,
                "isNeverEnd": False,
                "hour": trigger.get("hour", 10),
                "minute": trigger.get("minute", 0),
            },
            "stepTitle": "",
            "next": []
        }
        trigger_name = "cron"
    elif trigger["type"] == "RecordTrigger":
        trigger_step = {
            "id": trig_id,
            "type": "RecordTrigger",
            "data": {
                "tableId": trigger["tableId"],
                "filter": trigger.get("filter", {})
            },
            "stepTitle": "",
            "next": []
        }
        trigger_name = "record_change"
    else:
        return None, f"不支持的触发器类型: {trigger['type']}"

    # 构建动作
    action_steps = []
    prev_id = trig_id

    for i, action in enumerate(config.get("actions", [])):
        act_id = f"act{rand_id()}"

        # 构建接收人
        persons = []
        for r in action.get("receivers", []):
            persons.append({
                "type": "ref", "id": r, "entityId": r,
                "value": "", "tagType": "user", "owner_type": 0, "department": ""
            })

        # 构建消息内容
        content = action.get("content", "")
        rich_text = [{"type": "paragraph", "lineMarkerList": [],
                      "value": [{"type": "text", "text": content, "extra": {}}]}]

        action_step = {
            "id": act_id,
            "type": action.get("type", "LarkMessageAction"),
            "data": {
                "notifyIdentity": "mixed",
                "robotType": "baseApp",
                "persons": persons,
                "groups": [],
                "title": [],
                "titleTemplateColor": action.get("color", "purple"),
                "content": [],
                "btnList": [],
                "needBtn": False,
                "needTopBase": False,
                "needCompress": True,
                "sendMsgScene": "send",
                "senders": [],
                "senderType": 4,
                "attachments": [],
                "contentType": "rich_text",
                "richTextContent": rich_text,
                "buttonConfig": {"notRepeatClickMode": "AllUser", "mutualExclusion": False}
            },
            "stepTitle": action.get("title", ""),
            "version": "1.1.0",
            "next": []
        }

        # 链接步骤
        trigger_step["next"] = [{"ids": [act_id]}]
        action_steps.append(action_step)

    draft = {
        "steps": [trigger_step] + action_steps,
        "title": config.get("title", "自动化工作流"),
        "tabldFieldMap": {}
    }

    return draft, trigger_name


# ========== MCP 工具实现 ==========

def tool_list_workflows(app_token):
    """列出多维表格的所有自动化工作流"""
    return api_call("GET", f"/space/api/bitable/{app_token}/automation/list")


def tool_create_workflow(app_token, config):
    """创建自动化工作流"""
    draft, trigger_name = build_draft(config)
    if draft is None:
        return {"code": -1, "msg": trigger_name}

    body = {
        "token": app_token,
        "draft": json.dumps(draft, ensure_ascii=False),
        "extra": json.dumps({
            "TableMap": {}, "BlockMap": {},
            "WorkflowMap": {}, "RelationInfo": {}
        }),
        "triggerName": trigger_name,
        "status": 0,
        "source": "mcp_create"
    }
    return api_call("POST", "/space/api/bitable/automation/create", body)


def tool_create_daily_message(app_token, title, message, hour=10, minute=0, receivers=None):
    """创建每日定时消息提醒"""
    config = {
        "title": title,
        "trigger": {"type": "TimerTrigger", "rule": "DAILY", "hour": hour, "minute": minute},
        "actions": [{"type": "LarkMessageAction", "title": title, "content": message,
                      "receivers": receivers or [], "color": "purple"}]
    }
    return tool_create_workflow(app_token, config)


def tool_create_once_message(app_token, title, message, receivers=None):
    """创建一次性消息提醒"""
    config = {
        "title": title,
        "trigger": {"type": "TimerTrigger", "rule": "NO_REPEAT"},
        "actions": [{"type": "LarkMessageAction", "title": title, "content": message,
                      "receivers": receivers or [], "color": "blue"}]
    }
    return tool_create_workflow(app_token, config)


def tool_create_record_trigger(app_token, title, message, table_id, receivers=None):
    """创建记录变化触发消息"""
    config = {
        "title": title,
        "trigger": {"type": "RecordTrigger", "tableId": table_id},
        "actions": [{"type": "LarkMessageAction", "title": title, "content": message,
                      "receivers": receivers or [], "color": "green"}]
    }
    return tool_create_workflow(app_token, config)


# ========== MCP Server ==========

TOOLS = [
    {
        "name": "list_workflows",
        "description": "列出飞书多维表格的所有自动化工作流",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "多维表格 app_token"}
            },
            "required": ["app_token"]
        }
    },
    {
        "name": "create_workflow",
        "description": "创建飞书多维表格自动化工作流（通用接口）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "多维表格 app_token"},
                "config": {
                    "type": "object",
                    "description": "工作流配置",
                    "properties": {
                        "title": {"type": "string", "description": "工作流标题"},
                        "trigger": {
                            "type": "object",
                            "description": "触发器配置",
                            "properties": {
                                "type": {"type": "string", "enum": ["TimerTrigger", "RecordTrigger"]},
                                "rule": {"type": "string", "enum": ["DAILY", "NO_REPEAT", "WEEKLY"]},
                                "hour": {"type": "integer"},
                                "minute": {"type": "integer"},
                                "tableId": {"type": "string"}
                            }
                        },
                        "actions": {
                            "type": "array",
                            "description": "动作列表",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "title": {"type": "string"},
                                    "content": {"type": "string"},
                                    "receivers": {"type": "array", "items": {"type": "string"}},
                                    "color": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            },
            "required": ["app_token", "config"]
        }
    },
    {
        "name": "create_daily_message",
        "description": "创建每日定时消息提醒（快捷方式）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string", "description": "多维表格 app_token"},
                "title": {"type": "string", "description": "提醒标题"},
                "message": {"type": "string", "description": "消息内容"},
                "hour": {"type": "integer", "description": "发送时间-小时（默认10）"},
                "minute": {"type": "integer", "description": "发送时间-分钟（默认0）"},
                "receivers": {"type": "array", "items": {"type": "string"}, "description": "接收人 open_id 列表"}
            },
            "required": ["app_token", "title", "message"]
        }
    },
    {
        "name": "create_once_message",
        "description": "创建一次性消息提醒",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string"},
                "title": {"type": "string"},
                "message": {"type": "string"},
                "receivers": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["app_token", "title", "message"]
        }
    },
    {
        "name": "create_record_trigger",
        "description": "创建记录变化触发消息（当多维表格新增/修改记录时触发）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_token": {"type": "string"},
                "title": {"type": "string"},
                "message": {"type": "string"},
                "table_id": {"type": "string", "description": "数据表 ID"},
                "receivers": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["app_token", "title", "message", "table_id"]
        }
    }
]


class MCPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            req = json.loads(body)
        except:
            self._respond({"jsonrpc": "2.0", "id": None,
                           "error": {"code": -32700, "message": "Parse error"}})
            return

        method = req.get("method", "")
        params = req.get("params", {})
        req_id = req.get("id")

        if method == "initialize":
            self._respond({"jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "feishu-bitable-automation", "version": VERSION}
            }})
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
            self._respond({"jsonrpc": "2.0", "id": req_id,
                           "error": {"code": -32601, "message": f"Not found: {method}"}})

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {
                "status": "ok", "version": VERSION,
                "domain": CFG["domain"],
                "session": "configured" if CFG["session"] else "missing",
                "passport": "configured" if CFG["passport"] else "missing"
            })
        elif self.path == "/tools":
            self._json(200, {"tools": [t["name"] for t in TOOLS]})
        else:
            self.send_response(404)
            self.end_headers()

    def _call_tool(self, name, args):
        try:
            if name == "list_workflows":
                r = tool_list_workflows(args["app_token"])
            elif name == "create_workflow":
                r = tool_create_workflow(args["app_token"], args["config"])
            elif name == "create_daily_message":
                r = tool_create_daily_message(
                    args["app_token"], args["title"], args["message"],
                    args.get("hour", 10), args.get("minute", 0),
                    args.get("receivers"))
            elif name == "create_once_message":
                r = tool_create_once_message(
                    args["app_token"], args["title"], args["message"],
                    args.get("receivers"))
            elif name == "create_record_trigger":
                r = tool_create_record_trigger(
                    args["app_token"], args["title"], args["message"],
                    args["table_id"], args.get("receivers"))
            else:
                return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                        "isError": True}
            return {"content": [{"type": "text",
                                 "text": json.dumps(r, ensure_ascii=False, indent=2)}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {e}"}],
                    "isError": True}

    def _respond(self, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description="飞书多维表格自动化 MCP Server")
    parser.add_argument("--port", type=int, default=8067, help="端口（默认 8067）")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="监听地址")
    args = parser.parse_args()

    print(f"🚀 飞书多维表格自动化 MCP Server v{VERSION}")
    print(f"   地址: http://{args.host}:{args.port}")
    print(f"   飞书: {CFG['domain']}")
    print(f"   Session: {'✅' if CFG['session'] else '❌ 未配置'}")
    print(f"   Passport: {'✅' if CFG['passport'] else '❌ 未配置'}")
    print()

    if not CFG["session"]:
        print("⚠️  请设置环境变量：")
        print("   export FEISHU_SESSION=你的session值")
        print("   export FEISHU_CSRF_TOKEN=你的csrf_token")
        print("   export FEISHU_PASSPORT_TOKEN=你的passport_app_access_token")
        print()
        print("   获取方式：F12 → 应用程序 → Cookie → mi.feishu.cn")
        print()

    HTTPServer((args.host, args.port), MCPHandler).serve_forever()


if __name__ == "__main__":
    main()
