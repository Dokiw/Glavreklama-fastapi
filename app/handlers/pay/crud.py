from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.handlers.pay.interfaces import AsyncWalletRepository, AsyncPaymentRepository
from app.handlers.pay.schemas import OutWallets, CreatePaymentsService, CreatePaymentsOut, UpdatePayments, PaymentsOut, \
    CreateWallets, UpdateWalletsService, UpdateWallets, CreatePayments
from app.models import Wallet, Payments


# официальная библиотека YooKassa

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

    async def update_wallets_user(self, update_data: UpdateWallets) -> OutWallets:
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
    # todo - оплату необходимо улучшить по мере того, как буду появляться задачи с данными системами
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _to_dto(m: "Payments") -> PaymentsOut:
        if m is None:
            raise TypeError("_to_dto получил None")
        if isinstance(m, type):
            raise TypeError(f"_to_dto получил класс {m!r}, ожидается экземпляр User")
        return PaymentsOut(
            id=str(m.id),
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
            closed_at=m.closed_at if m.closed_at else None,
        )

    async def create_payments(self, create_data: CreatePayments) -> CreatePaymentsOut:
        m = Payments()
        m.user_id = create_data.user_id
        m.currency = create_data.currency
        m.amount_value = create_data.amount
        m.metadata_payments = create_data.metadata_payments
        m.description = create_data.description
        m.confirmation_url = create_data.return_url
        m.confirmation_type = create_data.confirmation_type
        m.wallet_id = create_data.wallet_id
        m.capture = create_data.capture
        m.idempotency_key = create_data.idempotency_key

        self.db.add(m)
        await self.db.flush()

        return CreatePaymentsOut(
            id=str(m.id),
            user_id=m.user_id,
            confirmation_url=m.confirmation_url,
            confirmation_type=m.confirmation_type,
            status=m.status,
            wallet_id=m.wallet_id,
            currency=m.currency,
        )

    async def update_payments(self, update_data: UpdatePayments) -> PaymentsOut:

        values = {"status": update_data.status}

        if update_data.payment_id is not None:
            values["yookassa_payment_id"] = update_data.payment_id

        if update_data.confirmation_type and update_data.confirmation_url:
            values["confirmation_url"] = update_data.confirmation_url
            values["confirmation_type"] = update_data.confirmation_type

        stmt = (
            update(Payments)
            .where(Payments.id == update_data.id)
            .values(**values)
            .returning(Payments)
        )

        result = await self.db.execute(stmt)
        result = result.scalar_one_or_none()

        return self._to_dto(result)

    async def get_payments_by_user_id(self, user_id: int) -> Optional[List[PaymentsOut]]:

        q = (
            select(Payments)
            .where(
                (Payments.user_id == user_id) &
                (Payments.status != "canceled")
            )
            .order_by(Payments.created_at.desc())
        )
        result = await self.db.execute(q)
        result = result.scalars().all()
        return [self._to_dto(r) for r in result] if result else None

    async def get_payments_by_user_id_last(self, user_id: int) -> Optional[PaymentsOut]:

        q = (
            select(Payments)
            .where(
                (Payments.user_id == user_id) &
                (Payments.status != "canceled")
            )
            .order_by(Payments.created_at.desc())
        )
        result = await self.db.execute(q)
        result = result.scalars().first()

        return self._to_dto(result) if result else None


    async def get_payments_by_id(self, payments_id: str) -> Optional[PaymentsOut]:
        result = await self.db.get(Payments, payments_id)
        return result if result else None

    async def get_payments_by_idempotency_id(self, idempotency_id: str) -> Optional[PaymentsOut]:
        q = (
            select(Payments)
            .where(
                (Payments.idempotency_key == idempotency_id) &
                (Payments.status != "canceled")
            )
            .limit(1)
        )
        result = await self.db.execute(q)
        result = result.scalar_one_or_none()
        return result
