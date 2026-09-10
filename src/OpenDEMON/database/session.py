from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from OpenDEMON.database.engine import AsyncSessionLocal

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get a database session."""
    async with AsyncSessionLocal() as session:
        yield session
