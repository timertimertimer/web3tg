from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class InlineCallbacks(CallbackData, prefix='social'):
    action: str


class ProfilesPagination(CallbackData, prefix='pag'):
    action: str
    page: int = None


def get_inline_buttons(buttons: list[str], adjust: int = 3) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    [builder.button(text=text, callback_data=InlineCallbacks(action=text)) for text in buttons]
    builder.adjust(adjust)
    return builder.as_markup()


def paginator(page: int = 0):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='⬅', callback_data=ProfilesPagination(
            action='prev', page=page).pack()),
        InlineKeyboardButton(text='Таски', callback_data=ProfilesPagination(
            action='Таски', page=page).pack()),
        InlineKeyboardButton(text='➡', callback_data=ProfilesPagination(
            action='next', page=page).pack()),
        width=3
    )
    return builder.as_markup()
