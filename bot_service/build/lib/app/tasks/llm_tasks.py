import asyncio

from aiogram import Bot

from app.core.config import settings
from app.infra.celery_app import celery_app
from app.services.openrouter_client import OpenRouterClient


@celery_app.task(name="llm_request")
def llm_request(
    tg_chat_id: int,
    prompt: str,
) -> None:
    asyncio.run(
        _process_request(
            tg_chat_id,
            prompt,
        )
    )


async def _process_request(
    tg_chat_id: int,
    prompt: str,
) -> None:
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    try:
        client = OpenRouterClient()

        response = await client.chat(prompt)

        await bot.send_message(
            tg_chat_id,
            response.content,
        )

    except Exception as exc:
        await bot.send_message(
            tg_chat_id,
            f"LLM error: {exc}",
        )

    finally:
        await bot.session.close()