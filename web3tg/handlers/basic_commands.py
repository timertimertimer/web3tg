from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from web3tg.keyboards import *
from web3tg.utils import SocialTasks

router = Router()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.set_state(SocialTasks.CHOOSE_SOCIAL)
    if message.text == '/start':
        fn = message.answer
    else:
        fn = message.edit_text  # callback
    await fn(
        f'<b>Choose</b>',
        reply_markup=fabrics.get_inline_buttons(['Social tasks', 'Profiles', 'Onchain tasks'])
    )
