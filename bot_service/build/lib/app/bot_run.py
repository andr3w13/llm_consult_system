"""
Отдельный entrypoint для aiogram polling.

Запускается как отдельный процесс:
    python -m app.run_bot
"""

import asyncio
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.dispatcher import setup_dispatcher
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info(
        "Starting Telegram bot [env=%s]",
        settings.ENV,
    )

    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )

    dp = setup_dispatcher()

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        logger.info("Closing bot session")
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())