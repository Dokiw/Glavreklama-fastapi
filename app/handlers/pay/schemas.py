from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# ---- Request / Input ---- wallets
class CreateWallets(BaseModel):
    user_id: int = Field(..., alias="UserId")

    class Config:
        validate_by_name = True


class UpdateWallets(BaseModel):
    id: int = Field(..., alias="Id")
    amount: Decimal = Field(..., alias="Amount")
    reason: Optional[str] = Field(None, alias="Reason")

    class Config:
        validate_by_name = True


# ---- Response / Output ---- wallets

class OutWallets(BaseModel):
    id: int = Field(..., alias="Id")
    user_id: int = Field(..., alias="UserId")
    balance: Decimal = Field(..., alias="Balance")
    updated_at: datetime = Field(..., alias="UpdatedAt")

    class Config:
        validate_by_name = True


# ------------------------------------------------

# ---- Request / Input ---- payments

class CreatePayments(BaseModel):
    user_id: int = Field(..., alias="UserId")
    amount: Decimal = Field(..., alias="Amount")
    return_url: str = Field(..., alias="ReturnUrl")
    description: Optional[str] = Field(None, alias="Description")
    currency: str = Field(..., alias="Currency")
    metadata_payments: Optional[dict] = Field(None, alias="MetadataPayments")

    class Config:
        validate_by_name = True


class UpdatePayments(BaseModel):
    id: str = Field(..., alias="Id")
    status: str = Field(..., alias="Status")
    confirmation_url: Optional[str] = Field(None, alias="ConfirmationUrl")
    closed_at: Optional[datetime] = Field(None, alias="ClosedAt")


# ---- Response / Output ---- payments

class CreatePaymentsOut(BaseModel):
    id: str = Field(..., alias="Id")
    confirmation_url: Optional[str] = Field(None, alias="ConfirmationUrl")
    status: str = Field(..., alias="Status")
    wallet_id: int = Field(..., alias="WalletId")
    currency: str = Field(..., alias="Currency")


class PaymentsOut(BaseModel):
    id: str = Field(..., alias="Id")
    user_id: int = Field(..., alias="UserId")
    wallet_id: int = Field(..., alias="WalletId")
    amount: Decimal = Field(..., alias="Amount")
    confirmation_url: Optional[str] = Field(None, alias="ConfirmationUrl")
    confirmation_type: Optional[str] = Field(None, alias="ConfirmationType")
    status: str = Field(..., alias="Status")
    yookassa_payment_id: str = Field(..., alias="YookassaPaymentId")
    currency: str = Field(..., alias="Currency")

    created_at: datetime = Field(..., alias="CreateAt")
    updated_at: Optional[datetime] = Field(None, alias="UpdatedAt")
    closed_at: Optional[datetime] = Field(None, alias="ClosedAt")
