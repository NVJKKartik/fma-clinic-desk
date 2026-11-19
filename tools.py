"""Tool schemas shown to the model, and each tool as a call to the shop's tools service at TOOLS_API_URL."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

_ORDER = {"type": "string", "description": "The order id, for example B-1001"}


def _tool(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


TOOLS = [
    _tool("lookup_order", "Look up one order: customer, item, total and status.", {"order_id": _ORDER}, ["order_id"]),
    _tool(
        "order_history",
        "Every event an order went through (placed, shipped, delivered), oldest first, with any note.",
        {"order_id": _ORDER},
        ["order_id"],
    ),
    _tool(
        "request_refund",
        "Ask for a refund of a delivered order. A store manager approves or declines every refund request.",
        {"order_id": _ORDER, "reason": {"type": "string", "description": "Why the customer wants a refund"}},
        ["order_id", "reason"],
    ),
    _tool(
        "refund_status",
        "A refund request and the store manager's decision so far: awaiting manager approval, approved or declined.",
        {"request_id": {"type": "string", "description": "The refund request id, for example R-1A2B3C"}},
        ["request_id"],
    ),
]


def _call(method: str, path: str, body: dict | None = None) -> dict:
    base = os.environ["TOOLS_API_URL"].rstrip("/")
    request = urllib.request.Request(
        f"{base}{path}",
        method=method,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            return json.load(error)
        except ValueError:
            return {"ok": False, "error": f"the tools service answered {error.code}"}


def run_tool(name: str, arguments: dict) -> dict:
    order = urllib.parse.quote(str(arguments.get("order_id") or "").strip(), safe="")
    if name == "lookup_order":
        return _call("GET", f"/orders/{order}")
    if name == "order_history":
        return _call("GET", f"/orders/{order}/history")
    if name == "request_refund":
        return _call("POST", "/refunds", {"order_id": arguments.get("order_id"), "reason": arguments.get("reason") or ""})
    if name == "refund_status":
        request = urllib.parse.quote(str(arguments.get("request_id") or "").strip(), safe="")
        return _call("GET", f"/refunds/{request}")
    return {"ok": False, "error": f"unknown tool {name}"}
