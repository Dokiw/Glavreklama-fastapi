from typing import Protocol, List, Optional
from app.handlers.session.schemas import *


class AsyncSessionRepository(Protocol):

    async def open_session(self, session_data: OpenSession) -> OutSession:
        ...

    async def close_session(self, session_id: int) -> None:
        ...

    async def refresh_session(self, refresh_data: RefreshSession) -> Optional[OutSession]:
        ...

    async def get_by_id_session(self, id_session: int) -> Optional[OutSession]:
        ...

    async def get_by_id_user_session(self, id_user: int) -> Optional[OutSession]:
        ...

    async def get_by_id_client_session(self, id_client: int) -> list[OutSession]:
        ...

    async def get_by_access_token_session(self, access_token: str) -> Optional[OutSession]:
        ...


class AsyncRefreshTokenRepository(Protocol):

    async def create_refresh_token(self, refresh_token_data: CreateRefreshToken) -> OutRefreshToken:
        ...

    async def update_refresh_token(self, refresh_token_data: UpdateRefreshToken) -> OutRefreshToken:
        ...

    async def get_by_id_refresh_token(self, id_refresh_token: int) -> Optional[OutRefreshToken]:
        ...

    async def get_by_session_id(self, id_session: int) -> list[Optional[OutRefreshToken]]:
        ...


class AsyncOauthClientRepository(Protocol):

    async def create_oauth_client(self, oauth_client_data: CreateOauthClient) -> OutOauthClient:
        ...

    async def update_oauth_client(self, oauth_client_data: UpdateOauthClient) -> OutOauthClient:
        ...

    async def get_by_id_oauth_client(self, id_oauth_client: int) -> Optional[OutOauthClient]:
        ...


class AsyncSessionService(Protocol):

    async def open_session(self, session_data: OpenSession) -> OutSession:
        ...

    async def close_session(self, id_session: int) -> None:
        ...

    async def validate_access_token_session(self, check_access_token_data: CheckSessionAccessToken) -> OutSession:
        ...

    async def validate_refresh_token_session(self, check_refresh_token_data: CheckSessionRefreshToken) -> OutSession:
        ...




class AsyncRefreshTokenService(Protocol):

    async def create_refresh_token(self, user_id: int) -> OutSession:
        ...

    async def check(self, refresh_token: str) -> Optional[OutSession]:
        ...

    async def get_by_id_session(self, session_id: int) -> Optional[List[OutSession]]:
        ...


class AsyncOauthClientService(Protocol):

    async def create_oauth_client(self, create_oauth_client_data: CreateOauthClient) -> OutSession:
        ...

    async def check_oauth_client(self,check_data: CheckOauthClient) -> Optional[OutOauthClient]:
        ...

    async def close_oauth_client(self,oauth_client_id: int) -> None:
        ...
