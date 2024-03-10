import os

from web3db import DBHelper


async def add_social_to_db(social_name: str, data: dict):
    db = DBHelper(os.getenv('CONNECTION_STRING'))
    d = {
        'twitter': db.add_twitter,
        'discord': db.add_discord,
        'mail': db.add_email
    }
    await d[social_name](**data)
