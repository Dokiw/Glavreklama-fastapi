from typing import Protocol, List, Optional
from app.handlers.session.schemas import *


class AsyncSessionRepository(Protocol):

    async def open_session(self, session_data: OpenSession) -> OutSession:
        ...

    async def close_session(self, session_id: int) -> None:
        ...

    async def refresh_session(self, refresh_data: RefreshSession) -> Optional[OutSession]:
        ...

    async def get_by_id_session(self,id_session: int) -> Optional[OutSession]:
        ...

    async def get_by_id_user_session(self,id_user: int) -> Optional[OutSession]:
        ...

    async def get_by_id_client_session(self,id_client: int) -> list[OutSession]:
        ...

    async def get_by_access_token_session(self,access_token: str) -> Optional[OutSession]:
        ...

class AsyncRefreshTokenRepository(Protocol):


    async def create_refresh_token(self,refresh_token_data: CreateRefreshToken) -> OutRefreshToken:
        ...

    async def update_refresh_token(self,refresh_token_data: UpdateRefreshToken) -> OutRefreshToken:
        ...

    async def get_by_id_refresh_token(self,id_refresh_token: int) -> Optional[OutRefreshToken]:
        ...

    async def get_by_session_id(self,id_session: int) -> list[Optional[OutRefreshToken]]:
        ...



class AsyncOauthClient(Protocol):

    async def create_oauth_client(self,oauth_client_data: CreateOauthClient) -> OutOauthClient:
        ...

    async def Update_oauth_client(self,oauth_client_data: UpdateOauthClient) -> OutOauthClient:
        ...

    async def get_by_id_oauth_client(self,id_oauth_client: int) -> Optional[OutOauthClient]:
        ...


