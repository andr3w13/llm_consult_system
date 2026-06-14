from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.infra.redis import get_redis
from app.core.jwt import validate_token
from app.services.token_storage import RedisTokenStorage
from app.tasks.llm_tasks import llm_request

router = Router()

redis_client = get_redis()
token_storage = RedisTokenStorage(redis_client)


@router.message(Command("token"))
async def token_handler(message: Message):
    parts = message.text.split(maxsplit=1)

    if len(parts) != 2:
        await message.answer("Использование: /token &lt;JWT&gt;")
        return

    token = parts[1]

    try:
        validate_token(token)

        await token_storage.set_token(
            message.from_user.id,
            token,
        )

        await message.answer(
            "Authorization successful."
        )

    except Exception:
        await message.answer(
            "Invalid token."
        )


@router.message()
async def llm_handler(message: Message):
    token = await token_storage.get_token(
        message.from_user.id
    )

    if not token:
        await message.answer(
            "Authorize first via /token"
        )
        return

    try:
        validate_token(token)

    except Exception:
        await message.answer(
            "Token invalid or expired."
        )
        return

    llm_request.delay(
        tg_chat_id=message.chat.id,
        prompt=message.text,
    )

    await message.answer(
        "Request accepted."
    )