import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
import asyncpg

from app.core.abs.unit_of_work import IUnitOfWorkAuth
from app.core.config import settings
from app.handlers.auth.dto import UserAuthData
from app.handlers.auth.interfaces import AsyncAuthService, AsyncRoleService
from app.handlers.auth.schemas import PaginateUser, LogInUser, RoleUser, AuthResponse, OutUser, Token, UserCreate, \
    UserCreateProvide, \
    AuthResponseProvide, LogInUserBot
from app.handlers.providers.schemas import ProviderRegisterRequest, ProviderLoginRequest, ProviderOut
from app.handlers.session.interfaces import AsyncSessionService, AsyncOauthClientService
from app.handlers.session.schemas import OpenSession, CheckSessionAccessToken, OutSession, CheckOauthClient
from app.handlers.providers.interfaces import AsyncProvidersService
from app.method.decorator import transactional
from app.method.initdatatelegram import check_telegram_init_data


# from app.method.initdatatelegram import verify_telegram_init_data


class SqlAlchemyAuth(AsyncAuthService):
    def __init__(
            self,
            uow: IUnitOfWorkAuth,
            session_service: AsyncSessionService,
            provide_user: AsyncProvidersService,
            role_service: AsyncRoleService,
            oauth_client_service: AsyncOauthClientService
    ):
        self.uow = uow
        self.session_service = session_service
        self.provide_user = provide_user
        self.role_service = role_service
        self.oauth_client_service = oauth_client_service

    @transactional()
    async def login_via_bots(self, login_data: LogInUserBot, ip: str,
                             user_agent: str) -> AuthResponse:
        auth: Optional[UserAuthData] = await self.uow.user_repo.get_auth_data(login_data.username)

        provider_login = ProviderLoginRequest(
            provider="telegram",
            provider_user_id=str(login_data.provider_user_id),
        )

        auth_provide: Optional[ProviderOut] = await self.provide_user.login_provider_user(provider_login)

        await self.oauth_client_service.check_oauth_client(
            check_data=CheckOauthClient(client_id=str(login_data.client_id),
                                        client_secret=str(login_data.client_secret)))

        if str(auth_provide.provider_user_id) != str(login_data.provider_user_id):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail=f"Invalid gleb")

        # выкидываем если нет пользователя и данных
        if not auth:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        session = await self.session_service.open_session(OpenSession(
            user_id=auth.id,
            client_id=login_data.client_id,
            ip_address=ip,
            user_agent=user_agent,
        ))

        # Формируем OutUser напрямую из auth (полей dataclass)
        out = OutUser(
            id=auth.id,
            username=auth.user_name,
            email=auth.email,
            first_name=auth.first_name,
            last_name=auth.last_name,
            role_id=auth.role_id,
        )

        token = Token(
            access_token=session.access_token,
            refresh_token=session.refresh_token
        )

        return AuthResponse(user_data=out, token=token)

    async def login(self, login_data: LogInUser, ip: str, user_agent: str, oauth_client: str) -> AuthResponse:
        try:
            async with self.uow:
                auth: Optional[UserAuthData] = await self.uow.user_repo.get_auth_data(login_data.username)

                # todo - НАДО СДЕЛАТЬ МЕТОД ДЛЯ ПОЛУЧЕНИЯ OAUTH_CLIE
                # oauth_client_data: Optional[OutSession] = await self.session_service.get_oauth_by_client(oauth_client)

                # выкидываем если нет пользователя и данных
                if not auth or not auth.verify_password(login_data.password):
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

                session = await self.session_service.open_session(OpenSession(
                    user_id=auth.id,
                    client_id=oauth_client,
                    ip_address=ip,
                    user_agent=user_agent,
                ))

                # Формируем OutUser напрямую из auth (полей dataclass)
                out = OutUser(
                    id=auth.id,
                    username=auth.user_name,
                    email=auth.email,
                    first_name=auth.first_name,
                    last_name=auth.last_name,
                    role_id=auth.role_id,
                )

                # todo - Проверить надо работу сессий
                token = Token(
                    access_token=session.access_token,
                    refresh_token=session.refresh_token
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

        return AuthResponse(user_data=out, token=token)

    async def logout(self, id_user: int, ip: str, user_agent: str, access_token: str) -> None:
        try:
            async with self.uow:
                session = await self.session_service.get_by_access_token_session(access_token)
                if session is None:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

                session_data = CheckSessionAccessToken(
                    user_id=session.user_id,
                    access_token=session.access_token,
                    ip_address=ip,
                    user_agent=user_agent
                )
                session: Optional[OutSession] = await self.session_service.validate_access_token_session(session_data)
                await self.session_service.close_session(session.id)
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            # Откатываем транзакцию при любой другой ошибке
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)} -- тут 1"
            )
        return None

    async def register(self, user_data: UserCreate, ip: str, user_agent: str, oauth_client: str) -> Optional[
        AuthResponse]:
        try:
            async with self.uow:
                user: Optional[OutUser] = await self.uow.user_repo.create_user(user_data)
                session_data = OpenSession(
                    user_id=user.id,
                    ip_address=ip,
                    user_agent=user_agent,
                    client_id=oauth_client,
                )
                session: Optional[OutSession] = await self.session_service.open_session(session_data)

        except IntegrityError as e:
            if isinstance(e.orig, asyncpg.exceptions.UniqueViolationError):
                if "users_email_key" in str(e.orig):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Пользователь с email {user_data.email} уже существует"
                    )
                # Если другая IntegrityError — пробрасываем дальше
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ошибка целостности данных"
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

        # todo - Необходимо доделать сессионность и закрытие сессии
        token = Token(access_token=session.access_token, refresh_token=session.refresh_token)

        return AuthResponse(user_data=OutUser.from_orm(user), token=token)

    async def login_from_provider(self, client_id: str, user_data: ProviderLoginRequest, ip: str, user_agent: str,
                                  oauth_client: str) -> (
            Optional)[AuthResponseProvide]:
        try:
            async with self.uow:

                provide: Optional[ProviderOut] = await self.provide_user.get_by_provider_and_user_id(user_data)

                if provide is None:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Отсутствуют данные")

                user = await self.uow.user_repo.get_by_id(provide.user_id)
                if user is None:
                    # нет связанного локального пользователя — логическая ошибка, можно создать или ошибку
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Provider привязан к несуществующему пользователю"
                    )

                # теперь у нас есть user и provide — открываем сессию
                session_data = OpenSession(
                    user_id=user.id,
                    ip_address=ip,
                    user_agent=user_agent,
                    client_id=client_id  # или передать client_id если есть
                )
                session: OutSession = await self.session_service.open_session(session_data)

                token = Token(access_token=session.access_token, refresh_token=session.refresh_token)

                result = AuthResponseProvide(
                    user_data=user,
                    token=token,
                    provide_data=provide,
                )
                return result

        except IntegrityError as e:
            # более детальная обработка unique violations
            pgcode = getattr(getattr(e, "orig", None), "pgcode", None)
            if pgcode == "23505":
                # можешь посмотреть e.orig для выяснения constraint name
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Нарушено уникальное ограничение")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ошибка целостности данных")
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            # Откатываем транзакцию при любой другой ошибке
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

    async def register_from_provider_or_get(
            self,
            init_data: str,
            ip: str,
            user_agent: str,
            oauth_client: str
    ) -> Optional[AuthResponseProvide]:
        try:
            async with self.uow:  # единая транзакция для всех операций
                init_data = await check_telegram_init_data(init_data, settings.BOT_TOKEN)

                # 2) parse user JSON
                try:
                    user_data = init_data["user"]
                except (json.JSONDecodeError, TypeError, KeyError):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Некорректный формат данных пользователя {init_data} and {settings.BOT_TOKEN}"
                    )

                provider = "telegram"
                provider_user_id = str(user_data["id"])
                plr = ProviderLoginRequest(provider="telegram", provider_user_id=str(user_data["id"]), )

                # 3) попробуем найти провайдера
                provide: Optional[ProviderOut] = await self.provide_user.get_by_provider_and_user_id(
                    plr
                )

                # 4) если провайдер найден — просто получаем связанного пользователя и дальше делаем сессию
                if provide is not None:
                    user = await self.uow.user_repo.get_by_id(provide.user_id)
                    if user is None:
                        # нет связанного локального пользователя — логическая ошибка, можно создать или ошибку
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Provider привязан к несуществующему пользователю"
                        )
                else:
                    # 5) подготовим данные для создания локального пользователя
                    # user_name обязателен для твоей схемы — делаем fallback если telegram.username отсутствует
                    username = user_data.get("username") or f"tg_{provider_user_id}"

                    user_create_payload = UserCreateProvide(
                        user_name=username,
                        first_name=user_data.get("first_name"),
                        last_name=user_data.get("last_name"),
                        email=None,
                        password=None
                    )

                    # 6) создаём локального пользователя (flush внутри create_user должен дать id)
                    user: OutUser = await self.uow.user_repo.create_user_provide(user_create_payload)

                    # 7) теперь создаём провайдера, привязанного к user.id
                    create_provider_payload = ProviderRegisterRequest(
                        provider=provider,
                        provider_user_id=provider_user_id,
                        username=user_data.get("username"),
                        first_name=user_data.get("first_name"),
                        last_name=user_data.get("last_name"),
                        photo_url=user_data.get("photo_url"),
                        is_premium=user_data.get("is_premium"),
                        auth_date=init_data["auth_date"].replace(tzinfo=None),
                        user_id=user.id,  # важно: привязываем к созданному пользователю
                    )

                    try:
                        provide = await self.provide_user.create_provider_user(create_provider_payload)
                    except IntegrityError as e:
                        # гонка: другой процесс уже создал provider; в этом случае читаем его и используем связанного
                        # user
                        pgcode = getattr(getattr(e, "orig", None), "pgcode", None)
                        if pgcode == "23505":
                            # повторно получим провайдера
                            plr = ProviderLoginRequest(provider="telegram", provider_user_id=str(user_data["id"]), )
                            provide = await self.provide_user.get_by_provider_and_user_id(
                                plr
                            )
                            if provide is None:
                                # неожиданно — пробрасываем
                                raise HTTPException(status_code=500, detail="Ошибка создания provider (race condition)")
                            # Если провайдер уже существует, возможно он привязан к другому user:
                            # решай в соответствии с бизнес-логикой — сейчас используем провайдера и его user
                            user = await self.uow.user_repo.get_by_id(provide.user_id)
                        else:
                            raise

                # 8) теперь у нас есть user и provide — открываем сессию
                session_data = OpenSession(
                    user_id=user.id,
                    ip_address=ip,
                    user_agent=user_agent,
                    client_id=oauth_client  # или передать client_id если есть
                )
                session: OutSession = await self.session_service.open_session(session_data)

                token = Token(access_token=session.access_token, refresh_token=session.refresh_token)

                result = AuthResponseProvide(
                    user_data=user,
                    token=token,
                    provide_data=provide,
                )

                return result

        except IntegrityError as e:
            # более детальная обработка unique violations
            pgcode = getattr(getattr(e, "orig", None), "pgcode", None)
            if pgcode == "23505":
                # можешь посмотреть e.orig для выяснения constraint name
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нарушено уникальное ограничение")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ошибка целостности данных")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    async def get_users(self, id_user: int, ip: str, user_agent: str, access_token: str,
                        offset: int, limit: int) -> (
            Optional)[List[OutUser]]:

        # проверяем состояния - доступ ток админ
        r_u = await self.role_service.is_admin(id_user)
        if not r_u:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Нет прав"
            )

        session_data = CheckSessionAccessToken(
            user_id=id_user,
            access_token=access_token,
            ip_address=ip,
            user_agent=user_agent
        )
        # Проверяем состояния сессии
        await self.session_service.validate_access_token_session(session_data)

        users = await self.uow.user_repo.list_users(offset=offset, limit=limit)
        total = await self.uow.user_repo.count_users()
        pag_user = PaginateUser(
            users=users,
            total=total,
            Offset_current=offset,
        )
        return pag_user

    @transactional()
    async def update_role(self, role_id: int, check_data: CheckSessionAccessToken) -> Optional[OutUser]:
        await self.role_service.is_admin(check_data.user_id)
        await self.session_service.validate_access_token_session(check_data)

        result = await self.uow.user_repo.update_role_users(user_id=check_data.user_id, role_id=role_id)

        return result

    @transactional()
    async def get_roles(self, check_data: CheckSessionAccessToken) -> List[Optional[RoleUser]]:
        await self.role_service.is_admin(check_data.user_id)
        return await self.role_service.get_roles_include()


class SqlAlchemyRole(AsyncRoleService):
    def __init__(self, uow: IUnitOfWorkAuth):
        self.uow = uow

    # Надо будет подумать, стоит ли в таком формате оставить или лучше поменять, потому что, в моём понимании
    # Это костыль, в текущий момент, но в дальнейшем может быть переработано в автоматическую систему по определенным грифам например
    async def is_admin(self, id_user: int) -> bool:
        try:
            async with self.uow:
                role: Optional[RoleUser] = await self.uow.role_repo.get_by_user_id(id_user)
                if not role:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

                if role.name not in ['Admin', 'Manager']:
                    return False

                return True
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            # Откатываем транзакцию при любой другой ошибке
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

    @transactional()
    async def get_roles_include(self) -> List[Optional[RoleUser]]:
        result = await self.uow.role.get_roles()
        return result
