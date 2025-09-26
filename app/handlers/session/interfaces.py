from typing import Protocol, List, Optional
from app.handlers.session.schemas import (
    OpenSession,
    OutSession,
    CheckSessionAccessToken,
    CheckSessionRefreshToken,
    OutRefreshToken,
    RefreshSession,
    LogoutSession, CreateRefreshToken, UpdateRefreshToken, CreateOauthClient, OutOauthClient, UpdateOauthClient,
    CheckOauthClient, OpenSessionRepo
)
import datetime


class AsyncSessionRepository(Protocol):

    async def open_session(self, session_data: OpenSessionRepo) -> OutSession:
        ...

    async def close_session(self, session_id: int) -> None:
        ...

    async def refresh_session(self, refresh_data: RefreshSession) -> Optional[OutSession]:
        ...

    async def get_by_id_session_refresh(self, id_session: int) -> Optional[OutSession]:
        ...

    async def get_by_id_user_session(self, id_user: int) -> Optional[OutSession]:
        ...

    async def get_by_id_client_session(self, id_client: int) -> list[OutSession]:
        ...

    async def get_by_access_token_session(self, access_token: str) -> Optional[OutSession]:
        ...

    async def deactivate_by_token_ip_ua(self, access_token: str, ip: str, user_agent: str,
                                        id_user: int | None = None) -> Optional[OutSession]:
        ...

    async def get_by_oauth_client_and_user_id(self, id_client: int, id_user: int) -> Optional[OutSession]:
        ...


class AsyncRefreshTokenRepository(Protocol):

    async def create_refresh_token(self, refresh_token_data: CreateRefreshToken) -> OutRefreshToken:
        ...

    async def update_refresh_token(self, refresh_token_data: UpdateRefreshToken) -> OutRefreshToken:
        ...

    async def get_by_id_refresh_token(self, id_refresh_token: int) -> Optional[OutRefreshToken]:
        ...

    async def get_by_session_id_refresh(self, id_session: int) -> list[Optional[OutRefreshToken]]:
        ...


class AsyncOauthClientRepository(Protocol):

    async def create_oauth_client(self, oauth_client_data: CreateOauthClient) -> Optional[OutOauthClient]:
        ...

    async def update_oauth_client(self, oauth_client_data: UpdateOauthClient) -> Optional[OutOauthClient]:
        ...

    async def get_by_id_oauth_client(self, id_oauth_client: int) -> Optional[OutOauthClient]:
        ...

    async def get_by_client_id_oauth(self, client_id: str) -> Optional[OutOauthClient]:
        ...


class AsyncSessionService(Protocol):

    async def get_oauth_by_client(self, client_id: str) -> OutSession:
        ...

    async def open_session(self, session_data: OpenSession) -> OutSession:
        ...

    async def close_session(self, id_session: int) -> None:
        ...

    async def validate_access_token_session(self, check_access_token_data: CheckSessionAccessToken) -> Optional[
        OutSession]:
        ...

    async def validate_refresh_token_session(self, check_refresh_token_data: CheckSessionRefreshToken) -> Optional[
        OutSession]:
        ...

    async def get_by_id_user_session(self, id_user: int) -> Optional[OutSession]:
        ...

    async def get_by_access_token_session(self, access_token: str) -> Optional[OutSession]:
        ...

    async def logout_session(self, logout_data: LogoutSession) -> Optional[OutSession]:
        ...


class AsyncRefreshTokenService(Protocol):

    async def create_refresh_token(self, session_id: int, expires_at: datetime.datetime) -> OutRefreshToken:
        ...

    async def check(self, id_refresh_token: int, refresh_token: str) -> Optional[OutRefreshToken]:
        ...

    async def get_by_id_session_refresh(self, session_id: int) -> Optional[List[OutRefreshToken]]:
        ...


class AsyncOauthClientService(Protocol):

    async def get_by_client_id_oauth(self, client_id: str) -> Optional[OutOauthClient]:
        ...

    async def create_oauth_client(self, create_oauth_client_data: CreateOauthClient) -> OutOauthClient:
        ...

    async def check_oauth_client(self, check_data: CheckOauthClient) -> Optional[OutOauthClient]:
        ...

    async def close_oauth_client(self, oauth_client_id: int) -> None:
        ...
