from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel
from pydantic import Field


class SubtractionBase(BaseModel):
    user_id: int = Field(..., alias="UserId")
    card: bool = Field(..., alias="Сard")


class SubtractionUpdate(BaseModel):
    user_id: int = Field(..., alias="UserId")
    card: bool = Field(..., alias="Сard")
    closed_at: Optional[datetime] = Field(..., alias="createdAt")

    class Config:
        from_attributes = True


class SubtractionRead(BaseModel):
    id: int = Field(..., alias="id")
    user_id: int = Field(..., alias="UserId")
    card: bool = Field(..., alias="Сard")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="createdAt")
    closed_at: Optional[datetime] = Field(..., alias="createdAt")

    class Config:
        from_attributes = True


class SubtractionList(BaseModel):
    subtractions: list = Field(..., alias="Subtractions")
    total: int = Field(..., alias="Total")
    offset: int = Field(..., alias="Offset")
    limit: int = Field(..., alias="Limit")

    class Config:
        from_attributes = True


class SubtractionCreate(BaseModel):
    user_id: int = Field(..., alias="UserId")

    class Config:
        validate_by_name = True
