from typing import Protocol, List, Optional
from app.handlers.providers.schemas import ProviderRegisterRequest, ProviderLoginRequest, ProviderOut


class AsyncProvidersService(Protocol):

    async def create_provider_user(self, created_data: ProviderRegisterRequest) -> Optional[ProviderOut]:
        ...

    async def login_provider_user(self, login_data: ProviderLoginRequest) -> Optional[ProviderOut]:
        ...

    async def get_by_provider_and_user_id(self, login_data: ProviderLoginRequest) -> Optional[ProviderOut]:
        ...


class AsyncProviderRepository(Protocol):

    async def create_provider_user(self, created_data: ProviderRegisterRequest) -> Optional[ProviderOut]:
        ...

    async def get_by_provider_and_user_id(self, provider: str, provider_user_id: str) -> Optional[ProviderOut]:
        ...

    async def get_by_id_provide(self, id_provide: int) -> Optional[ProviderOut]:
        ...
