import hashlib
import hmac
import json
from urllib.parse import unquote_plus, parse_qsl, unquote, parse_qs
from fastapi import HTTPException
from typing import Dict, Any
from datetime import datetime, timezone
from app.core.config import settings  # settings.BOT_TOKEN


async def parse_init_data(init_data: str) -> dict:
    return dict(parse_qs(init_data))


async def check_telegram_init_data(init_data: str, bot_token: str) -> dict:
    parsed = await parse_init_data(init_data)

    if not bot_token:
        raise HTTPException(status_code=500, detail="BOT_TOKEN не задан")

    hash_value = parsed['hash'][0]
    del parsed['hash']

    # формируем data_check_string для проверки хэша
    data_check_arr = []
    for key, value in parsed.items():
        data_check_arr.append(f"{key}={value[0]}")

    data_check_arr.sort()
    data_check_string = "\n".join(data_check_arr)

    # секретный ключ = HMAC-SHA256(botToken, "WebAppData")
    secret_key = hmac.new(
        "WebAppData".encode('utf-8'),
        bot_token.encode('utf-8'),
        hashlib.sha256
    ).digest()

    # считаем хэш от строки
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    if computed_hash != hash_value:
        raise HTTPException(status_code=400, detail="Invalid tgWebAppData hash")

    # Преобразуем данные в удобный формат
    result = {}
    for key, value in parsed.items():
        if key == "user":
            # Декодируем JSON пользователя
            user_json = unquote(value[0])
            result[key] = json.loads(user_json)
        elif key == "auth_date":
            # Преобразуем timestamp в datetime
            result[key] = datetime.fromtimestamp(int(value[0]), tz=timezone.utc)
        else:
            # Остальные значения оставляем как есть
            result[key] = value[0]

    return result
