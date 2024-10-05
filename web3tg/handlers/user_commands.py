import asyncio
import csv
from typing import BinaryIO

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from web3tg.keyboards import fabrics
from web3tg.utils.states import ZoraState, SocialTasks
from web3tg.utils.models import chains

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
            # tasks = [add_social_to_db(social, row) for row in csv_reader]
            tasks = []
            await asyncio.gather(*tasks)
        case _:
            await message.answer('Неверный формат файла')
            return
    await message.answer(f'Документ получен {message.document.file_name}')


@router.message(ZoraState.GET_LINKS)
async def get_links(message: Message, state: FSMContext):
    links = {}
    for line in message.text.split('\n'):
        link, amount = line.split()
        amount = int(amount) if amount.isdigit() else 1
        links[link] = amount
    await state.update_data(links=links)
    chains = {chain.name: False for chain in chains}
    await state.update_data(chains=chains)
    await message.answer(
        'Choose chain', reply_markup=fabrics.get_chain_choice_buttons(chains, ['Reset', 'Next'])
    )
