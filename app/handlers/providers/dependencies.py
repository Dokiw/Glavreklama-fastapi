# app/handlers/session/dependencies.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.handlers.providers.service import ProviderUserRepository
from app.handlers.providers.UOW import SqlAlchemyUnitOfWork, IUnitOfWorkProvider
from app.handlers.providers.interfaces import AsyncProvidersService


# фабрика UnitOfWork
async def get_uow(db: AsyncSession = Depends(get_db)) -> IUnitOfWorkProvider:
    async with SqlAlchemyUnitOfWork(lambda: db) as uow:
        yield uow


# фабрика сервиса сессий
def get_session_service(
        uow: IUnitOfWorkProvider = Depends(get_uow),
) -> AsyncProvidersService:
    return ProviderUserRepository(uow)


# alias для роутов
ProviderUserServiceDep = Annotated[ProviderUserRepository, Depends(get_session_service)]
