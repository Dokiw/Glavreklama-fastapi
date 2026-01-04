from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# ---- Request / Input ----
class CreateCoupon(BaseModel):
    user_id: int = Field(..., alias="UserId")
    name: str = Field(..., alias="name")
    description: Optional[str] = Field(None, alias="idUser")
    promo_count: int = Field(..., alias="idUser")
    status: Optional[bool] = Field(None, alias="Status")
    token_hash: str = Field(..., alias="tokenHash")

    class Config:
        validate_by_name = True


class CreateCouponService(BaseModel):
    user_id: int = Field(..., alias="UserId")
    name: str = Field(..., alias="name")
    description: Optional[str] = Field(None, alias="idUser")
    status: Optional[bool] = Field(None, alias="Status")

    class Config:
        validate_by_name = True


# ---- Response / Output ----
class OutCoupon(BaseModel):
    id: int = Field(..., alias="id")
    user_id: int = Field(..., alias="userId")
    name: str = Field(..., alias="name")
    description: Optional[str] = Field(None, alias="description")
    promo_count: int = Field(..., alias="promoCount")
    status: Optional[bool] = Field(None, alias="status")
    token_hash: Optional[str] = Field(None, alias="tokenHash")
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        populate_by_name = True  # чтобы можно было и по алиасам, и по имени


class PaginateOutCoupon(BaseModel):
    data: List[OutCoupon] = Field(...)
    count: int = Field(...)
    limit: int = Field(...)
    offset: int = Field(...)
