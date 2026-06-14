import pytest
import fakeredis.aioredis

from app.bot import handlers


@pytest.fixture
async def fake_redis():
    redis = fakeredis.aioredis.FakeRedis(
        decode_responses=True
    )

    handlers.get_redis = lambda: redis

    yield redis

    await redis.flushall()