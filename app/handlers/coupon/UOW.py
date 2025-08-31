from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.abs.unit_of_work import IUnitOfWorkCoupon
from app.handlers.coupon.interfaces import AsyncCouponRepository
from app.handlers.coupon.crud import CouponRepository


class SqlAlchemyUnitOfWork(IUnitOfWorkCoupon):
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._session: Optional[AsyncSession] = None
        self.coupon_repo: Optional[AsyncCouponRepository] = None

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        # Если session_factory асинхронная функция, нужно await
        self._session = self.session_factory()
        self.coupon_repo = CouponRepository(self._session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        await self._session.close()

    @property
    def coupon(self) -> AsyncCouponRepository:
        return self.coupon_repo

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
