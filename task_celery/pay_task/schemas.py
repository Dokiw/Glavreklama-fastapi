from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field


class SubtractionBase(BaseModel):
    user_id: int = Field(..., alias="UserId")
    card: bool = Field(..., alias="Card")  # исправил alias на латиницу

    model_config = {
        "populate_by_name": True,  # <-- позволяет заполнять модель по имени поля (user_id, card)
        "validate_assignment": True,
        "from_attributes": True,  # если ты используешь model.from_orm-style
    }


class SubtractionUpdate(BaseModel):
    user_id: int = Field(..., alias="UserId")
    card: Optional[bool] = Field(None, alias="Card")
    last_error: Optional[str] = Field(None, alias="LastError")
    idempotency_key: Optional[str] = Field(None, alias="IdempotencyKey")
    amount_value: Optional[Decimal] = Field(None, alias="AmountValue")
    next_run: Optional[datetime] = Field(None, alias="NextRun")
    status: Optional[str] = Field(None, alias="Status")
    attempts: Optional[int] = Field(None, alias="Attempts")
    last_tried_at: Optional[datetime] = Field(None, alias="LastTriedAt")

    model_config = {
        "populate_by_name": True,  # <-- позволяет заполнять модель по имени поля (user_id, card)
        "validate_assignment": True,
        "from_attributes": True,  # если ты используешь model.from_orm-style
    }


class SubtractionRead(BaseModel):
    id: str = Field(..., alias="Id")
    user_id: int = Field(..., alias="UserId")
    card: bool = Field(..., alias="Card")
    service_code: Optional[str] = Field(None, alias="ServiceCode")
    amount_value: Decimal = Field(..., alias="AmountValue")
    currency: str = Field(..., alias="Currency")
    billing_period: Optional[str] = Field(None, alias="BillingPeriod")
    next_run: Optional[datetime] = Field(None, alias="NextRun")
    status: str = Field(..., alias="Status")
    idempotency_key: Optional[str] = Field(None, alias="IdempotencyKey")
    attempts: int = Field(..., alias="Attempts")
    last_error: Optional[str] = Field(None, alias="LastError")
    last_tried_at: Optional[datetime] = Field(None, alias="LastTriedAt")
    created_at: datetime = Field(..., alias="CreatedAt")
    updated_at: datetime = Field(..., alias="UpdatedAt")
    closed_at: Optional[datetime] = Field(None, alias="ClosedAt")

    model_config = {
        "populate_by_name": True,  # <-- позволяет заполнять модель по имени поля (user_id, card)
        "validate_assignment": True,
        "from_attributes": True,  # если ты используешь model.from_orm-style
    }


class SubtractionList(BaseModel):
    subtractions: List[SubtractionRead] = Field(..., alias="Subtractions")
    total: int = Field(..., alias="Total")
    offset: int = Field(..., alias="Offset")
    limit: int = Field(..., alias="Limit")

    model_config = {
        "populate_by_name": True,  # <-- позволяет заполнять модель по имени поля (user_id, card)
        "validate_assignment": True,
        "from_attributes": True,  # если ты используешь model.from_orm-style
    }


class SubtractionCreate(BaseModel):
    user_id: int = Field(..., alias="UserId")
    card: bool = Field(..., alias="Card")

    # optional fields
    service_code: Optional[str] = Field(None, alias="ServiceCode")
    amount_value: Optional[Decimal] = Field(None, alias="AmountValue")
    currency: Optional[str] = Field(None, alias="Currency")
    billing_period: Optional[str] = Field(None, alias="BillingPeriod")
    next_run: Optional[datetime] = Field(None, alias="NextRun")
    status: Optional[str] = Field(None, alias="Status")
    idempotency_key: Optional[str] = Field(None, alias="IdempotencyKey")

    model_config = {
        "populate_by_name": True,  # <-- позволяет заполнять модель по имени поля (user_id, card)
        "validate_assignment": True,
        "from_attributes": True,  # если ты используешь model.from_orm-style
    }
