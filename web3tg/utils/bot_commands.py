from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup

from web3tg.keyboards import fabrics
from web3tg.utils.models import socials_menu_buttons, profiles_menu_buttons, onchain_menu_buttons
from web3tg.utils.states import SocialTasks, ProfilesTasks, OnchainTasks
from web3tg.utils.extra import get_social_tasks_buttons

__all__ = [
    "edit_dialog_message",
    "show_social_tasks",
    "show_profiles_tasks",
    "show_onchain_tasks"
]


async def edit_dialog_message(
        message: Message,
        text: str,
        buttons: list = None,
        reply_markup: InlineKeyboardMarkup = None
):
    buttons = buttons or []
    reply_markup = reply_markup or fabrics.get_inline_buttons(buttons + ['Таски'])
    await message.edit_text(text, reply_markup=reply_markup)


async def show_social_tasks(message: Message, social: str, state: FSMContext):
    buttons = list(get_social_tasks_buttons(social)) + list(socials_menu_buttons)
    await edit_dialog_message(
        message,
        f'<b>Social tasks. {social.capitalize()} таски</b>',
        reply_markup=fabrics.get_inline_buttons(buttons)
    )
    await state.set_state(SocialTasks.CHOOSE_TASK)


async def show_profiles_tasks(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(dialog_message=message)
    await edit_dialog_message(
        message,
        f'<b>Profiles tasks</b>\nChoose',
        reply_markup=fabrics.get_inline_buttons(profiles_menu_buttons)
    )
    await state.set_state(ProfilesTasks.CHOOSE_TASK)


async def show_onchain_tasks(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(dialog_message=message)
    await edit_dialog_message(
        message,
        '<b>Onchain tasks</b>\nChoose',
        reply_markup=fabrics.get_inline_buttons(onchain_menu_buttons)
    )
    await state.set_state(OnchainTasks.CHOOSE_TASK)
