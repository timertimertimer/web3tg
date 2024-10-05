from aiogram.fsm.state import StatesGroup, State


class SocialTasks(StatesGroup):
    CHOOSE_SOCIAL = State()
    CHOOSE_TASK = State()
    SETTINGS = State()

    CHOOSE_ACCOUNTS = State()
    CHOOSE_INPUT_DATA_TYPE = State()

    INPUT_SOURCES = State()
    INPUT_DATA = State()
    PROCESS_FILE = State()

    START_TASKS = State()


class ProfilesTasks(StatesGroup):
    CHOOSE_TASK = State()

    CHANGE_PROFILES_MODEL = State()
    INPUT_PROFILES_IDS_TO_CHANGE_MODEL = State()
    START_CHANGE_PROFILES_MODEL = State()

    EDIT_PROFILES_MODEL = State()

    TWO_FACTOR = State()


class OnchainTasks(StatesGroup):
    CHOOSE_TASK = State()

    TRANSFER_SOURCE = State()
    TRANSFER_DESTINATION = State()

    CHOOSE_STATS = State()


class ZoraState(StatesGroup):
    GET_LINKS = State()
    CHOOSE_CHAIN = State()
