import asyncio
import logging

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.callback_answer import CallbackAnswerMiddleware

from web3tg.callbacks import *
from web3tg.middlewares import CheckAdminMiddleware
from web3tg.handlers import (
    onchain_tasks_commands, social_tasks_commands, profiles_tasks_commands, basic_commands, user_commands
)
from web3tg.utils.env import Web3tgENV
from web3tg.utils.logger import InterceptHandler

bot = Bot(Web3tgENV.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


async def main() -> None:
    dp = Dispatcher()

    await bot.delete_webhook(drop_pending_updates=True)

    dp.message.middleware(CheckAdminMiddleware([int(el) for el in Web3tgENV.ADMINS.split(',')]))
    dp.callback_query.middleware(CallbackAnswerMiddleware())

    dp.include_routers(
        basic_commands.router,
        user_commands.router,

        main_callbacks.router,

        social_tasks_callbacks.router,
        social_tasks_commands.router,

        profiles_tasks_callbacks.router,
        profiles_tasks_commands.router,

        onchain_tasks_callbacks.router,
        onchain_tasks_commands.router
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO)
    await dp.start_polling(bot)


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
