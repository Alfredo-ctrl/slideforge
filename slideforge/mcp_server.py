"""MCP server over stdio. Hand-rolled JSON-RPC, no MCP SDK.

Tools: create_deck, create_deck_from_markdown, describe_deck, list_themes.
"""

import json
import sys

from . import __version__, build_deck, describe, from_markdown, list_themes

TOOLS = [
    {
        "name": "create_deck",
        "description": "Build a .pptx deck from a structure dict: title, author, theme, slides of type title, bullets, text, image or table.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "structure": {"type": "object", "description": "Deck structure dict"},
                "output": {"type": "string", "description": "Output .pptx path"},
                "theme": {"type": "string", "description": "Theme: light, dark or blue (default light)"},
            },
            "required": ["structure", "output"],
        },
    },
    {
        "name": "create_deck_from_markdown",
        "description": "Build a .pptx deck from Markdown text: '# ' is the deck title, '## ' starts a slide, '- ' are bullets, '![alt](path)' is an image slide, '| a | b |' rows are a table.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "markdown": {"type": "string", "description": "Markdown text"},
                "output": {"type": "string", "description": "Output .pptx path"},
                "theme": {"type": "string", "description": "Theme: light, dark or blue (default light)"},
            },
            "required": ["markdown", "output"],
        },
    },
    {
        "name": "describe_deck",
        "description": "Get slide count, title, author, size and dimensions of a .pptx deck.",
        "inputSchema": {
            "type": "object",
            "properties": {"input": {"type": "string", "description": "Deck path"}},
            "required": ["input"],
        },
    },
    {
        "name": "list_themes",
        "description": "List the built-in deck themes with their colors.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def _text_result(payload):
    return {"content": [{"type": "text", "text": json.dumps(payload)}]}


def _dispatch_tool(name, args):
    if name == "list_themes":
        return _text_result(list_themes())
    if name == "describe_deck":
        return _text_result(describe(args["input"]))
    if name == "create_deck":
        return _text_result(build_deck(args["structure"], args["output"], args.get("theme", "light")))
    if name == "create_deck_from_markdown":
        return _text_result(from_markdown(args["markdown"], args["output"], args.get("theme", "light")))
    raise ValueError(f"unknown tool '{name}'")


def run():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = req.get("method", "")
        req_id = req.get("id")
        if method in ("notifications/initialized", "notifications/cancelled"):
            continue
        if method == "initialize":
            result = {
                "protocolVersion": req.get("params", {}).get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "slideforge", "version": __version__},
            }
            resp = {"result": result}
        elif method == "ping":
            resp = {"result": {}}
        elif method == "tools/list":
            resp = {"result": {"tools": TOOLS}}
        elif method == "tools/call":
            try:
                resp = {"result": _dispatch_tool(req["params"]["name"], req["params"].get("arguments", {}))}
            except Exception as e:
                resp = {"result": {"content": [{"type": "text", "text": json.dumps({"error": str(e)})}], "isError": True}}
        else:
            resp = {"error": {"code": -32601, "message": f"method not found: {method}"}}
        if req_id is not None:
            print(json.dumps({"jsonrpc": "2.0", "id": req_id, **resp}), flush=True)
