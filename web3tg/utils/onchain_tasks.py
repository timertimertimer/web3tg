from web3mt.onchain.evm.client import Client
from web3tg.utils import chains


async def get_onchain_transfer_info():
    for chain in chains:
        client = Client(chain=chain)


async def get_cex_withdraw_info():
    ...


async def get_eth_warmed_profiles():
    ...
