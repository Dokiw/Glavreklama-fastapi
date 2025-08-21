import datetime
import time

from app.handlers.session.schemas import *

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select, update
from app.models.sessions.models import Session as SessionModel, RefreshToken as RefreshTokenModel, \
    OAuthClient as OAuthClientModel

from app.handlers.session.interfaces import AsyncSessionRepository, AsyncRefreshTokenRepository, AsyncOauthClient

from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from app.models.auth.models import User as UserModel, Role as RoleModel

import hashlib


class SessionRepository(AsyncSessionRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _to_dto(self, m: "SessionModel") -> OutSession:
        if m is None:
            raise TypeError("_to_dto получил None")
        if isinstance(m, type):
            raise TypeError(f"_to_dto получил класс {m!r}, ожидается экземпляр Session")

        # запросим последний refresh_token по created_at
        stmt = (
            select(RefreshTokenModel.id)
            .where(RefreshTokenModel.session_id == m.id and RefreshTokenModel.revoked == True)
            .order_by(RefreshTokenModel.created_at.desc())
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

        # Делаем уникальный токен
        timestamp = str(time.time()).encode()
        m.access_token = hashlib.sha256(timestamp).hexdigest()

        # Надо также сделать рефреш токен
        self.db.add(m)
        await self.db.commit()
        await self.db.refresh(m)
        return await self._to_dto(m)

    async def close_session(self, session_id: int) -> None:
        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(is_active=False)
        )
        await self.db.execute(stmt)
        await self.db.commit()

        return None

    async def refresh_session(self, refresh_data: RefreshSession) -> Optional[OutSession]:

        new_token = refresh_data.access_token
        if not new_token:
            timestamp = str(time.time()).encode()
            new_token = hashlib.sha256(timestamp).hexdigest()

        # Строим UPDATE-запрос
        stmt = (
            update(SessionModel)
            .where(SessionModel.id == refresh_data.id)
            .values(
                user_id=refresh_data.user_id,
                client_id=refresh_data.client_id,
                ip_address=refresh_data.ip_address,
                user_agent=refresh_data.user_agent,
                access_token=new_token
            )
            .returning(SessionModel)  # чтобы получить обновлённый объект
        )

        result = await self.db.execute(stmt)
        row = result.first()
        await self.db.commit()

        if row is None:
            return None

        return await self._to_dto(row[0])

    async def get_by_id_session(self, id_session: int) -> Optional[OutSession]:
        result = await self.db.get(SessionModel, id_session)
        return await self._to_dto(result) if result else None

    async def get_by_id_user_session(self, user_id: int) -> Optional[OutSession]:
        q = select(SessionModel).where(SessionModel.user_id == user_id)
        result = await self.db.execute(q)
        result = result.scalar_one_or_none()
        return await self._to_dto(result)

    async def get_by_id_client_session(self, client_id: int) -> list[OutSession]:
        q = select(SessionModel).where(SessionModel.client_id == client_id)
        result = await self.db.execute(q)
        sessions = result.scalars().all()
        return [await self._to_dto(r) for r in sessions]

    async def get_by_access_token_session(self, access_token: str) -> Optional[OutSession]:
        q = select(SessionModel).where(SessionModel.access_token == access_token)
        result = await self.db.execute(q)
        session = result.scalar_one_or_none()
        return await self._to_dto(session)


class RefreshTokenRepository(AsyncRefreshTokenRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    async def _to_dto(m: "RefreshTokenModel") -> OutRefreshToken:
        if m is None:
            raise TypeError("_to_dto получил None")
        if isinstance(m, type):
            raise TypeError(f"_to_dto получил класс {m!r}, ожидается экземпляр Session")

        return OutRefreshToken(
            id=m.id,
            session_id=m.session_id,
            revoked=m.revoked,
            created_at=m.created_at,
            expires_at=m.expires_at,
            used_at=m.used_at,
            token_hash=m.token_hash,
        )

    async def create_refresh_token(self, refresh_token_data: CreateRefreshToken) -> OutRefreshToken:
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

    async def update_refresh_token(self, refresh_token_data: UpdateRefreshToken) -> OutRefreshToken:
        #todo - нужно поменять генерацию токена, у него есть проблемы
        timestamp = str(time.time()).encode()
        new_token = hashlib.sha256(timestamp).hexdigest()

        stmt = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.id == refresh_token_data.id)
            .values(
                session_id=refresh_token_data.session_id,
                revoked=refresh_token_data.revoked,
                token_hash=new_token,
                expires_at=refresh_token_data.expires_at
            )
            .returning(RefreshTokenModel)
        )

        result = await self.db.execute(stmt)
        result = result.scalar_one_or_none()
        await self.db.commit()

        return await self._to_dto(result)

    async def get_by_id_refresh_token(self, id_refresh_token: int) -> Optional[OutRefreshToken]:
        result = await self.db.get(RefreshTokenModel, id_refresh_token)
        return self._to_dto(result) if result else None

    async def get_by_session_id(self, id_session: int, offset: int = 0, limit: int = 50) -> list[
        Optional[OutRefreshToken]]:
        stmt = (
            select(RefreshTokenModel)
            .where(RefreshTokenModel.session_id == id_session)
            .order_by(RefreshTokenModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        result = result.scalars().all()
        return [await self._to_dto(r) for r in result]


class OauthClient(AsyncOauthClient):
    def __init__(self, db: AsyncSession):
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
        m = OAuthClientModel()
        m.name = oauth_client_data.name
        m.client_id = oauth_client_data.client_id

        timestamp = str(time.time()).encode()
        m.client_secret = hashlib.sha256(timestamp)

        m.created_at = datetime.datetime.now()
        m.redirect_url = oauth_client_data.redirect_url
        m.grant_types = oauth_client_data.grant_types
        m.is_confidential = oauth_client_data.is_confidential
        m.revoked = True
        m.scopes = m.scopes
        m.updated_at = datetime.datetime.now()

        self.db.add(m)
        await self.db.commit()
        await self.db.refresh(m)
        return await self._to_dto(m)

    async def update_oauth_client(self, oauth_client_data: UpdateOauthClient) -> OutOauthClient:
        stmt = (
            update(OAuthClientModel)
            .where(OAuthClientModel.id == oauth_client_data.id)
            .values(
                name=oauth_client_data.name,
                client_id=oauth_client_data.client_id,
                redirect_url=oauth_client_data.redirect_url,
                grant_types=oauth_client_data.grant_types,
                scopes=oauth_client_data.scopes,
                is_confidential=oauth_client_data.is_confidential,
            )
        )

        result = await self.db.execute(stmt)
        result = result.scalar_one_or_none()
        await self.db.commit()

        return await self._to_dto(result)

    async def get_by_id_oauth_client(self, id_oauth_client: int) -> Optional[OutOauthClient]:
        result = self.db.get(OAuthClientModel, id_oauth_client)
        return self._to_dto(result) if result else None
