from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup
from web3db import *
from web3mt.evm import Chain, Zora, Arbitrum, Optimism, Ethereum

from .tw import twitter_actions
from .states import SocialTasks, ProfilesTasks
from web3tg.keyboards import fabrics


def get_social_tasks_buttons(social: str) -> dict:
    return {
        'Twitter': twitter_actions
    }[social]


async def edit_dialog_message(
        message: Message,
        text: str,
        buttons: list = None,
        reply_markup: InlineKeyboardMarkup = None
):
    buttons = buttons or []
    reply_markup = reply_markup or fabrics.get_inline_buttons(buttons + ['Таски'])
    await message.edit_text(text, reply_markup=reply_markup)


async def show_social_tasks(message: Message, social: str, state: FSMContext):
    buttons = list(get_social_tasks_buttons(social)) + list(menu_buttons)
    await edit_dialog_message(
        message,
        f'<b>Social tasks. {social.capitalize()} таски</b>',
        reply_markup=fabrics.get_inline_buttons(buttons)
    )
    await state.set_state(SocialTasks.CHOOSE_TASK)


async def show_profiles_tasks(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(dialog_message=message)
    await edit_dialog_message(
        message,
        f'<b>Profiles tasks</b>\nChoose',
        reply_markup=fabrics.get_inline_buttons(profiles_tasks_buttons + ['Меню'])
    )
    await state.set_state(ProfilesTasks.CHOOSE_TASK)


def get_text_for_current_page_profiles(profiles: list[Profile], page: int):
    text = '<b>Введите id профилей</b>\n'
    for profile_id, login, ready in profiles[page * 10:(page + 1) * 10]:  # type: Profile
        line = f'{profile_id} | {login}'
        line = f'<b><i>{line}</i></b>' if ready else line
        text += line + '\n'
    return text


help_string = """
Формат CSV
Первая строка в файле задает формат данных. 
Mail - login:password
Discord - login:password:email_password:auth_token (auth_token ОБЯЗАТЕЛЬНО, а если нет, то login и password ОБЯЗАТЕЛЬНО)
Twitter - login:password:email:email_password:auth_token (auth_token ОБЯЗАТЕЛЬНО, а если нет, то login и password ОБЯЗАТЕЛЬНО, email и email_password только если есть)
"""

menu_buttons = {
    'Текущие': 'Текущие профили и таски',
    'Профили': 'Определенные профили, рандомные по прокси из каждой пачки или все?',
    'Очистить': 'Успешно очищено',
    'Запуск': 'Таски запущены',
    'Меню': 'Меню'
}
input_data_types_buttons = {
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
profiles_tasks_buttons = ['Change social', '2FA']
models = {'Twitter': Twitter, 'Discord': Discord, 'Github': Github, 'Proxy': Proxy, 'Email': Email}

CHAINS: list[Chain] = [Zora, Base, Arbitrum, Optimism, Ethereum]
