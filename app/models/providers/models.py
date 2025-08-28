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


class UserProviders(Base):
    __tablename__ = "user_providers"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_provider_provider_user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. 'telegram', 'google'
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)  # например telegram user.id как строка

    # профильные поля (копируем из initData / профиля)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_premium: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # auth metadata
    auth_date: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # relations
    user: Mapped["User"] = relationship("User", back_populates="providers")
    sessions: Mapped[List["Session"]] = relationship(
        "Session",
        back_populates="provider",
        passive_deletes=True
    )