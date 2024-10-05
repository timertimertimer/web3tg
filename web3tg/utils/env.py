import os
from dotenv import load_dotenv

load_dotenv()


class Web3tgENV:
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    CONNECTION_STRING = os.getenv("CONNECTION_STRING")

    CAPSOLVER_API_KEY = os.getenv("CAPSOLVER_API_KEY")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMINS = os.getenv("ADMINS")

    USER_AGENT = os.getenv("USER_AGENT")
