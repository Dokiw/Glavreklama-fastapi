from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.abs.unit_of_work import IUnitOfWorkSession
from app.handlers.session.interfaces import (AsyncSessionRepository, AsyncRefreshTokenRepository,
                                             AsyncOauthClientRepository)
from app.handlers.session.crud import SessionRepository, RefreshTokenRepository, OauthClientRepository


class SqlAlchemyUnitOfWork(IUnitOfWorkSession):
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._session: Optional[AsyncSession] = None

    async def __aenter__(self):
        self._session = self.session_factory()
        self.sessions_repo = SessionRepository(self._session)
        self.refresh_tokens_repo = RefreshTokenRepository(self._session)
        self.oauth_clients_repo = OauthClientRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        await self._session.close()

    @property
    def sessions(self) -> AsyncSessionRepository:
        return self.sessions_repo

    @property
    def refresh_tokens(self) -> AsyncRefreshTokenRepository:
        return self.refresh_tokens_repo

    @property
    def oauth_clients(self) -> AsyncOauthClientRepository:
        return self.oauth_clients_repo

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()

