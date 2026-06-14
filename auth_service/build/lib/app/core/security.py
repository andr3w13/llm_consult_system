"""
auth_service/app/core/security.py

Все криптографические примитивы сервиса:
  - хэширование паролей через bcrypt (passlib)
  - создание и декодирование JWT (python-jose)

Почему passlib + bcrypt==4.3.0?
  passlib 1.7.4 не поддерживает bcrypt >= 4.4, поэтому в pyproject.toml
  явно прибит bcrypt==4.3.0. Это known issue в passlib, который не
  обновлялся с 2020 года.

Почему decode_token НЕ оборачивает исключения?
  Он пробрасывает jose-исключения наверх, чтобы вызывающий слой
  (api/deps.py) сам решал, в какое HTTP-исключение их конвертировать.
  Это чистое разделение слоёв: security.py не знает об HTTP.
"""
from datetime import datetime, timedelta, timezone

from jose import jwt  # noqa: F401  (F401 — re-export)
from passlib.context import CryptContext

from app.core.config import settings

# ── Пароли ──────────────────────────────────────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Возвращает bcrypt-хэш пароля."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Сравнивает открытый пароль с хэшем (timing-safe)."""
    return _pwd_context.verify(plain_password, hashed_password)


# ── JWT ─────────────────────────────────────────────────────────────────────

def create_access_token(subject: int, role: str) -> str:
    """
    Создаёт подписанный JWT.

    Payload:
        sub  — строковое представление user.id (стандарт RFC 7519)
        role — роль пользователя (передаётся в Bot Service через токен)
        iat  — время выпуска
        exp  — время истечения

    Алгоритм: HS256 (HMAC-SHA256). Секрет хранится только в .env.
    Bot Service использует тот же секрет для локальной валидации без
    обращения к Auth Service.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(subject),   # по стандарту sub — строка
        "role": role,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> dict:
    """
    Декодирует и верифицирует JWT.

    Пробрасывает:
        jose.ExpiredSignatureError — токен истёк
        jose.JWTError              — любая другая ошибка подписи / структуры
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
