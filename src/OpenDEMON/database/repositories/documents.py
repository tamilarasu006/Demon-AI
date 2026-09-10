from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from OpenDEMON.database.models import Document, DocumentChunk

class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_document(self, user_id: str, title: str, content: str) -> Document:
        doc = Document(user_id=user_id, title=title, content=content)
        self.session.add(doc)
        await self.session.commit()
        return doc

    async def add_chunk(self, document_id: str, user_id: str, content: str, embedding: list[float], chunk_index: int) -> DocumentChunk:
        chunk = DocumentChunk(
            document_id=document_id,
            user_id=user_id,
            content=content,
            embedding=embedding,
            chunk_index=chunk_index
        )
        self.session.add(chunk)
        await self.session.commit()
        return chunk
