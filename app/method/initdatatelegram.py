import hmac
import hashlib
import json
import time
from typing import Any, Dict, Optional

from fastapi import HTTPException, status, Request

from app.core.config import settings


def _extract_raw_user_json_from_raw_body(raw_body: bytes) -> Optional[str]:
    """
    Попытка вытащить оригинальную подстроку JSON для "user": {...} из raw_body.
    Работает символьно, учитывает вложенные фигурные скобки и кавычки.
    Возвращает строку (без ведущ/зам символов), либо None.
    """
    s = raw_body.decode("utf-8", errors="replace")
    key = '"user"'
    idx = s.find(key)
    if idx == -1:
        return None
    # найти ':' после "user"
    idx_colon = s.find(":", idx + len(key))
    if idx_colon == -1:
        return None
    # перейти к первому значащему символу после :
    i = idx_colon + 1
    n = len(s)
    while i < n and s[i].isspace():
        i += 1
    if i >= n:
        return None
    if s[i] != "{":
        # если user не объект — вернуть до следующей запятой/скобки
        # но Telegram всегда присылает объект
        j = i
        while j < n and s[j] not in ",}]\n\r":
            j += 1
        return s[i:j].strip()
    # теперь i указывает на '{' — нужно найти соответствующую '}'
    depth = 0
    in_string = False
    escape = False
    j = i
    while j < n:
        ch = s[j]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    # включительно j
                    return s[i:j + 1]
        j += 1
    return None


async def validate_init_data_debug(
    init_data: Dict[str, Any],
    raw_body: Optional[bytes] = None,
    ttl: int = 300,
) -> Dict[str, Any]:
    """
    Диагностическая валидация:
      - пытаем вариации сериализации user (raw, json.dumps с/без sort_keys, ensure_ascii)
      - считаем хешы двумя способами (WebApp и LoginWidget)
      - возвращаем подробный report: список попыток, и итог.
    Возвращает словарь с большим отчётом.
    """
    report = {
        "valid": False,
        "reason": None,
        "received_hash": None,
        "auth_date": None,
        "ttl_ok": None,
        "attempts": [],  # список dict с подробностями каждой попытки
        "note": "Проверьте BOT_TOKEN, и по возможности используйте raw_body для точного совпадения JSON user.",
    }

    if not isinstance(init_data, dict):
        report["reason"] = "init_data не dict"
        return report

    if "hash" not in init_data:
        report["reason"] = "нет поля hash"
        return report
    if "auth_date" not in init_data:
        report["reason"] = "нет поля auth_date"
        return report

    received_hash = str(init_data["hash"])
    report["received_hash"] = received_hash

    # raw_user, если можем извлечь
    raw_user = None
    if raw_body is not None:
        raw_user = _extract_raw_user_json_from_raw_body(raw_body)

    # подготовим варианты представления user
    user_variants = {}

    # 1) если raw_user есть — попробуем её прямо (строка как пришла)
    if raw_user is not None:
        user_variants["raw_user_from_body"] = raw_user

    # 2) сериализация из parsed dict (несортированные ключи)
    u = init_data.get("user")
    if isinstance(u, dict):
        # compact JSON with ensure_ascii True/False, with/without sort_keys
        user_variants["json_ensure_ascii_true"] = json.dumps(u, separators=(",", ":"), ensure_ascii=True)
        user_variants["json_ensure_ascii_false"] = json.dumps(u, separators=(",", ":"), ensure_ascii=False)
        user_variants["json_sorted_keys"] = json.dumps(u, separators=(",", ":"), ensure_ascii=True, sort_keys=True)
    else:
        # если user уже строка (например, Body parser сохранил оригинал) — используем как есть
        user_variants["user_as_str"] = str(u)

    # подготовим остальные поля: для всех полей кроме hash и signature используем
    # сериализацию значений, где dict -> json.dumps(..., ensure_ascii=True)
    excluded = {"hash", "signature"}
    base_values = {}
    for k, v in init_data.items():
        if k in excluded:
            continue
        if k == "user":
            continue
        if isinstance(v, dict):
            base_values[k] = json.dumps(v, separators=(",", ":"), ensure_ascii=True)
        else:
            base_values[k] = str(v)

    # секреты: попробуем оба варианта
    bot_token = settings.BOT_TOKEN
    if not bot_token:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Bot token not configured")

    secret_methods = {
        "webapp_hmac_WebAppData": hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest(),
        "login_sha256_bot_token": hashlib.sha256(bot_token.encode("utf-8")).digest(),
    }

    # Перебор вариантов
    for secret_name, secret_key in secret_methods.items():
        for uv_name, uv_value in user_variants.items():
            # соберём data_for_check с текущим user-вариантом
            data_for_check = dict(base_values)
            data_for_check["user"] = uv_value
            # keys sorted
            items = [f"{k}={data_for_check[k]}" for k in sorted(data_for_check.keys())]
            data_check_string = "\n".join(items)
            # вычислим хеш
            calc_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
            attempt = {
                "secret_method": secret_name,
                "user_variant": uv_name,
                "data_check_string": data_check_string,
                "secret_key_hex": secret_key.hex(),
                "calculated_hash": calc_hash,
                "match": hmac.compare_digest(calc_hash, received_hash),
                # полезно увидеть длину/байты
                "data_check_bytes_len": len(data_check_string.encode("utf-8")),
            }
            report["attempts"].append(attempt)
            if attempt["match"]:
                report["valid"] = True
                report["reason"] = "hash matched"
                # возвращаем первый успешный вариант
                report["matched_attempt"] = attempt
                break
        if report["valid"]:
            break

    # TTL check (покажем отдельно)
    try:
        auth_date = int(init_data.get("auth_date"))
        report["auth_date"] = auth_date
        report["ttl_ok"] = (time.time() - auth_date) <= ttl
        if not report["ttl_ok"] and not report["valid"]:
            report["reason"] = (report["reason"] or "") + " | auth_date older than TTL"
    except Exception as e:
        report["auth_date_error"] = str(e)

    if not report["valid"] and report["reason"] is None:
        report["reason"] = "Ни один вариант не совпал. Проверьте BOT_TOKEN или формат входных данных."

    return report
