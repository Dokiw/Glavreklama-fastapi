from typing import Optional, Dict, Any
import json
import aiohttp
from aiohttp import BasicAuth, ClientTimeout
from app.core.config import settings
from app.handlers.auth.interfaces import AsyncRoleService
from app.handlers.session.dependencies import SessionServiceDep
from app.handlers.session.schemas import CheckSessionAccessToken
from app.handlers.gpt.interfaces import AsyncGPTService


class SqlAlchemyGPT(AsyncGPTService):
    def __init__(self, role_service: AsyncRoleService, session_service: SessionServiceDep):
        self.role_service = role_service
        self.session_service = session_service
        # Прокси и аутентификация
        self.proxy_url = settings.proxy_url
        self.proxy_auth = BasicAuth(settings.proxy_username, settings.proxy_password) \
            if settings.proxy_username else None
        # Таймаут на весь запрос
        self.timeout = ClientTimeout(total=30)

    async def create_gtp_promt(
        self,
        model: str,
        system_prompt: str,
        image_url: Optional[str],
        check_data: CheckSessionAccessToken
    ) -> Dict[str, Any]:

        # 1) Проверки доступа
        await self.role_service.is_admin(check_data.user_id)
        await self.session_service.validate_access_token_session(check_data)

        # 2) Данные для запроса OpenAI
        url = "https://api.openai.com/v1/chat/completions"
        api_key = settings.CHATGPT_API

        if not api_key:
            raise RuntimeError("OPENAI API key not set (Settings.CHATGPT_API)")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if image_url:
            messages.append({
                "role": "user",
                "content": f"Посмотри на изображение по ссылке и опиши его: {image_url}"
            })

        payload = {
            "model": model,
            "messages": messages,
            "max_completion_tokens": 1024,
        }

        try:
            # --- ВАЖНО: proxy передаётся именно здесь, напрямую в post ---
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    proxy=self.proxy_url,
                    proxy_auth=self.proxy_auth
                ) as resp:
                    status = resp.status
                    text = await resp.text()
                    try:
                        body = json.loads(text)
                    except ValueError:
                        body = {"text": text}

                    return {
                        "status": status,
                        "response": body,
                        "request": {
                            "url": url,
                            "headers": {k: ("REDACTED" if k.lower() == "authorization" else v) for k, v in headers.items()},
                            "json": payload,
                        },
                        "api_key": api_key,
                        "proxy": self.proxy_url,
                        "proxy_auth": self.proxy_auth,
                        "error": status >= 400
                    }

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
                "api_key": api_key,
                "proxy": self.proxy_url,
                "proxy_auth": self.proxy_auth,
            }

        except Exception as e:
            return {
                "status": None,
                "response": None,
                "error": True,
                "error_message": f"Unexpected error: {e}",
            }
