import asyncio

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from web3db import Profile

from main import bot
from handlers.basic_commands import start as main_start
from keyboards import fabrics
from data import get_all_accounts_by_social, get_random_accounts_by_proxy
from extra.tasks import process_tasks
from extra.tw import Tweet, TwitterInteraction, Quote, Reply, twitter_actions, twitter_account_settings
from utils import (
    SocialTasks, show_social_tasks, edit_dialog_message, menu_buttons,
    input_data_types_buttons, show_profiles_tasks, profiles_amount_type
)

router = Router()


@router.callback_query(fabrics.InlineCallbacks.filter(F.action == 'Social tasks'))
async def social_tasks(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    await state.update_data(dialog_message=call.message)
    await state.set_state(SocialTasks.CHOOSE_SOCIAL)
    await edit_dialog_message(
        call.message,
        '<b>Social tasks</b>\nChoose',
        reply_markup=fabrics.get_inline_buttons(['Twitter', 'Меню'])
    )


@router.callback_query(SocialTasks.CHOOSE_SOCIAL, fabrics.InlineCallbacks.filter(F.action.in_(['Twitter'])))
async def tasks_menu(
        call: CallbackQuery,
        callback_data: fabrics.InlineCallbacks,
        state: FSMContext
):
    social = callback_data.action
    await state.update_data(social=social)
    await state.update_data(social_tasks=dict())
    await state.update_data(profiles_ids=set())
    await state.update_data(all_profiles=await get_all_accounts_by_social(social))
    await state.set_state(SocialTasks.CHOOSE_TASK)
    await show_social_tasks(call.message, social, state)


@router.callback_query(fabrics.InlineCallbacks.filter(F.action == 'Таски'))
@router.callback_query(SocialTasks.INPUT_PROFILES_IDS, fabrics.ProfilesPagination.filter(F.action == 'Таски'))
async def return_to_tasks(
        call: CallbackQuery,
        callback_data: fabrics.InlineCallbacks | fabrics.ProfilesPagination,
        state: FSMContext
):
    data = await state.get_data()
    current_state = await state.get_state()
    if 'SocialTasks' in current_state:
        await show_social_tasks(call.message, data["social"], state)
    else:
        await show_profiles_tasks(call.message, state)


@router.callback_query(SocialTasks.CHOOSE_TASK, fabrics.InlineCallbacks.filter(F.action == 'Текущие'))
async def show_current_state(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    data = await state.get_data()
    text = (
            f'<b>{menu_buttons[callback_data.action]}</b>\n'
            f'<b>Профили:</b>\n{data["profiles_ids"] or ""}\n<b>Таски:</b>\n'
            + '\n'.join([f'{i}. {getattr(task, "label", task)} {sources or ""}'
                         for i, (task, sources) in enumerate(data['social_tasks'].items(), 1)])
    )
    await edit_dialog_message(call.message, text, buttons=['Запуск'])


@router.callback_query(
    SocialTasks.CHOOSE_TASK,
    fabrics.InlineCallbacks.filter(F.action == 'Очистить')
)
async def clear_current_state(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    await state.update_data(social_tasks=dict())
    await state.update_data(profiles_ids=set())
    await call.answer(f"{menu_buttons[callback_data.action]}")


@router.callback_query(SocialTasks.CHOOSE_TASK, fabrics.InlineCallbacks.filter(F.action == 'Запуск'))
async def start_tasks(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    data = await state.get_data()
    social = data['social']
    social_tasks = data['social_tasks']
    profiles_ids = data['profiles_ids']
    if social_tasks and profiles_ids:
        asyncio.create_task(process_tasks(social, social_tasks, profiles_ids, bot, call.message.chat.id))
        await state.update_data(social_tasks=dict())
        await state.update_data(profiles_ids=set())
        await call.answer(f"{menu_buttons[callback_data.action]}")
    else:
        await call.answer(f"Таски или аккаунты пустые, скипаю...")


@router.callback_query(fabrics.InlineCallbacks.filter(F.action == 'Меню'))
async def return_to_main_menu(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext) -> None:
    await state.clear()
    await main_start(call.message, state)


@router.callback_query(SocialTasks.CHOOSE_TASK, fabrics.InlineCallbacks.filter(F.action == 'Tweet'))
async def tweet_task(
        call: CallbackQuery,
        callback_data: fabrics.InlineCallbacks,
        state: FSMContext
):
    data = await state.get_data()
    await state.update_data(current_task=Tweet())
    s = (f'<b>{data["social"]} Tweet</b>\n' +
         '\n'.join([f'{i + 1}. {text}' for i, text in enumerate(input_data_types_buttons.values())]))
    await edit_dialog_message(call.message, s, list(input_data_types_buttons.keys()))
    await state.set_state(SocialTasks.CHOOSE_INPUT_DATA_TYPE)


@router.callback_query(SocialTasks.CHOOSE_TASK, fabrics.InlineCallbacks.filter(F.action == 'Settings'))
async def settings(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext) -> None:
    data = await state.get_data()
    social = data['social']
    await state.set_state(SocialTasks.SETTINGS)
    await edit_dialog_message(
        call.message,
        f'<b>Social tasks. {social.capitalize()}. Настройки</b>',
        buttons=list(twitter_account_settings)
    )


@router.callback_query(SocialTasks.SETTINGS, fabrics.InlineCallbacks.filter(F.action.in_(twitter_account_settings)))
async def settings_tasks(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    data = await state.get_data()
    social_tasks: dict[TwitterInteraction: set] = data['social_tasks']
    social_tasks[twitter_account_settings[callback_data.action]] = None
    await call.answer(f'Задача {callback_data.action} добавлена в список задач')
    await show_social_tasks(call.message, data['social'], state)


@router.callback_query(
    SocialTasks.CHOOSE_TASK,
    fabrics.InlineCallbacks.filter(F.action.in_(twitter_actions) & ~F.action.in_(['Tweet', 'Settings', 'Профили']))
)
async def not_tweet_task(
        call: CallbackQuery,
        callback_data: fabrics.InlineCallbacks,
        state: FSMContext
):
    data = await state.get_data()
    current_task: TwitterInteraction = twitter_actions[callback_data.action]()
    await state.update_data(current_task=current_task)
    description = current_task.description[0] if isinstance(current_task, (
        Quote, Reply)) else current_task.description
    s = f'<b>{data["social"]} {str(current_task.__class__.__name__)}</b>\n{description}'
    await edit_dialog_message(call.message, s)
    await state.set_state(SocialTasks.INPUT_SOURCES)


@router.callback_query(
    SocialTasks.CHOOSE_INPUT_DATA_TYPE,
    fabrics.InlineCallbacks.filter(F.action.in_(['Свой', 'Любой по крипте', 'По промпту']))
)
async def input_data_text_type_choice(
        call: CallbackQuery,
        callback_data: fabrics.InlineCallbacks,
        state: FSMContext
):
    data = await state.get_data()
    current_task: TwitterInteraction = data['current_task']
    current_task.generate = True
    input_data_type = callback_data.action
    if input_data_type == 'Любой по крипте':
        current_task.text_or_prompt = f'Любой'
        social_tasks: dict[TwitterInteraction: set] = data['social_tasks']
        social_tasks[current_task] = data.get('input_sources', set())
        await state.update_data(social_tasks=social_tasks)
        await return_to_tasks(call, callback_data, state)
    else:
        if isinstance(current_task, (Quote, Reply)):
            description = current_task.description[1]
        else:
            description = current_task.description
        text = f'<b>{data["social"]} {str(current_task.__class__.__name__)} {callback_data.action}</b>\n{description}'
        await state.update_data(input_data_type=input_data_type)
        await edit_dialog_message(call.message, text)
        await state.set_state(SocialTasks.INPUT_DATA)


@router.callback_query(
    SocialTasks.CHOOSE_INPUT_DATA_TYPE,
    fabrics.InlineCallbacks.filter(F.action.in_(['EVM', 'Aptos', 'Solana']))
)
async def input_data_wallet_type_choice(
        call: CallbackQuery,
        callback_data: fabrics.InlineCallbacks,
        state: FSMContext
) -> None:
    data = await state.get_data()
    current_task: TwitterInteraction = data['current_task']
    current_task.text_or_prompt = callback_data.action
    match callback_data.action:
        case 'EVM':
            current_task.evm = True
        case 'Aptos':
            current_task.aptos = True
        case 'Solana':
            current_task.solana = True
    social_tasks: dict[TwitterInteraction: set] = data['social_tasks']
    social_tasks[current_task] = data.get('input_sources', set())
    await state.update_data(social_tasks=social_tasks)
    await return_to_tasks(call, callback_data, state)


def get_text_for_current_page_profiles(profiles: list[Profile], page: int):
    text = '<b>Введите id профилей</b>\n'
    for profile_id, login, ready in profiles[page * 10:(page + 1) * 10]:  # type: Profile
        line = f'{profile_id} | {login}'
        line = f'<b><i>{line}</i></b>' if ready else line
        text += line + '\n'
    return text


@router.callback_query(
    SocialTasks.CHOOSE_TASK,
    fabrics.InlineCallbacks.filter(F.action == 'Профили')
)
async def show_accounts(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    await edit_dialog_message(
        call.message,
        f'<b>{menu_buttons[callback_data.action]}</b>',
        reply_markup=fabrics.get_inline_buttons(profiles_amount_type + ['Таски'], 1)
    )
    await state.set_state(SocialTasks.CHOOSE_ACCOUNTS)


@router.callback_query(
    SocialTasks.CHOOSE_ACCOUNTS,
    fabrics.InlineCallbacks.filter(F.action == 'IDs')
)
async def get_profiles_ids_choice(
        call: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    text = get_text_for_current_page_profiles(data['all_profiles'], 0)
    await edit_dialog_message(message=call.message, text=text, reply_markup=fabrics.paginator())
    await state.set_state(SocialTasks.INPUT_PROFILES_IDS)


@router.callback_query(SocialTasks.INPUT_PROFILES_IDS,
                       fabrics.ProfilesPagination.filter(F.action.in_(['next', 'prev'])))
async def profiles_pagination(
        call: CallbackQuery,
        callback_data: fabrics.ProfilesPagination,
        state: FSMContext
):
    data = await state.get_data()
    all_profiles = data['all_profiles']
    page_num = int(callback_data.page)
    page = page_num - 1 if page_num > 0 else 0

    if callback_data.action == "next":
        page = page_num + 1 if (page_num + 1) * 10 < len(all_profiles) else page_num

    text = get_text_for_current_page_profiles(all_profiles, page)

    await edit_dialog_message(
        message=call.message,
        text=text,
        reply_markup=fabrics.paginator(page=page)
    )


@router.callback_query(
    SocialTasks.CHOOSE_ACCOUNTS,
    fabrics.InlineCallbacks.filter(F.action == 'Гретые')
)
async def ready_profiles(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    data = await state.get_data()
    await state.update_data(profiles_ids={profile[0] for profile in data['all_profiles'] if profile[-1]})
    await show_social_tasks(data['dialog_message'], data["social"], state)
    await call.answer('Выбраны прогретые профили')


@router.callback_query(
    SocialTasks.CHOOSE_ACCOUNTS,
    fabrics.InlineCallbacks.filter(F.action == 'Рандом')
)
async def proxy_random_profiles(
        call: CallbackQuery,
        callback_data: fabrics.InlineCallbacks,
        state: FSMContext
):
    data = await state.get_data()
    await call.answer('Выбраны рандомные по прокси профили')
    await state.update_data(profiles_ids=await get_random_accounts_by_proxy(data["social"]))
    await show_social_tasks(data['dialog_message'], data["social"], state)


@router.callback_query(
    SocialTasks.CHOOSE_ACCOUNTS,
    fabrics.InlineCallbacks.filter(F.action == 'Все')
)
async def all_profiles(
        call: CallbackQuery,
        callback_data: fabrics.InlineCallbacks,
        state: FSMContext
):
    data = await state.get_data()
    await state.update_data(profiles_ids={el[0] for el in data['all_profiles']})
    await show_social_tasks(data['dialog_message'], data["social"], state)
    await call.answer('Выбраны все профили')
