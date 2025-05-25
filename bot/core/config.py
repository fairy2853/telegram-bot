from pathlib import Path
from pydantic_settings import BaseSettings
from .logging_config import setup_logging


class Setting(BaseSettings):
    ENVIRONMENT: str = "dev"

    # General
    VERSION: str = "0.0.1"
    PROJECT_NAME: str = "insurance-bot"

    ROOT_DIR: Path = Path(__file__).parent.parent.parent

    # Google
    GENAI_API_KEY: str

    # Telegram
    TELEGRAM_BOT_TOKEN: str

    # MINDEE
    MINDEE_API_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


setup_logging()
settings = Setting()
