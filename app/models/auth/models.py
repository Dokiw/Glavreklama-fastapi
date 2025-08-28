from typing import List

from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from passlib.hash import bcrypt

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger,primary_key=True)
    first_name: Mapped[str | None] = mapped_column(String(255),nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255),nullable=True)
    user_name: Mapped[str] = mapped_column(String(255),unique=True)
    email: Mapped[str | None] = mapped_column(String(255),unique=True,nullable=True)

    pass_hash: Mapped[str | None] = mapped_column("pass",String(255),nullable=True)

    role_id: Mapped[int | None] = mapped_column(
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True
    )

    status: Mapped[bool] = mapped_column(Boolean,default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")

    # NEW: провайдеры (telegram, google, ...)
    providers: Mapped[List["UserProviders"]] = relationship(
        "UserProviders",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property
    def password(self) -> None:
        raise AttributeError("Password is write-only")

    @password.setter
    def password(self, plaintext: str) -> None:
        """Хэшируем пароль при установке через property."""
        self.pass_hash = bcrypt.hash(plaintext)

    def verify_password(self, plaintext: str) -> bool:
        return bcrypt.verify(plaintext, self.pass_hash)

    async def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_name": self.user_name,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "role_id": self.role_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigInteger,primary_key=True)
    name: Mapped[str] = mapped_column(String(100),unique=True)
    description: Mapped[str | None] = mapped_column(Text,nullable=True)

    users: Mapped[List["User"]] = relationship("User", back_populates="role")
