from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
import asyncpg
from app.handlers.auth.dto import UserAuthData
from app.handlers.auth.interfaces import AsyncAuthService, AsyncUserRepository, AsyncRoleRepository
from app.handlers.auth.schemas import LogInUser, RoleUser, AuthResponse, OutUser, Token, UserCreate

class SqlAlchemyAuth(AsyncAuthService):
    def __init__(
            self, user_repo: AsyncUserRepository,
            role_repo: AsyncRoleRepository
    ):
        self.user_repo = user_repo
        self.role_repo = role_repo

    async def identification(self, id_user: int) -> Optional[RoleUser]:
        role: Optional[RoleUser] = await self.role_repo.get_by_user_id(id_user)
        if not role:
            raise None
        return RoleUser(
            name=role.name,
            description=role.description
        )

    async def login(self, login_data: LogInUser) -> AuthResponse:
        auth: Optional[UserAuthData] = await self.user_repo.get_auth_data(login_data.username)
        #выкидываем если нету пользователя и данных
        if not auth or not auth.verify_password(login_data.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        #todo Нужно подключить интерфейс для работы выдачи токена и сверки

        # Формируем OutUser напрямую из auth (полей dataclass)
        out = OutUser(
            id=auth.id,
            username=auth.user_name,
            email=auth.email,
            first_name=auth.first_name,
            last_name=auth.last_name,
        )

        # Токен у тебя пока заглушка — можно вернуть пустой Token или None
        #todo - Необходимо добавить открытие сессии и передавать данные
        token = Token(access_token="", refresh_token=None)

        return AuthResponse(user_data=out, token=token)

    async def logout(self, user_id: int) -> None:
        #todo - Необходимо доделать сессионность и закрытие сессии
        return None

    async def register(self,user_data: UserCreate) -> Optional[AuthResponse]:
        try:
            user: Optional[OutUser] = await self.user_repo.create_user(user_data)
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
                detail="Ошибка целостности данных"
            )

        # todo - Необходимо доделать сессионность и закрытие сессии
        token = Token(access_token="", refresh_token=None)

        return AuthResponse(user_data = OutUser.from_orm(user),token=token)





