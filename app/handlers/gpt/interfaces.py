from typing import Protocol, List, Optional, Dict, Any
from app.handlers.auth.schemas import (
    RoleUser,
    OutUser,
    UserCreate,
    LogInUser,
    AuthResponse, AuthResponseProvide, UserCreateProvide
)
from app.handlers.coupon.schemas import CreateCoupon, OutCoupon, CreateCouponService
from app.handlers.gpt.schemas import OutGPTkey
from app.handlers.session.schemas import CheckSessionAccessToken


class AsyncGPTService(Protocol):

    async def create_gtp_promt(self, model: str, system_prompt: str, image_url: Optional[str],
                               check_data: CheckSessionAccessToken) \
            -> dict:
        ...

    async def get_property_key(self, oauth_client: str, check_data: CheckSessionAccessToken) \
            -> OutGPTkey:
        ...
