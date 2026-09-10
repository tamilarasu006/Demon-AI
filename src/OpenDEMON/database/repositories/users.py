from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from OpenDEMON.database.models import User, UserProfile

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, email: str, name: str, picture: Optional[str] = None) -> User:
        user = User(email=email, name=name, picture=picture)
        self.session.add(user)
        await self.session.flush()
        profile = UserProfile(user_id=user.id)
        self.session.add(profile)
        await self.session.commit()
        return user

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
