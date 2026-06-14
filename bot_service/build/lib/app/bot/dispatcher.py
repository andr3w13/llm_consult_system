from aiogram import Dispatcher

from app.bot.handlers import router


def setup_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    dp.include_router(router)

    return dp