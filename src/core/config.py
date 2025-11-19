import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    DB_HOST: str | None = os.getenv("DB_HOST")
    DB_USER: str | None = os.getenv("DB_USER")
    DB_PASS: str | None = os.getenv("DB_PASS")
    INSTANCE_CONNECTION_NAME: str | None = os.getenv("INSTANCE_CONNECTION_NAME")
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
