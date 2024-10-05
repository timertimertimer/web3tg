from web3tg.utils import db, models


async def get_all_accounts_by_social(social: str, ids: list = None) -> list[tuple[int, str, bool]]:
    return await db.get_profiles_light_by_model(models[social], ids)


async def get_random_accounts_by_proxy(social: str) -> list[int]:
    return await db.get_random_profiles_ids_by_proxy(models[social])
