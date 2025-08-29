from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ---- Request / Input ----

class ProviderRegisterRequest(BaseModel):
    provider: str  # 'telegram', 'google'
    provider_user_id: str
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    photo_url: Optional[str]
    is_premium: Optional[bool]
    auth_date: Optional[datetime]
    user_id: int


class ProviderLoginRequest(BaseModel):
    provider: str
    provider_user_id: str


# ---- Response / Output ----

class ProviderOut(BaseModel):
    provider: str  # 'telegram', 'google'
    provider_user_id: str
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    photo_url: Optional[str]
    is_premium: Optional[bool]
    auth_date: Optional[datetime]
    user_id: int
