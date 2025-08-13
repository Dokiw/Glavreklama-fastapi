from typing import Optional

from app.handlers.auth.interfaces import AsyncAuthService, AsyncUserRepository
from app.handlers.auth.crud import UserRepository
from app.handlers.auth.schemas import LogInUser, RoleUser, AuthResponse


class SqlAlchemyAuth(AsyncAuthService):
    def __init__(self, user_repo: AsyncUserRepository):
        self.user_repo = user_repo

    async def identification(self, id_user: int) -> Optional[RoleUser]:
        return None

    async def login(self, login_data: LogInUser) -> AuthResponse:
        return None

    async def logout(self, user_id: int) -> None:
        return None






