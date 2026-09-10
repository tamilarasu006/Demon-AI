from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from OpenDEMON.database.models import Trace, TraceStep
import json

class TraceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_trace(self, user_id: str, trace_id: str, query: str, agent: str, result: str, metadata: dict) -> Trace:
        trace = Trace(
            user_id=user_id,
            trace_id=trace_id,
            query=query,
            agent=agent,
            result=result,
            metadata_json=json.dumps(metadata)
        )
        self.session.add(trace)
        await self.session.commit()
        return trace

    async def get_traces(self, user_id: str, limit: int = 100) -> List[Trace]:
        stmt = select(Trace).where(Trace.user_id == user_id).order_by(desc(Trace.started_at)).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
