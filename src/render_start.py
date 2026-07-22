"""Render.com entry point — starts DEMON API with echo fallback engine.

Render injects PORT as an env var. No Ollama or API key needed for
the demo mode; set OPENAI_API_KEY or ANTHROPIC_API_KEY env vars in
the Render dashboard to enable real LLM responses.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Sequence

# ------------------------------------------------------------------
# Register echo fallback engine BEFORE any serve imports
# ------------------------------------------------------------------
from OpenDEMON.core.registry import EngineRegistry
from OpenDEMON.core.types import Message
from OpenDEMON.engine._stubs import InferenceEngine, StreamChunk


class EchoEngine(InferenceEngine):
    """Demo engine used when no real LLM is configured."""

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
            f"To enable real AI responses, set one of these environment variables "
            f"in your Render dashboard:\n"
            f"- `NVIDIA_API_KEY` — for NVIDIA NIM (Llama, Nemotron, Mistral)\n"
            f"- `OPENAI_API_KEY` — for GPT-4o, GPT-4.1, etc.\n"
            f"- `ANTHROPIC_API_KEY` — for Claude models\n"
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
        if os.environ.get("NVIDIA_API_KEY"):
            return [
                "meta/llama-3.3-70b-instruct",
                "meta/llama-3.1-405b-instruct",
                "nvidia/llama-3.1-nemotron-ultra-253b-v1",
                "mistralai/mistral-large-2-instruct",
                "google/gemma-3-27b-it",
            ]
        return ["echo-1"]

    def health(self) -> bool:
        return True


if not EngineRegistry.contains("echo"):
    EngineRegistry.register_value("echo", EchoEngine)

# Patch get_engine to fall back to echo when no real engine is available
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
# Start server
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

    # NVIDIA NIM — OpenAI-compatible at integrate.api.nvidia.com/v1
    nvidia_key = os.environ.get("NVIDIA_API_KEY", "")
    if nvidia_key:
        os.environ["OPENAI_API_KEY"] = nvidia_key
        os.environ.setdefault("OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1")
        print("[OpenDemon] NVIDIA NIM active — integrate.api.nvidia.com", flush=True)

    config = load_config()
    register_builtin_models()

    engine_name, engine = _patched_get_engine(config)

    # Pick default model
    default_model = "echo-1"
    if nvidia_key:
        default_model = "meta/llama-3.3-70b-instruct"
    elif os.environ.get("OPENAI_API_KEY") and not nvidia_key:
        default_model = "gpt-4o-mini"
    elif os.environ.get("ANTHROPIC_API_KEY"):
        default_model = "claude-haiku-4-5"

    print(f"[OpenDemon] Engine  : {engine_name}", flush=True)
    print(f"[OpenDemon] Model   : {default_model}", flush=True)
    print(f"[OpenDemon] Listening on {host}:{port}", flush=True)

    # Initialize MongoDB connection if URI is provided
    if os.environ.get("MONGODB_URI"):
        try:
            from OpenDEMON.mongodb import get_db
            get_db()  # triggers connection + ping
        except Exception as exc:
            print(f"[OpenDemon] MongoDB init error: {exc}", flush=True)

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
