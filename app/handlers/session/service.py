from typing import Optional

from fastapi import HTTPException, status, Depends
from sqlalchemy.exc import IntegrityError

import asyncpg

from app.models.sessions.models import Session as SessionModel, RefreshToken as RefreshTokenModel, \
    OAuthClient as OAuthClientModel

from app.handlers.session.interfaces import AsyncSessionRepository, AsyncRefreshTokenRepository, \
    AsyncOauthClientRepository, AsyncRefreshTokenService, AsyncOauthClientService
from app.handlers.session.schemas import OpenSession, OutSession, CheckOauthClient, CreateOauthClient, OutOauthClient, \
    CheckSessionAccessToken, CheckSessionRefreshToken


class SqlAclchemyServiceSession():
    def __init__(self, session_repo: AsyncSessionRepository):
        self.session_repo = session_repo

    async def _to_dto(self,m: "SessionModel") -> OutSession:

        return OutSession(
            id=m.id,
            user_id=m.user_id,
            client_id=m.client_id,
            access_token=m.access_token,
            refresh_token=m.refresh_tokens,
            is_active=m.is_active,
            logged_out_at=m.logged_out_at,
            created_at=m.created_at,
            last_used_at=m.last_used_at
        )
    async def open_session(self, session_data: OpenSession) -> OutSession:
        return None

    async def close_session(self, id_session: int) -> None:
        return None

    async def validate_access_token_session(self, check_access_token_data: CheckSessionAccessToken) -> OutSession:

        return None

    async def validate_refresh_token_session(self, check_refresh_token_data: CheckSessionRefreshToken) -> OutSession:

        return None


class SqlAlchemyServiceRefreshToken(AsyncRefreshTokenService):

    def __init__(self, refresh_token_repo: AsyncSessionRepository):
        self.session_repo = refresh_token_repo


class SqlAlchemyServiceOauthClient(AsyncOauthClientService):

    def __init__(self, oauth_client_repo: AsyncOauthClientRepository):
        self.oauth_client_repo = oauth_client_repo

    async def create_oauth_client(self, create_oauth_client_data: CreateOauthClient) -> OutSession:
        return None

    async def check_oauth_client(self, check_data: CheckOauthClient) -> Optional[OutOauthClient]:
        return None

    async def close_oauth_client(self, oauth_client_id: int) -> None:
        return None
