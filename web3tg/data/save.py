from web3tg.utils import db


async def add_social_to_db(social_name: str, data: dict):
    d = {
        'twitter': db.add_twitter,
        'discord': db.add_discord,
        'mail': db.add_email
    }
    await d[social_name](**data)
