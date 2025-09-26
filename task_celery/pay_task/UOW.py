from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.abs.unit_of_work import IUnitOfWorkSubtraction
from app.handlers.pay.crud import SubtractionRepository
from app.handlers.pay.interfaces import AsyncSubtractionRepository


class SqlAlchemyUnitOfWork(IUnitOfWorkSubtraction):
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._session: Optional[AsyncSession] = None

    async def __aenter__(self):
        self._session = self.session_factory()
        self._subtraction_repo = SubtractionRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()  # автоматически сохраняем изменения
        else:
            await self.rollback()
        await self._session.close()

    @property
    def subtraction_repo(self) -> "AsyncSubtractionRepository":
        return self._subtraction_repo

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()

