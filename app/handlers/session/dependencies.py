# app/handlers/session/dependencies.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.handlers.session.service import SqlAlchemyServiceRefreshToken, SqlAlchemyServiceSession
from app.handlers.session.UOW import SqlAlchemyUnitOfWork, IUnitOfWorkSession
from app.handlers.session.crud import SessionRepository, RefreshTokenRepository
from app.handlers.session.interfaces import AsyncSessionService, AsyncRefreshTokenService


# фабрика UnitOfWork
async def get_uow(db: AsyncSession = Depends(get_db)) -> IUnitOfWorkSession:
    async with SqlAlchemyUnitOfWork(lambda: db) as uow:
        yield uow


# фабрика сервиса refresh токенов
def get_refresh_service(uow: IUnitOfWorkSession = Depends(get_uow)) -> AsyncRefreshTokenService:
    return SqlAlchemyServiceRefreshToken(uow)


# фабрика сервиса сессий
def get_session_service(
    uow: IUnitOfWorkSession = Depends(get_uow),
    refresh_service: AsyncRefreshTokenService = Depends(get_refresh_service),
) -> AsyncSessionService:
    return SqlAlchemyServiceSession(uow, refresh_service)


# alias для роутов
SessionServiceDep = Annotated[SqlAlchemyServiceSession, Depends(get_session_service)]
