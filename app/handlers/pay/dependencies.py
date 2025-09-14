# app/handlers/session/dependencies.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.handlers.pay.interfaces import AsyncWalletService, AsyncPaymentService, AsyncApiPaymentService
from app.handlers.pay.service import SqlAlchemyServiceWallet, SqlAlchemyServicePayment, SqlAlchemyServicePaymentApi

from app.handlers.session.dependencies import SessionServiceDep

from app.handlers.pay.UOW import SqlAlchemyUnitOfWorkWallet, SqlAlchemyUnitOfWorkPayment, IUnitOfWorkWallet, \
    IUnitOfWorkPayment


# фабрика UnitOfWork
async def get_uow_wallet(db: AsyncSession = Depends(get_db)) -> IUnitOfWorkWallet:
    async with SqlAlchemyUnitOfWorkWallet(lambda: db) as uow:
        yield uow


# фабрика сервиса сессий
def get_session_service(
        session_service: SessionServiceDep,
        uow: IUnitOfWorkWallet = Depends(get_uow_wallet)
) -> AsyncWalletService:
    return SqlAlchemyServiceWallet(session_service=session_service, uow=uow)


# alias для роутов
walletServiceDep = Annotated[SqlAlchemyServiceWallet, Depends(get_session_service)]


# фабрика UnitOfWork
async def get_uow_payment(db: AsyncSession = Depends(get_db)) -> IUnitOfWorkPayment:
    async with SqlAlchemyUnitOfWorkPayment(lambda: db) as uow:
        yield uow


# фабрика сервиса сессий
def get_session_service_payment(
        session_service: SessionServiceDep,
        wallet_service: walletServiceDep,
        payment_service_api: SqlAlchemyServicePaymentApi = Depends(),
        uow: IUnitOfWorkPayment = Depends(get_uow_payment)
) -> AsyncPaymentService:
    return SqlAlchemyServicePayment(session_service=session_service, uow=uow, wallet_service=wallet_service,
                                    payment_service_api=payment_service_api)


# alias для роутов
paymentServiceDep = Annotated[SqlAlchemyServicePayment, Depends(get_session_service_payment)]
