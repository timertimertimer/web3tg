import asyncio

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from web3tg.callbacks.main_callbacks import return_to_tasks
from web3tg.main import bot
from web3tg.keyboards import fabrics
from web3tg.data import get_all_accounts_by_social, get_random_accounts_by_proxy
from web3tg.utils import (
    SocialTasks, socials_menu_buttons, input_data_types_buttons_for_twitter, profiles_amount_type,
    process_social_tasks, TweetAction, TweetInteraction, QuoteAction, ReplyAction, twitter_actions,
    twitter_account_settings
)
from web3tg.utils.bot_commands import edit_dialog_message, show_social_tasks

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


@router.callback_query(SocialTasks.CHOOSE_TASK, fabrics.InlineCallbacks.filter(F.action == 'Текущие'))
async def show_current_state(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    data = await state.get_data()
    text = (
            f'<b>{socials_menu_buttons[callback_data.action]}</b>\n'
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
    await call.answer(f"{socials_menu_buttons[callback_data.action]}")


@router.callback_query(SocialTasks.CHOOSE_TASK, fabrics.InlineCallbacks.filter(F.action == 'Запуск'))
async def start_tasks(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    data = await state.get_data()
    social = data['social']
    social_tasks = data['social_tasks']
    profiles_ids = data['profiles_ids']
    if social_tasks and profiles_ids:
        asyncio.create_task(process_social_tasks(social, social_tasks, profiles_ids, bot, call.message.chat.id))
        await state.update_data(social_tasks=dict())
        await state.update_data(profiles_ids=set())
        await call.answer(f"{socials_menu_buttons[callback_data.action]}")
    else:
        await call.answer(f"Таски или аккаунты пустые, скипаю...")


@router.callback_query(SocialTasks.CHOOSE_TASK, fabrics.InlineCallbacks.filter(F.action == 'Tweet'))
async def tweet_task(
        call: CallbackQuery,
        callback_data: fabrics.InlineCallbacks,
        state: FSMContext
):
    data = await state.get_data()
    await state.update_data(current_task=TweetAction())
    s = (f'<b>{data["social"]} Tweet</b>\n' +
         '\n'.join([f'{i + 1}. {text}' for i, text in enumerate(input_data_types_buttons_for_twitter.values())]))
    await edit_dialog_message(call.message, s, list(input_data_types_buttons_for_twitter.keys()))
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
    social_tasks: dict[TweetInteraction: set] = data['social_tasks']
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
    current_task: TweetInteraction = twitter_actions[callback_data.action]()
    await state.update_data(current_task=current_task)
    description = current_task.description[0] if isinstance(current_task, (
        QuoteAction, ReplyAction)) else current_task.description
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
    current_task: TweetInteraction = data['current_task']
    current_task.generate = True
    input_data_type = callback_data.action
    if input_data_type == 'Любой по крипте':
        current_task.text_or_prompt = f'Любой'
        social_tasks: dict[TweetInteraction: set] = data['social_tasks']
        social_tasks[current_task] = data.get('input_sources', set())
        await state.update_data(social_tasks=social_tasks)
        await return_to_tasks(call, callback_data, state)
    else:
        if isinstance(current_task, (QuoteAction, ReplyAction)):
            description = current_task.description[1]
        else:
            description = current_task.description
        text = f'<b>{data["social"]} {str(current_task.__class__.__name__)} {callback_data.action}</b>\n{description}'
        await state.update_data(input_data_type=input_data_type)
        await edit_dialog_message(call.message, text)
        await state.set_state(SocialTasks.INPUT_DATA)


@router.callback_query(
    SocialTasks.CHOOSE_INPUT_DATA_TYPE,
    fabrics.InlineCallbacks.filter(F.action.in_(['EVM', 'Aptos', 'Solana', 'Bitcoin (Segwit)', 'Bitcoin (Taproot)']))
)
async def input_data_wallet_type_choice(
        call: CallbackQuery,
        callback_data: fabrics.InlineCallbacks,
        state: FSMContext
) -> None:
    data = await state.get_data()
    current_task: TweetInteraction = data['current_task']
    current_task.text_or_prompt = callback_data.action
    match callback_data.action:
        case 'EVM':
            current_task.evm = True
        case 'Aptos':
            current_task.aptos = True
        case 'Solana':
            current_task.solana = True
        case 'Bitcoin (Segwit)':
            current_task.bitcoin_segwit = True
        case 'Bitcoin (Taproot)':
            current_task.bitcoin_taproot = True
    social_tasks: dict[TweetInteraction: set] = data['social_tasks']
    social_tasks[current_task] = data.get('input_sources', set())
    await state.update_data(social_tasks=social_tasks)
    await return_to_tasks(call, callback_data, state)


@router.callback_query(
    SocialTasks.CHOOSE_TASK,
    fabrics.InlineCallbacks.filter(F.action == 'Профили')
)
async def show_accounts(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    await edit_dialog_message(
        call.message,
        f'<b>{socials_menu_buttons[callback_data.action]}</b>',
        reply_markup=fabrics.get_inline_buttons(profiles_amount_type + ['Таски'], 1)
    )
    await state.set_state(SocialTasks.CHOOSE_ACCOUNTS)


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
