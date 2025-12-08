import math
from datetime import datetime
from decimal import Decimal
from typing import Optional
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta

from app.core.abs.unit_of_work import IUnitOfWorkSubtraction
from app.handlers.pay.interfaces import AsyncWalletService
from app.handlers.pay.schemas import UpdateWalletsService
from app.handlers.session.interfaces import AsyncSessionService
from app.handlers.session.schemas import CheckSessionAccessToken
from app.main import logger
from app.method.decorator import transactional
from task_celery.pay_task.interfaces import AsyncSubtractionService
from task_celery.pay_task.schemas import SubtractionRead, SubtractionUpdate, SubtractionCreate

TZ = ZoneInfo("Europe/Moscow")


class SqlAlchemySubtractionService(AsyncSubtractionService):
    def __init__(self, uow: IUnitOfWorkSubtraction, session_service: AsyncSessionService,
                 wallet_service: AsyncWalletService):
        self.uow = uow
        self.session_service = session_service
        self.wallet_service = wallet_service

    @staticmethod
    async def _advance_next_run(current: datetime, billing_period: Optional[str]) -> Optional[datetime]:
        if not billing_period:
            return None
        try:
            parts = billing_period.strip().lower().split()
            qty = int(parts[0])
            unit = parts[1] if len(parts) > 1 else "month"
        except Exception:
            # fallback: add 1 month
            return current + relativedelta(months=1)

        if "month" in unit:
            return current + relativedelta(months=qty)
        if "day" in unit:
            return current + relativedelta(days=qty)
        if "year" in unit:
            return current + relativedelta(years=qty)
        return current + relativedelta(months=qty)

    @transactional()
    async def create_subtraction_user(self, create_data: SubtractionCreate,
                                      check_data: CheckSessionAccessToken) -> SubtractionRead:
        await self.session_service.validate_access_token_session(check_data)
        result = await self.uow.subtraction_repo.create_subtraction_user(create_data)
        return result

    @transactional()
    async def get_subtraction_by_id(self, id: int, check_data: CheckSessionAccessToken) -> Optional[SubtractionRead]:
        await self.session_service.validate_access_token_session(check_data)
        result = await self.uow.subtraction_repo.get_subtraction_by_id(id)
        return result

    @transactional()
    async def get_subtraction_user_by_id(self, user_id: int, check_data: CheckSessionAccessToken) -> Optional[
        SubtractionRead]:
        await self.session_service.validate_access_token_session(check_data)
        result = await self.uow.subtraction_repo.get_subtraction_user_by_id(user_id)
        return result

    @transactional()
    async def update_subtraction_user(self, update_data: SubtractionUpdate,
                                      check_data: CheckSessionAccessToken) -> SubtractionRead:
        await self.session_service.validate_access_token_session(check_data)
        result = await self.uow.subtraction_repo.update_subtraction_user(update_data)
        return result

    @transactional()
    async def process_subtraction(self, sub: SubtractionRead):
        try:
            w = await self.wallet_service.get_wallet_by_user_id_internal(sub.user_id)

            if not w:
                sub.last_error = "no_wallet"
                sub.status = f"paused"
                up_data = SubtractionUpdate(
                    user_id=sub.user_id,
                    last_error=sub.last_error,
                    status=sub.status
                )
                await self.uow.subtraction_repo.update_subtraction_user(up_data)
                logger.error("User %s has no wallet", sub.user_id)
                return

            if w.balance < Decimal(sub.amount_value):
                up_data = SubtractionUpdate(
                    user_id=sub.user_id,
                    last_error=sub.last_error,
                    status="paused",
                )

                await self.uow.subtraction_repo.update_subtraction_user(up_data)
                logger.warning("Insufficient funds for user %s (need %s, have %s)", sub.user_id, sub.amount_value,
                               w.balance)
                return False

            if not sub.idempotency_key:
                new_key = f"sub:u{sub.user_id}:s{sub.service_code or sub.id}:{sub.next_run.strftime('%Y%m%d') if sub.next_run else datetime.utcnow().strftime('%Y%m%d')}"
                up_data = SubtractionUpdate(
                    user_id=sub.user_id,
                    idempotency_key=new_key,
                )
                await self.uow.subtraction_repo.update_subtraction_user(up_data)
                sub.idempotency_key = new_key

            up_wal = UpdateWalletsService(
                id=w.id,
                amount=sub.amount_value,
                reason="minus",
            )
            try:
                updated = await self.wallet_service.update_wallets_user_internal(update_data=up_wal)
            except Exception as exc:
                # transient error — инкремент attempts и пометка ошибки
                logger.exception("Wallet update error for user %s: %s", sub.user_id, exc)
                up_data = SubtractionUpdate(
                    user_id=sub.user_id,
                    last_error=str(exc)[:1000],
                    attempts=(sub.attempts or 0) + 1,
                    last_tried_at=datetime.now(TZ),
                )
                await self.uow.subtraction_repo.update_subtraction_user(up_data)
                return False

            if not updated:
                # сервис вернул False — обрабатываем как ошибку
                up_data = SubtractionUpdate(
                    user_id=sub.user_id,
                    last_error="wallet_update_failed",
                    attempts=(sub.attempts or 0) + 1,
                    last_tried_at=datetime.now(TZ),
                )
                await self.uow.subtraction_repo.update_subtraction_user(up_data)
                logger.error("Wallet update returned False for user %s", sub.user_id)
                return False

            # 5) успешный дебит: обновляем Subtraction: attempts reset, last_error=None, advance next_run
            new_next = await self._advance_next_run(sub.next_run or datetime.now(TZ), sub.billing_period)
            up_data = SubtractionUpdate(
                user_id=sub.user_id,
                last_error=None,
                attempts=0,
                last_tried_at=datetime.now(TZ),
                next_run=new_next,
                status="active"
            )
            await self.uow.subtraction_repo.update_subtraction_user(up_data)

            logger.info("Subtraction succeeded for user %s amount=%s", sub.user_id, sub.amount_value)
            return True

        except Exception as e:

            # критическая ошибка — логируем и помечаем попытку
            logger.exception("process_subtraction unexpected error for user %s: %s", sub.user_id, e)
            up_data = SubtractionUpdate(
                user_id=sub.user_id,
                last_error=str(e)[:1000],
                attempts=(sub.attempts or 0) + 1,
                last_tried_at=datetime.now(TZ),

            )
            await self.uow.subtraction_repo.update_subtraction_user(up_data)
            return False

    async def auto_payment_service(self) -> bool:
        total_pool = await self.uow.subtraction_repo.get_subtractions_count_internal()
        if not total_pool:
            return True

        BATCH = 100

        pages = math.ceil(total_pool / BATCH)

        for page in range(pages):
            offset = page * BATCH
            list_subtrc = await self.uow.subtraction_repo.get_subtractions_internal(limit=BATCH, offset=offset)

            for sub_trac in list_subtrc:
                try:
                    # каждое списание должно быть СВОЕЙ транзакцией -> process_subtraction помечен @transactional()
                    await self.process_subtraction(sub_trac)
                except Exception as e:
                    logger.error("Subtraction failed for user %s: %s", sub_trac.user_id, e)
        return True

