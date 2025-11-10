from typing import Optional, Dict, Any
import json
import aiohttp
from aiohttp import BasicAuth, ClientTimeout
from app.core.config import settings
from app.handlers.auth.interfaces import AsyncRoleService
from app.handlers.gpt.schemas import OutGPTkey
from app.handlers.session.dependencies import SessionServiceDep, OauthClientServiceDep
from app.handlers.session.schemas import CheckSessionAccessToken
from app.handlers.gpt.interfaces import AsyncGPTService
from app.method.aes import encrypt
from fastapi import HTTPException, status


class SqlAlchemyGPT(AsyncGPTService):
    def __init__(self, role_service: AsyncRoleService, session_service: SessionServiceDep, oauth_client_service: OauthClientServiceDep):
        self.role_service = role_service
        self.session_service = session_service
        self.oauth_client_service = oauth_client_service

        # Прокси и аутентификация
        self.proxy_url = settings.proxy_url
        self.proxy_auth = BasicAuth(settings.proxy_username, settings.proxy_password) \
            if settings.proxy_username else None
        # Таймаут на весь запрос
        self.timeout = ClientTimeout(total=120)

    async def create_gtp_promt(
        self,
        model: str,
        system_prompt: str,
        image_url: Optional[str],
        check_data: CheckSessionAccessToken
    ) -> Dict[str, Any]:

        # 1) Проверки доступа
        #await self.role_service.is_admin(check_data.user_id)
        await self.session_service.validate_access_token_session(check_data)
        # 2) Данные для запроса OpenAI
        url = "https://api.openai.com/v1/responses"

        api_key = settings.CHATGPT_API

        if not api_key:
            raise RuntimeError("OPENAI API key not set (Settings.CHATGPT_API)")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        input_content = []

        if system_prompt:
            input_content.append({"type": "input_text", "text": system_prompt})

        if image_url:
            input_content.append({"type": "input_image", "image_url": image_url, "detail": "high"})

        payload = {
            "model": model,
            "input": [
                {
                    "role": "user",
                    "content": input_content
                }
            ],
            "max_output_tokens": 4096
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

    async def get_property_key(self, oauth_client: str, check_data: CheckSessionAccessToken) \
            -> OutGPTkey:
        try:
            # 1) Проверки доступа
            #await self.role_service.is_admin(check_data.user_id)
            await self.session_service.validate_access_token_session(check_data)

            oauth_client_data = await self.oauth_client_service.get_by_client_id_oauth(oauth_client)
            if oauth_client_data.is_confidential and not oauth_client_data.client_secret:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Нету доступа"
                )

            api_key = settings.CHATGPT_API
            aes_data = await encrypt(plaintext=api_key, password=oauth_client_data.client_secret)

            return OutGPTkey(
                user_id=check_data.user_id,
                data=aes_data
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )



