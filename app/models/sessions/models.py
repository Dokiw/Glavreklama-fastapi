from typing import List
from typing import Optional

from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    func,
    Integer,
    Index,  
    text,   
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(BigInteger,primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    client_id: Mapped[Optional[int]] = mapped_column(BigInteger,ForeignKey("oauth_clients.id"),nullable=True)
    access_token: Mapped[Optional[str]] = mapped_column(Text,nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String,nullable=True)
    user_agent: Mapped[Optional[str]]= mapped_column(Text,nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)

    logged_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime,nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="sessions")

    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="session",
        foreign_keys="[RefreshToken.session_id]",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    client: Mapped[Optional["OAuthClient"]] = relationship("OAuthClient",back_populates="sessions")

    # Исправляем индекс - должен быть для user_id
    __table_args__ = (
        Index('sessions_user_id_is_active_idx', 'user_id', 'is_active'),
        Index('sessions_client_id_index', 'client_id'),
    )

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(BigInteger,primary_key=True)
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sessions.id"))
    token_hash: Mapped[str] = mapped_column(String(255),unique=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    session: Mapped["Session"] = relationship("Session", back_populates="refresh_tokens")

    # Добавляем индекс для refresh_tokens
    __table_args__ = (
        Index('refresh_tokens_session_id_index', 'session_id'),
    )

class OAuthClient(Base):
    __tablename__ = "oauth_clients"

    id: Mapped[int] = mapped_column(BigInteger,primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    client_id: Mapped[str] = mapped_column(String(100),unique=True)
    client_secret: Mapped[str] = mapped_column(String(255))
    redirect_url: Mapped[str | None] = mapped_column(Text,nullable=True)
    grant_types: Mapped[list[str]] = mapped_column(ARRAY(String), server_default=text("ARRAY['authorization_code']"))
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), server_default=text("ARRAY[]::TEXT[]"))
    is_confidential: Mapped[bool] = mapped_column(Boolean)
    revoked: Mapped[bool] = mapped_column(Boolean)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="client")
