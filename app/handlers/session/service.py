import asyncio
import datetime
import hashlib
from datetime import time
import datetime as dt
from typing import Optional, List, cast

import hmac, logging


from fastapi import HTTPException, status, Depends
from sqlalchemy.exc import IntegrityError
import ipaddress
import asyncpg

from app.core.abs.unit_of_work import IUnitOfWorkSession
from app.models.sessions.models import Session as SessionModel, RefreshToken as RefreshTokenModel, \
    OAuthClient as OAuthClientModel

from app.handlers.session.interfaces import AsyncSessionRepository, AsyncRefreshTokenRepository, \
    AsyncOauthClientRepository, AsyncRefreshTokenService, AsyncOauthClientService, AsyncSessionService
from app.handlers.session.schemas import OpenSession, OutSession, CheckOauthClient, CreateOauthClient, OutOauthClient, \
    CheckSessionAccessToken, CheckSessionRefreshToken, OutRefreshToken, UpdateOauthClient, CreateRefreshToken, \
    UpdateRefreshToken, RefreshSession, LogoutSession




# todo: заменить генерацию токена на безопасную для продакшена
class SqlAlchemyServiceSession(AsyncSessionService):
    def __init__(self, uow: IUnitOfWorkSession, refresh_service: AsyncRefreshTokenService):
        self.uow = uow
        self.refresh_service = refresh_service

    async def open_session(self, session_data: OpenSession) -> OutSession:
        try:
            async with self.uow:

                # Создаем сессию
                session = await self.uow.sessions.open_session(session_data)

                # Создаем refresh token

                session_id: int = session.id
                expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)

                refresh_token = await self.refresh_service.create_refresh_token(session_id=session_id,
                                                                                expires_at=expires_at)

                # Обновляем сессию
                session.refresh_token = refresh_token.token_hash

                # Коммитим транзакцию
                await self.uow.commit()
                return session
        except IntegrityError as e:
            # Откатываем транзакцию при ошибке целостности
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка целостности данных при создании сессии"
            )
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            # Откатываем транзакцию при любой другой ошибке
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

    async def close_session(self, id_session: int) -> None:
        try:
            async with self.uow:
                await self.uow.sessions.close_session(id_session)

                await self.uow.commit()
        except IntegrityError as e:
            pgcode = getattr(getattr(e, "orig", None), "pgcode", None)
            if pgcode == "23505":  # unique_violation
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Нарушено уникальное ограничение"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка целостности данных"
            )
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)} -- тут 3"
            )

    async def validate_access_token_session(self, check_access_token_data: CheckSessionAccessToken) -> Optional[
        OutSession]:
        try:
            async with self.uow:
                session = await self.uow.sessions.get_by_id_session_refresh(check_access_token_data.id)

                if session is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Отсутствует данные"
                    )

                if session.user_id != check_access_token_data.user_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Ошибка целостности данных"
                    )
                if session.access_token != check_access_token_data.access_token:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Ошибка целостности данных"
                    )

                if session.ip_address and check_access_token_data.ip_address:
                    session_net = ipaddress.ip_network(f"{session.ip_address}/24", strict=False)
                    current_ip = ipaddress.ip_address(check_access_token_data.ip_address)
                    if current_ip not in session_net:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ошибка целостности данных")

                if session.user_agent != check_access_token_data.user_agent:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Ошибка целостности данных"
                    )

                timestamp = str(time()).encode()

                session.access_token = hashlib.sha256(timestamp).hexdigest()

                session_data = RefreshSession(
                    **session.model_dump(exclude={
                        "refresh_token", "is_active", "logged_out_at",
                        "created_at", "last_used_at"
                    }),
                    refresh_token=session.refresh_token,  # если есть
                    id_address=session.ip_address,  # мэппинг IP
                )

                session = await self.uow.sessions.refresh_session(session_data)

                await self.uow.commit()
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)} -- тут 2"
            )

        return session

    async def validate_refresh_token_session(
            self, check_refresh_token_data: CheckSessionRefreshToken
    ) -> OutSession:
        try:
            async with self.uow:
                session = await self.uow.sessions.get_by_id_user_session(check_refresh_token_data.user_id)
                if session is None:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Отсутствует данные")

                refresh_datas = await self.refresh_service.get_by_id_session_refresh(session.id)

                if not refresh_datas:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Отсутствует данные")

                # создаём задачи для параллельной проверки токенов
                tasks = [
                    self.refresh_service.check(rd.id, check_refresh_token_data.refresh_token)
                    for rd in refresh_datas if not rd.revoked
                ]

                # запускаем все проверки параллельно
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # берём первый успешный токен
                refresh_data: Optional[OutRefreshToken] = None
                for r in results:
                    if isinstance(r, HTTPException):
                        continue
                    refresh_data = r
                    break

                if refresh_data is None:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail=f"Нет действительного refresh токена -- {print([r for r in results])}")

                # Проверка пользователя
                if session.user_id != check_refresh_token_data.user_id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ошибка целостности данных")

                # Проверка IP
                if session.ip_address and check_refresh_token_data.ip_address:
                    import ipaddress
                    session_net = ipaddress.ip_network(f"{session.ip_address}/24", strict=False)
                    current_ip = ipaddress.ip_address(check_refresh_token_data.ip_address)
                    if current_ip not in session_net:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ошибка целостности данных")

                # Проверка User-Agent
                if session.user_agent and check_refresh_token_data.user_agent:
                    if session.user_agent != check_refresh_token_data.user_agent:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ошибка целостности данных")

                # Подставляем «живой» токен
                session.refresh_token = refresh_data.token_hash
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

        return session

    async def get_by_id_user_session(self, id_user: int) -> Optional[OutSession]:
        try:
            async with self.uow:
                session: Optional[OutSession] = await self.uow.sessions.get_by_id_session_refresh(id_user)

                if session is None:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Отсутствует данные")
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

        return session

    async def get_by_access_token_session(self, access_token: str) -> Optional[OutSession]:
        try:
            async with self.uow:
                session: Optional[OutSession] = await self.uow.sessions.get_by_access_token_session(access_token)

                if session is None:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Отсутствует данные")
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )
        return session

    async def logout_session(self, logout_data: LogoutSession) -> Optional[OutSession]:
        try:
            async with self.uow:
                session = await self.uow.sessions.deactivate_by_token_ip_ua(
                    access_token=logout_data.access_token,
                    id_user=logout_data.user_id,
                    ip=logout_data.id_address,
                    user_agent=logout_data.user_agent,
                )

                if session is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Ошибка целостности данных"
                    )
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

        return session


class SqlAlchemyServiceRefreshToken(AsyncRefreshTokenService):
    def __init__(self, uow: IUnitOfWorkSession):
        self.uow = uow

    @staticmethod
    async def _to_dto(m: "RefreshTokenModel") -> OutRefreshToken:
        if m is None:
            raise TypeError("_to_dto получил None")
        if isinstance(m, type):
            raise TypeError(f"_to_dto получил класс {m!r}, ожидается экземпляр Session")

        return OutRefreshToken(
            id=m.id,
            session_id=m.session_id,
            revoked=m.revoked,
            created_at=m.created_at,
            expires_at=m.expires_at,
            used_at=m.used_at,
            token_hash=m.token_hash,
        )

    async def create_refresh_token(self, session_id: int, expires_at: datetime) -> OutRefreshToken:
        try:
            async with self.uow:
                refresh_data: OutRefreshToken = await self.uow.refresh_tokens.create_refresh_token(CreateRefreshToken(
                        session_id=session_id,
                        expires_at=expires_at if expires_at else None
                    )
                )

                await self.uow.commit()

        except IntegrityError as e:
            # Проверяем код ошибки PostgreSQL (уникальное ограничение)
            pgcode = await getattr(getattr(e, "orig", None), "pgcode", None)
            if pgcode == "23505":  # unique_violation
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Нарушено уникальное ограничение"
                )

            # Если другая IntegrityError — пробрасываем как общую
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка целостности данных"
            )
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

        return refresh_data

    async def check(self, id_refresh_token: int, refresh_token: str) -> Optional[OutRefreshToken]:
        try:
            async with self.uow:
                refresh_data = await self.uow.refresh_tokens.get_by_id_refresh_token(id_refresh_token)

                if refresh_data is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Отсутствует данные"
                    )

                if refresh_data.token_hash != hashlib.sha256(refresh_token.encode()).hexdigest():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ошибка целостности данных -------- {refresh_data} и {hashlib.sha256(refresh_token.encode()).hexdigest()} "
                    )

                if refresh_data.revoked:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ошибка целостности данных"
                    )

                if refresh_data.expires_at < dt.datetime.now(dt.timezone.utc):
                    refresh_data.revoked = True
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ошибка целостности данных"
                    )

                update_dto = UpdateRefreshToken(
                    id=refresh_data.id,
                    session_id=refresh_data.session_id,
                    revoked=refresh_data.revoked,
                    expires_at=refresh_data.expires_at
                )

                refresh_data = await self.uow.refresh_tokens.update_refresh_token(update_dto)
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

        return refresh_data

    async def get_by_id_session_refresh(self, session_id: int) -> Optional[List[OutSession]]:
        try:
            async with self.uow:
                sessions: List[Optional[OutSession]] = await self.uow.refresh_tokens.get_by_session_id_refresh(
                    session_id)
                if sessions is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Ошибка целостности данных"
                    )
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )
        return sessions


class SqlAlchemyServiceOauthClient(AsyncOauthClientService):
    def __init__(self, uow: IUnitOfWorkSession):
        self.uow = uow

    async def create_oauth_client(self, create_oauth_client_data: CreateOauthClient) -> OutOauthClient:
        try:
            async with self.uow:
                client: Optional[OutOauthClient] = await self.uow.oauth_clients.create_oauth_client(
                    create_oauth_client_data)
        except IntegrityError as e:
            # Проверяем код ошибки PostgreSQL (уникальное ограничение)
            pgcode = getattr(getattr(e, "orig", None), "pgcode", None)
            if pgcode == "23505":  # unique_violation
                # Определяем, какой именно уникальный ключ нарушен
                if "oauth_clients_client_id_key" in str(e.orig):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Пользователь с client_id {create_oauth_client_data.client_id} уже существует"
                    )
                else:
                    # Другая уникальность
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Нарушено уникальное ограничение"
                    )
            # Если другая IntegrityError — пробрасываем как общую
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка целостности данных"
            )
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )
        return client

    async def check_oauth_client(self, check_data: CheckOauthClient) -> Optional[OutOauthClient]:
        try:
            async with self.uow:
                client_data: Optional[OutOauthClient] = await self.uow.oauth_clients.get_by_client_id_oauth(
                    check_data.client_id)

                if client_data is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Ошибка целостности данных"
                    )

                if client_data.is_confidential is not None and client_data.is_confidential != check_data.is_confidential:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Неверно переданы данные"
                    )

                if check_data.client_secret is not None and client_data.client_secret != check_data.client_secret:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Неверно переданы данные"
                    )

                if client_data.scopes and check_data.scopes:
                    if set(client_data.scopes) != set(check_data.scopes):
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Неверно переданы данные"
                        )

                if check_data.redirect_url is not None and client_data.redirect_url != check_data.redirect_url:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Неверно переданы данные"
                    )

                if client_data.grant_types and check_data.grant_types:
                    if set(client_data.grant_types) != set(check_data.grant_types):
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Неверно переданы данные"
                        )
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )
        return client_data

    async def close_oauth_client(self, oauth_client_id: int) -> None:
        try:
            async with self.uow:
                oauth_client = await self.uow.oauth_clients.get_by_id_oauth_client(oauth_client_id)
                if oauth_client is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"OAuth client с id={oauth_client_id} не найден"
                    )
                update_data = UpdateOauthClient(
                    id=oauth_client_id,
                    revoked=True
                )
                await self.uow.oauth_clients.update_oauth_client(update_data)
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )
        return None
