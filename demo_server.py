"""Demo server: starts DEMON API on localhost:8000 with an echo engine.

No Ollama or cloud API key needed. The echo engine returns a canned response
so the web UI works end-to-end for demonstration purposes.

Usage:
    .venv/Scripts/python.exe demo_server.py
"""
from __future__ import annotations

import asyncio
import logging
import sys
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Sequence

# ------------------------------------------------------------------
# 1. Define and register a no-op echo engine BEFORE any serve imports
# ------------------------------------------------------------------
from OpenDEMON.core.registry import EngineRegistry
from OpenDEMON.core.types import Message
from OpenDEMON.engine._stubs import InferenceEngine, StreamChunk


class EchoEngine(InferenceEngine):
    """Demo engine: echoes the last user message back as Markdown."""

    engine_id = "echo"

    def generate(
        self,
        messages: Sequence[Message],
        *,
        model: str = "echo-1",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        last = next(
            (m.content for m in reversed(list(messages)) if m.role.value == "user"),
            "Hello!",
        )
        reply = (
            f"**DEMON Echo** *(demo mode — no real LLM connected)*\n\n"
            f"You said: *{last}*\n\n"
            f"---\n"
            f"To connect a real model:\n"
            f"- Start Ollama: `ollama serve` then `ollama pull llama3`\n"
            f"- Or set `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` in your environment"
        )
        return {
            "content": reply,
            "finish_reason": "stop",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 30,
                "total_tokens": 40,
            },
        }

    async def stream(
        self,
        messages: Sequence[Message],
        *,
        model: str = "echo-1",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        result = self.generate(messages, model=model)
        for word in result["content"].split(" "):
            yield word + " "
            await asyncio.sleep(0.015)

    def list_models(self) -> List[str]:
        return ["echo-1"]

    def health(self) -> bool:
        return True


# Register under key "echo"
if not EngineRegistry.contains("echo"):
    EngineRegistry.register_value("echo", EchoEngine)

# ------------------------------------------------------------------
# 2. Patch get_engine so it always falls back to EchoEngine
# ------------------------------------------------------------------
import OpenDEMON.engine as _eng_mod

_real_get_engine = _eng_mod.get_engine


def _patched_get_engine(config, engine_key=None, model=None):
    result = _real_get_engine(config, engine_key, model=model)
    if result is None:
        print("[demo_server] No engine found — using EchoEngine fallback.")
        return ("echo", EchoEngine())
    return result


_eng_mod.get_engine = _patched_get_engine

# Also patch inside _discovery so serve.py's internal calls work
import OpenDEMON.engine._discovery as _disc_mod
_disc_mod.get_engine = _patched_get_engine

# ------------------------------------------------------------------
# 3. Start the server
# ------------------------------------------------------------------
import uvicorn
from OpenDEMON.core.config import load_config
from OpenDEMON.core.events import EventBus
from OpenDEMON.intelligence import register_builtin_models
from OpenDEMON.server.app import create_app

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    config = load_config()
    register_builtin_models()

    engine_name, engine = _patched_get_engine(config)
    print(f"[demo_server] Engine: {engine_name}")
    print(f"[demo_server] Starting API server on http://127.0.0.1:8000")
    print(f"[demo_server] Open the frontend at http://127.0.0.1:5173")
    print()

    bus = EventBus()

    app = create_app(
        engine,
        "echo-1",
        agent=None,
        bus=bus,
        engine_name=engine_name,
        agent_name="",
        config=config,
    )

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
