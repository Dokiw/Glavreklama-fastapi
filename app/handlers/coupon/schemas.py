from typing import Optional
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


class CreateCouponService(BaseModel):
    user_id: int = Field(..., alias="UserId")
    name: str = Field(..., alias="name")
    description: Optional[str] = Field(None, alias="idUser")
    status: Optional[bool] = Field(None, alias="Status")


# ---- Response / Output ----
class OutCoupon(BaseModel):
    id: int = Field(..., alias="Id")
    user_id: int = Field(..., alias="userId")
    name: str = Field(..., alias="name")
    description: Optional[str] = Field(None, alias="idUser")
    promo_count: int = Field(..., alias="idUser")
    status: Optional[bool] = Field(None, alias="status")
    token_hash: str = Field(..., alias="tokenHash")
    created_at: datetime = Field(..., alias="createdAt")
