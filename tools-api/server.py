"""The Corner Bookshop's tools service: orders, their history and refund requests over HTTP, kept in Postgres.

GET  /health
GET  /orders/{order_id}            an order
GET  /orders/{order_id}/history    the events it went through, oldest first
POST /refunds                      {"order_id", "reason"}: a refund request for the manager to decide
GET  /refunds/{request_id}         a refund request and the manager's decision so far

Each request opens its own connection to DATABASE_URL: the database can be replaced between requests.
"""

from __future__ import annotations

import json
import os
import uuid
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

# The schema, when this service can see it: Postgres's own init applies it under Compose.
SCHEMAS = (Path(__file__).resolve().parent.parent / "db" / "schema.sql", Path.cwd() / "db" / "schema.sql")
SEED_ORDERS = [
    ("B-1001", "Ana Ruiz", "The Left Hand of Darkness", Decimal("18.50"), "delivered"),
    ("B-1002", "Bo Lindqvist", "A Wizard of Earthsea (boxed set)", Decimal("64.00"), "delivered"),
    ("B-1003", "Chen Wei", "Piranesi", Decimal("22.00"), "shipped"),
]
SEED_EVENTS = [
    ("B-1001", "2026-11-02", "placed", None), ("B-1001", "2026-11-03", "shipped", None),
    ("B-1001", "2026-11-06", "delivered", None),
    ("B-1002", "2026-11-04", "placed", None), ("B-1002", "2026-11-05", "shipped", None),
    ("B-1002", "2026-11-09", "delivered", "box arrived damaged"),
    ("B-1003", "2026-11-12", "placed", None), ("B-1003", "2026-11-14", "shipped", None),
]


def _connect():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row, autocommit=True)


def setup() -> None:
    """The schema when this service can see it and the tables are missing, and the shop's orders when the database
    holds none."""
    schema = next((path for path in SCHEMAS if path.is_file()), None)
    with _connect() as db:
        if schema is not None:
            db.execute(schema.read_text(encoding="utf-8"))
        if db.execute("SELECT to_regclass('orders') IS NULL AS missing").fetchone()["missing"]:
            return
        if db.execute("SELECT count(*) AS n FROM orders").fetchone()["n"] == 0:
            for row in SEED_ORDERS:
                db.execute("INSERT INTO orders VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING", row)
            for row in SEED_EVENTS:
                db.execute("INSERT INTO order_events (order_id, at, event, note) VALUES (%s, %s, %s, %s)", row)


def _plain(row: dict) -> dict:
    return json.loads(json.dumps(row, default=str))


def lookup_order(order_id: str) -> tuple[int, dict]:
    with _connect() as db:
        row = db.execute("SELECT * FROM orders WHERE order_id = %s", (order_id.strip().upper(),)).fetchone()
    return (200, {"ok": True, "order": _plain(row)}) if row else (404, {"ok": False, "error": f"no order {order_id}"})


def order_history(order_id: str) -> tuple[int, dict]:
    with _connect() as db:
        rows = db.execute(
            "SELECT at, event, note FROM order_events WHERE order_id = %s ORDER BY at, id", (order_id.strip().upper(),)
        ).fetchall()
    return 200, {"ok": True, "events": [{k: v for k, v in _plain(row).items() if v is not None} for row in rows]}


def request_refund(order_id: str, reason: str) -> tuple[int, dict]:
    order_id = order_id.strip().upper()
    with _connect() as db:
        order = db.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,)).fetchone()
        if order is None:
            return 404, {"ok": False, "error": f"no order {order_id}"}
        if order["status"] != "delivered":
            return 409, {"ok": False, "error": f"order {order_id} is {order['status']}; only a delivered order can be refunded"}
        request = db.execute(
            "INSERT INTO refund_requests (request_id, order_id, reason, amount) VALUES (%s, %s, %s, %s) RETURNING *",
            (f"R-{uuid.uuid4().hex[:6].upper()}", order_id, reason, order["total"]),
        ).fetchone()
    return 201, {"ok": True, "refund": _plain(request)}


def refund_status(request_id: str) -> tuple[int, dict]:
    with _connect() as db:
        row = db.execute("SELECT * FROM refund_requests WHERE request_id = %s", (request_id.strip().upper(),)).fetchone()
    return (200, {"ok": True, "refund": _plain(row)}) if row else (404, {"ok": False, "error": f"no refund request {request_id}"})


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return

    def _send(self, status: int, payload: dict) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        parts = [part for part in self.path.split("?", 1)[0].split("/") if part]
        if parts == ["health"]:
            self._send(200, {"status": "ok"})
        elif len(parts) == 2 and parts[0] == "orders":
            self._send(*lookup_order(parts[1]))
        elif len(parts) == 3 and parts[0] == "orders" and parts[2] == "history":
            self._send(*order_history(parts[1]))
        elif len(parts) == 2 and parts[0] == "refunds":
            self._send(*refund_status(parts[1]))
        else:
            self._send(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0].rstrip("/") != "/refunds":
            self._send(404, {"ok": False, "error": "not_found"})
            return
        size = int(self.headers.get("content-length") or 0)
        try:
            body = json.loads(self.rfile.read(size) or b"{}")
        except json.JSONDecodeError:
            self._send(400, {"ok": False, "error": "the body was not JSON"})
            return
        self._send(*request_refund(str(body.get("order_id") or ""), str(body.get("reason") or "")))


def main() -> None:
    setup()
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), Handler).serve_forever()


if __name__ == "__main__":
    main()
