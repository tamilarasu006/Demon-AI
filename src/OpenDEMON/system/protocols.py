"""Structural protocols for substituting fakes in place of DEMONSystem."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Protocol

if TYPE_CHECKING:
    from OpenDEMON.core.config import DEMONConfig
    from OpenDEMON.core.events import EventBus
    from OpenDEMON.engine._stubs import InferenceEngine
    from OpenDEMON.security.capabilities import CapabilityPolicy
    from OpenDEMON.sessions.session import SessionStore
    from OpenDEMON.tools._stubs import BaseTool
    from OpenDEMON.tools.storage._stubs import MemoryBackend
    from OpenDEMON.traces.collector import TraceCollector
    from OpenDEMON.traces.store import TraceStore


class OrchestratorDeps(Protocol):
    """Minimum surface of DEMONSystem that QueryOrchestrator depends on.

    Tests can satisfy this with a lightweight class — no need to construct
    the full DEMONSystem dataclass or materialize every subsystem.
    """

    config: DEMONConfig
    bus: EventBus
    engine: InferenceEngine
    engine_key: str
    model: str
    agent_name: str
    tools: List[BaseTool]
    memory_backend: Optional[MemoryBackend]
    capability_policy: Optional[CapabilityPolicy]
    session_store: Optional[SessionStore]
    trace_store: Optional[TraceStore]
    trace_collector: Optional[TraceCollector]  # written by _run_agent

    # Optional attribute (getattr with default) — declared for type clarity.
    _skill_few_shot_examples: Any
