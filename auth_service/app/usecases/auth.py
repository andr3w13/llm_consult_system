import logging

from app.core.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.users import UsersRepository
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserPublic

logger = logging.getLogger(__name__)


class AuthUseCase:
    def __init__(self, users_repo: UsersRepository) -> None:
        self._repo = users_repo

    async def register(self, data: RegisterRequest) -> UserPublic:
        existing = await self._repo.get_by_email(data.email)
        if existing:
            raise UserAlreadyExistsError()

        hashed = hash_password(data.password)
        user = await self._repo.create(
            username=data.username,
            email=data.email,
            password_hash=hashed,
        )
        logger.info("Registered user id=%d email=%r", user.id, user.email)
        return UserPublic.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self._repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        token = create_access_token(subject=user.id, role=user.role)
        logger.info("User id=%d logged in", user.id)
        return TokenResponse(access_token=token)

    async def get_me(self, user_id: int) -> UserPublic:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        return UserPublic.model_validate(user)