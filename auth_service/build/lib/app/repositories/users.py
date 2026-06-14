"""
auth_service/app/repositories/users.py

Репозиторий доступа к пользователям в БД.

Принципы Repository Pattern:
  1. Только операции с БД — никакой бизнес-логики.
  2. Не выбрасывает HTTPException — только возвращает None или кидает
     низкоуровневые исключения БД (IntegrityError и т.д.).
  3. Принимает AsyncSession через __init__ — зависимость инжектируется снаружи,
     это упрощает тестирование (можно подставить мок-сессию).

Usecase-слой (usecases/auth.py) вызывает репозиторий и интерпретирует
результат в бизнес-логику.
"""
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
        await self._session.refresh(user)  # обновить id и server_default-поля
        logger.info("Created user id=%d email=%r", user.id, user.email)
        return user
