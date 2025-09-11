from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.handlers.pay.interfaces import AsyncWalletRepository, AsyncPaymentRepository
from app.handlers.pay.schemas import OutWallets, CreatePayments, CreatePaymentsOut, UpdatePayments, PaymentsOut, \
    CreateWallets, UpdateWalletsService
from app.models import Wallet, Payments


class WalletRepository(AsyncWalletRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _to_dto(m: "Wallet") -> OutWallets:
        if m is None:
            raise TypeError("_to_dto получил None")
        if isinstance(m, type):
            raise TypeError(f"_to_dto получил класс {m!r}, ожидается экземпляр User")
        return OutWallets(
            id=m.id,
            user_id=m.user_id,
            balance=m.balance,
            updated_at=m.updated_at,
        )

    async def create_wallet_user(self, create_data: CreateWallets) -> OutWallets:
        m = Wallet()
        m.user_id = create_data.user_id
        self.db.add(m)
        await self.db.flush()
        return self._to_dto(m)

    async def update_wallets_user(self, update_data: UpdateWalletsService) -> OutWallets:
        stmt = (
            update(Wallet)
            .where(
                Wallet.id == update_data.id,
            )
            .values(
                balance=Wallet.balance + update_data.amount,
                updated_at=func.now()
            )
            .returning(Wallet)
        )
        result = await self.db.execute(stmt)
        result = result.scalar_one_or_none()

        return self._to_dto(result) if result else None

    async def get_wallet_by_id(self, id: int) -> Optional[OutWallets]:
        result = await self.db.get(Wallet, id)
        return self._to_dto(result) if result else None

    async def get_wallet_by_user_id(self, user_id: int) -> Optional[OutWallets]:
        q = (
            select(Wallet)
            .where(Wallet.user_id == user_id)
            .limit(1)
        )
        result = await self.db.execute(q)
        result = result.scalars().first()
        return self._to_dto(result) if result else None


class PaymentRepository(AsyncPaymentRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _to_dto(m: "Payments") -> PaymentsOut:
        if m is None:
            raise TypeError("_to_dto получил None")
        if isinstance(m, type):
            raise TypeError(f"_to_dto получил класс {m!r}, ожидается экземпляр User")
        return PaymentsOut(
            id=m.id,
            user_id=m.user_id,
            wallet_id=m.wallet_id,
            amount=m.amount_value,
            confirmation_url=m.confirmation_url if m.confirmation_url else None,
            confirmation_type=m.confirmation_type if m.confirmation_type else None,
            status=m.status,
            yookassa_payment_id=m.yookassa_payment_id,
            currency=m.currency,
            idempotency_key=m.idempotency_key if m.idempotency_key else None,

            created_at=m.created_at,
            updated_at=m.updated_at if m.updated_at else None,
            closed_at=m.closed_at if m.closed_at else None ,
        )

    async def create_payments(self) -> CreatePaymentsOut:
        ...

    async def update_payments(self) -> PaymentsOut:
        ...

    async def get_payments_by_user_id(self) -> Optional[PaymentsOut]:
        ...

    async def get_payments_by_id(self) -> Optional[PaymentsOut]:
        ...

    async def get_payments_by_idempotency_id(self) -> Optional[PaymentsOut]:
        ...
