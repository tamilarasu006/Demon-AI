"""PostgreSQL-backed trace store (replaces SQLite TraceStore for multi-user cloud deployments).

The class is a drop-in replacement for ``OpenDEMON.traces.store.TraceStore``
when a ``DATABASE_URL`` environment variable is configured. It uses the
shared SQLAlchemy async engine and the ``traces`` / ``trace_steps`` models.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, List, Optional

from OpenDEMON.core.events import Event, EventBus, EventType
from OpenDEMON.core.types import StepType, Trace, TraceStep

logger = logging.getLogger(__name__)


class PGTraceStore:
    """Async-compatible PostgreSQL trace store.

    Can be used as a drop-in for ``TraceStore`` in async FastAPI contexts.
    For sync callers the ``save_sync`` / ``get_sync`` helpers run the event
    loop inline.
    """

    def __init__(self, user_id: str = "system") -> None:
        self._user_id = user_id

    # ------------------------------------------------------------------
    # Async API
    # ------------------------------------------------------------------

    async def save_async(self, trace: Trace, *, user_id: Optional[str] = None) -> None:
        """Persist a complete trace to PostgreSQL."""
        from OpenDEMON.database.engine import AsyncSessionLocal
        from OpenDEMON.database.models.trace import Trace as DBTrace, TraceStep as DBStep

        uid = user_id or self._user_id
        async with AsyncSessionLocal() as session:
            db_trace = DBTrace(
                user_id=uid,
                trace_id=trace.trace_id,
                query=trace.query,
                agent=trace.agent,
                model=trace.model,
                engine=trace.engine,
                result=trace.result,
                outcome=trace.outcome,
                feedback=trace.feedback,
                started_at=trace.started_at,
                ended_at=trace.ended_at,
                total_tokens=trace.total_tokens,
                total_latency_seconds=trace.total_latency_seconds,
                metadata_json=json.dumps(trace.metadata),
                messages_json=json.dumps(trace.messages),
            )
            session.add(db_trace)
            for idx, step in enumerate(trace.steps):
                db_step = DBStep(
                    trace_id=trace.trace_id,
                    user_id=uid,
                    step_index=idx,
                    step_type=step.step_type.value if isinstance(step.step_type, StepType) else step.step_type,
                    timestamp=step.timestamp,
                    duration_seconds=step.duration_seconds,
                    input_json=json.dumps(step.input),
                    output_json=json.dumps(step.output),
                    metadata_json=json.dumps(step.metadata),
                )
                session.add(db_step)
            try:
                await session.commit()
            except Exception as exc:
                await session.rollback()
                logger.warning("PGTraceStore.save_async failed: %s", exc)

    async def get_async(self, trace_id: str, user_id: Optional[str] = None) -> Optional[Trace]:
        """Retrieve a trace by trace_id."""
        from sqlalchemy import select
        from OpenDEMON.database.engine import AsyncSessionLocal
        from OpenDEMON.database.models.trace import Trace as DBTrace, TraceStep as DBStep

        uid = user_id or self._user_id
        async with AsyncSessionLocal() as session:
            stmt = select(DBTrace).where(
                DBTrace.trace_id == trace_id,
                DBTrace.user_id == uid,
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return self._db_to_trace(row, await self._fetch_steps(session, trace_id))

    async def list_async(self, *, user_id: Optional[str] = None, limit: int = 100) -> List[Trace]:
        """Return the most recent traces for a user."""
        from sqlalchemy import select, desc
        from OpenDEMON.database.engine import AsyncSessionLocal
        from OpenDEMON.database.models.trace import Trace as DBTrace

        uid = user_id or self._user_id
        async with AsyncSessionLocal() as session:
            stmt = select(DBTrace).where(DBTrace.user_id == uid).order_by(desc(DBTrace.started_at)).limit(limit)
            result = await session.execute(stmt)
            rows = result.scalars().all()
            traces = []
            for row in rows:
                steps = await self._fetch_steps(session, row.trace_id)
                traces.append(self._db_to_trace(row, steps))
            return traces

    async def update_feedback_async(self, trace_id: str, score: float, user_id: Optional[str] = None) -> bool:
        """Update the feedback score for a trace."""
        from sqlalchemy import update
        from OpenDEMON.database.engine import AsyncSessionLocal
        from OpenDEMON.database.models.trace import Trace as DBTrace

        uid = user_id or self._user_id
        async with AsyncSessionLocal() as session:
            stmt = (
                update(DBTrace)
                .where(DBTrace.trace_id == trace_id, DBTrace.user_id == uid)
                .values(feedback=score)
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    # ------------------------------------------------------------------
    # Sync wrappers (for backward compatibility with sync code)
    # ------------------------------------------------------------------

    def save(self, trace: Trace, *, user_id: Optional[str] = None) -> None:
        """Sync wrapper around save_async."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self.save_async(trace, user_id=user_id))
            else:
                loop.run_until_complete(self.save_async(trace, user_id=user_id))
        except Exception as exc:
            logger.warning("PGTraceStore.save failed: %s", exc)

    def subscribe_to_bus(self, bus: EventBus) -> None:
        """Subscribe to TRACE_COMPLETE events on bus."""
        bus.subscribe(EventType.TRACE_COMPLETE, self._on_event)

    def _on_event(self, event: Event) -> None:
        trace = event.data.get("trace")
        if isinstance(trace, Trace):
            self.save(trace)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _fetch_steps(self, session, trace_id: str):
        from sqlalchemy import select
        from OpenDEMON.database.models.trace import TraceStep as DBStep
        stmt = select(DBStep).where(DBStep.trace_id == trace_id).order_by(DBStep.step_index)
        result = await session.execute(stmt)
        return result.scalars().all()

    def _db_to_trace(self, row, steps) -> Trace:
        return Trace(
            trace_id=row.trace_id,
            query=row.query,
            agent=row.agent,
            model=row.model,
            engine=row.engine,
            result=row.result,
            outcome=row.outcome,
            feedback=row.feedback,
            started_at=row.started_at,
            ended_at=row.ended_at,
            total_tokens=row.total_tokens,
            total_latency_seconds=row.total_latency_seconds,
            metadata=json.loads(row.metadata_json or "{}"),
            messages=json.loads(row.messages_json or "[]"),
            steps=[
                TraceStep(
                    step_type=StepType(s.step_type),
                    timestamp=s.timestamp,
                    duration_seconds=s.duration_seconds,
                    input=json.loads(s.input_json or "{}"),
                    output=json.loads(s.output_json or "{}"),
                    metadata=json.loads(s.metadata_json or "{}"),
                )
                for s in steps
            ],
        )


def get_trace_store(user_id: str = "system") -> "PGTraceStore | None":
    """Return a PGTraceStore if DATABASE_URL is configured, else None."""
    if os.environ.get("DATABASE_URL"):
        return PGTraceStore(user_id=user_id)
    return None


__all__ = ["PGTraceStore", "get_trace_store"]
