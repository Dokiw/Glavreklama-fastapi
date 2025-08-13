from app.db.session import *
from app.handlers.auth.schemas import OutUser, UserCreate
from app.models.auth import *
from sqlalchemy.ext.asyncio import AsyncSession
from app.handlers.auth.interfaces import AsyncUserRepository


from sqlalchemy import select

from typing import TYPE_CHECKING, Optional, List
if TYPE_CHECKING:
    from app.models.auth.models import User as UserModel

class UserRepository(AsyncUserRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _to_dto(m: "UserModel") -> OutUser:
        if m is None:
            raise TypeError("_to_dto получил None")
        if isinstance(m, type):
            raise TypeError(f"_to_dto получил класс {m!r}, ожидается экземпляр User")
        return OutUser(
            id=m.id,
            username=m.user_name,  #Cм. Замечание ниже по именам полей
            email=m.email
        )

    async def create_user(self, user_in: UserCreate) -> OutUser:
        m = UserModel(username=user_in.username, email=user_in.email)
        m.password = user_in.password
        self.db.add(m)
        await self.db.commit()
        await self.db.refresh(m)
        return self._to_dto(m)

    async def list_users(self, limit: int = 100, offset: int = 0) -> List[OutUser]:
        q = select(UserModel).offset(offset).limit(limit)
        result = await self.db.execute(q)
        users = result.scalars().all()
        return [self._to_dto(r) for r in users]

    async def get_by_id(self, id_user: int) -> Optional[OutUser]:
        m = await self.db.get(UserModel, id_user)
        return self._to_dto(m) if m else None

    async def get_by_username(self, user_name: str) -> Optional[OutUser]:
        q = select(UserModel).where(UserModel.user_name == user_name)
        result = await self.db.execute(q)
        user = result.scalar_one_or_none()
        return self._to_dto(user) if user else None


