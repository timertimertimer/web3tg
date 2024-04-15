import asyncio
import os
import random
from dotenv import load_dotenv

from aiogram import Bot
from web3db import DBHelper

from extra.tw import TwitterTaskManager, TwitterInteraction, TwoFactor
from extra.logger import logger

from web3db.models import Profile

load_dotenv()

db = DBHelper(os.getenv('CONNECTION_STRING'))


async def process_tasks(
        social: str,
        social_tasks: dict[TwitterInteraction, set],
        profiles_id: set,
        bot: Bot = None,
        chat_id: int = None
) -> None:
    async def process_profile(current_profile: Profile):
        match social:
            case 'Twitter':
                task_manager = TwitterTaskManager(current_profile)
            case _:
                return
        for task in random.sample(list(social_tasks), len(social_tasks)):
            if not social_tasks[task]:
                result = await task.start(task_manager)
                if bot:
                    await bot.send_message(chat_id, result)
                delay = random.uniform(10, 15)
                logger.info(f'{current_profile.id} | Sleeping for {delay} seconds')
                await asyncio.sleep(delay)
            else:
                for source in random.sample(list(social_tasks[task]), len(social_tasks[task])):
                    task.source = source
                    result = await task.start(task_manager)
                    if bot:
                        await bot.send_message(chat_id, result)
                    delay = random.uniform(10, 15)
                    logger.info(f'{current_profile.id} | Sleeping for {delay} seconds')
                    await asyncio.sleep(delay)
        if bot:
            await bot.send_message(chat_id, f'{current_profile.id} | {social} tasks completed')

    tasks = []
    profiles = await db.get_rows_by_id(profiles_id, Profile)
    for profile in profiles:
        tasks.append(asyncio.create_task(process_profile(profile)))
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(process_tasks(
        social='Twitter',
        social_tasks={
            TwoFactor(): set(),
        },
        profiles_id={100}
    ))
