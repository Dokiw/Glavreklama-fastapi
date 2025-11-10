from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.abs.unit_of_work import IUnitOfWorkWallet, IUnitOfWorkPayment
from app.handlers.pay.crud import WalletRepository, PaymentRepository
from app.handlers.pay.interfaces import AsyncSubtractionRepository, AsyncPaymentRepository, AsyncWalletRepository


class SqlAlchemyUnitOfWorkWallet(IUnitOfWorkWallet):
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._session: Optional[AsyncSession] = None

    async def __aenter__(self):
        self._session = await self.session_factory()
        self._wallet_repo = WalletRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()  # автоматически сохраняем изменения
        else:
            await self.rollback()
        await self._session.close()

    @property
    def wallet_repo(self) -> "AsyncWalletRepository":
        return self._wallet_repo

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()


class SqlAlchemyUnitOfWorkPayment(IUnitOfWorkPayment):
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._session: Optional[AsyncSession] = None

    async def __aenter__(self):
        self._session = self.session_factory()
        self._payment_repo = PaymentRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()  # автоматически сохраняем изменения
        else:
            await self.rollback()
        await self._session.close()

    @property
    def payment_repo(self) -> "AsyncPaymentRepository":
        return self._payment_repo

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()

