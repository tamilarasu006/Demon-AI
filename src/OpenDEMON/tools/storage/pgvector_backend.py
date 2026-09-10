"""PostgreSQL + pgvector memory backend.

Registers as the ``pgvector`` backend in the MemoryRegistry.
Requires the ``pgvector`` Python package and a DATABASE_URL pointing to a
PostgreSQL instance with the ``vector`` extension enabled.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from OpenDEMON.core.events import EventType, get_event_bus
from OpenDEMON.core.registry import MemoryRegistry
from OpenDEMON.tools.storage._stubs import (
    MemoryBackend,
    MemoryBackendUnavailable,
    RetrievalResult,
)

logger = logging.getLogger(__name__)


@MemoryRegistry.register("pgvector")
class PGVectorMemory(MemoryBackend):
    """Semantic memory backend using PostgreSQL + pgvector.

    Stores documents in the ``memories`` table and performs cosine-similarity
    searches using the ``<=>`` pgvector operator.
    """

    backend_id: str = "pgvector"

    def __init__(
        self,
        embedder=None,
        user_id: str = "system",
    ) -> None:
        if not os.environ.get("DATABASE_URL"):
            raise MemoryBackendUnavailable(
                "PGVectorMemory requires DATABASE_URL to be set."
            )
        self._user_id = user_id
        self._embedder = embedder

    # ------------------------------------------------------------------
    # MemoryBackend interface
    # ------------------------------------------------------------------

    def store(
        self,
        content: str,
        *,
        source: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Embed *content* and persist to PostgreSQL. Returns doc id."""
        import asyncio

        embedding = self._embed(content)
        doc_id = asyncio.get_event_loop().run_until_complete(
            self._store_async(content, embedding, metadata or {})
        )
        bus = get_event_bus()
        bus.publish(
            EventType.MEMORY_STORE,
            {"backend": self.backend_id, "doc_id": doc_id, "source": source},
        )
        return doc_id

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        **kwargs: Any,
    ) -> List[RetrievalResult]:
        """Embed *query* and find nearest neighbours via pgvector cosine distance."""
        import asyncio

        if not query.strip():
            return []

        embedding = self._embed(query)
        results = asyncio.get_event_loop().run_until_complete(
            self._retrieve_async(embedding, top_k=top_k)
        )
        bus = get_event_bus()
        bus.publish(
            EventType.MEMORY_RETRIEVE,
            {"backend": self.backend_id, "query": query, "num_results": len(results)},
        )
        return results

    def delete(self, doc_id: str) -> bool:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._delete_async(doc_id))

    def clear(self) -> None:
        import asyncio
        asyncio.get_event_loop().run_until_complete(self._clear_async())

    def count(self) -> int:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._count_async())

    def close(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Async internals
    # ------------------------------------------------------------------

    async def _store_async(self, content: str, embedding: List[float], metadata: dict) -> str:
        from OpenDEMON.database.engine import AsyncSessionLocal
        from OpenDEMON.database.models.memory import Memory
        from OpenDEMON.database.base import uuid_gen

        doc_id = uuid_gen()
        async with AsyncSessionLocal() as session:
            mem = Memory(
                id=doc_id,
                user_id=self._user_id,
                content=content,
                embedding=embedding,
                metadata_json=json.dumps(metadata),
            )
            session.add(mem)
            await session.commit()
        return doc_id

    async def _retrieve_async(self, embedding: List[float], top_k: int) -> List[RetrievalResult]:
        from sqlalchemy import select, text
        from OpenDEMON.database.engine import AsyncSessionLocal
        from OpenDEMON.database.models.memory import Memory

        async with AsyncSessionLocal() as session:
            # Use pgvector cosine distance operator (<=>)
            stmt = (
                select(Memory, Memory.embedding.cosine_distance(embedding).label("dist"))
                .where(Memory.user_id == self._user_id)
                .order_by(text("dist"))
                .limit(top_k)
            )
            result = await session.execute(stmt)
            rows = result.all()
            return [
                RetrievalResult(
                    doc_id=row.Memory.id,
                    content=row.Memory.content,
                    score=float(1.0 - row.dist),
                    metadata=json.loads(row.Memory.metadata_json or "{}"),
                )
                for row in rows
            ]

    async def _delete_async(self, doc_id: str) -> bool:
        from sqlalchemy import delete
        from OpenDEMON.database.engine import AsyncSessionLocal
        from OpenDEMON.database.models.memory import Memory

        async with AsyncSessionLocal() as session:
            stmt = delete(Memory).where(Memory.id == doc_id, Memory.user_id == self._user_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def _clear_async(self) -> None:
        from sqlalchemy import delete
        from OpenDEMON.database.engine import AsyncSessionLocal
        from OpenDEMON.database.models.memory import Memory

        async with AsyncSessionLocal() as session:
            await session.execute(delete(Memory).where(Memory.user_id == self._user_id))
            await session.commit()

    async def _count_async(self) -> int:
        from sqlalchemy import select, func
        from OpenDEMON.database.engine import AsyncSessionLocal
        from OpenDEMON.database.models.memory import Memory

        async with AsyncSessionLocal() as session:
            stmt = select(func.count()).select_from(Memory).where(Memory.user_id == self._user_id)
            result = await session.execute(stmt)
            return result.scalar_one()

    # ------------------------------------------------------------------
    # Embedding helper
    # ------------------------------------------------------------------

    def _embed(self, text: str) -> List[float]:
        """Convert text to a float vector using the configured embedder."""
        if self._embedder is None:
            raise MemoryBackendUnavailable(
                "PGVectorMemory requires an embedder. Pass one at construction."
            )
        import numpy as np
        vec = self._embedder.embed([text])
        if hasattr(vec, "tolist"):
            return vec[0].tolist()
        return list(vec[0])


__all__ = ["PGVectorMemory"]
