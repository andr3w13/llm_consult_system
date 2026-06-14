from redis.asyncio import Redis


class RedisTokenStorage:
    def __init__(self, redis: Redis):
        self._redis = redis

    def _key(self, tg_user_id: int) -> str:
        return f"tg_token:{tg_user_id}"

    async def set_token(
        self,
        tg_user_id: int,
        token: str,
    ) -> None:
        await self._redis.set(
            self._key(tg_user_id),
            token,
        )

    async def get_token(
        self,
        tg_user_id: int,
    ) -> str | None:
        return await self._redis.get(
            self._key(tg_user_id)
        )