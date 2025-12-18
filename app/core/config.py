import logging
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from yookassa import Webhook

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
    DB_ENGINE: str
    DB_TYPE: str

    WEBHOOK_URL: str

    proxy_url: str

    proxy_username: str
    proxy_password: str

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    CHATGPT_API: str

    SECRET_KEY: str
    SHOP_ID: str

    # === Настройки (лучше читать из переменных окружения) ===
    SMTP_HOST: str
    SMTP_PORT: str
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    FROM_ADDRESS: str
    CONFIRMATION_BASE_URL: str

    # Секрет для подписи токенов (обязательно заменить на безопасный секрет)
    TOKEN_SECRET: str
    TOKEN_SALT: str




    class Config:
        env_file = ENV_PATH  # чтобы pydantic тоже читал из .env


settings = Settings()

# Логируем основные переменные (без пароля!)
logger.info(f"DB_USER={settings.DB_USER}")
logger.info(f"DB_NAME={settings.DB_NAME}")
logger.info(f"DB_HOST={settings.DB_HOST}:{settings.DB_PORT}")
