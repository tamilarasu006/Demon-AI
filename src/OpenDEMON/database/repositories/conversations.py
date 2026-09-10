from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from OpenDEMON.database.models import Conversation, Message

class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_conversation(self, user_id: str, title: Optional[str] = None) -> Conversation:
        conv = Conversation(user_id=user_id, title=title)
        self.session.add(conv)
        await self.session.commit()
        return conv

    async def get_conversation(self, user_id: str, conversation_id: str) -> Optional[Conversation]:
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_conversations(self, user_id: str, limit: int = 100) -> List[Conversation]:
        stmt = select(Conversation).where(Conversation.user_id == user_id).order_by(desc(Conversation.updated_at)).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_message(self, user_id: str, conversation_id: str, role: str, content: str) -> Message:
        msg = Message(user_id=user_id, conversation_id=conversation_id, role=role, content=content)
        self.session.add(msg)
        await self.session.commit()
        return msg

    async def get_messages(self, user_id: str, conversation_id: str) -> List[Message]:
        stmt = select(Message).where(
            Message.conversation_id == conversation_id,
            Message.user_id == user_id
        ).order_by(Message.created_at)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
