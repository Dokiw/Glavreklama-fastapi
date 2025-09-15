import hashlib
import json
import os
from typing import Optional, List, Dict, Any
import time
from datetime import datetime, timedelta, UTC

import aiohttp

from app.core.config import settings
from app.handlers.auth.interfaces import AsyncRoleService
from app.handlers.coupon.interfaces import AsyncCouponService
from app.handlers.coupon.UOW import SqlAlchemyUnitOfWork
from app.handlers.coupon.schemas import CreateCoupon, OutCoupon, CreateCouponService
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.core.abs.unit_of_work import IUnitOfWorkWallet, IUnitOfWorkCoupon
from app.handlers.gpt.interfaces import AsyncGPTService
from app.handlers.session.dependencies import SessionServiceDep
from app.handlers.session.schemas import CheckSessionAccessToken
from app.method.decorator import transactional


class SqlAlchemyGPT(AsyncGPTService):
    def __init__(self, role_service: AsyncRoleService, session_service: SessionServiceDep):
        self.session_service = session_service
        self.role_service = role_service

    async def create_gtp_promt(
        self,
        model: str,
        system_prompt: str,
        image_url: Optional[str],
        check_data: CheckSessionAccessToken
    ) -> Dict[str, Any]:
        # 1) проверки доступа
        await self.role_service.is_admin(check_data.user_id)
        await self.session_service.validate_access_token_session(check_data)

        # 2) собираем данные для запроса к OpenAI
        url = "https://api.openai.com/v1/chat/completions"

        api_key = settings.CHATGPT_API
        if not api_key:
            raise RuntimeError("OPENAI API key not set (Settings.CHATGPT_API)")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Формируем messages: system + user
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Гарантируем, что всегда есть пользовательское сообщение с content
        if image_url:
            user_content = (
                "Посмотри на изображение по ссылке и опиши его: основные объекты, стиль, "
                "возможные текстовые элементы на картинке и любые примечательные детали.\n"
                f"{image_url}"
            )
            messages.append({"role": "user", "content": user_content})

        # Полезные параметры (проверь лимит токенов для выбранной модели)
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 1024,
        }

        # Подготовим пример curl — JSON экранируем безопасно
        curl_body = json.dumps(payload, ensure_ascii=False)
        # экранируем одинарные кавычки для вставки в одинарные quotes в оболочке
        curl_body_escaped = curl_body.replace("'", "\\'")
        curl_cmd = (
            "curl -X POST https://api.openai.com/v1/chat/completions "
            "-H 'Content-Type: application/json' "
            "-H 'Authorization: Bearer <OPENAI_API_KEY>' "
            f"-d '{curl_body_escaped}'"
        )

        timeout = aiohttp.ClientTimeout(total=30)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    status = resp.status
                    text = await resp.text()

                    # Пытаемся распарсить JSON; если не получается — возвращаем raw text
                    try:
                        body = json.loads(text)
                    except ValueError:
                        body = {"text": text}

                    result = {"status": status, "response": body, "request": {
                        "url": url,
                        # в возвращаемом описании запроса скрываем ключ
                        "headers": {k: ("REDACTED" if k.lower() == "authorization" else v) for k, v in headers.items()},
                        "json": payload,
                    }, "curl_example": curl_cmd, "error": status >= 400}

                    return result

        except aiohttp.ClientError as e:
            return {
                "status": None,
                "response": None,
                "error": True,
                "error_message": f"aiohttp.ClientError: {e}",
                "request": {
                    "url": url,
                    "headers": {k: ("REDACTED" if k.lower() == "authorization" else v) for k, v in headers.items()},
                    "json": payload,
                },
            }
        except Exception as e:
            return {
                "status": None,
                "response": None,
                "error": True,
                "error_message": f"Unexpected error: {e}",
            }
