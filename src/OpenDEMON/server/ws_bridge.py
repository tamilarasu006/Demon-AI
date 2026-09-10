"""WebSocket bridge: EventBus → connected WebSocket clients."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from OpenDEMON.core.events import Event, EventBus, EventType

try:
    from fastapi import APIRouter, WebSocket, WebSocketDisconnect
except ImportError:  # pragma: no cover
    pass  # FastAPI is optional; create_ws_router will fail at call time

logger = logging.getLogger(__name__)

# Agent-related event types to forward
_AGENT_EVENTS = {
    EventType.AGENT_TICK_START,
    EventType.AGENT_TICK_END,
    EventType.AGENT_TICK_ERROR,
    EventType.AGENT_BUDGET_EXCEEDED,
    EventType.AGENT_STALL_DETECTED,
    EventType.AGENT_MESSAGE_RECEIVED,
    EventType.AGENT_CHECKPOINT_SAVED,
    EventType.TOOL_CALL_START,
    EventType.TOOL_CALL_END,
    EventType.INFERENCE_START,
    EventType.INFERENCE_END,
}


def create_ws_router(event_bus: EventBus) -> Any:
    """Create a FastAPI router with a WebSocket endpoint for agent events."""
    router = APIRouter()
    # Each connected client gets a queue + loop ref for thread-safe event delivery
    clients: dict[WebSocket, tuple[asyncio.Queue, asyncio.AbstractEventLoop]] = {}

    def _on_event(event: Event) -> None:
        """Forward event to all connected WebSocket client queues (thread-safe)."""
        payload = {
            "type": event.event_type.value,
            "timestamp": event.timestamp,
            "data": event.data or {},
        }
        for ws, (queue, loop) in list(clients.items()):
            agent_filter = getattr(ws, "_agent_filter", None)
            # Tick events carry "agent_id"; tool-call events carry "agent".
            # Match either so a per-agent subscriber actually receives the
            # tool calls that make up its live trace (without this, only
            # tick_start/end pass the filter and the trace looks empty).
            data = event.data or {}
            event_agent = data.get("agent_id") or data.get("agent")
            if agent_filter and event_agent != agent_filter:
                continue
            try:
                loop.call_soon_threadsafe(queue.put_nowait, payload)
            except (RuntimeError, asyncio.QueueFull):
                pass  # Loop closed or client is slow

    # Subscribe to all agent events
    for event_type in _AGENT_EVENTS:
        event_bus.subscribe(event_type, _on_event)

    @router.websocket("/v1/agents/events")
    async def agent_events(websocket: WebSocket) -> None:
        from OpenDEMON.server.auth_middleware import websocket_authorized

        expected_key = getattr(websocket.app.state, "api_key", "")
        if not websocket_authorized(websocket, expected_key):
            # 1008 = policy violation; reject before accepting the connection.
            await websocket.close(code=1008)
            return
        await websocket.accept()
        # Parse agent_id filter from query string
        agent_id = websocket.query_params.get("agent_id")
        websocket._agent_filter = agent_id  # type: ignore[attr-defined]
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        loop = asyncio.get_running_loop()
        clients[websocket] = (queue, loop)
        try:
            while True:
                payload = await queue.get()
                await websocket.send_json(payload)
        except WebSocketDisconnect:
            pass
        finally:
            clients.pop(websocket, None)

    return router


def create_ws_chat_router(event_bus: "EventBus") -> Any:
    """Create a FastAPI router with a WebSocket chat endpoint.

    Supports an optional ``"skills"`` key in incoming JSON messages to
    restrict the Active_Skill_Set for that message.
    """
    from OpenDEMON.core.events import EventBus as _EventBus  # noqa: F401

    router = APIRouter()

    @router.websocket("/v1/chat/ws")
    async def ws_chat(websocket: WebSocket) -> None:  # type: ignore[name-defined]
        from OpenDEMON.server.auth_middleware import websocket_authorized

        expected_key = getattr(websocket.app.state, "api_key", "")
        if not websocket_authorized(websocket, expected_key):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        try:
            while True:
                try:
                    data = await websocket.receive_json()
                except Exception:
                    break

                # --- Task 7.1: read optional "skills" key ---
                requested_skills: list[str] | None = None
                raw_skills = data.get("skills")
                if raw_skills and isinstance(raw_skills, list):
                    requested_skills = [s for s in raw_skills if isinstance(s, str) and s.strip()]

                # --- Task 7.2: validate skills, send error and skip if invalid ---
                validated_skills: list[str] | None = None
                if requested_skills:
                    skill_manager = getattr(websocket.app.state, "skill_manager", None)
                    if skill_manager is not None:
                        from OpenDEMON.skills.validation import (
                            UnknownSkillsError as _USE,
                            resolve_skill_names as _rsn,
                        )
                        try:
                            validated_skills = _rsn(
                                requested_skills,
                                skill_manager,
                                catalog_is_empty=len(skill_manager.skill_names()) == 0,
                            )
                        except _USE as exc:
                            error_payload: dict = {"type": "error", "unknown_skills": exc.unknown_names}
                            if exc.catalog_empty:
                                error_payload["detail"] = "No skills are installed."
                            await websocket.send_json(error_payload)
                            continue  # do NOT process this message

                # --- Task 7.3: apply filtered skill tools before dispatch ---
                if validated_skills:
                    skill_manager = getattr(websocket.app.state, "skill_manager", None)
                    if skill_manager is not None:
                        _active_tools = skill_manager.get_filtered_skill_tools(validated_skills)
                        logger.debug(
                            "WS chat: active skill tools for request: %s",
                            [getattr(t, "spec", t) and t.spec.name for t in _active_tools],
                        )

                # --- Dispatch message to engine/agent ---
                content = data.get("content", "")
                if not content:
                    await websocket.send_json({"type": "error", "detail": "Missing 'content' field."})
                    continue

                engine = getattr(websocket.app.state, "engine", None)
                agent = getattr(websocket.app.state, "agent", None)
                model = getattr(websocket.app.state, "model", "") or ""

                if engine is None:
                    await websocket.send_json({"type": "error", "detail": "No inference engine available."})
                    continue

                try:
                    from OpenDEMON.core.types import Message, Role
                    messages = [Message(role=Role.USER, content=content)]
                    if agent is not None:
                        from OpenDEMON.agents._stubs import AgentContext
                        result = agent.run(content, context=AgentContext())
                        reply = result.content if hasattr(result, "content") else str(result)
                    else:
                        result = engine.generate(messages, model=model)
                        reply = result.get("content", "") if isinstance(result, dict) else str(result)
                    await websocket.send_json({"type": "message", "content": reply})
                except Exception as exc:
                    logger.error("WS chat error: %s", exc, exc_info=True)
                    await websocket.send_json({"type": "error", "detail": str(exc)})

        except Exception:
            pass

    return router


__all__ = ["create_ws_router", "create_ws_chat_router"]
