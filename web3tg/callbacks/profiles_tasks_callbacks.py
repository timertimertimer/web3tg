from typing import TYPE_CHECKING

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from web3tg.keyboards import fabrics
from web3tg.utils import ProfilesTasks, edit_dialog_message, show_profiles_tasks, ProfilesInteraction

if TYPE_CHECKING:
    from web3db import Profile

router = Router()


@router.callback_query(fabrics.InlineCallbacks.filter(F.action == 'Profiles'))
async def profiles_tasks(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    await show_profiles_tasks(call.message, state)


@router.callback_query(ProfilesTasks.CHOOSE_TASK, fabrics.InlineCallbacks.filter(F.action == 'Change social'))
async def tasks_menu(
        call: CallbackQuery,
        callback_data: fabrics.InlineCallbacks,
        state: FSMContext
):
    await state.set_state(ProfilesTasks.CHANGE_PROFILES_MODEL)
    await edit_dialog_message(
        call.message,
        '<b>Profiles. Change social</b>\nChoose social',
        ['Twitter', 'Discord', 'Github', 'Email']
    )


@router.callback_query(
    ProfilesTasks.CHANGE_PROFILES_MODEL,
    fabrics.InlineCallbacks.filter(F.action.in_(['Twitter', 'Discord', 'Github', 'Email']))
)
async def change_profiles_model(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    social = callback_data.action
    await state.update_data(social=social)
    await state.update_data(delete_models_email=False)
    await state.update_data(delete_model=False)
    buttons = [f'Delete {social} [NO]'] + ([f'Delete {social}\'s email [NO]'] if social != 'Email' else [])
    await state.set_state(ProfilesTasks.INPUT_PROFILES_IDS_TO_CHANGE_MODEL)
    await edit_dialog_message(
        call.message,
        f'<b>Profiles. Change social. {social}</b>\nВведите id профилей',
        reply_markup=fabrics.get_inline_buttons(buttons + ['Таски'], adjust=1)
    )


@router.callback_query(
    ProfilesTasks.INPUT_PROFILES_IDS_TO_CHANGE_MODEL,
    fabrics.InlineCallbacks.filter(F.action.in_(
        [f'Delete {social}\'s email [NO]' for social in ['Twitter', 'Discord', 'Github']]
        + [f'Delete {social}\'s email [YES]' for social in ['Twitter', 'Discord', 'Github']]
        + [f'Delete {social} [NO]' for social in ['Twitter', 'Discord', 'Github', 'Email']]
        + [f'Delete {social} [YES]' for social in ['Twitter', 'Discord', 'Github', 'Email']]
    ))
)
async def change_profiles_model_extra(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    data = await state.get_data()
    social = data['social']
    if 'email' in callback_data.action:
        delete_models_email = not data['delete_models_email']
        delete_model = data['delete_model']
    else:
        delete_model = not data['delete_model']
        delete_models_email = data['delete_models_email']
    await state.update_data(delete_models_email=delete_models_email)
    await state.update_data(delete_model=delete_model)
    buttons = [f'Delete {social} [{"YES" if delete_model else "NO"}]'] + (
        [f'Delete {social}\'s email [{"YES" if delete_models_email else "NO"}]'] if social != 'Email' else []
    )
    await edit_dialog_message(
        call.message,
        f'<b>Profiles. Change social. {social}</b>\nВведите id профилей',
        reply_markup=fabrics.get_inline_buttons(buttons + ['Таски'], adjust=1)
    )


@router.callback_query(ProfilesTasks.START_CHANGE_PROFILES_MODEL, fabrics.InlineCallbacks.filter(F.action == 'Запуск'))
async def start_change_profiles_model(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    data = await state.get_data()
    social = data['social']
    profiles_ids = data['profiles_ids']
    delete_model = data['delete_model']
    delete_models_email = data['delete_models_email']
    edited_model = await ProfilesInteraction.change_profile_model(
        social=social,
        delete_model=delete_model,
        delete_models_email=delete_models_email,
        profiles_ids=profiles_ids
    )
    if edited_model:
        s = f'{social} профилей {profiles_ids} изменен'
    else:
        s = f'Не удалось изменить {social} профилей {profiles_ids}'
    await call.message.answer(s)
    await show_profiles_tasks(call.message, state)


@router.callback_query(ProfilesTasks.CHOOSE_TASK, fabrics.InlineCallbacks.filter(F.action == '2FA'))
async def two_factor(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    await state.set_state(ProfilesTasks.TWO_FACTOR)
    await edit_dialog_message(call.message, '<b>Profiles. 2FA</b>\nChoose social', ['Twitter'])


@router.callback_query(ProfilesTasks.TWO_FACTOR, fabrics.InlineCallbacks.filter(F.action == 'Twitter'))
async def twitter_two_factor(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    social = callback_data.action
    await state.update_data(social=social)
    profiles: list[Profile] = await ProfilesInteraction.get_profiles_models_with_2fa(social)
    await state.update_data(profiles_with_totp=profiles)
    await edit_dialog_message(
        call.message,
        f'<b>Profiles. 2FA. {social}</b>\nChoose profile',
        buttons=[str(profile.id) for profile in profiles]
    )


@router.callback_query(ProfilesTasks.TWO_FACTOR, fabrics.InlineCallbacks.filter(F.action.isdigit()))
async def twitter_two_factor_code(call: CallbackQuery, callback_data: fabrics.InlineCallbacks, state: FSMContext):
    data = await state.get_data()
    social = data['social']
    profiles_with_totp = data['profiles_with_totp']
    code = await ProfilesInteraction.get_2fa_code(
        social,
        [profile for profile in profiles_with_totp if profile.id == int(callback_data.action)][0]
    )
    await edit_dialog_message(
        call.message,
        f'<b>Profiles. 2FA. {social}</b>\nChoose profile.\n{callback_data.action} code - <i>{code}</i>',
        buttons=[str(profile.id) for profile in profiles_with_totp]
    )
