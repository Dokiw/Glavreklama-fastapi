from app.handlers.providers.schemas import ProviderRegisterRequest, ProviderLoginRequest, ProviderOut

from sqlalchemy.ext.asyncio import AsyncSession
from app.handlers.providers.interfaces import AsyncProviderRepository
from sqlalchemy import select
from app.models.providers.models import UserProviders

from typing import Optional, List


class ProvideRepository(AsyncProviderRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _to_dto(m: "UserProviders") -> ProviderOut:
        if m is None:
            raise TypeError("_to_dto получил None")
        if isinstance(m, type):
            raise TypeError(f"_to_dto получил класс {m!r}, ожидается экземпляр User")
        return ProviderOut(
            provider=m.provider,
            provider_user_id=m.provider_user_id,
            username=m.username,
            first_name=m.first_name,
            last_name=m.last_name,
            photo_url=m.photo_url,
            is_premium=m.is_premium,
            auth_date=m.auth_date,
            user_id=m.user_id
        )

    async def create_provider_user(self, created_data: ProviderRegisterRequest) -> Optional[ProviderOut]:
        m = UserProviders()
        m.provider = created_data.provider
        m.provider_user_id = created_data.provider_user_id
        m.user_id = created_data.user_id
        m.username = created_data.username
        m.first_name = created_data.first_name
        m.last_name = created_data.last_name
        m.photo_url = created_data.photo_url
        m.is_premium = created_data.is_premium
        m.auth_date = created_data.auth_date
        self.db.add(m)
        await self.db.flush()
        return self._to_dto(m)

    async def get_by_provider_and_user_id(self, provider: str, provider_user_id: str) -> Optional[ProviderOut]:
        stmt = (
            select(UserProviders)
            .where((UserProviders.provider_user_id == provider_user_id) & (UserProviders.provider == provider))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        result = result.scalar_one_or_none()
        return self._to_dto(result) if result else None

    async def get_by_id_provide(self, id_provide: int) -> Optional[ProviderOut]:
        provide: Optional[Optional] = await self.db.get(UserProviders, id_provide)
        return self._to_dto(provide) if provide else None
