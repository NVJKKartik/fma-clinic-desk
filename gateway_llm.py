"""The model as a LiveKit LLM, through the OpenAI-compatible gateway at LLM_BASE_URL.

Some providers behind the gateway (Vertex among them) stream a `usage` object with null counts on some chunks, which
LiveKit rejects; a small transport drops those and keeps the real one.
"""

from __future__ import annotations

import json
import os

import httpx
from livekit.plugins import openai as lk_openai
from openai import AsyncOpenAI


def _fix_line(line: bytes) -> bytes:
    if not line.startswith(b"data: {"):
        return line
    try:
        chunk = json.loads(line[6:])
    except ValueError:
        return line
    usage = chunk.get("usage")
    if isinstance(usage, dict) and (usage.get("prompt_tokens") is None or usage.get("completion_tokens") is None):
        chunk.pop("usage")
        return b"data: " + json.dumps(chunk).encode()
    return line


class _StreamFix(httpx.AsyncBaseTransport):
    def __init__(self) -> None:
        self._inner = httpx.AsyncHTTPTransport(retries=2)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        request.headers["Accept-Encoding"] = "identity"  # the rewrite needs plain SSE lines
        response = await self._inner.handle_async_request(request)
        if "text/event-stream" not in response.headers.get("content-type", ""):
            return response
        upstream = response.stream

        async def lines():
            buffer = b""
            async for part in upstream:
                buffer += part
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    yield _fix_line(line) + b"\n"
            if buffer:
                yield _fix_line(buffer)

        class _Stream(httpx.AsyncByteStream):
            def __aiter__(self):
                return lines()

            async def aclose(self) -> None:
                await upstream.aclose()

        return httpx.Response(
            response.status_code,
            headers=response.headers,
            stream=_Stream(),
            request=request,
            extensions=response.extensions,
        )


def build_llm(temperature: float) -> lk_openai.LLM:
    client = AsyncOpenAI(
        base_url=os.environ["LLM_BASE_URL"].rstrip("/"),
        api_key=os.environ["LLM_API_KEY"],
        http_client=httpx.AsyncClient(transport=_StreamFix(), timeout=60),
    )
    return lk_openai.LLM(model=os.environ["LLM_MODEL"], client=client, temperature=temperature)
