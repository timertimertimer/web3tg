import re
import ssl
import email
import socket
import asyncio
import imaplib
from email.message import Message
from collections import defaultdict
from typing import Iterable, Callable, Optional

from aiohttp_proxy import ProxyConnector
from aioimaplib import IMAP4_SSL, get_running_loop, IMAP4ClientProtocol, Abort


class ProxyIMAPClient(IMAP4_SSL):
    def __init__(self, *args, proxy: str = None, **kwargs):
        self.proxy = proxy
        super().__init__(*args, **kwargs)

    async def __aenter__(self):
        await self.wait_hello_from_server()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.logout()

    async def create_socket_through_proxy(
            self, host, port,
    ) -> socket.socket:
        proxy = ProxyConnector.from_url(self.proxy)
        return await proxy.connect(dest_host=host, dest_port=port)

    def create_client(self, host: str, port: int, loop: asyncio.AbstractEventLoop,
                      conn_lost_cb: Callable[[Optional[Exception]], None] = None,
                      ssl_context: ssl.SSLContext = None):
        local_loop = loop if loop is not None else get_running_loop()

        if ssl_context is None:
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

        async def create_connection():
            sock = await self.create_socket_through_proxy(host, port)
            await local_loop.create_connection(
                lambda: self.protocol, sock=sock, ssl=ssl_context, server_hostname=host)

        if self.proxy:
            self.protocol = IMAP4ClientProtocol(local_loop, conn_lost_cb)
            local_loop.create_task(create_connection())
        else:
            super().create_client(host, port, local_loop, conn_lost_cb, ssl_context)

    async def get_messages_from_folders(self, folders: Iterable[str], charset: str) -> dict[str: list[Message]]:
        messages = defaultdict(list)
        for folder in folders:
            try:
                result, data = await self.select(folder)
            except Abort as e:
                pass
            if result != 'OK':
                # print(f"Failed to select folder {folder}: {data}")
                continue

            result, data = await self.search("ALL", charset=charset)
            if result == 'OK':
                for number_bytes in data[0].split():
                    number = number_bytes.decode('utf-8')
                    result, data = await self.fetch(number, '(RFC822)')
                    if result == 'OK':
                        messages[folder].append(email.message_from_bytes(data[1]))
            else:
                # print(f"SEARCH command failed in folder {folder}: {data}")
                pass

        return messages


hosts = {
    'rambler.ru': 'imap.rambler.ru',
    'outlook.com': 'outlook.office365.com',
    'gmail.com': 'imap.gmail.com',
    'mail.ru': 'imap.mail.ru'
}


async def get_message(username: str, password: str, proxy: str = None):
    host = hosts[username.split('@')[1]]
    async with ProxyIMAPClient(host=host, proxy=proxy) as mail:
        try:
            resp = await mail.login(username, password)
        except imaplib.IMAP4.error:
            print('Login failed')
            return
        inbox_messages = (await mail.get_messages_from_folders(
            ['INBOX'],
            charset=('US-ASCII' if host == hosts['outlook.com'] else 'utf-8')
        ))
        last_message = inbox_messages['INBOX'][-1]
        for part in last_message.walk():
            if part.get_content_type() == "text/plain" or part.get_content_type() == "text/html":
                message = part.get_payload(decode=True)
                break
    return message.decode(('iso-8859-1' if host == hosts['outlook.com'] else 'utf-8'))


async def get_verify_location_link(username, password, proxy):
    message = await get_message(username, password, proxy)
    link = re.search('https:\/\/click\.discord\.com\/ls\/click\?upn=[^\s]+', message).group()
    return link


__all__ = [
    'ProxyIMAPClient',
    'get_verify_location_link'
]
