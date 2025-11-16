# app/handlers/session/dependencies.py
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.abs.unit_of_work import IUnitOfWorkSubtraction, IUnitOfWorkSession, IUnitOfWorkWallet
from app.db.session import get_db
from app.handlers.pay.UOW import IUnitOfWorkPayment, SqlAlchemyUnitOfWorkWallet
from app.handlers.pay.dependencies import walletServiceDep
from app.handlers.pay.interfaces import AsyncPaymentService
from app.handlers.pay.service import SqlAlchemyServicePayment, SqlAlchemyServiceWallet
from app.handlers.session.UOW import SqlAlchemyUnitOfWork
from app.handlers.session.dependencies import SessionServiceDep
from app.handlers.session.service import SqlAlchemyServiceSession, SqlAlchemyServiceOauthClient, \
    SqlAlchemyServiceRefreshToken
from task_celery.pay_task.UOW import SqlAlchemyUnitOfWorkSubtraction
from task_celery.pay_task.interfaces import AsyncSubtractionService
from task_celery.pay_task.service import SqlAlchemySubtractionService


# фабрика UnitOfWork
async def get_uow_subtraction(db: AsyncSession = Depends(get_db)) -> IUnitOfWorkSubtraction:
    async with SqlAlchemyUnitOfWorkSubtraction(lambda: db) as uow:
        yield uow


def get_session_service_subtraction(
        session_service: SessionServiceDep,
        wallet_service: walletServiceDep,
        uow: IUnitOfWorkSubtraction = Depends(get_uow_subtraction)
) -> AsyncSubtractionService:
    return SqlAlchemySubtractionService(session_service=session_service, uow=uow, wallet_service=wallet_service)

from contextlib import asynccontextmanager

@asynccontextmanager
async def get_subtraction_uow(session):
    uow = SqlAlchemyUnitOfWorkSubtraction(lambda: session)
    await uow.__aenter__()
    try:
        yield uow
    finally:
        await uow.__aexit__(None, None, None)


async def build_subtraction_service() -> SqlAlchemySubtractionService:
    agen = get_db()  # async generator
    session = await agen.__anext__()  # получаем AsyncSession
    try:
        async with get_subtraction_uow(session) as subtraction_uow:
            session_uow = SqlAlchemyUnitOfWork(lambda: session)
            wallet_uow = SqlAlchemyUnitOfWorkWallet(lambda: session)

            session_service = SqlAlchemyServiceSession(
                uow=session_uow,
                refresh_service=SqlAlchemyServiceRefreshToken(session_uow),
                oauth_client=SqlAlchemyServiceOauthClient(session_uow)
            )

            wallet_service = SqlAlchemyServiceWallet(
                uow=wallet_uow,
                session_service=session_service
            )

            subtraction_service = SqlAlchemySubtractionService(
                uow=subtraction_uow,
                session_service=session_service,
                wallet_service=wallet_service
            )

            return subtraction_service
    finally:
        await agen.aclose()

subtractionServiceDep = Annotated[SqlAlchemySubtractionService, Depends(get_session_service_subtraction)]
