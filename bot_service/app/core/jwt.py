import logging

from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings

logger = logging.getLogger(__name__)


class TokenValidationError(Exception):
    """Базовое исключение валидации JWT в Bot Service."""


class TokenExpiredError(TokenValidationError):
    """JWT существует и имеет корректную подпись, но срок истёк."""


class InvalidTokenError(TokenValidationError):
    """JWT отсутствует, повреждён или имеет неверную подпись."""


def validate_token(token: str) -> dict:
    """
    Валидирует JWT и возвращает payload.

    Проверяет:
      - Подпись: HMAC-SHA256 с JWT_SECRET
      - Срок действия: exp-claim

    Возвращает dict с полями:
      sub  — str(user_id) из Auth Service
      role — роль пользователя
      iat  — время выдачи
      exp  — время истечения

    Raises:
      TokenExpiredError  — срок действия истёк
      InvalidTokenError  — любая другая ошибка
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALG],
        )
        logger.debug("Token validated, sub=%s role=%s", payload.get("sub"), payload.get("role"))
        return payload
    except ExpiredSignatureError as exc:
        raise TokenExpiredError("JWT has expired") from exc
    except JWTError as exc:
        raise InvalidTokenError(f"JWT validation failed: {exc}") from exc