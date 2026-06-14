"""
auth_service/app/api/deps.py

Зависимости FastAPI (Dependency Injection).

Принцип: каждая зависимость — единственная точка создания объекта.
  get_db()          → отдаёт AsyncSession на время запроса, закрывает после
  get_users_repo()  → создаёт репозиторий с сессией
  get_auth_uc()     → создаёт usecase с репозиторием
  get_current_user_id() → извлекает и валидирует JWT, возвращает user_id

Почему функции, а не классы?
  FastAPI Depends работает с любыми callable. Функции проще тестировать
  (можно переопределить через app.dependency_overrides в тестах).
"""
import logging
from typing import AsyncGenerator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTokenError, TokenExpiredError
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.repositories.users import UsersRepository
from app.usecases.auth import AuthUseCase

logger = logging.getLogger(__name__)

# tokenUrl совпадает с путём логина — Swagger UI использует это для кнопки Authorize
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Генератор AsyncSession.

    Использует context manager: сессия гарантированно закрывается после
    выхода из зависимости, даже если эндпоинт выбросил исключение.
    """
    async with AsyncSessionLocal() as session:
        yield session


def get_users_repo(db: AsyncSession = Depends(get_db)) -> UsersRepository:
    return UsersRepository(session=db)


def get_auth_uc(
    users_repo: UsersRepository = Depends(get_users_repo),
) -> AuthUseCase:
    return AuthUseCase(users_repo=users_repo)


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
) -> int:
    """
    Извлекает user_id из Bearer-токена.

    Порядок проверки:
      1. Токен должен присутствовать (oauth2_scheme выбросит 401 если нет).
      2. Подпись и срок действия проверяются jose-библиотекой.
      3. Поле sub должно присутствовать и быть конвертируемо в int.

    Конвертация jose-исключений в наши HTTP-исключения происходит здесь,
    а не в security.py — следуем принципу разделения ответственности.
    """
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
        return user_id
    except ExpiredSignatureError:
        raise TokenExpiredError()
    except (JWTError, KeyError, ValueError) as exc:
        logger.warning("Token validation failed: %s", exc)
        raise InvalidTokenError()
