from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from web3tg.keyboards import fabrics
from web3tg.utils import OnchainTasks, get_onchain_transfer_info, show_onchain_tasks, edit_dialog_message
from web3tg.utils.models import chains

router = Router()


@router.callback_query(fabrics.InlineCallbacks.filter(F.action == 'Onchain tasks'))
async def onchain_tasks(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    await show_onchain_tasks(call.message, state)


@router.callback_query(OnchainTasks.CHOOSE_TASK, fabrics.InlineCallbacks.filter(F.action == 'Transfer'))
async def transfer(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    text = f'<b>1. Введите source id профиля и выберите source chain</b>'
    onchain_transfer_info_text = await get_onchain_transfer_info()

    await edit_dialog_message(call.message, text, buttons=chains)
    await state.set_state(OnchainTasks.TRANSFER_SOURCE)


@router.callback_query(OnchainTasks.TRANSFER_SOURCE, fabrics.InlineCallbacks.filter(F.action.in_(chains)))
async def source_chain(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    data = await state.get_data()
    await state.update_data(source_chain=callback_data.action)
    source_profile_id: int = data.get('source_profile_id')
    if source_profile_id:
        text = f'<b>2. Source: {source_profile_id} ({source_chain}). Введите destination id профиля</b>'
        await edit_dialog_message(call.message, text, buttons=chains)
        await state.set_state(OnchainTasks.TRANSFER_DESTINATION)
    else:
        text = f'<b>1. Source chain: {callback_data.action}. Введите source id профиля</b>'
        await edit_dialog_message(call.message, text)


@router.callback_query(OnchainTasks.TRANSFER_DESTINATION, fabrics.InlineCallbacks.filter(F.action.in_(chains)))
async def destination_chain(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    await state.update_data(destination_chain=callback_data.action)
    text = '<b>Введите destination id профиля</b>'
    await edit_dialog_message(call.message, text)

    data = await state.get_data()
    await state.update_data(destination_chain=callback_data.action)
    destination_profile_id: int = data.get('destination_profile_id')
    if destination_profile_id:
        await show_transfer_info(state)
    else:
        text = f'<b>2. Destination chain: {callback_data.action}. Введите destination id профиля</b>'
        await edit_dialog_message(call.message, text)


@router.callback_query(OnchainTasks.CHOOSE_TASK, fabrics.InlineCallbacks.filter(F.action == 'Stats'))
async def stats(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    await edit_dialog_message(call.message, '<b>Выберите</b>', onchain_stats_buttons)
    await state.set_state(OnchainTasks.CHOOSE_STATS)


@router.callback_query(OnchainTasks.CHOOSE_STATS, fabrics.InlineCallbacks.filter(F.action == 'ETH гретые'))
async def eth_warmed(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    ...
