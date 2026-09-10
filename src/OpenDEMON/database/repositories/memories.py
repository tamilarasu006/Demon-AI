from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from OpenDEMON.database.models import Memory
import json

class MemoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_memory(self, user_id: str, content: str, embedding: list[float], metadata: dict) -> Memory:
        mem = Memory(
            user_id=user_id,
            content=content,
            embedding=embedding,
            metadata_json=json.dumps(metadata)
        )
        self.session.add(mem)
        await self.session.commit()
        return mem

    async def search_memories(self, user_id: str, query_embedding: list[float], limit: int = 5) -> List[Memory]:
        stmt = select(Memory).where(Memory.user_id == user_id).order_by(
            Memory.embedding.cosine_distance(query_embedding)
        ).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
