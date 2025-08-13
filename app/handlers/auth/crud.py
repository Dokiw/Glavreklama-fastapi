from app.db.session import *
from app.models.auth import *
from sqlalchemy.ext.asyncio import AsyncSession
from app.handlers.auth.interfaces import *


class SqlAlchemyUserRepo(AsyncUserRepository):
    def __init__(self,db: AsyncSession):
        self.db = AsyncSession

    async def create_user(self,user_in: UserCreate) -> OutUser:
        return None

    async def list_users(self, limit: int = 100, offset: int = 0) -> List[OutUser]:
        return []

    async def get_by_id(self,id_user: int) -> Optional[OutUser]:
        return None

    async def get_by_username(self,user_name: str) -> Optional[OutUser]:
        return None


class SqlAlchemyAuth(AsyncAuthService):
    def __init__(self,db: AsyncSession):
        self.db = AsyncSession

    async def identification(self,id_user: int) -> Optional[RoleUser]:
        return None

    async def login(self, login_data: LogInUser) -> AuthResponse:
        return AuthResponse(
            user=OutUser(id=1, username=login_data.username),
            token={"access_token": "fake", "refresh_token": None}
        )

    async def logout(self, user_id: int) -> None:
        return None

