"""Front-desk chat agent for Maple Street Clinic.

Serves an OpenAI-compatible chat endpoint (POST /v1/chat/completions, GET /health) using only
the standard library. Behaviour is set by instructions.md; patients and appointments live in memory.
"""

from __future__ import annotations

import json
import os
import urllib.request
import uuid
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import config
import seed
import tools

INSTRUCTIONS_FILE = Path(__file__).with_name("instructions.md")


def system_prompt() -> str:
    text = INSTRUCTIONS_FILE.read_text(encoding="utf-8")
    today = date.today()
    replacements = {
        "{{today}}": f"{today.strftime('%A')} {today.isoformat()}",
        "{{hours}}": config.HOURS_TEXT,
        "{{cancel_hours}}": str(config.CANCELLATION_WINDOW_HOURS),
        "{{cancel_fee}}": str(config.CANCELLATION_FEE),
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text


def _llm(messages: list[dict]) -> dict:
    base_url = os.environ["LLM_BASE_URL"].rstrip("/")
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(
            {
                "model": os.environ["LLM_MODEL"],
                "messages": messages,
                "tools": tools.TOOLS,
                "temperature": config.TEMPERATURE,
            }
        ).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "authorization": f"Bearer {os.environ['LLM_API_KEY']}",
        },
    )
    with urllib.request.urlopen(request, timeout=config.LLM_TIMEOUT_SECONDS) as response:
        return json.load(response)["choices"][0]["message"]


def _run_tool(call: dict) -> tuple[dict, dict]:
    """The parsed arguments and the result of one tool call."""
    try:
        arguments = json.loads(call["function"]["arguments"] or "{}")
    except json.JSONDecodeError:
        return {}, {"ok": False, "error": "arguments were not valid JSON"}
    try:
        return arguments, tools.run_tool(call["function"]["name"], arguments)
    except Exception as exc:  # the model sees the failure and can correct the call
        return arguments, {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def reply(history: list[dict]) -> tuple[str, list[dict]]:
    """The assistant's answer, and the tools it ran to give it."""
    turns = [m for m in history if m.get("role") in ("user", "assistant")]
    conversation = [{"role": "system", "content": system_prompt()}]
    conversation += turns[-config.HISTORY_MESSAGES :]
    completed: list[dict] = []
    for _ in range(config.MAX_TOOL_ROUNDS):
        message = _llm(conversation)
        calls = message.get("tool_calls") or []
        if not calls:
            return message.get("content") or "", completed
        conversation.append(message)
        for call in calls:
            arguments, result = _run_tool(call)
            conversation.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)})
            completed.append(
                {
                    "id": uuid.uuid4().hex,
                    "name": call["function"]["name"],
                    "arguments": arguments,
                    "result": result,
                    "error": result.get("ok") is False,
                }
            )
    return "Sorry, I could not finish that request. Please call the clinic again.", completed


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
        if self.path.rstrip("/") == "/health":
            self._send(200, {"status": "ok"})
        else:
            self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path.rstrip("/") not in ("/v1/chat/completions", "/chat/completions"):
            self._send(404, {"error": "not_found"})
            return
        try:
            size = int(self.headers.get("content-length") or 0)
            body = json.loads(self.rfile.read(size) or b"{}")
            content, completed = reply(body.get("messages") or [])
        except Exception as exc:
            self._send(500, {"error": {"type": type(exc).__name__, "message": str(exc)}})
            return
        self._send(
            200,
            {
                "object": "chat.completion",
                "model": os.environ.get("LLM_MODEL", ""),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
                # The tools this reply ran, in order: id, name, arguments, result, error.
                "completed_tools": completed,
            },
        )


def main() -> None:
    for name in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        if not os.environ.get(name):
            raise SystemExit(f"{name} is not set")
    system_prompt()  # fail at startup if instructions.md is missing
    seed.seed()
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), Handler).serve_forever()


if __name__ == "__main__":
    main()
