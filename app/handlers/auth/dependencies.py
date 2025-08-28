from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.handlers.auth.schemas import LogInUser, AuthResponse
from app.handlers.auth.service import SqlAlchemyAuth
from app.handlers.auth.UOW import SqlAlchemyUnitOfWork, IUnitOfWorkAuth
from app.handlers.session.dependencies import SessionServiceDep  # <- твой сервис сессий
from app.handlers.session.service import AsyncSessionService  # <- интерфейс/сервис сессий
from fastapi import Depends
from app.handlers.providers.dependencies import ProviderUserServiceDep


# фабрика UoW
async def get_uow(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[IUnitOfWorkAuth, None]:
    uow = SqlAlchemyUnitOfWork(lambda: db)  # тут session_factory — обычная функция
    async with uow:
        yield uow


# фабрика сервиса Auth с передачей SessionService
def get_auth_service(
        session_service: SessionServiceDep,
        provide_user: ProviderUserServiceDep,
        uow: IUnitOfWorkAuth = Depends(get_uow),
) -> SqlAlchemyAuth:
    return SqlAlchemyAuth(uow, session_service, provide_user)


async def get_auth_service_dep(
        session_service: SessionServiceDep,
        provide_user: ProviderUserServiceDep,
        uow: IUnitOfWorkAuth = Depends(get_uow),
) -> SqlAlchemyAuth:
    return SqlAlchemyAuth(uow, session_service, provide_user)


# alias для роутов
AuthServiceDep = Annotated[SqlAlchemyAuth, Depends(get_auth_service)]
