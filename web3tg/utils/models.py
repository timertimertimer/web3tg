from web3db.models import *
from web3mt.onchain.evm.models import *
from web3mt.onchain.evm.models import Fantom, ZetaChain

__all__ = [
    "socials_menu_buttons",
    "profiles_menu_buttons",
    "onchain_menu_buttons",
    "input_data_types_buttons_for_twitter",
    "profiles_amount_type",
    "models",
    "chains"
]

socials_menu_buttons = {
    'Текущие': 'Текущие профили и таски',
    'Профили': 'Определенные профили, рандомные по прокси из каждой пачки или все?',
    'Очистить': 'Успешно очищено',
    'Запуск': 'Таски запущены',
    'Меню': 'Меню'
}
profiles_menu_buttons = ['Change social', 'Edit social', '2FA', 'Меню']
onchain_menu_buttons = ['Transfer', 'Withdraw', 'Stats', 'Меню']

input_data_types_buttons_for_twitter = {
    'Свой': 'Хотите написать свой текст',
    'Любой по крипте': 'Сгенерировать текст связанный с криптовалютами',
    'По промпту': 'Сгенерировать по промпту',
    'EVM': 'Кошелек евм',
    'Aptos': 'Кошелек аптос',
    'Solana': 'Кошелек солана',
    'Bitcoin (Segwit)': 'Кошелек биткоин (Segwit)',
    'Bitcoin (Taproot)': 'Кошелек биткоин (Taproot)'
}
profiles_amount_type = [
    'IDs',
    'Гретые',
    'Рандом',
    'Все'
]
models = {'Twitter': Twitter, 'Discord': Discord, 'Github': Github, 'Proxy': Proxy, 'Email': Email}

chains: list[Chain] = [
    Ethereum, Arbitrum, Optimism, Base, Zora, Scroll, Linea, zkSync,
    Polygon, Avalanche, Metis, Fantom, BNB, opBNB, ZetaChain
]

onchain_stats_buttons = ['ETH гретые']