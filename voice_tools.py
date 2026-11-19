"""The order desk's tools as LiveKit function tools. Each runs its function in `orders`, read from the module when
called."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from livekit.agents import function_tool

import orders

_ORDER = {"type": "string", "description": "The order id, for example B-1001"}

SCHEMAS = [
    {
        "name": "lookup_order",
        "description": "Look up one order: customer, item, total and status.",
        "parameters": {"type": "object", "properties": {"order_id": _ORDER}, "required": ["order_id"]},
    },
    {
        "name": "request_refund",
        "description": "Ask for a refund of a delivered order. A store manager approves or declines every refund request.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": _ORDER, "reason": {"type": "string", "description": "Why the caller wants a refund"}},
            "required": ["order_id", "reason"],
        },
    },
]


def _run(name: str, arguments: dict[str, Any]) -> dict:
    try:
        if name == "lookup_order":
            return orders.lookup_order(str(arguments.get("order_id") or ""))
        if name == "request_refund":
            return orders.request_refund(str(arguments.get("order_id") or ""), str(arguments.get("reason") or ""))
        return {"ok": False, "error": f"unknown tool {name}"}
    except Exception as exc:  # noqa: BLE001 - a tool failure must never end the call
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _make(schema: dict[str, Any]):
    name = schema["name"]

    async def handler(raw_arguments: dict[str, object]) -> str:
        return json.dumps(await asyncio.to_thread(_run, name, dict(raw_arguments or {})), default=str)

    return function_tool(handler, raw_schema=schema)


def build_tools() -> list:
    return [_make(schema) for schema in SCHEMAS]
