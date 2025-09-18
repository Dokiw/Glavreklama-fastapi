from typing import Optional

from app.core.abs.unit_of_work import IUnitOfWorkProvider
from app.handlers.providers.interfaces import AsyncProvidersService
from app.handlers.providers.schemas import ProviderRegisterRequest, ProviderOut, ProviderLoginRequest
from fastapi import HTTPException, status


class ProviderUserRepository(AsyncProvidersService):
    def __init__(self, uow: IUnitOfWorkProvider):
        self.uow = uow

    async def create_provider_user(self, created_data: ProviderRegisterRequest) -> Optional[ProviderOut]:
        try:
            async with self.uow:
                provide: Optional[ProviderOut] = await self.uow.provider.create_provider_user(created_data)
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)} -- log1"
            )
        return provide

    async def login_provider_user(self, login_data: ProviderLoginRequest) -> Optional[ProviderOut]:
        try:
            async with self.uow:
                provide: Optional[ProviderOut] = await self.uow.provider.get_by_provider_and_user_id(provider=login_data.provider, provider_user_id= login_data.provider_user_id)

                if provide is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ошибка целостности данных "
                    )

        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )
        return provide

    async def get_by_provider_and_user_id(self, login_data: ProviderLoginRequest) -> Optional[ProviderOut]:
        try:
            async with self.uow:
                provide: Optional[ProviderOut] = await self.uow.provider.get_by_provider_and_user_id(login_data.provider,login_data.provider_user_id)

                if provide is None:
                    return None

        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )
        return provide
