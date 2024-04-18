from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from web3tg.keyboards import *
from web3tg.utils import help_string, SocialTasks

router = Router()


@router.message(Command('help'))
async def help_(message: Message) -> None:
    await message.answer(help_string)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.set_state(SocialTasks.CHOOSE_SOCIAL)
    if message.text != '/start':  # callback
        fn = message.edit_text
    else:
        fn = message.answer
    await fn(
        f'<b>Choose</b>',
        reply_markup=fabrics.get_inline_buttons(['Social tasks', 'Profiles',
                                                 # 'Zora'
                                                 ])
    )
