import asyncio
import os
import secrets
import string
import g4f
from abc import ABC, abstractmethod

from json import JSONDecodeError
from pathlib import Path
from random import uniform

from dotenv import load_dotenv

from twitter import Client, Account
from twitter.errors import HTTPException, Unauthorized
from twitter.models import UserData
from web3db import DBHelper

from web3db.models import Profile

from extra.logger import logger
from extra.windows import set_windows_event_loop_policy
from extra.web3 import get_evm_address, get_aptos_address, get_solana_address

load_dotenv()
set_windows_event_loop_policy()

dir_path = Path(__file__).resolve().parent
db = DBHelper(os.getenv('CONNECTION_STRING'))
capsolver_api_key = os.getenv('CAPSOLVER_API_KEY')


class TwitterTaskManager:

    def __init__(self, profile: Profile):
        self.client = Client(
            account=Account(
                auth_token=profile.twitter.auth_token,
                ct0=None,
                id=None,
                name=None,
                username=None,
                password=profile.twitter.password,
                email=None,
                totp_secret=None,
                backup_code=None
            ),
            capsolver_api_key=capsolver_api_key,
            proxy=profile.proxy.proxy_string,
            verify=False,
        )
        self.profile = profile

    async def tweet(self, text: str, image: bytes = None) -> str:
        # TODO: обработку картинок
        try:
            tweet_id = await self.client.tweet(text)
            log = f'{self.profile.id} | {Tweet.success.format(username=self.profile.twitter.login, tweet_id=tweet_id)}'
            logger.success(log)
        except (HTTPException, Unauthorized) as e:
            log = f'{self.profile.id} | {Tweet.error.format(username=self.profile.twitter.login, e=e)}'
            logger.error(log)
        return log

    async def reply(self, tweet_id: int, text: str, image: bytes = None) -> str:
        try:
            new_tweet_id = await self.client.reply(tweet_id, text)
            log = (
                f"{self.profile.id} | "
                f"{Reply.success.format(username=self.profile.twitter.login, tweet_id=tweet_id, new_tweet_id=new_tweet_id)}"
            )
            logger.success(log)
        except (HTTPException, Unauthorized) as e:
            log = (
                f"{self.profile.id} | "
                f"{Reply.error.format(username=self.profile.twitter.login, source=tweet_id, e=e)}"
            )
            logger.error(log)
        return log

    async def get_user_data(self, username: str = None) -> UserData | str:
        username = self.profile.twitter.login if not username else username
        username = username.split('/')[-1]
        try:
            user_data = await self.client.request_user_data(username)
            if user_data:
                log = (
                    f"{self.profile.id} | {TwitterInteraction.success.format(username=self.profile.twitter.login)}"
                    f"Got user data from {username} with {user_data.followers_count} followers"
                )
                logger.success(log)
                return user_data
            else:
                error_message = 'User {username} is suspended or doesn\'t exist'
                log = (
                    f"{self.profile.id} | "
                    f"{TwitterInteraction.error.format(username=self.profile.twitter.login, action='get user data from', source=username, e=error_message)}"
                )
                logger.error(log)
        except (HTTPException, Unauthorized) as e:
            log = (
                f"{self.profile.id} | "
                f"{TwitterInteraction.error.format(username=self.profile.twitter.login, action='get user data from', source=username, e=e)}"
            )
            logger.error(log)
        except JSONDecodeError:
            delay = 60 * 10
            log = (
                f'{self.profile.id} | '
                f"{TwitterInteraction.error.format(username=self.profile.twitter.login, action='get user data from', source=username, e=f'Got rate limit. Sleeping for {delay} seconds...')}"
            )
            logger.error(log)
            await asyncio.sleep(60 * 10)
        return log

    async def follow_by_username(self, username: str = None) -> str:
        username = self.profile.twitter.login if not username else username
        username = username.split('/')[-1]
        user_data = await self.get_user_data(username)
        if isinstance(user_data, str):
            return user_data
        await asyncio.sleep(uniform(3, 5))
        try:
            result = await self.client.follow(user_data.id)
            if result:
                log = (
                    f"{self.profile.id} | "
                    f"{Follow.success.format(username=self.profile.twitter.login, following_username=username)}"
                )
                logger.success(log)
            else:
                log = (
                    f"{self.profile.id} | "
                    f"{Follow.error.format(username=self.profile.twitter.login, source=username, e=f'Something wrong happened with following {username} - {result}')}"
                )
                logger.error(log)
        except (HTTPException, Unauthorized) as e:
            log = (
                f"{self.profile.id} | "
                f"{Follow.error.format(username=self.profile.twitter.login, source=username, e=e)}"
            )
            logger.error(log)
        return log

    async def like(self, tweet_id: int) -> str:
        try:
            result = await self.client.like(tweet_id)
            if result:
                log = (
                    f'{self.profile.id} | '
                    f'{Like.success.format(username=self.profile.twitter.login, tweet_id=tweet_id)}'
                )
                logger.success(log)
            else:
                log = (
                    f"{self.profile.id} | "
                    f"{Like.error.format(username=self.profile.twitter.login, source=tweet_id, e=f'Something wrong happened with {tweet_id} - {result}')}"
                )
                logger.error(log)
        except (HTTPException, Unauthorized) as e:
            log = (
                f"{self.profile.id} | "
                f"{Like.error.format(username=self.profile.twitter.login, source=tweet_id, e=e)}"
            )
            logger.error(log)
        return log

    async def repost(self, tweet_id: int) -> str:
        try:
            result = await self.client.repost(tweet_id)
            log = (
                f'{self.profile.id} | '
                f'{Repost.success.format(username=self.profile.twitter.login, tweet_id=tweet_id)}'
            )
            logger.success(log)
        except (HTTPException, Unauthorized) as e:
            log = (
                f"{self.profile.id} | "
                f"{Repost.error.format(username=self.profile.twitter.login, source=tweet_id, e=e)}"
            )
            logger.error(log)
        return log

    async def quote(self, tweet_url: str, text: str, image: bytes = None) -> str:
        try:
            result = await self.client.quote(tweet_url, text)
            log = (
                f'{self.profile.id} | '
                f'{Quote.success.format(username=self.profile.twitter.login, tweet_url=tweet_url, result=result)}'
            )
            logger.success(log)
        except (HTTPException, Unauthorized) as e:
            log = (
                f"{self.profile.id} | "
                f"{Quote.error.format(username=self.profile.twitter.login, source=tweet_url, e=e)}"
            )
            logger.error(log)
        return log

    async def change_password(self) -> str:
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(characters) for _ in range(50))
        try:
            result = await self.client.change_password(password)
        except (HTTPException, Unauthorized) as e:
            log = (
                f"{self.profile.id} | "
                f"{ChangePassword.error.format(username=self.profile.twitter.login, e=e)}"
            )
            logger.error(log)
        else:
            if result:
                new_password = self.client.account.password
                log = (
                    f'{self.profile.id} | '
                    f'{ChangePassword.success.format(username=self.profile.twitter.login, password=self.profile.twitter.password, new_password=new_password, auth_token=self.client.account.auth_token)}'
                )
                logger.success(log)
                self.profile.twitter.auth_token = self.client.account.auth_token
                self.profile.twitter.password = new_password
                await db.edit(self.profile)
            else:
                log = (
                    f"{self.profile.id} | "
                    f"{ChangePassword.error.format(username=self.profile.twitter.login, e='')}"
                )
                logger.error(log)
        return log

    async def add_2fa(self) -> str:
        try:
            if await self.client.totp_is_enabled():
                log = (
                    f"{self.profile.id} | "
                    f"{TwoFactor.already_added.format(username=self.profile.twitter.login)}"
                )
                logger.debug(log)
            else:
                await self.client.enable_totp()
                totp_secret = self.client.account.totp_secret
                backup_code = self.client.account.backup_code
                self.profile.twitter.totp_secret = totp_secret
                self.profile.twitter.backup_code = backup_code
                await db.edit(self.profile.twitter)
                log = (
                    f"{self.profile.id} | "
                    f"{TwoFactor.success.format(username=self.profile.twitter.login, totp_secret=totp_secret, backup_code=backup_code)}"
                )
                logger.success(log)
        except (HTTPException, Unauthorized) as e:
            print(e.api_codes)
            if 366 in e.api_codes:
                e = 'Need to verify email'
            log = (
                f"{self.profile.id} | "
                f"{TwoFactor.error.format(username=self.profile.twitter.login, e=e)}"
            )
            logger.error(log)
        return log


class TwitterInteraction(ABC):
    description: str
    success: str = '{username} | '
    error: str = '{username} | Failed to {action} {source}. {e}'

    def __init__(self, *args, **kwargs):
        # self.username = kwargs.get('username')
        # self.tweet_id = kwargs.get('tweet_id')
        # self.tweet_url = kwargs.get('tweet_url')
        self.source: int | str = kwargs.get('source')
        self.text_or_prompt: str | None = kwargs.get('text_or_prompt')
        self.generate: bool | None = kwargs.get('generate')
        self.image: bytes | None = kwargs.get('image')
        self.evm: bool | None = kwargs.get('evm_wallet')
        self.aptos: bool | None = kwargs.get('aptos_wallet')
        self.solana: bool | None = kwargs.get('solana_wallet')

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

    @abstractmethod
    async def start(self, ttm: TwitterTaskManager):
        pass

    @staticmethod
    async def generate_crypto_text(user_prompt: str, proxy: str) -> str:
        try:
            response = await g4f.ChatCompletion.create_async(
                model=g4f.models.default,
                messages=[{
                    "role": "user",
                    "content": user_prompt
                }],
                provider=g4f.Provider.GeminiProChat,
                proxy=proxy,
                verify=False
            )
            return response
        except Exception as e:
            logger.error(e)


class Tweet(TwitterInteraction, ABC):
    description: str = 'Введите текст (+картинку beta)'
    success: str = TwitterInteraction.success + 'Tweeted {tweet_id}'
    error: str = TwitterInteraction.error.replace('{action}', 'tweet')

    async def start(self, ttm: TwitterTaskManager) -> str:
        if self.generate:
            text = self.generate_crypto_text(self.text_or_prompt, ttm.profile.proxy.proxy_string)
        elif self.evm:
            text = get_evm_address(ttm.profile)
        elif self.aptos:
            text = get_aptos_address(ttm.profile)
        elif self.solana:
            text = get_solana_address(ttm.profile)
        else:
            text = self.text_or_prompt
        return await ttm.tweet(text)

    def __str__(self):
        return (
                super().__str__() +
                f'({self.text_or_prompt[:6]}, '
                f'{f"generate=True, " if self.generate else ""}'
                f'{f"evm=True, " if self.evm else ""}'
                f'{f"aptos=True, " if self.aptos else ""}'
                f'{f"solana=True, " if self.solana else ""}'
                f'with_image={self.image == True})'
        )


class Follow(TwitterInteraction, ABC):
    description: str = 'Введите логины'
    success: str = TwitterInteraction.success + 'Followed {following_username}'
    error: str = TwitterInteraction.error.replace('{action}', 'follow')

    async def start(self, ttm: TwitterTaskManager) -> str:
        return await ttm.follow_by_username(self.source)


class Like(TwitterInteraction, ABC):
    description: str = 'Введите id постов'
    success: str = TwitterInteraction.success + 'Liked {tweet_id}'
    error: str = TwitterInteraction.error.replace('{action}', 'like')

    async def start(self, ttm: TwitterTaskManager) -> str:
        return await ttm.like(self.source)


class Repost(TwitterInteraction, ABC):
    description: str = 'Введите id постов'
    success: str = TwitterInteraction.success + 'Reposted {tweet_id}'
    error: str = TwitterInteraction.error.replace('{action}', 'repost')

    async def start(self, ttm: TwitterTaskManager) -> str:
        return await ttm.repost(self.source)


class Quote(TwitterInteraction, ABC):
    description: list[str] = ['Введите ссылки на посты', 'Введите текст (+картинку beta)']
    success: str = TwitterInteraction.success + 'Quoted {tweet_url}, tweet ID: {result}'
    error: str = TwitterInteraction.error.replace('{action}', 'quote')

    async def start(self, ttm: TwitterTaskManager) -> str:
        if self.generate:
            text = self.generate_crypto_text(self.text_or_prompt, ttm.profile.proxy.proxy_string)
        elif self.evm:
            text = get_evm_address(ttm.profile)
        elif self.aptos:
            text = get_aptos_address(ttm.profile)
        elif self.solana:
            text = get_solana_address(ttm.profile)
        else:
            text = self.text_or_prompt
        return await ttm.quote(self.source, text, self.image)

    def __str__(self):
        return (
                super().__str__() +
                f'({self.text_or_prompt[:6]}, '
                f'{f"generate=True, " if self.generate else ""}'
                f'{f"evm=True, " if self.evm else ""}'
                f'{f"aptos=True, " if self.aptos else ""}'
                f'{f"solana=True, " if self.solana else ""}'
                f'with_image={self.image == True})'
        )


class Reply(TwitterInteraction, ABC):
    description: list[str] = ['Вставьте id постов', 'Введите текст (+картинку beta)']
    success: str = TwitterInteraction.success + 'Replied {tweet_id}, reply id: {new_tweet_id}'
    error: str = TwitterInteraction.error.replace('{action}', 'reply')

    async def start(self, ttm: TwitterTaskManager) -> str:
        if self.generate:
            text = self.generate_crypto_text(self.text_or_prompt, ttm.profile.proxy.proxy_string)
        elif self.evm:
            text = get_evm_address(ttm.profile)
        elif self.aptos:
            text = get_aptos_address(ttm.profile)
        elif self.solana:
            text = get_solana_address(ttm.profile)
        else:
            text = self.text_or_prompt
        return await ttm.reply(
            self.source.split('/')[-1] if self.source.startswith('http') else self.source,
            text,
            self.image
        )

    def __str__(self):
        return (
                super().__str__() +
                f'({self.text_or_prompt[:6]}, '
                f'{f"generate=True, " if self.generate else ""}'
                f'{f"evm=True, " if self.evm else ""}'
                f'{f"aptos=True, " if self.aptos else ""}'
                f'{f"solana=True, " if self.solana else ""}'
                f'with_image={self.image == True})'
        )


class ChangePassword:
    label: str = 'Change password'
    success: str = TwitterInteraction.success + 'Changed password {password} to {new_password}. New auth token - {auth_token}'
    error: str = '{username} | Failed to change password. {e} '

    def __new__(cls):
        raise NotImplementedError("Экземпляры класса ChangePassword не могут быть созданы")

    @staticmethod
    async def start(ttm: TwitterTaskManager) -> str:
        return await ttm.change_password()


class TwoFactor:
    label: str = 'Add 2FA'
    success: str = TwitterInteraction.success + 'Added 2FA. 2FA key - {totp_secret}, backup code - {backup_code}'
    error: str = '{username} | Failed to add 2FA. {e}'
    already_added: str = '{username} | 2FA already added'

    def __new__(cls):
        raise NotImplementedError("Экземпляры класса TwoFactor не могут быть созданы")

    @staticmethod
    async def start(ttm: TwitterTaskManager):
        return await ttm.add_2fa()


twitter_account_settings = {
    'Change password': ChangePassword,
    'Add 2FA': TwoFactor
}
twitter_actions = {
    'Tweet': Tweet,
    'Like': Like,
    'Follow': Follow,
    'Repost': Repost,
    'Quote': Quote,
    'Reply': Reply,
    'Settings': twitter_account_settings
}
