import os

from capmonstercloudclient import CapMonsterClient, ClientOptions
from capmonstercloudclient.requests import HcaptchaProxylessRequest

from http.client import HTTPException
from discord import CaptchaRequired, Client

from extra.logger import logger


async def solve_captcha(cr: CaptchaRequired, client: Client):
    client_options = ClientOptions(api_key=os.getenv('CAPMONSTER_API_KEY'))
    cap_monster_client = CapMonsterClient(options=client_options)
    hcaptcharequest = HcaptchaProxylessRequest(
        websiteUrl=cr.response.url,
        websiteKey=cr.sitekey,
        data=cr.rqdata
    )
    while True:
        try:
            resp = await cap_monster_client.solve_captcha(hcaptcharequest)
            return resp['gRecaptchaResponse']
        except HTTPException:
            pass
