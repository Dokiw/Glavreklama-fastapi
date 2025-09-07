import hashlib
from datetime import datetime as dt, timezone


import time
from sqlalchemy.ext.asyncio import AsyncSession

from typing import TYPE_CHECKING, Optional, List

from app.handlers.coupon.schemas import OutCoupon, CreateCoupon
from app.handlers.coupon.interfaces import AsyncCouponService, AsyncCouponRepository
from app.main import logger
from app.models import CouponUser

from sqlalchemy import select, update


class CouponRepository(AsyncCouponRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _to_dto(self, m: "CouponUser") -> OutCoupon:
        if m is None:
            raise TypeError("_to_dto получил None")
        if isinstance(m, type):
            raise TypeError(f"_to_dto получил класс {m!r}, ожидается экземпляр Session")

        return OutCoupon(
            id=m.id,
            name=m.name,
            user_id=m.user_id,
            description=m.description,
            promo_count=m.promo_count,
            status=m.status,
            token_hash=m.token_hash,
            created_at=m.created_at
        )

    async def create_coupon(self, coupon_data: CreateCoupon) -> Optional[OutCoupon]:
        m = CouponUser()
        m.created_at = dt.now(timezone.utc)

        m.token_hash = coupon_data.token_hash

        m.is_active = True
        m.status = coupon_data.status
        m.user_id = coupon_data.user_id
        m.promo_count = coupon_data.promo_count
        m.description = coupon_data.description
        m.name = coupon_data.name

        self.db.add(m)
        await self.db.flush()

        return await self._to_dto(m) if m else None

    async def get_by_user_id(self, user_id: int) -> Optional[List[OutCoupon]]:
        q = select(CouponUser).where((CouponUser.user_id == user_id) & (CouponUser.is_active == True)).order_by(CouponUser.created_at.desc()).limit(5)
        result = await self.db.execute(q)
        sessions = result.scalars().all()
        if sessions is None:
            return None
        return [await self._to_dto(r) for r in sessions]

    async def get_info_by_coupon_id(self, id: int) -> Optional[OutCoupon]:
        result = await self.db.get(CouponUser, id)
        return await self._to_dto(result) if result else None

    async def get_by_token_hash(self, token: str) -> Optional[OutCoupon]:
        q = (
            select(CouponUser)
            .where(
                (CouponUser.token_hash == token) & (CouponUser.is_active == True)
            )
            .order_by(CouponUser.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(q)
        result = result.scalars().first()
        return await self._to_dto(result) if result else None

    async def used_coupon(self, user_id: int, token: str) -> Optional[OutCoupon]:
        stmt = (
            update(CouponUser)
            .where(
                (CouponUser.user_id == user_id) & (CouponUser.token_hash == token) & (CouponUser.is_active == True)
            )
        )

        stmt = stmt.values(is_active=False).returning(CouponUser)
        result = await self.db.execute(stmt)

        result = result.scalar_one_or_none()

        return await self._to_dto(result) if result else None
