"""
auth_service/app/core/exceptions.py

Иерархия HTTP-исключений Auth Service.

Зачем собственные исключения вместо raise HTTPException(...)?
  - Единственная точка изменения статус-кодов и сообщений.
  - Usecase-слой бросает исключения, не зная об HTTP — это clean architecture.
  - В deps.py и routes легко перехватывать конкретные типы.
  - Читаемость: UserAlreadyExistsError говорит сама за себя.

Регистрация обработчика в main.py:
    @app.exception_handler(BaseHTTPException)
    async def handler(request, exc): ...
"""
from fastapi import HTTPException, status


class BaseHTTPException(HTTPException):
    """Базовый класс. Подклассы определяют status_code и detail как атрибуты."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            status_code=self.__class__.status_code,
            detail=detail or self.__class__.detail,
        )


# ── 4xx ─────────────────────────────────────────────────────────────────────

class UserAlreadyExistsError(BaseHTTPException):
    """409 — пользователь с таким email уже зарегистрирован."""
    status_code = status.HTTP_409_CONFLICT
    detail = "User with this email already exists"


class InvalidCredentialsError(BaseHTTPException):
    """401 — неверный email или пароль."""
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid email or password"


class InvalidTokenError(BaseHTTPException):
    """401 — токен неверной структуры или с неверной подписью."""
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid or malformed token"


class TokenExpiredError(BaseHTTPException):
    """401 — срок действия токена истёк."""
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Token has expired"


class UserNotFoundError(BaseHTTPException):
    """404 — пользователь не найден."""
    status_code = status.HTTP_404_NOT_FOUND
    detail = "User not found"


class PermissionDeniedError(BaseHTTPException):
    """403 — недостаточно прав."""
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Permission denied"
