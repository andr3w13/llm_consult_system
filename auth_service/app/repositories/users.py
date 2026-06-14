import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User

logger = logging.getLogger(__name__)


class UsersRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        username: str,
        email: str,
        password_hash: str,
        role: str = "user",
    ) -> User:
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        logger.info("Created user id=%d email=%r", user.id, user.email)
        return user
