from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from web3tg.handlers.basic_commands import start as main_start

from web3tg.keyboards import fabrics
from web3tg.utils import (
    SocialTasks, show_social_tasks, show_profiles_tasks, get_text_for_current_page_profiles, edit_dialog_message
)

router = Router()


@router.callback_query(fabrics.InlineCallbacks.filter(F.action == 'Меню'))
async def return_to_main_menu(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext) -> None:
    await state.clear()
    await main_start(call.message, state)


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


@router.callback_query(
    SocialTasks.INPUT_PROFILES_IDS,
    fabrics.ProfilesPagination.filter(F.action.in_(['next', 'prev']))
)
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
