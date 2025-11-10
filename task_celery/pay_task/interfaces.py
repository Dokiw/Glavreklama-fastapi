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
from task_celery.pay_task.schemas import SubtractionBase, SubtractionRead, SubtractionUpdate, SubtractionCreate


class AsyncSubtractionService(Protocol):

    async def create_subtraction_user(self, create_data: SubtractionCreate, check_data: CheckSessionAccessToken) -> SubtractionRead:
        ...

    async def get_subtraction_by_id(self, id: int, check_data: CheckSessionAccessToken) -> Optional[SubtractionRead]:
        ...

    async def get_subtraction_user_by_id(self, user_id: int, check_data: CheckSessionAccessToken) -> Optional[SubtractionRead]:
        ...

    async def update_subtraction_user(self, update_data: SubtractionUpdate, check_data: CheckSessionAccessToken) -> SubtractionRead:
        ...
