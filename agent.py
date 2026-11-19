"""Corner Bookshop order desk, by phone: a LiveKit voice worker. Orders live in memory."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import config
import gateway_llm
import orders
import voice_tools

INSTRUCTIONS = (Path(__file__).parent / "instructions.md").read_text(encoding="utf-8")
GREETING = "Corner Bookshop order desk. How can I help with your order?"
REQUIRED_ENV = [
    "LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "DEEPGRAM_API_KEY", "LLM_BASE_URL", "LLM_API_KEY",
    "LLM_MODEL",
]


def check_env() -> None:
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name, "").strip()]
    if missing:
        sys.exit("Missing required environment variables: " + ", ".join(missing))


def prewarm(proc) -> None:
    from livekit.plugins import silero

    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx) -> None:
    from livekit.agents import Agent, AgentSession
    from livekit.plugins import deepgram

    await ctx.connect()
    session = AgentSession(
        stt=deepgram.STT(model=config.STT_MODEL, language=config.STT_LANGUAGE),
        llm=gateway_llm.build_llm(config.LLM_TEMPERATURE),
        tts=deepgram.TTS(model=config.TTS_MODEL),
        vad=ctx.proc.userdata["vad"],
        max_tool_steps=config.MAX_TOOL_STEPS,
    )
    await session.start(agent=Agent(instructions=INSTRUCTIONS, tools=voice_tools.build_tools()), room=ctx.room)
    await session.say(GREETING)


def main() -> None:
    from livekit.agents import WorkerOptions, cli

    check_env()
    orders.seed()
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name=os.environ.get("LIVEKIT_AGENT_NAME", ""),
        )
    )


if __name__ == "__main__":
    main()
