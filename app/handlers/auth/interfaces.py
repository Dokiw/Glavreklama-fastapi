from typing import Protocol, List, Optional, Dict, Any
from app.handlers.auth.schemas import (
    RoleUser,
    OutUser,
    UserCreate,
    LogInUser,
    AuthResponse, AuthResponseProvide, UserCreateProvide
)
from app.handlers.auth.dto import UserAuthData
from app.handlers.providers.schemas import ProviderRegisterRequest, ProviderLoginRequest
from app.handlers.session.schemas import CheckSessionAccessToken


class AsyncRoleRepository(Protocol):

    async def get_by_id(self, role_id: int) -> Optional[RoleUser]:
        ...

    async def get_by_user_id(self, id_user: int) -> Optional[RoleUser]:
        ...


# для работы с пользователем
class AsyncUserRepository(Protocol):
    """Абстракция репозитория для работы с пользователями (асинхронная)."""

    async def get_by_id(self, id_user: int) -> Optional[OutUser]:
        ...

    async def get_by_username(self, user_name: str) -> Optional[OutUser]:
        ...

    async def create_user(self, user_in: UserCreate) -> OutUser:
        ...

    async def create_user_provide(self, user_in: UserCreateProvide) -> OutUser:
        ...

    async def list_users(self, limit: int = 100, offset: int = 0) -> List[OutUser]:
        ...

    async def get_auth_data(self, user_name: str) -> Optional[UserAuthData]:
        ...


# для аунтификации и авторизации
class AsyncAuthService(Protocol):
    """Сервис авторизации/аутентификации."""

    async def identification(self, id_user: int, ip: str, user_agent: str, access_token: str) -> Optional[RoleUser]:
        ...

    async def login(self, login_data: LogInUser, ip: str,
                    user_agent: str) -> AuthResponse:  # например возвращает токен + user
        ...

    async def logout(self, id_user: int, ip: str, user_agent: str, access_token: str) -> None:
        ...

    async def register(self, user_data: UserCreate, ip: str, user_agent: str) -> Optional[OutUser]:
        ...

    async def login_from_provider(self, user_data: ProviderLoginRequest, ip: str, user_agent: str) -> (
            Optional)[AuthResponseProvide]:
        ...

    async def register_from_provider_or_get(self, init_data: str, ip: str, user_agent: str) -> (
            Optional)[AuthResponseProvide]:
        ...
