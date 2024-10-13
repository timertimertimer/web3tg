import asyncio
import random
import pyotp
from aiogram import Bot
from web3db.models import RemoteProfile as Profile
from web3db.core import ModelType
from web3tg.utils.tw import *
from web3tg.utils.db import db
from web3tg.utils.logger import my_logger
from web3tg.utils.models import models


class ProfilesInteraction:

    @staticmethod
    async def change_profile_model(
            social: str,
            profiles_ids: set[int],
            delete_model: bool = False,
            delete_models_email: bool = False
    ) -> ModelType | None:
        return await db.change_profile_model(list(profiles_ids), models[social], delete_model, delete_models_email)

    @staticmethod
    async def get_profiles_models_with_2fa(social: str) -> list[ModelType]:
        return await db.get_profiles_with_totp_by_model(models[social])

    @staticmethod
    async def get_2fa_code(social: str, profile: Profile) -> str:
        return pyotp.TOTP(getattr(profile, models[social].__name__.lower()).totp_secret).now()


async def process_social_tasks(
        social: str,
        social_tasks: dict[TweetInteraction, set],
        profiles_id: set,
        bot: Bot = None,
        chat_id: int = None
) -> None:
    async def process_profile(current_profile: Profile):
        match social:
            case 'Twitter':
                task_manager = TwitterTaskManager(current_profile)
            case _:  # TODO
                return
        for task in random.sample(list(social_tasks), len(social_tasks)):
            if not social_tasks[task]:  # Without sources
                result = await task.start(task_manager)
                if bot:
                    await bot.send_message(chat_id, result)
                delay = random.uniform(10, 15)
                my_logger.info(f'{current_profile.id} | Sleeping for {delay} seconds')
                await asyncio.sleep(delay)
            else:  # With sources
                for source in random.sample(list(social_tasks[task]), len(social_tasks[task])):
                    task.source = source
                    result = await task.start(task_manager)
                    if bot:
                        await bot.send_message(chat_id, result)
                    delay = random.uniform(10, 15)
                    my_logger.info(f'{current_profile.id} | Sleeping for {delay} seconds')
                    await asyncio.sleep(delay)

        info_message = f'{current_profile.id} | {social} tasks completed'
        my_logger.success(info_message)
        if bot:
            await bot.send_message(chat_id, info_message)

    tasks = []
    profiles = await db.get_rows_by_id(profiles_id, Profile)
    for profile in profiles:
        tasks.append(asyncio.create_task(process_profile(profile)))
    await asyncio.gather(*tasks)
    info_message = f'All {social} tasks completed'
    my_logger.success(info_message)
    if bot:
        await bot.send_message(chat_id, info_message)


__all__ = [
    'process_social_tasks',
    'ProfilesInteraction'
]

if __name__ == '__main__':
    asyncio.run(process_social_tasks(
        social='Twitter',
        social_tasks={
            LikeAction(): set([1842235137112576305]),
            RepostAction(): set([1842235137112576305]),
            ReplyAction(bitcoin_taproot=True): set([1842235137112576305]),
        },
        profiles_id={
            100, 101, 102, 103, 104, 105, 106, 107,
            108, 110, 111, 112, 113, 114, 115, 116, 118, 119, 120,
            121, 122, 123, 124, 125
        }
    ))
