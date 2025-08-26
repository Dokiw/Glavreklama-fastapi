from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
import asyncpg

from app.core.abs.unit_of_work import IUnitOfWorkAuth
from app.handlers.auth.dto import UserAuthData
from app.handlers.auth.interfaces import AsyncAuthService, AsyncUserRepository, AsyncRoleRepository
from app.handlers.auth.schemas import LogInUser, RoleUser, AuthResponse, OutUser, Token, UserCreate
from app.handlers.session.interfaces import AsyncSessionService
from app.handlers.session.schemas import OpenSession, CheckSessionAccessToken, OutSession


class SqlAlchemyAuth(AsyncAuthService):
    def __init__(
            self,
            uow: IUnitOfWorkAuth,
            session_service: AsyncSessionService
    ):
        self.uow = uow
        self.session_service = session_service

    async def identification(self, id_user: int, ip: str, user_agent: str, access_token: str) -> Optional[RoleUser]:
        try:
            async with self.uow:
                session = await self.session_service.get_by_access_token_session(access_token)
                if session is None:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
                session_data = CheckSessionAccessToken(
                    id=session.id,
                    user_id=session.user_id,
                    access_token=session.access_token,
                    ip_address=ip,
                    user_agent=user_agent,
                )

                await self.session_service.validate_access_token_session(session_data)
                role: Optional[RoleUser] = await self.uow.role_repo.get_by_user_id(id_user)
                if not role:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        except Exception as e:
            # Откатываем транзакцию при любой другой ошибке
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

        return RoleUser(
            name=role.name,
            description=role.description
        )

    async def login(self, login_data: LogInUser, ip: str, user_agent: str) -> AuthResponse:
        try:
            async with self.uow:
                auth: Optional[UserAuthData] = await self.uow.user_repo.get_auth_data(login_data.username)
                # выкидываем если нет пользователя и данных
                if not auth or not auth.verify_password(login_data.password):
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
                )

                # todo - Проверить надо работу сессий
                token = Token(
                    access_token=session.access_token,
                    refresh_token=session.refresh_token
                )

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
                    id=session.id,
                    user_id=session.user_id,
                    access_token=session.access_token,
                    ip_address=ip,
                    user_agent=user_agent,
                )
                session: Optional[OutSession] = await self.session_service.validate_access_token_session(session_data)
                await self.session_service.close_session(session.id)
        except Exception as e:
            # Откатываем транзакцию при любой другой ошибке
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )
        return None

    async def register(self, user_data: UserCreate, ip: str, user_agent: str) -> Optional[AuthResponse]:
        try:
            async with self.uow:
                user: Optional[OutUser] = await self.uow.user_repo.create_user(user_data)
                session_data = OpenSession(
                    user_id=user.id,
                    client_id=None,
                    ip_address=ip,
                    user_agent=user_agent,
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
                detail=f"Ошибка целостности данных и {str(e)}"
            )
        except Exception as e:
            # Откатываем транзакцию при любой другой ошибке
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

        # todo - Необходимо доделать сессионность и закрытие сессии
        token = Token(access_token=session.access_token, refresh_token=session.refresh_token)

        return AuthResponse(user_data=OutUser.from_orm(user), token=token)
