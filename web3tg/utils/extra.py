from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from web3db.models import RemoteProfile as Profile

from web3tg.utils import twitter_actions


def get_social_tasks_buttons(social: str) -> dict:
    return {'Twitter': twitter_actions}[social]


def get_text_for_current_page_profiles(profiles: list['Profile'], page: int):
    text = '<b>Введите id профилей</b>\n'
    for profile_id, login, ready in profiles[page * 10:(page + 1) * 10]:  # type: Profile
        line = f'{profile_id} | {login}'
        line = f'<b><i>{line}</i></b>' if ready else line
        text += line + '\n'
    return text
