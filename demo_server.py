"""Demo/local server for OpenDemon.

Reads NVIDIA_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY from environment
and connects to the appropriate cloud engine. Falls back to echo mode
when no key is set.

Usage:
    # With NVIDIA NIM:
    $env:NVIDIA_API_KEY='nvapi-...'
    .venv\Scripts\python.exe demo_server.py

    # Without any key (echo mode):
    .venv\Scripts\python.exe demo_server.py
"""
from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Sequence

# ------------------------------------------------------------------
# 0. Apply API keys BEFORE any OpenDEMON imports so cloud engine
#    clients are initialized with the correct credentials
# ------------------------------------------------------------------
_nvidia_key = os.environ.get("NVIDIA_API_KEY", "")
if _nvidia_key:
    os.environ["OPENAI_API_KEY"] = _nvidia_key
    os.environ.setdefault("OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1")
    print("[OpenDemon] NVIDIA NIM active — integrate.api.nvidia.com", flush=True)

# ------------------------------------------------------------------
# 1. Register echo fallback engine
# ------------------------------------------------------------------
from OpenDEMON.core.registry import EngineRegistry
from OpenDEMON.core.types import Message
from OpenDEMON.engine._stubs import InferenceEngine


class EchoEngine(InferenceEngine):
    """Fallback engine when no real LLM is configured."""

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
            (m.content for m in reversed(list(messages)) if getattr(m.role, "value", m.role) == "user"),
            "Hello!",
        )
        reply = (
            f"**OpenDemon** *(demo mode — no real LLM connected)*\n\n"
            f"You said: *{last}*\n\n"
            f"To connect a real model:\n"
            f"- Set `NVIDIA_API_KEY` to use NVIDIA NIM models\n"
            f"- Or set `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`"
        )
        return {
            "content": reply,
            "finish_reason": "stop",
            "usage": {"prompt_tokens": 10, "completion_tokens": 30, "total_tokens": 40},
        }

    async def stream(
        self,
        messages: Sequence[Message],
        *,
        model: str = "echo-1",
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        result = self.generate(messages)
        for word in result["content"].split(" "):
            yield word + " "
            await asyncio.sleep(0.015)

    def list_models(self) -> List[str]:
        return ["echo-1"]

    def health(self) -> bool:
        return True


if not EngineRegistry.contains("echo"):
    EngineRegistry.register_value("echo", EchoEngine)

# ------------------------------------------------------------------
# 2. Patch get_engine to fall back to EchoEngine
# ------------------------------------------------------------------
import OpenDEMON.engine as _eng_mod
import OpenDEMON.engine._discovery as _disc_mod

_real_get_engine = _eng_mod.get_engine


def _patched_get_engine(config, engine_key=None, model=None):
    result = _real_get_engine(config, engine_key, model=model)
    if result is None:
        return ("echo", EchoEngine())
    return result


_eng_mod.get_engine = _patched_get_engine
_disc_mod.get_engine = _patched_get_engine

# ------------------------------------------------------------------
# 3. Start server
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

    # Pick best default model
    default_model = "echo-1"
    if _nvidia_key:
        default_model = "meta/llama-3.1-8b-instruct"
        engine_name = "cloud"
    elif os.environ.get("OPENAI_API_KEY"):
        default_model = "gpt-4o-mini"
        engine_name = "cloud"
    elif os.environ.get("ANTHROPIC_API_KEY"):
        default_model = "claude-haiku-4-5"
        engine_name = "cloud"

    print(f"[OpenDemon] Engine  : {engine_name}", flush=True)
    print(f"[OpenDemon] Model   : {default_model}", flush=True)
    print(f"[OpenDemon] API     : http://127.0.0.1:8000", flush=True)
    print(f"[OpenDemon] UI      : http://127.0.0.1:5173", flush=True)

    bus = EventBus()

    app = create_app(
        engine,
        default_model,
        agent=None,
        bus=bus,
        engine_name=engine_name,
        agent_name="",
        config=config,
    )

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
