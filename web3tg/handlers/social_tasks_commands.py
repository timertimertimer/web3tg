from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from web3tg.utils import SocialTasks, TweetInteraction, QuoteAction, ReplyAction, input_data_types_buttons_for_twitter
from web3tg.utils.bot_commands import edit_dialog_message, show_social_tasks

router = Router()


@router.message(SocialTasks.INPUT_SOURCES)
async def process_input_sources(message: Message, state: FSMContext):
    data = await state.get_data()
    current_task: TweetInteraction = data['current_task']
    input_sources = set(message.text.split('\n'))
    await message.delete()
    if isinstance(current_task, (QuoteAction, ReplyAction)):
        await state.update_data(input_sources=input_sources)
        s = (f'<b>{data["social"]} {str(current_task.__class__.__name__)}\n{current_task.description[1]}</b>\n' +
             '\n'.join([f'{i + 1}. {text}' for i, text in enumerate(input_data_types_buttons_for_twitter.values())]))
        await edit_dialog_message(data['dialog_message'], s, list(input_data_types_buttons_for_twitter.keys()))
        await state.set_state(SocialTasks.CHOOSE_INPUT_DATA_TYPE)
    else:
        social_tasks: dict = data['social_tasks']
        social_tasks[current_task] = input_sources
        await state.update_data(social_tasks=social_tasks)
        await show_social_tasks(data['dialog_message'], data["social"], state)


@router.message(SocialTasks.INPUT_DATA)
async def process_input_data(message: Message, state: FSMContext):
    input_data = message.text
    await message.delete()
    data = await state.get_data()
    social_tasks: dict = data['social_tasks']
    current_task: TweetInteraction = data['current_task']
    input_data_type = data['input_data_type']
    current_task.text_or_prompt = input_data
    current_task.generate = input_data_type in ['Любой по крипте', 'По промпту']
    input_sources = data.get('input_sources', set())
    social_tasks[current_task] = input_sources
    await state.update_data(social_tasks=social_tasks)
    await show_social_tasks(data['dialog_message'], data["social"], state)


@router.message(SocialTasks.CHOOSE_ACCOUNTS)
async def profiles_ids_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    profiles = set(message.text.split())
    await message.delete()
    current_profiles: set = data.get('profiles_ids', set())
    if all(map(str.isdigit, profiles)):
        current_profiles.update({int(el) for el in profiles})
        await state.update_data(profiles_ids=current_profiles)
    await show_social_tasks(data['dialog_message'], data["social"], state)
