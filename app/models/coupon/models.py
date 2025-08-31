from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    func,
    text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from passlib.hash import bcrypt
from app.db.base import Base


class CouponUser(Base):
    __tablename__ = "coupon_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(100))

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    promo_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    status: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    token_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)

    # relations
    user: Mapped["User"] = relationship("User", back_populates="coupons")


