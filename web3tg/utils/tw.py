import asyncio
import secrets
import string
from typing import Callable

import g4f
from abc import ABC
from json import JSONDecodeError
from pathlib import Path
from random import uniform
from twitter import Client, Account
from twitter.errors import HTTPException, Unauthorized, AccountSuspended, FailedToFindDuplicatePost
from twitter.models import User, Tweet
from web3db.models import RemoteProfile as Profile
from web3mt.utils import sleep

from .db import db
from .env import Web3tgENV
from .windows import set_windows_event_loop_policy
from .logger import my_logger

set_windows_event_loop_policy()
dir_path = Path(__file__).resolve().parent

__all__ = [
    'TwitterTaskManager',
    'TweetInteraction',
    'UnlockAction', 'ChangePasswordAction', 'TwoFactorAction',
    'TweetAction', 'FollowAction', 'LikeAction', 'RepostAction', 'QuoteAction', 'ReplyAction',
    'twitter_account_settings', 'twitter_actions'
]


class Action(ABC):
    name: str
    description: str
    success: str = '{username} | '
    error: str = '{username} | Failed to {action} {source}'

    def __init__(self, *args, **kwargs):
        self.source: int | str = kwargs.get('source')

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()


class TwitterTaskManager:

    def __init__(self, profile: Profile):
        self.client = Client(
            account=Account(
                auth_token=profile.twitter.auth_token,
                ct0=None,
                id=None,
                name=None,
                username=profile.twitter.login,
                password=profile.twitter.password,
                email=profile.twitter.email.login if profile.twitter.email else None,
                totp_secret=profile.twitter.totp_secret if profile.twitter.totp_secret else None,
                backup_code=profile.twitter.backup_code if profile.twitter.backup_code else None
            ),
            capsolver_api_key=Web3tgENV.CAPSOLVER_API_KEY,
            proxy=profile.proxy.proxy_string,
            verify=False,
            impersonate=False
        )
        self.profile = profile

    def __repr__(self):
        return str(self)

    def __str__(self):
        self.profile.twitter.auth_token = self.client.account.auth_token
        return f'{self.profile.id} | {self.client.account.auth_token}'

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.profile.twitter.auth_token != self.client.account.auth_token:
            self.profile.twitter.auth_token = self.client.account.auth_token
            await db.edit(self.profile)

    async def call_func(self, func: Callable, error_log: str, *args, **kwargs):
        while True:
            try:
                response = await func(*args, **kwargs)
                return response
            except (HTTPException, Unauthorized) as e:
                if not (
                        e.response.status_code == 200
                        and (226 in e.api_codes or 344 in e.api_codes)
                ):
                    if 366 in e.api_codes:
                        e = 'Need to verify email'
                    my_logger.error(f'{error_log}. {e}')
                    return
                await sleep(5, 10)
            except AccountSuspended as e:
                my_logger.error(f'{error_log}. {e}')
                return
            except KeyError as e:
                if e.args != ('result',):  # if false - Authorization: Status is a duplicate. (187)
                    raise

    async def tweet(self, text: str, image: bytes = None) -> str:
        # TODO: обработку картинок
        tweet: Tweet = await self.call_func(
            self.client.tweet,
            f'{self.profile.id} | {TweetAction.error.format(username=self.profile.twitter.login, source=text)}',
            text
        )
        log = f'{self.profile.id} | {TweetAction.success.format(username=self.profile.twitter.login, tweet_id=tweet.id)}'
        my_logger.success(log)
        return log

    async def reply(self, tweet_id: int, text: str, image: bytes = None) -> str | None:
        try:
            tweet: Tweet = await self.call_func(
                self.client.reply,
                f"{self.profile.id} | {ReplyAction.error.format(username=self.profile.twitter.login, source=tweet_id)}",
                tweet_id, text
            )
        except FailedToFindDuplicatePost as e:
            log = (
                f"{self.profile.id} | "
                f"{ReplyAction.success.format(username=self.profile.twitter.login, tweet_id=tweet_id, new_tweet_id=f'Already replied tweet  with text: {text}')}"
            )
        else:
            if not tweet:
                return
            log = (
                f"{self.profile.id} | "
                f"{ReplyAction.success.format(username=self.profile.twitter.login, tweet_id=tweet_id, new_tweet_id=tweet.id)}"
            )
        my_logger.success(log)
        return log

    async def get_user_data(self, username: str = None) -> User | str:
        username = self.profile.twitter.login if not username else username
        username = username.split('/')[-1]
        try:
            user_data = await self.call_func(
                self.client.request_user_by_username,
                (
                    f"{self.profile.id} | "
                    f"{TweetInteraction.error.format(username=self.profile.twitter.login, action='get user data from', source=username)}"
                ),
                username
            )
            if user_data:
                log = (
                    f"{self.profile.id} | {TweetInteraction.success.format(username=self.profile.twitter.login)}. "
                    f"Got user data from {username} with {user_data.followers_count} followers"
                )
                my_logger.success(log)
                return user_data
            else:
                log = (
                    f"{self.profile.id} | "
                    f"{TweetInteraction.error.format(username=self.profile.twitter.login, action='get user data from', source=username)}. User {username} is suspended or doesn\'t exist"
                )
                my_logger.error(log)
        except JSONDecodeError:
            delay = 60 * 10
            log = (
                f'{self.profile.id} | '
                f"{TweetInteraction.error.format(username=self.profile.twitter.login, action='get user data from', source=username)}. {f'Got rate limit. Sleeping for {delay} seconds...'}"
            )
            my_logger.error(log)
            await asyncio.sleep(60 * 10)
        return log

    async def follow_by_username(self, username: str = None) -> str:
        username = self.profile.twitter.login if not username else username
        username = username.split('/')[-1]
        user_data = await self.get_user_data(username)
        if isinstance(user_data, str):
            return user_data
        await asyncio.sleep(uniform(3, 5))
        result = await self.call_func(
            self.client.follow,
            f"{self.profile.id} | {FollowAction.error.format(username=self.profile.twitter.login, source=username)}",
            user_data.id
        )
        if result:
            log = (
                f"{self.profile.id} | "
                f"{FollowAction.success.format(username=self.profile.twitter.login, following_username=username)}"
            )
            my_logger.success(log)
        else:
            log = (
                f"{self.profile.id} | "
                f"{FollowAction.error.format(username=self.profile.twitter.login, source=username)}. {f'Something wrong happened with following {username} - {result}'}"
            )
            my_logger.error(log)
        return log

    async def like(self, tweet_id: int) -> str:
        result = await self.call_func(
            self.client.like,
            f"{self.profile.id} | {LikeAction.error.format(username=self.profile.twitter.login, source=tweet_id)}",
            tweet_id
        )
        if result:
            log = (
                f'{self.profile.id} | {LikeAction.success.format(username=self.profile.twitter.login, tweet_id=tweet_id)}'
            )
            my_logger.success(log)
            return log

    async def repost(self, tweet_id: int) -> str:
        error_log = f"{self.profile.id} | {RepostAction.error.format(username=self.profile.twitter.login, source=tweet_id)}"
        tweet: Tweet = await self.call_func(self.client.repost, error_log, tweet_id)
        log = (
            f'{self.profile.id} | {RepostAction.success.format(username=self.profile.twitter.login, tweet_id=tweet_id)}'
        )
        my_logger.success(log)
        return log

    async def quote(self, tweet_url: str, text: str, image: bytes = None) -> str:
        result = await self.call_func(
            self.client.quote,
            f"{self.profile.id} | {QuoteAction.error.format(username=self.profile.twitter.login, source=tweet_url)}",
            tweet_url, text
        )
        log = (
            f'{self.profile.id} | '
            f'{QuoteAction.success.format(username=self.profile.twitter.login, tweet_url=tweet_url, result=result)}'
        )
        my_logger.success(log)
        return log

    async def change_password(self) -> str:
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(characters) for _ in range(50))
        result = await self.call_func(
            self.client.change_password,
            f"{self.profile.id} | {ChangePasswordAction.error.format(username=self.profile.twitter.login)}",
            password
        )
        if result:
            new_password = self.client.account.password
            log = (
                f'{self.profile.id} | '
                f'{ChangePasswordAction.success.format(username=self.profile.twitter.login, password=self.profile.twitter.password, new_password=new_password, auth_token=self.client.account.auth_token)}'
            )
            my_logger.success(log)
            self.profile.twitter.auth_token = self.client.account.auth_token
            self.profile.twitter.password = new_password
            await db.edit(self.profile)
        else:
            log = f"{self.profile.id} | {ChangePasswordAction.error.format(username=self.profile.twitter.login)}"
            my_logger.error(log)
        return log

    async def add_2fa(self) -> str:
        totp_is_enabled = await self.call_func(
            self.client.totp_is_enabled,
            (
                f"{self.profile.id} | "
                f"{TwoFactorAction.error.format(username=self.profile.twitter.login)}"
            )
        )
        if totp_is_enabled:
            log = f"{self.profile.id} | {TwoFactorAction.already_added.format(username=self.profile.twitter.login)}"
            my_logger.debug(log)
        else:
            await self.client.enable_totp()
            totp_secret = self.client.account.totp_secret
            backup_code = self.client.account.backup_code
            self.profile.twitter.totp_secret = totp_secret
            self.profile.twitter.backup_code = backup_code
            await db.edit(self.profile.twitter)
            log = (
                f"{self.profile.id} | "
                f"{TwoFactorAction.success.format(username=self.profile.twitter.login, totp_secret=totp_secret, backup_code=backup_code)}"
            )
            my_logger.success(log)
        return log


class ActionWithSource(Action, ABC):
    async def start(self, ttm: TwitterTaskManager):
        pass


class ActionWithoutSource(Action, ABC):
    def __new__(cls):
        raise NotImplementedError(f"Экземпляры класса {cls.name} не могут быть созданы")

    @staticmethod
    async def start(ttm: TwitterTaskManager):
        pass


class TweetInteraction(ActionWithSource, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_or_prompt: str | None = kwargs.get('text_or_prompt')
        self.generate: bool | None = kwargs.get('generate')
        self.image: bytes | None = kwargs.get('image')
        self.evm: bool | None = kwargs.get('evm_wallet')
        self.aptos: bool | None = kwargs.get('aptos_wallet')
        self.solana: bool | None = kwargs.get('solana_wallet')
        self.bitcoin_segwit: bool | None = kwargs.get('bitcoin_segwit')
        self.bitcoin_taproot: bool | None = kwargs.get('bitcoin_taproot')

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
            my_logger.error(e)

    async def get_text(self, ttm: TwitterTaskManager) -> str:
        if self.generate:
            text = self.generate_crypto_text(self.text_or_prompt, ttm.profile.proxy.proxy_string)
        elif self.evm:
            text = ttm.profile.evm_address
        elif self.aptos:
            text = ttm.profile.aptos_address
        elif self.solana:
            text = ttm.profile.solana_address
        elif self.bitcoin_segwit:
            text = ttm.profile.btc_native_segwit_address
        elif self.bitcoin_taproot:
            text = ttm.profile.btc_taproot_address
        else:
            text = self.text_or_prompt
        return text


class TweetAction(TweetInteraction, ABC):
    name: str = 'Tweet'
    description: str = 'Введите текст (+картинку beta)'
    success: str = TweetInteraction.success + 'Tweeted {tweet_id}'
    error: str = TweetInteraction.error.replace('{action}', 'tweet')

    async def start(self, ttm: TwitterTaskManager) -> str:
        return await ttm.tweet(await self.get_text(ttm))

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


class FollowAction(ActionWithSource, ABC):
    name: str = 'Follow'
    description: str = 'Введите логины'
    success: str = ActionWithSource.success + 'Followed {following_username}'
    error: str = ActionWithSource.error.replace('{action}', 'follow')

    async def start(self, ttm: TwitterTaskManager) -> str:
        return await ttm.follow_by_username(self.source)


class LikeAction(TweetInteraction, ABC):
    name: str = 'Like'
    description: str = 'Введите id постов'
    success: str = TweetInteraction.success + 'Liked {tweet_id}'
    error: str = TweetInteraction.error.replace('{action}', 'like')

    async def start(self, ttm: TwitterTaskManager) -> str:
        return await ttm.like(int(self.source))


class RepostAction(TweetInteraction, ABC):
    name: str = 'Repost'
    description: str = 'Введите id постов'
    success: str = TweetInteraction.success + 'Reposted {tweet_id}'
    error: str = TweetInteraction.error.replace('{action}', 'repost')

    async def start(self, ttm: TwitterTaskManager) -> str:
        return await ttm.repost(int(self.source))


class QuoteAction(TweetInteraction, ABC):
    name: str = 'Quote'
    description: list[str] = ['Введите ссылки на посты', 'Введите текст (+картинку beta)']
    success: str = TweetInteraction.success + 'Quoted {tweet_url}, tweet ID: {result}'
    error: str = TweetInteraction.error.replace('{action}', 'quote')

    async def start(self, ttm: TwitterTaskManager) -> str:
        return await ttm.quote(self.source, await self.get_text(ttm), self.image)

    def __str__(self):
        return (
                super().__str__() +
                f'({self.text_or_prompt[:6]}{"..." if len(self.text_or_prompt) > 6 else ""}, '
                f'{f"generate=True, " if self.generate else ""}'
                f'{f"evm=True, " if self.evm else ""}'
                f'{f"aptos=True, " if self.aptos else ""}'
                f'{f"solana=True, " if self.solana else ""}'
                f'with_image={self.image == True})'
        )


class ReplyAction(TweetInteraction, ABC):
    name: str = 'Reply'
    description: list[str] = ['Вставьте id постов', 'Введите текст (+картинку beta)']
    success: str = TweetInteraction.success + 'Replied {tweet_id}, reply id: {new_tweet_id}'
    error: str = TweetInteraction.error.replace('{action}', 'reply')

    async def start(self, ttm: TwitterTaskManager) -> str:
        if isinstance(self.source, str):
            if self.source.startswith('http'):
                source = int(self.source.split('/')[-1])
            else:
                source = int(self.source)
        return await ttm.reply(self.source, await self.get_text(ttm), self.image)

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


class UnlockAction(ActionWithoutSource, ABC):
    name: str = 'Unlock'
    success: str = Action.success + 'Unlocked'
    error: str = '{username} | Failed to unlock account. {e} '

    @staticmethod
    async def start(ttm: TwitterTaskManager) -> str:
        await ttm.get_user_data()
        await ttm.client.unlock()
        return f'{ttm.profile.id} | Account status - {ttm.client.account.status}'


class ChangePasswordAction(ActionWithoutSource, ABC):
    name: str = 'Change password'
    success: str = Action.success + 'Changed password {password} to {new_password}. New auth token - {auth_token}'
    error: str = '{username} | Failed to change password. {e} '

    @staticmethod
    async def start(ttm: TwitterTaskManager) -> str:
        return await ttm.change_password()


class TwoFactorAction(ActionWithoutSource, ABC):
    label: str = 'Add 2FA'
    success: str = Action.success + 'Added 2FA. 2FA key - {totp_secret}, backup code - {backup_code}'
    error: str = '{username} | Failed to add 2FA. {e}'
    already_added: str = '{username} | 2FA already added'

    @staticmethod
    async def start(ttm: TwitterTaskManager):
        return await ttm.add_2fa()


twitter_account_settings = {
    'Change password': ChangePasswordAction,
    'Add 2FA': TwoFactorAction,
    'Unlock': UnlockAction,
}
twitter_actions = {
    'Tweet': TweetAction,
    'Like': LikeAction,
    'Follow': FollowAction,
    'Repost': RepostAction,
    'Quote': QuoteAction,
    'Reply': ReplyAction,
    'Settings': twitter_account_settings
}
