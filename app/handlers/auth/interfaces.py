from typing import Protocol, List, Optional
from app.handlers.auth.schemas import *

#для работы с пользователем
class AsyncUserRepository(Protocol):
    """Абстракция репозитория для работы с пользователями (асинхронная)."""
    async def get_by_id(self,id_user: int) -> Optional[OutUser]:
        ...

    async def get_by_username(self,user_name: str) -> Optional[OutUser]:
        ...

    async def create_user(self,user_in: UserCreate) -> OutUser:
        ...

    async def list_users(self, limit: int = 100, offset: int = 0) -> List[OutUser]:
        ...

#для аунтификации и авторизации
class AsyncAuthService(Protocol):
    """Сервис авторизации/аутентификации."""
    async def identification(self,id_user: int) -> Optional[RoleUser]:
        ...

    async def login(self, login_data: LogInUser) -> AuthResponse:  # например возвращает токен + user
        ...

    async def logout(self, user_id: int) -> None:
        ...

