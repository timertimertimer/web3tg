from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from web3tg.keyboards import fabrics
from web3tg.utils.bot_commands import edit_dialog_message
from web3tg.utils.states import ZoraState
from web3tg.utils.models import chains

router = Router()


@router.callback_query(fabrics.InlineCallbacks.filter(F.action == 'Zora'))
async def zora(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    await edit_dialog_message(
        call.message, 'Write links from zora.co', reply_markup=fabrics.get_inline_buttons(['Меню'])
    )
    await state.set_state(ZoraState.GET_LINKS)


@router.callback_query(ZoraState.CHOOSE_CHAIN, fabrics.InlineCallbacks.filter(F.action.in_(list(map(str, chains)))))
async def chains_callback(call: CallbackQuery, callback_data: fabrics.ZoraCallbacks, state: FSMContext):
    data = await state.get_data()
    chains = data['chains']
    current_chain = callback_data.chain
    chains[current_chain] = not chains[current_chain]
    await state.update_data(chains=chains)
    await call.message.edit_text(
        'Choose chain', reply_markup=fabrics.get_chain_choice_buttons(chains, ['Reset', 'Next'])
    )


@router.callback_query(ZoraState.CHOOSE_CHAIN, fabrics.InlineCallbacks.filter(F.action == 'Next'))
async def all_info(call: CallbackQuery, callback_data: fabrics.ZoraCallbacks, state: FSMContext):
    await call.message.edit_text('Collecting info...', reply_markup=fabrics.get_start_button())
    data = await state.get_data()
    links = data['links']
    chains = data['chains']
    for link, amount in links.items():
        ...
    await call.message.edit_text('', reply_markup=fabrics.get_start_button())
