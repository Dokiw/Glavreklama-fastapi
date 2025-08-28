import logging
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# 🔧 Настройка логгера
logger = logging.getLogger("settings")
logger.setLevel(logging.INFO)

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # glavreklama/
ENV_PATH = BASE_DIR / ".env"

# Загружаем .env
if load_dotenv(dotenv_path=ENV_PATH):
    logger.info(f".env файл загружен: {ENV_PATH}")
else:
    logger.warning(f".env файл НЕ найден по пути: {ENV_PATH}")

class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str
    BOT_TOKEN: str

    class Config:
        env_file = ENV_PATH  # чтобы pydantic тоже читал из .env

settings = Settings()

# Логируем основные переменные (без пароля!)
logger.info(f"DB_USER={settings.DB_USER}")
logger.info(f"DB_NAME={settings.DB_NAME}")
logger.info(f"DB_HOST={settings.DB_HOST}:{settings.DB_PORT}")
