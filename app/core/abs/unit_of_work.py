# app/core/abs/unit_of_work.py
from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from typing import Optional

from app.handlers.auth.interfaces import AsyncUserRepository, AsyncRoleRepository
from app.handlers.session.interfaces import AsyncSessionRepository, AsyncRefreshTokenRepository, \
    AsyncOauthClientRepository

from app.handlers.providers.interfaces import AsyncProviderRepository
from app.handlers.coupon.interfaces import AsyncCouponRepository


class IUnitOfWorkSession(AbstractAsyncContextManager, ABC):
    sessions: AsyncSessionRepository
    refresh_tokens: AsyncRefreshTokenRepository
    oauth_clients: AsyncOauthClientRepository

    @property
    @abstractmethod
    def sessions(self) -> "AsyncSessionRepository":
        pass

    @property
    @abstractmethod
    def refresh_tokens(self) -> "AsyncRefreshTokenRepository":
        pass

    @property
    @abstractmethod
    def oauth_clients(self) -> "AsyncOauthClientRepository":
        pass

    @abstractmethod
    async def commit(self):
        pass

    @abstractmethod
    async def rollback(self):
        pass


class IUnitOfWorkAuth(AbstractAsyncContextManager, ABC):
    user_repo: AsyncUserRepository
    role_repo: AsyncRoleRepository

    @property
    @abstractmethod
    def user(self) -> "AsyncUserRepository":
        pass

    @property
    @abstractmethod
    def role(self) -> "AsyncRoleRepository":
        pass

    @abstractmethod
    async def commit(self):
        pass

    @abstractmethod
    async def rollback(self):
        pass


class IUnitOfWorkProvider(AbstractAsyncContextManager, ABC):
    Provider: AsyncProviderRepository

    @property
    @abstractmethod
    def provider(self) -> "AsyncProviderRepository":
        pass

    @abstractmethod
    async def commit(self):
        pass

    @abstractmethod
    async def rollback(self):
        pass


class IUnitOfWorkCoupon(AbstractAsyncContextManager, ABC):
    Coupon: AsyncCouponRepository

    @property
    @abstractmethod
    def coupon(self) -> "AsyncCouponRepository":
        pass

    @abstractmethod
    async def commit(self):
        pass

    @abstractmethod
    async def rollback(self):
        pass
