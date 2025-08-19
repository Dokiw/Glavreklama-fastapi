import datetime
import time

from app.handlers.session.schemas import *

from sqlalchemy.ext.asyncio import AsyncSession


from sqlalchemy import select
from app.models.sessions.models import Session as SessionModel, RefreshToken as RefreshTokenModel,OAuthClient as OAuthClientModel

from app.handlers.session.interfaces import AsyncSessionRepository,AsyncRefreshTokenRepository,AsyncOauthClient

from typing import TYPE_CHECKING, Optional, List
if TYPE_CHECKING:
    from app.models.auth.models import User as UserModel, Role as RoleModel

import hashlib



class SessionRepository(AsyncSessionRepository):
    def __init__(self,db: AsyncSession):
        self.db = db
    async def _to_dto(self,m: "SessionModel") -> OutSession:
        if m is None:
            raise TypeError("_to_dto получил None")
        if isinstance(m,type):
            raise TypeError(f"_to_dto получил класс {m!r}, ожидается экземпляр Session")

        # запросим последний refresh_token по created_at
        stmt = (
            select(RefreshToken.id)
            .where(RefreshToken.session_id == m.id)
            .order_by(RefreshToken.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        last_refresh_token_id = result.scalar_one_or_none()

        return OutSession(
            id=m.id,
            user_id=m.user_id,
            client_id=m.client_id,
            access_token=m.access_token,
            refresh_token_id=last_refresh_token_id,
            is_active=m.is_active,
            logged_out_at=m.logged_out_at,
            created_at=m.created_at,
            last_used_at=m.last_used_at,
        )
    async def open_session(self, session_data: OpenSession) -> OutSession:

        m = SessionModel()
        m.user_id = session_data.user_id
        m.ip_address = session_data.id_address
        m.user_agent = session_data.user_agent
        m.client_id = session_data.client_id
        m.is_active = True
        m.created_at = datetime.datetime.now()
        m.last_used_at = datetime.datetime.now()
        timestamp = str(time.time()).encode()
        m.access_token = hashlib.sha256(timestamp)

        self.db.add(m)
        await self.db.commit()
        await self.db.refresh(m)
        return await self._to_dto(m)

    async def close_session(self, session_id: int) -> None:

        return None

    async def refresh_session(self, refresh_data: RefreshSession) -> Optional[OutSession]:

        return None

    async def get_by_id_session(self,id_session: int) -> OutSession:

        return None


class RefreshTokenRepository(AsyncRefreshTokenRepository):
    def __init__(self,db: AsyncSession):
        self.db = db

    @staticmethod
    async def _to_dto(m: "RefreshTokenModel") -> OutRefreshToken:
        if m is None:
            raise TypeError("_to_dto получил None")
        if isinstance(m,type):
            raise TypeError(f"_to_dto получил класс {m!r}, ожидается экземпляр Session")

        return OutRefreshToken(
            id = m.id,
            session_id = m.session_id,
            revoked = m.revoked,
            created_at = m.created_at,
            expires_at = m.expires_at,
            used_at = m.used_at,
            token_hash = m.token_hash,
        )

    async def create_refresh_token(self,refresh_token_data: CreateRefreshToken) -> OutRefreshToken:
        m = RefreshTokenModel()
        m.session_id = refresh_token_data.session_id
        m.revoked = True
        m.expires_at = refresh_token_data.expires or str(time.time() + 86400)
        m.created_at = datetime.datetime.now()
        m.used_at = datetime.datetime.now()

        timestamp = str(time.time()).encode()

        m.token_hash = hashlib.sha256(timestamp)

        self.db.add(m)
        await self.db.commit()
        await self.db.refresh(m)
        return await self._to_dto(m)

    async def update_refresh_token(self,refresh_token_data: UpdateRefreshToken) -> OutRefreshToken:

        return None

    async def get_by_id_refresh_token(self,id_refresh_token: int) -> Optional[OutRefreshToken]:

        return None

    async def get_by_session_id(self, id_session: int) -> list[Optional[OutRefreshToken]]:

        return None

class OauthClient(AsyncOauthClient):

    def __init__(self,db: AsyncSession):
        self.db = db

    @staticmethod
    async def _to_dto(m: "OAuthClientModel") -> OutOauthClient:
        if m is None:
            raise TypeError("_to_dto получил None")
        if isinstance(m, type):
            raise TypeError(f"_to_dto получил класс {m!r}, ожидается экземпляр Session")

        return OutOauthClient(
            id=m.id,
            name=m.name,
            client_id=m.client_id,
            client_secret=m.client_secret,
            redirect_url=m.redirect_url,
            grand_types=m.grant_types,
            scope=m.scopes,
            is_confidential=m.is_confidential,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    async def create_oauth_client(self, oauth_client_data: CreateOauthClient) -> OutOauthClient:

        return None

    async def Update_oauth_client(self,oauth_client_data: UpdateOauthClient) -> OutOauthClient:

        return None

    async def get_by_id_oauth_client(self, id_oauth_client: int) -> Optional[OutOauthClient]:

        return None
