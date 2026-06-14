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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
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
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
        return user_id
    except ExpiredSignatureError:
        raise TokenExpiredError()
    except (JWTError, KeyError, ValueError) as exc:
        logger.warning("Token validation failed: %s", exc)
        raise InvalidTokenError()
