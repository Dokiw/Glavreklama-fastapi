from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.abs.unit_of_work import IUnitOfWorkProvider
from app.handlers.providers.interfaces import AsyncProviderRepository
from app.handlers.providers.crud import ProvideRepository


class SqlAlchemyUnitOfWork(IUnitOfWorkProvider):
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._session: Optional[AsyncSession] = None

    async def __aenter__(self):
        self._session = await self.session_factory()
        self.provider_repo = ProvideRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()  # автоматически сохраняем изменения
        else:
            await self.rollback()
        await self._session.close()

    @property
    def provider(self) -> "AsyncProviderRepository":
        return self.provider_repo

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
