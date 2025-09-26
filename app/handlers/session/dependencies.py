# app/handlers/session/dependencies.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.handlers.session.service import SqlAlchemyServiceRefreshToken, SqlAlchemyServiceSession, \
    SqlAlchemyServiceOauthClient
from app.handlers.session.UOW import SqlAlchemyUnitOfWork, IUnitOfWorkSession
from app.handlers.session.crud import SessionRepository, RefreshTokenRepository
from app.handlers.session.interfaces import AsyncSessionService, AsyncRefreshTokenService, AsyncOauthClientService


# фабрика UnitOfWork
async def get_uow(db: AsyncSession = Depends(get_db)) -> IUnitOfWorkSession:
    async with SqlAlchemyUnitOfWork(lambda: db) as uow:
        yield uow


# фабрика сервиса refresh токенов
def get_refresh_service(uow: IUnitOfWorkSession = Depends(get_uow)) -> AsyncRefreshTokenService:
    return SqlAlchemyServiceRefreshToken(uow)


def get_oauth_service(uow: IUnitOfWorkSession = Depends(get_uow)) -> AsyncOauthClientService:
    return SqlAlchemyServiceOauthClient(uow)


# фабрика сервиса сессий
def get_session_service(
        uow: IUnitOfWorkSession = Depends(get_uow),
        refresh_service: AsyncRefreshTokenService = Depends(get_refresh_service),
        oauth_client: AsyncOauthClientService = Depends(get_oauth_service)
) -> AsyncSessionService:
    return SqlAlchemyServiceSession(uow, refresh_service, oauth_client)


# alias для роутов
SessionServiceDep = Annotated[SqlAlchemyServiceSession, Depends(get_session_service)]


def get_oauth_client_service(
        uow: IUnitOfWorkSession = Depends(get_uow),
) -> AsyncOauthClientService:
    return SqlAlchemyServiceOauthClient(uow)


OauthClientServiceDep = Annotated[SqlAlchemyServiceOauthClient, Depends(get_oauth_client_service)]
