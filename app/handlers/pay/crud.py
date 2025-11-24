from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.handlers.pay.interfaces import AsyncSubtractionRepository, AsyncPaymentRepository
from app.handlers.pay.schemas import OutWallets, CreatePaymentsService, CreatePaymentsOut, UpdatePayments, PaymentsOut, \
    CreateWallets, UpdateWalletsService, UpdateWallets, CreatePayments
from app.models import Wallet, Payments, Subtraction
from task_celery.pay_task.schemas import SubtractionBase, SubtractionUpdate, SubtractionRead, SubtractionList, \
    SubtractionCreate


# официальная библиотека YooKassa

class WalletRepository(AsyncSubtractionRepository):
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
            meta_data=m.metadata_payments,
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


class SubtractionRepository(AsyncSubtractionRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _to_dto(m: Subtraction) -> SubtractionRead:
        if m is None:
            raise TypeError("_to_dto получил None")
        # если случайно передан класс, защитим
        if isinstance(m, type):
            raise TypeError(f"_to_dto получил класс {m!r}, ожидается экземпляр Subtraction")

        # безопасно читаем поля (модель должна содержать эти атрибуты)
        return SubtractionRead(
            Id=str(m.id),
            UserId=m.user_id,
            Card=bool(m.card),
            ServiceCode=getattr(m, "service_code", None),
            AmountValue=getattr(m, "amount_value", Decimal("0.00")),
            Currency=getattr(m, "currency", "RUB"),
            BillingPeriod=getattr(m, "billing_period", None),
            NextRun=getattr(m, "next_run", None),
            Status=getattr(m, "status", "active"),
            IdempotencyKey=getattr(m, "idempotency_key", None),
            Attempts=getattr(m, "attempts", 0),
            LastError=getattr(m, "last_error", None),
            LastTriedAt=getattr(m, "last_tried_at", None),
            CreatedAt=m.created_at,
            UpdatedAt=m.updated_at,
            ClosedAt=getattr(m, "closed_at", None),
        )

    async def create_subtraction_user(self, create_data: SubtractionCreate) -> SubtractionRead:
        m = Subtraction()
        m.user_id = create_data.user_id
        m.card = create_data.card

        # optional fields
        if getattr(create_data, "service_code", None) is not None:
            m.service_code = create_data.service_code
        if getattr(create_data, "amount_value", None) is not None:
            m.amount_value = create_data.amount_value
        if getattr(create_data, "currency", None) is not None:
            m.currency = create_data.currency
        if getattr(create_data, "billing_period", None) is not None:
            m.billing_period = create_data.billing_period
        if getattr(create_data, "next_run", None) is not None:
            m.next_run = create_data.next_run
        m.status = create_data.status or "active"
        if getattr(create_data, "idempotency_key", None):
            m.idempotency_key = create_data.idempotency_key

        self.db.add(m)
        # flush so id and defaults are populated, but do not commit here (caller controls transaction)
        await self.db.flush()
        # refresh to obtain DB-set defaults (if any)
        await self.db.refresh(m)
        return self._to_dto(m)

    async def get_subtraction_by_id(self, id: str) -> Optional[SubtractionRead]:
        # id is uuid stored as PG_UUID(as_uuid=True) -> pass as str or uuid.UUID
        result = await self.db.get(Subtraction, id)
        return self._to_dto(result) if result else None

    async def get_subtractions(self, limit: int = 50, offset: int = 0) -> List[SubtractionRead]:
        q = (
            select(Subtraction)
            .order_by(Subtraction.next_run)  # сортируем по ближайшему запуску
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(q)
        rows = result.scalars().all()
        return [self._to_dto(r) for r in rows]

    async def get_subtractions_internal(self, limit: int = 50, offset: int = 0) -> List[SubtractionRead]:
        q = (
            select(Subtraction)
            .where(
                (Subtraction.next_run <= datetime.now(ZoneInfo("Europe/Moscow"))) &
                (Subtraction.status != "canceled") &
                (Subtraction.card == False)
            )
            .order_by(Subtraction.next_run)  # сортируем по ближайшему запуску
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(q)
        rows = result.scalars().all()
        return [self._to_dto(r) for r in rows]

    async def get_subtractions_count_internal(self) -> int:
        count_q = ((select(func.count(Subtraction.id))
        .where(
            (Subtraction.next_run <= datetime.now(ZoneInfo("Europe/Moscow"))) &
            (Subtraction.status != "canceled") &
            (Subtraction.card == False)
        ))
        )
        count_result = await self.db.execute(count_q)
        total = count_result.scalar_one()
        return total

    async def get_subtractions_count(self) -> int:
        count_q = select(func.count(Subtraction.id))
        count_result = await self.db.execute(count_q)
        total = count_result.scalar_one()
        return total

    async def get_subtraction_user_by_id(self, user_id: int) -> Optional[SubtractionRead]:
        q = (
            select(Subtraction)
            .where(Subtraction.user_id == user_id)
            .limit(1)
        )
        result = await self.db.execute(q)
        m = result.scalar_one_or_none()
        return self._to_dto(m) if m else None

    async def update_subtraction_user(self, update_data: SubtractionUpdate) -> Optional[SubtractionRead]:
        # Берём запись по user_id, изменяем нужные поля. Возвращаем DTO.
        q = select(Subtraction).where(Subtraction.user_id == update_data.user_id).limit(1).with_for_update(of=Subtraction)
        res = await self.db.execute(q)
        m = res.scalar_one_or_none()
        if not m:
            return None

        # apply updates if provided
        if update_data.card is not None:
            m.card = update_data.card

        if update_data.next_run is not None:
            m.next_run = update_data.next_run

        if update_data.status is not None:
            m.status = update_data.status

        if update_data.amount_value is not None:
            m.amount_value = update_data.amount_value

        if update_data.last_error is not None:
            m.last_error = update_data.last_error

        if update_data.idempotency_key is not None:
            m.idempotency_key = update_data.idempotency_key

        if update_data.attempts is not None:
            m.attempts = update_data.attempts

        if update_data.last_error is not None:
            m.last_tried_at = update_data.last_tried_at

        m.updated_at = datetime.now(ZoneInfo("Europe/Moscow"))
        # flush and refresh
        await self.db.flush()
        await self.db.refresh(m)
        return self._to_dto(m)
