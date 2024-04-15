import asyncio
import csv
from typing import BinaryIO

from dotenv import load_dotenv

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from data import add_social_to_db
from extra.tw import Quote, Reply, TwitterInteraction
from utils import SocialTasks, edit_dialog_message, show_social_tasks, input_data_types_buttons, ProfilesTasks

from web3tg.keyboards import fabrics
from web3tg.utils import ZoraState, CHAINS

load_dotenv()

router = Router()


@router.message(F.document, SocialTasks.PROCESS_FILE)
async def process_file(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    social = data['social']
    file = await message.document.bot.get_file(message.document.file_id)
    result: BinaryIO = await message.document.bot.download(file)
    file_format = message.document.file_name.split('.')[-1]
    file_content = result.read().decode('utf-8')
    match file_format:
        case 'csv':
            csv_reader = csv.DictReader(
                f=file_content.splitlines(),
                delimiter=':',
                quotechar='"'
            )
            tasks = [add_social_to_db(social, row) for row in csv_reader]
            await asyncio.gather(*tasks)
        case _:
            await message.answer('Неверный формат файла')
            return
    await message.answer(f'Документ получен {message.document.file_name}')


@router.message(SocialTasks.INPUT_SOURCES)
async def process_input_sources(message: Message, state: FSMContext):
    data = await state.get_data()
    current_task: TwitterInteraction = data['current_task']
    input_sources = set(message.text.split('\n'))
    await message.delete()
    if isinstance(current_task, (Quote, Reply)):
        await state.update_data(input_sources=input_sources)
        s = (f'<b>{data["social"]} {str(current_task.__class__.__name__)}\n{current_task.description[1]}</b>\n' +
             '\n'.join([f'{i + 1}. {text}' for i, text in enumerate(input_data_types_buttons.values())]))
        await edit_dialog_message(data['dialog_message'], s, list(input_data_types_buttons.keys()))
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
    current_task: TwitterInteraction = data['current_task']
    input_data_type = data['input_data_type']
    current_task.text_or_prompt = input_data
    current_task.generate = input_data_type in ['Любой по крипте', 'По промпту']
    input_sources = data.get('input_sources', set())
    social_tasks[current_task] = input_sources
    await state.update_data(social_tasks=social_tasks)
    await show_social_tasks(data['dialog_message'], data["social"], state)


@router.message(SocialTasks.INPUT_PROFILES_IDS)
async def profiles_ids_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    profiles = set(message.text.split())
    await message.delete()
    current_profiles: set = data.get('profiles_ids', set())
    if all(map(str.isdigit, profiles)):
        current_profiles.update({int(el) for el in profiles})
        await state.update_data(profiles_ids=current_profiles)
    await show_social_tasks(data['dialog_message'], data["social"], state)


@router.message(ProfilesTasks.INPUT_PROFILES_IDS_TO_CHANGE_MODEL)
async def profiles_ids_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    social = data['social']
    profiles = set(message.text.split())
    await message.delete()
    if all(map(str.isdigit, profiles)):
        await state.update_data(profiles_ids={int(el) for el in profiles})
        await state.set_state(ProfilesTasks.START_CHANGE_PROFILES_MODEL)
        text = (
                   f'<b>Profiles. Change social. {social}</b>\n'
                   f'IDs: <i>{profiles}</i>\n'
                   f'Удалить текущий аккаунт - <i>{"YES" if data["delete_model"] else "NO"}</i>\n'
               ) + (
                   f'Удалить почту, привязанную к текущему аккаунту - '
                   f'<i>{"YES" if data["delete_models_email"] else "NO"}</i>'
                   if social != 'Email' else ''
               )
        await edit_dialog_message(data['dialog_message'], text, buttons=['Запуск'])
    else:
        await edit_dialog_message(
            data['dialog_message'],
            f'<b>Profiles. Change social. {social}</b>\nНеверно. Введите id профилей еще раз'
        )


@router.message(ZoraState.GET_LINKS)
async def get_links(message: Message, state: FSMContext):
    links = {}
    for line in message.text.split('\n'):
        link, amount = line.split()
        amount = int(amount) if amount.isdigit() else 1
        links[link] = amount
    await state.update_data(links=links)
    chains = {chain.name: False for chain in CHAINS}
    await state.update_data(chains=chains)
    await message.answer(
        'Choose chain', reply_markup=fabrics.get_chain_choice_buttons(chains, ['Reset', 'Next'])
    )
