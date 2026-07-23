"""Render.com / local entry point for OpenDemon API server.

ENV vars are set FIRST before any OpenDEMON imports so that
CloudEngine._init_clients() picks them up correctly.
"""
from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Sequence

# ------------------------------------------------------------------
# 0. Set env vars BEFORE any OpenDEMON imports
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
    """Fallback engine when no real LLM is reachable."""

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
            f"**OpenDemon** *(demo mode — no LLM configured)*\n\n"
            f"You said: *{last}*\n\n"
            f"---\n"
            f"Set `NVIDIA_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY` "
            f"in your environment to enable real AI responses."
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
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        result = self.generate(messages, model=model)
        for word in result["content"].split(" "):
            yield word + " "
            await asyncio.sleep(0.01)

    def list_models(self) -> List[str]:
        return ["echo-1"]

    def health(self) -> bool:
        return True


if not EngineRegistry.contains("echo"):
    EngineRegistry.register_value("echo", EchoEngine)

# ------------------------------------------------------------------
# 2. Patch get_engine to use CloudEngine when key is set,
#    otherwise fall back to EchoEngine
# ------------------------------------------------------------------
import OpenDEMON.engine as _eng_mod
import OpenDEMON.engine._discovery as _disc_mod

_real_get_engine = _eng_mod.get_engine


def _patched_get_engine(config, engine_key=None, model=None):
    # If a cloud key is set, try the cloud engine first
    if os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"):
        try:
            from OpenDEMON.engine.cloud import CloudEngine
            cloud = CloudEngine()
            if cloud.health():
                return ("cloud", cloud)
        except Exception:
            pass

    # Try the normal discovery
    result = _real_get_engine(config, engine_key, model=model)
    if result is not None:
        return result

    # Final fallback: echo engine
    return ("echo", EchoEngine())


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

    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"

    config = load_config()
    register_builtin_models()

    engine_name, engine = _patched_get_engine(config)

    # Pick default model
    default_model = "echo-1"
    if _nvidia_key:
        default_model = "meta/llama-3.3-70b-instruct"
    elif os.environ.get("OPENAI_API_KEY") and not _nvidia_key:
        default_model = "gpt-4o-mini"
    elif os.environ.get("ANTHROPIC_API_KEY"):
        default_model = "claude-haiku-4-5"

    print(f"[OpenDemon] Engine  : {engine_name}", flush=True)
    print(f"[OpenDemon] Model   : {default_model}", flush=True)
    print(f"[OpenDemon] Listening on {host}:{port}", flush=True)

    # Initialize MongoDB if URI set
    if os.environ.get("MONGODB_URI"):
        try:
            from OpenDEMON.mongodb import get_db
            get_db()
        except Exception as exc:
            print(f"[OpenDemon] MongoDB error: {exc}", flush=True)

    bus = EventBus()

    app = create_app(
        engine,
        default_model,
        agent=None,
        bus=bus,
        engine_name=engine_name,
        agent_name="",
        config=config,
        cors_origins=["*"],
    )

    uvicorn.run(app, host=host, port=port, log_level="info")
