import os
import secrets
import asyncio
from string import ascii_letters, punctuation, digits
from dotenv import load_dotenv

from discord import Forbidden, Client
from better_proxy import Proxy
from aiohttp_proxy import ProxyConnector

from web3db.core import DBHelper
from web3db.models import Profile

from extra.logger import logger
from extra.capmonster import solve_captcha

load_dotenv()

discord_social_tasks_buttons = {
    'join guild': 'Введите ссылки или коды приглашений'
}


def generate_random_password(n):
    all_characters = ascii_letters + punctuation + digits
    password = ''.join(secrets.choice(all_characters) for _ in range(n))
    return password


class DiscordClient(Client):
    def __init__(self, profile: Profile):
        super().__init__(captcha_handler=solve_captcha)
        self.http.connector = ProxyConnector.from_url(
            url=Proxy.from_str(proxy=profile.proxy.proxy_string).as_url, verify_ssl=False
        )
        self.profile = profile
        self.db = DBHelper(url=os.getenv('CONNECTION_STRING'))

    async def __aenter__(self):
        await super().__aenter__()
        await self.login(self.profile.discord.auth_token)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)
        logger.info(f'{self.profile.id} | {self.user.email}:{self.http.token}')

    async def invite(self, invite_url: str):
        try:
            invite_res = await self.accept_invite(invite_url)
            return invite_res
        except Forbidden as e:
            logger.error(f"{self.profile.id} | Can't join guild {invite_url} - {e.status} {e.text}")

    async def change_password(self) -> tuple[str, str]:
        logger.info(f'{self.profile.id} | Current password - {self.profile.discord.password}')
        new_password = generate_random_password(50)
        await self.user.edit(
            password=self.profile.discord.password,
            new_password=new_password
        )
        logger.success(f"{self.profile.id} | Changed password to {new_password}")
        logger.success(f"{self.profile.id} | New token - {self.http.token}")
        self.profile.discord.password = new_password
        self.profile.discord.auth_token = self.http.token
        await self.db.edit(self.profile)
        return new_password, self.http.token

    async def join_pandez(self):
        logger.info(f'{self.profile.id} | ')


async def start():
    db = DBHelper(url=os.getenv('CONNECTION_STRING'))
    profiles = await db.get_all_from_table(Profile)
    for profile in profiles:
        async with DiscordClient(profile) as client:
            await client.invite('https://discord.gg/whalesmarket')


if __name__ == '__main__':
    asyncio.run(start())
