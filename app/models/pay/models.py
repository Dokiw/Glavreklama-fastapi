from typing import List, Optional
from decimal import Decimal, ROUND_DOWN
from typing import Optional, Any, Dict
from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    func,
    text,
    Numeric,
    Index, Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from passlib.hash import bcrypt

from app.db.base import Base
from app.models.coupon import CouponUser


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now())

    # relationship -> User (one-to-one)
    # uselist=False потому что у каждого user ровно один wallet (если это так в твоей логике)
    user: Mapped["User"] = relationship("User", back_populates="wallet", uselist=False)

    # payments, которые ссылаются на этот wallet
    payments: Mapped[List["Payments"]] = relationship(
        "Payments",
        back_populates="wallet",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Payments(Base):
    __tablename__ = "payments"
    __table_args__ = (
        # составной индекс для быстрого поиска "открытых" транзакций по user + status
        Index("idx_payments_user_status", "user_id", "status"),

        # частичный уникальный индекс: уникальность только для ненулевых ключей
        # (предотвращает дублирование idempotency_key, но позволяет NULLы)
        Index(
            "uq_payments_idempotency_not_null",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL")
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    wallet_id: Mapped[int] = mapped_column(
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    amount_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB")
    status: Mapped[str] = mapped_column(String(32), nullable=False,
                                        default="INIT")  # INIT, CREATED, PENDING, SUCCEEDED, FAILED, CANCELED
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True, index=True)
    yookassa_payment_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    confirmation_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    confirmation_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    capture: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    metadata_payments: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now())
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # relationships
    user: Mapped["User"] = relationship("User", back_populates="payments", lazy="joined")
    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="payments", lazy="joined")