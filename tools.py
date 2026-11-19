"""Tool schemas shown to the model and the dispatch table."""

from __future__ import annotations

import orders

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
]


def run_tool(name: str, arguments: dict) -> dict:
    """Runs one tool by name. Each tool is read from its module when called."""
    if name == "lookup_order":
        return orders.lookup_order(arguments["order_id"])
    if name == "order_history":
        return {"ok": True, "events": list(orders.order_history(arguments["order_id"]))}
    if name == "request_refund":
        return orders.request_refund(arguments["order_id"], arguments.get("reason") or "")
    return {"ok": False, "error": f"unknown tool {name}"}
