from app.handlers.auth.dto import UserAuthData
from app.handlers.auth.schemas import OutUser, UserCreate, RoleUser, UserCreateProvide
from sqlalchemy.ext.asyncio import AsyncSession
from app.handlers.auth.interfaces import AsyncUserRepository, AsyncRoleRepository
from sqlalchemy import select, func
from app.models.auth.models import User as UserModel, Role as RoleModel

from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from app.models.auth.models import User as UserModel, Role as RoleModel


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
            username=m.user_name,
            email=m.email,
            first_name=m.first_name,
            last_name=m.last_name
        )

    async def create_user(self, user_in: UserCreate) -> OutUser:
        m = UserModel()
        m.user_name = user_in.user_name
        m.password = user_in.password or None
        m.email = user_in.email or None
        m.first_name = user_in.first_name or None
        m.last_name = user_in.last_name or None
        self.db.add(m)
        await self.db.flush()
        return self._to_dto(m)

    async def create_user_provide(self, user_in: UserCreateProvide) -> OutUser:
        m = UserModel()
        m.user_name = user_in.user_name
        m.email = user_in.email or None
        m.first_name = user_in.first_name or None
        m.last_name = user_in.last_name or None
        self.db.add(m)
        await self.db.flush()
        return self._to_dto(m)

    async def count_users(self) -> int:
        count_q = select(func.count(UserModel.id))
        count_result = await self.db.execute(count_q)
        total = count_result.scalar_one()
        return total

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

    async def get_auth_data(self, user_name: str) -> Optional[UserAuthData]:
        q = select(UserModel).where(UserModel.user_name == user_name)
        result = await self.db.execute(q)
        user = result.scalar_one_or_none()
        if user is None:
            return None
        return UserAuthData(
            id=user.id,
            pass_hash=user.pass_hash,
            user_name=user.user_name,
            email=user.email,
            last_name=user.last_name,
            first_name=user.first_name,
        )


class RoleRepository(AsyncRoleRepository):  # Исправлено наследование
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, role_id: int) -> Optional[RoleUser]:
        q = select(RoleModel).where(RoleModel.id == role_id).limit(1)
        result = await self.db.execute(q)
        role = result.scalar_one_or_none()
        if role is None:
            return None
        return RoleUser(name=role.name, description=role.description)

    async def get_by_user_id(self, id_user: int) -> Optional[RoleUser]:
        q = select(RoleModel).join(UserModel, RoleModel.id == UserModel.role_id).where(UserModel.id == id_user).limit(1)
        result = await self.db.execute(q)
        role = result.scalar_one_or_none()
        if role is None:
            return None
        return RoleUser(name=role.name, description=role.description)
