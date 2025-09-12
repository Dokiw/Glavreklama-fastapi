# app/handlers/session/dependencies.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.handlers.auth.dependencies import RoleServiceDep

from app.handlers.session.dependencies import SessionServiceDep

from app.handlers.coupon.UOW import SqlAlchemyUnitOfWork, IUnitOfWorkWallet
from app.handlers.coupon.interfaces import AsyncCouponService
from app.handlers.coupon.service import SqlAlchemyCoupon


# фабрика UnitOfWork
async def get_uow(db: AsyncSession = Depends(get_db)) -> IUnitOfWorkWallet:
    async with SqlAlchemyUnitOfWork(lambda: db) as uow:
        yield uow


# фабрика сервиса сессий
def get_session_service(
        session_service: SessionServiceDep,
        role_service: RoleServiceDep,
        uow: IUnitOfWorkWallet = Depends(get_uow)
) -> AsyncCouponService:
    return SqlAlchemyCoupon(session_service=session_service, uow=uow, role_service=role_service)


# alias для роутов
couponServiceDep = Annotated[SqlAlchemyCoupon, Depends(get_session_service)]
