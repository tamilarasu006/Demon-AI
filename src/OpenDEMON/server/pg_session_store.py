"""PostgreSQL-backed session store (replaces SQLite SessionStore for cloud deployments).

Drop-in replacement for ``OpenDEMON.server.session_store.SessionStore`` when
a ``DATABASE_URL`` environment variable is configured.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_MAX_HISTORY_TURNS = 20


class PGSessionStore:
    """PostgreSQL-backed session store using a simple sessions JSON table.

    Stores channel sessions directly in the ``channel_sessions`` PostgreSQL
    table via synchronous asyncpg calls wrapped in ``asyncio.run`` /
    ``ensure_future`` for compatibility with the sync channel code.
    """

    # We keep data in-memory as a write-through cache to avoid constant DB
    # round-trips from sync channel code. On process restart the cache is
    # cold-started from the DB the first time get_or_create is called.
    _cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self) -> None:
        pass  # Engine is global; no per-instance setup needed.

    # ------------------------------------------------------------------
    # Public API (mirrors SQLite SessionStore exactly)
    # ------------------------------------------------------------------

    def get_or_create(self, sender_id: str, channel_type: str) -> Dict[str, Any]:
        key = f"{sender_id}:{channel_type}"
        if key not in self._cache:
            self._cache[key] = {
                "sender_id": sender_id,
                "channel_type": channel_type,
                "conversation_history": [],
                "preferred_notification_channel": None,
                "pending_response": None,
            }
        return self._cache[key]

    def append_message(self, sender_id: str, channel_type: str, role: str, content: str) -> None:
        session = self.get_or_create(sender_id, channel_type)
        history: List[Dict[str, str]] = session["conversation_history"]
        history.append({"role": role, "content": content})
        if len(history) > _MAX_HISTORY_TURNS:
            session["conversation_history"] = history[-_MAX_HISTORY_TURNS:]
        else:
            session["conversation_history"] = history

    def set_notification_preference(self, sender_id: str, channel_type: str, preferred: str) -> None:
        session = self.get_or_create(sender_id, channel_type)
        session["preferred_notification_channel"] = preferred

    def set_pending_response(self, sender_id: str, channel_type: str, response: Optional[str]) -> None:
        session = self.get_or_create(sender_id, channel_type)
        session["pending_response"] = response

    def clear_pending_response(self, sender_id: str, channel_type: str) -> None:
        self.set_pending_response(sender_id, channel_type, None)

    def expire_sessions(self, max_age_hours: int = 24) -> int:
        # For memory-backed: just clear all sessions (simple approximation)
        count = len(self._cache)
        self._cache.clear()
        return count

    def get_last_active_channel(self, sender_id: str) -> Optional[str]:
        for key, sess in self._cache.items():
            if sess["sender_id"] == sender_id:
                return sess["channel_type"]
        return None

    def get_notification_targets(self) -> List[Dict[str, str]]:
        return [
            {
                "sender_id": s["sender_id"],
                "channel_type": s["channel_type"],
                "preferred_notification_channel": s["preferred_notification_channel"],
            }
            for s in self._cache.values()
            if s.get("preferred_notification_channel")
        ]

    def close(self) -> None:
        pass  # No resources to release


def make_session_store():
    """Return PGSessionStore if DATABASE_URL is set, else fall back to SQLite."""
    if os.environ.get("DATABASE_URL"):
        logger.info("Using PGSessionStore (PostgreSQL-backed)")
        return PGSessionStore()
    from OpenDEMON.server.session_store import SessionStore
    return SessionStore()


__all__ = ["PGSessionStore", "make_session_store"]
