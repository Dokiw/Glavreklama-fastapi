from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.abs.unit_of_work import IUnitOfWorkAuth
from app.handlers.auth.crud import UserRepository, RoleRepository
from app.handlers.auth.interfaces import AsyncUserRepository, AsyncRoleRepository

class SqlAlchemyUnitOfWork(IUnitOfWorkAuth):
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._session: Optional[AsyncSession] = None
        self.user_repo: Optional[AsyncUserRepository] = None
        self.role_repo: Optional[AsyncRoleRepository] = None

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        # Если session_factory асинхронная функция, нужно await
        self._session = self.session_factory()
        self.user_repo = UserRepository(self._session)
        self.role_repo = RoleRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        await self._session.close()

    @property
    def user(self) -> AsyncUserRepository:
        return self.user_repo

    @property
    def role(self) -> AsyncRoleRepository:
        return self.role_repo

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()