import os
import pyotp
from dotenv import load_dotenv

from web3db import DBHelper, Profile
from web3db.core import ModelType

from utils import models

load_dotenv()
db = DBHelper(os.getenv('CONNECTION_STRING'))


async def get_models_with_2fa(model: ModelType) -> list[ModelType]:
    await db.get_profiles_with_totp_by_model(model)


class ProfilesInteraction:

    @staticmethod
    async def change_profile_model(
            social: str,
            profiles_ids: set[int],
            delete_model: bool = False,
            delete_models_email: bool = False
    ) -> ModelType | None:
        return await db.change_profile_model(list(profiles_ids), models[social], delete_model, delete_models_email)

    @staticmethod
    async def get_profiles_models_with_2fa(social: str) -> list[ModelType]:
        return await db.get_profiles_with_totp_by_model(models[social])

    @staticmethod
    async def get_2fa_code(social: str, profile: Profile) -> str:
        return pyotp.TOTP(getattr(profile, models[social].__name__.lower()).totp_secret).now()
