"""The Corner Bookshop's tools service: orders, their history and refund requests over HTTP. Seeded in memory.

GET  /health
GET  /orders/{order_id}            an order
GET  /orders/{order_id}/history    the events it went through, oldest first
POST /refunds                      {"order_id", "reason"}: a refund request for the manager to decide
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import orders


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

    def _answer(self, result: dict) -> None:
        self._send(200 if result.get("ok") else 404, result)

    def do_GET(self) -> None:
        parts = [part for part in self.path.split("?", 1)[0].split("/") if part]
        if parts == ["health"]:
            self._send(200, {"status": "ok"})
        elif len(parts) == 2 and parts[0] == "orders":
            self._answer(orders.lookup_order(parts[1]))
        elif len(parts) == 3 and parts[0] == "orders" and parts[2] == "history":
            self._send(200, {"ok": True, "events": list(orders.order_history(parts[1]))})
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
        result = orders.request_refund(str(body.get("order_id") or ""), str(body.get("reason") or ""))
        self._send(201 if result.get("ok") else 409, result)


def main() -> None:
    orders.seed()
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8081"))), Handler).serve_forever()


if __name__ == "__main__":
    main()
