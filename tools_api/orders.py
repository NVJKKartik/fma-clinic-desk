"""Orders, their history and refund requests for the Corner Bookshop order desk. Seeded in memory at startup."""

from __future__ import annotations

import threading
import uuid

_LOCK = threading.Lock()

ORDERS: dict[str, dict] = {}
HISTORY: dict[str, list[dict]] = {}
REFUNDS: dict[str, dict] = {}


def seed() -> None:
    """Three orders, each with the events it went through."""
    with _LOCK:
        ORDERS.clear()
        HISTORY.clear()
        REFUNDS.clear()
        ORDERS.update(
            {
                "B-1001": {"order_id": "B-1001", "customer": "Ana Ruiz", "item": "The Left Hand of Darkness",
                           "total": 18.50, "status": "delivered"},
                "B-1002": {"order_id": "B-1002", "customer": "Bo Lindqvist", "item": "A Wizard of Earthsea (boxed set)",
                           "total": 64.00, "status": "delivered"},
                "B-1003": {"order_id": "B-1003", "customer": "Chen Wei", "item": "Piranesi",
                           "total": 22.00, "status": "shipped"},
            }
        )
        HISTORY.update(
            {
                "B-1001": [
                    {"at": "2026-11-02", "event": "placed"},
                    {"at": "2026-11-03", "event": "shipped"},
                    {"at": "2026-11-06", "event": "delivered"},
                ],
                "B-1002": [
                    {"at": "2026-11-04", "event": "placed"},
                    {"at": "2026-11-05", "event": "shipped"},
                    {"at": "2026-11-09", "event": "delivered", "note": "box arrived damaged"},
                ],
                "B-1003": [
                    {"at": "2026-11-12", "event": "placed"},
                    {"at": "2026-11-14", "event": "shipped"},
                ],
            }
        )


def lookup_order(order_id: str) -> dict:
    """One order: its customer, item, total and status."""
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        return {"ok": False, "error": f"no order {order_id}"}
    return {"ok": True, "order": dict(order)}


def order_history(order_id: str):
    """Each event an order went through, oldest first, one at a time."""
    for event in HISTORY.get(order_id.strip().upper(), []):
        yield dict(event)


def request_refund(order_id: str, reason: str) -> dict:
    """Asks for a refund of a delivered order. A store manager decides every refund; the desk never approves one."""
    order_id = order_id.strip().upper()
    with _LOCK:
        order = ORDERS.get(order_id)
        if order is None:
            return {"ok": False, "error": f"no order {order_id}"}
        if order["status"] != "delivered":
            return {"ok": False, "error": f"order {order_id} is {order['status']}; only a delivered order can be refunded"}
        request = {"request_id": f"R-{uuid.uuid4().hex[:6].upper()}", "order_id": order_id, "reason": reason,
                   "amount": order["total"], "status": "awaiting manager approval"}
        REFUNDS[request["request_id"]] = request
        return {"ok": True, "refund": dict(request)}
