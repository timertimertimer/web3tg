import os

from web3db.core import DBHelper

from utils import models


async def get_all_accounts_by_social(social: str, ids: list = None) -> list[tuple[int, str, bool]]:
    db = DBHelper(url=os.getenv('CONNECTION_STRING'))
    return await db.get_profiles_light_by_model(models[social], ids)


async def get_random_accounts_by_proxy(social: str) -> list[int]:
    db = DBHelper(url=os.getenv('CONNECTION_STRING'))
    return await db.get_random_profiles_ids_by_proxy(models[social])
