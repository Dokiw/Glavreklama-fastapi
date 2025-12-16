from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# ---- Request / Input ----
class CreateCoupon(BaseModel):
    user_id: int = Field(..., alias="UserId")
    name: str = Field(..., alias="Name")
    description: Optional[str] = Field(None, alias="UserID")
    promo_count: int = Field(..., alias="UserId")
    status: Optional[bool] = Field(None, alias="Status")
    token_hash: str = Field(..., alias="TokenHash")

    class Config:
        validate_by_name = True


class CreateCouponService(BaseModel):
    user_id: int = Field(..., alias="UserId")
    name: str = Field(..., alias="Name")
    description: Optional[str] = Field(None, alias="UserId")
    status: Optional[bool] = Field(None, alias="Status")

    class Config:
        validate_by_name = True


# ---- Response / Output ----
class OutCoupon(BaseModel):
    id: int = Field(..., alias="Id")
    user_id: int = Field(..., alias="UserId")
    name: str = Field(..., alias="Name")
    description: Optional[str] = Field(None, alias="Description")
    promo_count: int = Field(..., alias="PromoCount")
    status: Optional[bool] = Field(None, alias="Status")
    token_hash: Optional[str] = Field(None, alias="TokenHash")
    created_at: datetime = Field(..., alias="CreatedAt")

    class Config:
        populate_by_name = True  # чтобы можно было и по алиасам, и по имени
