
import pytestimport fakeredis.aioredis
from datetime import datetime, timedelta, timezone

from jose import jwt as jose_jwt

from app.core.config import settings
from app.bot.handlers import router as main_router
from app.services.token_storage import RedisTokenStorage


@pytest.fixture
async def fake_redis():
    """Создаёт изолированный fakeredis для одного теста."""
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.flushall()
    await r.aclose()


@pytest.fixture
def token_storage(fake_redis):
    return RedisTokenStorage(fake_redis)


@pytest.fixture
def router(token_storage):
    """Использует реальный роутер, подменяя хранилище токенов на тестовое."""
    import app.bot.handlers as handlers
    # Подменяем глобальный token_storage внутри модуля handlers на наш фейковый
    handlers.token_storage = token_storage
    return main_router


def make_valid_token(sub: str = "42", role: str = "user") -> str:
    """Создаёт валидный JWT для тестов."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=1),
    }
    return jose_jwt.encode(
        payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG
    )


def make_expired_token() -> str:
    """Создаёт просроченный JWT для негативных тестов."""
    payload = {
        "sub": "1",
        "role": "user",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    return jose_jwt.encode(
        payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG
    )