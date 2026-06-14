from datetime import datetime, timedelta, timezone

from jose import jwt 
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


def create_access_token(subject: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(subject), 
        "role": role,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
