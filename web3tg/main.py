import asyncio
import logging
import os

from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode
from aiogram.utils.callback_answer import CallbackAnswerMiddleware

from callbacks import social_tasks_callbacks, profiles_tasks_callbacks
from extra.logger import InterceptHandler
from handlers import basic_commands, user_commands
from middlewares import CheckAdminMiddleware

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)


async def start_bot() -> None:
    dp = Dispatcher()

    await bot.delete_webhook(drop_pending_updates=True)

    dp.message.middleware(CheckAdminMiddleware([int(el) for el in os.getenv('ADMINS').split(',')]))
    dp.callback_query.middleware(CallbackAnswerMiddleware())

    dp.include_routers(
        basic_commands.router,
        user_commands.router,

        social_tasks_callbacks.router,
        profiles_tasks_callbacks.router
    )
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_bot())
