from typing import Protocol, List, Optional, Dict, Any
from app.handlers.auth.schemas import (
    RoleUser,
    OutUser,
    UserCreate,
    LogInUser,
    AuthResponse, AuthResponseProvide, UserCreateProvide
)
from app.handlers.coupon.schemas import CreateCoupon, OutCoupon, CreateCouponService
from app.handlers.session.schemas import CheckSessionAccessToken


class AsyncCouponRepository(Protocol):

    async def create_coupon(self, coupon_data: CreateCoupon) -> Optional[OutCoupon]:
        ...

    async def get_by_user_id(self, user_id: int) -> Optional[List[OutCoupon]]:
        ...

    async def get_info_by_coupon_id(self, id: int) -> Optional[OutCoupon]:
        ...

    async def get_by_token_hash(self, token: str) -> Optional[OutCoupon]:
        ...

    async def used_coupon(self, user_id: int, token: str) -> Optional[OutCoupon]:
        ...


class AsyncCouponService(Protocol):
    """Сервис для купонов"""

    async def create_coupon(self, coupon_data: CreateCouponService, check_data: CheckSessionAccessToken) -> Optional[OutCoupon]:
        ...

    async def used_coupon(self, user_id: int, token: str, check_data: CheckSessionAccessToken) -> Optional[OutCoupon]:
        ...

    async def get_by_user_id(self, check_data: CheckSessionAccessToken) -> Optional[List[OutCoupon]]:
        ...

    async def get_info_by_coupon_id(self, id: int, check_data: CheckSessionAccessToken) -> Optional[OutCoupon]:
        ...

    async def get_by_token_hash(self, token: str, check_data: CheckSessionAccessToken) -> Optional[OutCoupon]:
        ...

    async def get_by_any_user_id(self,id_user:int, check_data: CheckSessionAccessToken) -> Optional[List[OutCoupon]]:
        ...
