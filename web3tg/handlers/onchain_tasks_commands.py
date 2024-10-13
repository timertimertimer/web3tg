from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from web3tg.utils.states import OnchainTasks
from web3tg.utils.models import chains
from web3tg.utils.bot_commands import edit_dialog_message
from web3tg.utils.onchain_tasks import get_onchain_transfer_info

router = Router()


@router.message(OnchainTasks.TRANSFER_SOURCE)
async def get_source_profile(message: Message, state: FSMContext):
    data = await state.get_data()
    await message.delete()
    if not message.text.isdigit():
        return
    source_profile_id = int(message.text)
    await state.update_data(source_profile_id=source_profile_id)
    source_chain = data.get('source_chain', None)
    if source_chain:
        text = f'<b>1. Source: {source_profile_id} ({source_chain}).\n2. Введите destination id профиля и выберите destination chain</b>'
        await state.set_state(OnchainTasks.TRANSFER_DESTINATION)
    else:
        text = f'<b>1. Source: {source_profile_id}. Выберите source chain</b>'
    await edit_dialog_message(data['dialog_message'], text, buttons=chains)


@router.message(OnchainTasks.TRANSFER_DESTINATION)
async def get_destination_profile(message: Message, state: FSMContext):
    data = await state.get_data()
    await message.delete()
    if not message.text.isdigit():
        return
    destination_profile_id = int(message.text)
    await state.update_data(destination_profile_id=destination_profile_id)
    destination_chain = data.get('destination_chain', None)
    if destination_chain:
        text = await get_onchain_transfer_info(state)  # FIXME
    else:
        text = f'<b>2. Destination: {destination_profile_id}. Выберите destination chain</b>'
    await edit_dialog_message(data['dialog_message'], text, buttons=chains)
