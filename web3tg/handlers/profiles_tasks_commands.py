from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from web3tg.utils import ProfilesTasks
from web3tg.utils.bot_commands import edit_dialog_message

router = Router()


@router.message(ProfilesTasks.INPUT_PROFILES_IDS_TO_CHANGE_MODEL)
async def profiles_ids_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    social = data['social']
    profiles = set(message.text.split())
    await message.delete()
    if all(map(str.isdigit, profiles)):
        await state.update_data(profiles_ids={int(el) for el in profiles})
        await state.set_state(ProfilesTasks.START_CHANGE_PROFILES_MODEL)
        text = (
                   f'<b>Profiles. Change social. {social}</b>\n'
                   f'IDs: <i>{profiles}</i>\n'
                   f'Удалить текущий аккаунт - <i>{"YES" if data["delete_model"] else "NO"}</i>\n'
               ) + (
                   f'Удалить почту, привязанную к текущему аккаунту - '
                   f'<i>{"YES" if data["delete_models_email"] else "NO"}</i>'
                   if social != 'Email' else ''
               )
        await edit_dialog_message(data['dialog_message'], text, buttons=['Запуск'])
    else:
        await edit_dialog_message(
            data['dialog_message'],
            f'<b>Profiles. Change social. {social}</b>\nНеверно. Введите id профилей еще раз'
        )
