import asyncio
import datetime
import hashlib
import logging
import uuid
from datetime import time
import datetime as dt
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import aiohttp
from yookassa import Payment
from typing import Optional, List, Dict, Any
import yookassa
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
import ipaddress
from yookassa.domain.common.user_agent import Version
from yookassa import Configuration

from app.core.abs.unit_of_work import IUnitOfWorkWallet, IUnitOfWorkPayment
from app.core.config import settings, logger
from app.handlers.pay.interfaces import AsyncPaymentService, AsyncWalletService, AsyncApiPaymentService
from app.handlers.pay.schemas import CreatePaymentsService, UpdatePayments, CreatePaymentsOut, PaymentsOut, \
    CreateWallets, \
    OutWallets, UpdateWalletsService, UpdateWallets, CreatePayments
from app.handlers.session.interfaces import AsyncSessionService
from app.handlers.session.schemas import CheckSessionAccessToken
from app.method.decorator import transactional


class SqlAlchemyServicePayment(AsyncPaymentService):
    # todo - подключить апи
    def __init__(self, uow: IUnitOfWorkPayment, session_service: AsyncSessionService,
                 payment_service_api: AsyncApiPaymentService, wallet_service: AsyncWalletService):
        self.uow = uow
        self.session_service = session_service
        self.wallet_service = wallet_service
        self.payment_service_api = payment_service_api

    @transactional()
    async def create_payments(self, create_data: CreatePaymentsService, check_data: CheckSessionAccessToken) -> (
            CreatePaymentsOut | PaymentsOut):
        session = await self.session_service.validate_access_token_session(check_data)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка целостности данных"
            )

        result = await self.uow.payment_repo.get_payments_by_user_id_last(create_data.user_id)
        if result is not None:
            if result.status == "pending" or result.status == "waiting_for_capture" and result.amount == create_data.amount:
                return result

        idempotence_key = str(uuid.uuid4())
        result = await self.uow.payment_repo.create_payments(CreatePayments(
            user_id=create_data.user_id,
            wallet_id=create_data.wallet_id,
            amount=create_data.amount,
            return_url=create_data.return_url,
            confirmation_type=create_data.confirmation_type,
            description=create_data.description,
            currency=create_data.currency,
            capture=create_data.capture,
            metadata_payments=create_data.metadata_payments,
            idempotency_key=idempotence_key,
        )
        )

        api_payment = await self.payment_service_api.create_payment(
            amount=create_data.amount,
            return_url=create_data.return_url,
            description=create_data.description,
            user_id=str(create_data.user_id),
            payment_id=result.id,
            idemp=idempotence_key,
        )

        confirmation = api_payment.get("confirmation") or {}
        confirmation_url = confirmation.get("confirmation_url")
        confirmation_type = confirmation.get("type")

        update_data = await self.uow.payment_repo.update_payments(UpdatePayments(
            id=result.id,
            status=api_payment.get("status"),
            payment_id=api_payment.get("id"),
            confirmation_url=confirmation_url,
            confirmation_type=confirmation_type,
        ))

        response_obj = CreatePaymentsOut(
            id=str(result.id),
            user_id=result.user_id,
            confirmation_url=update_data.confirmation_url,
            confirmation_type=update_data.confirmation_type,
            status=update_data.status,
            wallet_id=result.wallet_id,
            currency=result.currency,
        )
        return response_obj

    # todo - необходимо дописать момент, чтобы он позволял нам переводить статусы именно от программы
    @transactional()
    async def update_payments(self, update_data: UpdatePayments, check_data: CheckSessionAccessToken) -> PaymentsOut:
        session = await self.session_service.validate_access_token_session(check_data)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка целостности данных"
            )
        result = await self.uow.payment_repo.update_payments(update_data)
        return result

    @transactional()
    async def get_payments_by_user_id(self, check_data: CheckSessionAccessToken) -> Optional[List[PaymentsOut]]:
        session = await self.session_service.validate_access_token_session(check_data)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка целостности данных"
            )
        result = await self.uow.payment_repo.get_payments_by_user_id(check_data.user_id)

        return result

    @transactional()
    async def get_payments_by_id(self, payments_id: str, check_data: CheckSessionAccessToken) -> Optional[PaymentsOut]:
        session = await self.session_service.validate_access_token_session(check_data)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка целостности данных"
            )
        result = await self.uow.payment_repo.get_payments_by_id(payments_id)

        return result

    @transactional()
    async def get_payments_by_idempotency_id(self, idempotency_id: str, check_data: CheckSessionAccessToken) -> (
            Optional[PaymentsOut]):
        session = await self.session_service.validate_access_token_session(check_data)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка целостности данных"
            )
        result = await self.uow.payment_repo.get_payments_by_idempotency_id(idempotency_id)
        return result

    @transactional()
    async def webhook_api(self, payload: Dict[str, Any], headers: Dict[str, str], remote_addr: Optional[str] = None) -> \
    Optional[PaymentsOut]:
        logger = logging.getLogger("payments.webhook")
        try:
            if remote_addr:
                try:
                    ip = ipaddress.ip_address(remote_addr)
                except Exception:
                    logger.warning("Invalid remote_addr sent to webhook: %s", remote_addr)

            # --- extract payment object (defensive) ---
            payment_obj = {}
            if isinstance(payload, dict):
                payment_obj = payload.get("object") or payload.get("payment") or payload
                # unwrap nested object.object
                if isinstance(payment_obj, dict) and payment_obj.get("object"):
                    payment_obj = payment_obj.get("object")
            if not isinstance(payment_obj, dict):
                payment_obj = {}

            # --- idempotence: from headers or payload.metadata ---
            idemp = (
                headers.get("Idempotence-Key")
                or headers.get("Idempotence-key")
                or headers.get("idempotence-key")
                or payment_obj.get("metadata", {}).get("idempotence_key")
                or payload.get("metadata", {}).get("idempotence_key")
            )
            logger.debug("Webhook: extracted idempotence: %s", idemp)

            # --- external payment id (several places) ---
            ext_payment_id = (
                    payment_obj.get("id")
                    or payment_obj.get("payment_id")
                    or payment_obj.get("external_id")
                    or payment_obj.get("metadata", {}).get("payment_id")
                    or payload.get("id")
                    or payload.get("payment_id")
            )
            logger.debug("Webhook: extracted external payment id: %s", ext_payment_id)

            # --- normalize status / event ---
            raw_status = (payment_obj.get("status") or payload.get("status") or payload.get("event") or "").strip()
            status_normalized = None
            if isinstance(raw_status, str) and raw_status:
                # handle events like "payment.succeeded"
                if raw_status.startswith("payment.") and "." in raw_status:
                    status_normalized = raw_status.split(".", 1)[1].lower()
                else:
                    status_normalized = raw_status.lower()
            logger.debug("Webhook: raw_status=%s normalized=%s", raw_status, status_normalized)

            # --- try find local payment by idempotence first ---
            local_payment = None
            if idemp:
                try:
                    local_payment = await self.uow.payment_repo.get_payments_by_idempotency_id(idemp)
                    logger.debug("Webhook: found by idempotence: %s", getattr(local_payment, "id", None))
                except AttributeError:
                    logger.debug("payment_repo.get_payments_by_idempotency_id missing")
                except Exception as e:
                    logger.exception("payment_repo.get_payments_by_idempotency_id raised: %s", e)

            # --- if not found, try a set of getters by external id (try all until found) ---
            if local_payment is None and ext_payment_id:
                possible_getters = (
                    "get_payments_by_yookassa_id",
                    "get_payments_by_external_id",
                    "get_payments_by_payment_id",
                    "get_by_yookassa_id",
                    "get_by_external_id",
                    "get_by_payment_id",
                    "get_payments_by_id",  # in case repo supports lookup by external id here (unlikely)
                )
                for name in possible_getters:
                    getter = getattr(self.uow.payment_repo, name, None)
                    if callable(getter):
                        try:
                            found = await getter(ext_payment_id)
                            if found:
                                local_payment = found
                                logger.debug("Webhook: found local payment via %s -> %s", name,
                                             getattr(local_payment, "id", None))
                                break
                        except Exception as e:
                            logger.debug("repo getter %s raised: %s", name, e)

            # --- if still not found: log and exit (we don't create new records by design) ---
            if local_payment is None:
                logger.info("Webhook: local payment not found (idemp=%s ext_id=%s). Payload: %s", idemp, ext_payment_id,
                            payload)
                return None

            # --- protect from double-crediting: if local already final, return DTO ---
            local_status = getattr(local_payment, "status", None)
            if local_status and str(local_status).lower() in ("succeeded", "paid", "completed"):
                logger.info("Webhook: payment %s (local id=%s) already in final state '%s', skipping",
                            ext_payment_id, getattr(local_payment, "id", None), local_status)
                # return fresh DTO from repo (not raw ORM)
                try:
                    # try to fetch DTO by id (repo method name may differ)
                    if hasattr(self.uow.payment_repo, "get_payments_by_id"):
                        return await self.uow.payment_repo.get_payments_by_id(str(getattr(local_payment, "id")))
                except Exception:
                    logger.debug("Couldn't fetch DTO for already-final payment; returning None")
                return None

            # --- success states set ---
            success_states = {"succeeded", "paid", "success", "completed"}
            try:
                # Map boolean flags if provider sets 'paid': True
                if status_normalized is None and payment_obj.get("paid") is True:
                    status_normalized = "succeeded"

                if status_normalized in success_states:
                    # amount extraction
                    raw_amount = None
                    if isinstance(payment_obj.get("amount"), dict):
                        raw_amount = payment_obj.get("amount", {}).get("value")
                    raw_amount = raw_amount or payment_obj.get("sum") or payment_obj.get("amount") or getattr(
                        local_payment, "amount", None)

                    try:
                        dec_amount = Decimal(str(raw_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    except Exception:
                        dec_amount = Decimal(str(getattr(local_payment, "amount", 0))).quantize(Decimal("0.01"),
                                                                                                rounding=ROUND_HALF_UP)

                    wallet_id = getattr(local_payment, "wallet_id", None)
                    if wallet_id is None:
                        logger.error("Webhook: local payment has no wallet_id (local id=%s). Can't credit.",
                                     getattr(local_payment, "id", None))
                        # update status anyway
                        await self.uow.payment_repo.update_payments(UpdatePayments(
                            id=str(getattr(local_payment, "id")),
                            status=raw_status,
                            payment_id=ext_payment_id,
                            confirmation_url=(payment_obj.get("confirmation") or {}).get("confirmation_url"),
                            confirmation_type=(payment_obj.get("confirmation") or {}).get("type"),
                        ))
                        return None

                    # credit wallet
                    await self.wallet_service.update_wallets_user_internal(UpdateWalletsService(
                        id=wallet_id,
                        amount=dec_amount,
                        reason="plus"
                    ))

                    # update local payment (use str(id) to avoid UUID->str issues)
                    updated = await self.uow.payment_repo.update_payments(UpdatePayments(
                        id=str(getattr(local_payment, "id")),
                        status=raw_status,
                        payment_id=ext_payment_id,
                        confirmation_url=(payment_obj.get("confirmation") or {}).get("confirmation_url"),
                        confirmation_type=(payment_obj.get("confirmation") or {}).get("type"),
                    ))

                    logger.info("Webhook: payment %s (local id=%s) succeeded — wallet %s credited %s", ext_payment_id,
                                getattr(local_payment, "id"), wallet_id, dec_amount)
                    return updated
                else:
                    # intermediate / failed status: just update the payment row
                    updated = await self.uow.payment_repo.update_payments(UpdatePayments(
                        id=str(getattr(local_payment, "id")),
                        status=raw_status,
                        payment_id=ext_payment_id,
                        confirmation_url=(payment_obj.get("confirmation") or {}).get("confirmation_url"),
                        confirmation_type=(payment_obj.get("confirmation") or {}).get("type"),
                    ))
                    logger.info("Webhook: payment %s (local id=%s) updated to status '%s'", ext_payment_id,
                                getattr(local_payment, "id"), raw_status)
                    return updated

            except IntegrityError as ie:
                logger.exception("Webhook integrity error while processing payment %s local id=%s: %s", ext_payment_id,
                                 getattr(local_payment, "id"), ie)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB integrity error")
            except Exception as e:
                logger.exception("Webhook processing failed for payment %s local id=%s: %s", ext_payment_id,
                                 getattr(local_payment, "id"), e)
                raise

        except Exception as e:
            logger.exception("Unhandled exception in webhook_api: %s", e)
            raise


class SqlAlchemyServiceWallet(AsyncWalletService):
    def __init__(self, uow: IUnitOfWorkWallet, session_service: AsyncSessionService):
        self.uow = uow
        self.session_service = session_service

    @transactional()
    async def create_wallet_or_get_wallet(self, check_data: CheckSessionAccessToken) -> OutWallets:
        session = await self.session_service.validate_access_token_session(check_data)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка целостности данных"
            )

        wallet = await self.uow.wallet_repo.get_wallet_by_user_id(session.user_id)
        if wallet:
            return wallet

        result = await self.uow.wallet_repo.create_wallet_user(CreateWallets(user_id=session.user_id))
        return result

    @transactional()
    async def update_wallets_user(self, update_data: UpdateWalletsService,
                                  check_data: CheckSessionAccessToken) -> OutWallets:
        session = await self.session_service.validate_access_token_session(check_data)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка целостности данных"
            )

        hash_table = {
            'plus': 1,
            'minus': -1
        }

        if update_data.reason not in hash_table:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверный reason: {update_data.reason}"
            )

        result = await self.uow.wallet_repo.update_wallets_user(UpdateWallets(
            id=update_data.id,
            amount=update_data.amount * hash_table[update_data.reason]
        ))
        return result

    @transactional()
    async def update_wallets_user_internal(self, update_data: UpdateWalletsService) -> OutWallets:
        hash_table = {
            'plus': 1,
            'minus': -1
        }

        if update_data.reason not in hash_table:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверный reason: {update_data.reason}"
            )

        result = await self.uow.wallet_repo.update_wallets_user(UpdateWallets(
            id=update_data.id,
            amount=update_data.amount * hash_table[update_data.reason]
        ))
        return result

    @transactional()
    async def get_wallet_by_id(self, id: int, check_data: CheckSessionAccessToken) -> Optional[OutWallets]:
        session = await self.session_service.validate_access_token_session(check_data)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка целосности данных"
            )
        result = await self.uow.wallet_repo.get_wallet_by_id(id)
        return result


class ApiError(Exception):
    def __init__(self, status: Optional[int] = None, body: Optional[Any] = None):
        self.status = status
        self.body = body
        super().__init__(f"API error {status}: {body}")


class SqlAlchemyServicePaymentApi:
    """
    Обёртка над официальным SDK yookassa.
    - Поддерживает использование глобального settings (если http_client/secret/shop не переданы),
      но также позволяет явную передачу параметров в __init__.
    - SDK синхронный, поэтому вызывает сетевые операции через asyncio.to_thread.
    """

    def __init__(
            self,
            timeout: int = 10,  # пока не используется SDK напрямую, но оставлено для совместимости
            max_retries: int = 3,
            # логика повторов оставлена на уровне вызова (см. ниже), но SDK обычно сам справляется
            secret_key: str = settings.SECRET_KEY,
            shop_id: str = settings.SHOP_ID,
    ):
        self.secret_key = secret_key
        self.shop_id = shop_id
        self.timeout = timeout
        self.max_retries = max_retries

        # Инициализация глобальной конфигурации SDK
        Configuration.account_id = self.shop_id.strip()
        Configuration.secret_key = self.secret_key.strip()

    async def find_by_local_payment_id(self, local_payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Ищет оплату по local_payment_id. Пытается сначала запросом по metadata.payment_id,
        если API/SDK не поддерживает такую фильтрацию — делает постраничный перебор и фильтрацию на стороне клиента.
        Возвращает dict(payment) или None.
        """
        try:
            # попробуем сразу запросить список с фильтром по metadata.payment_id (если SDK/сервер это поддерживает)
            params = {"limit": 1, "metadata.payment_id": local_payment_id}
            res = await asyncio.to_thread(Payment.list, params)
            items = getattr(res, "items", None)
            if items:
                first = items[0]
                return dict(first)
        except Exception:
            # тихо падаем в fallback — возможно сервер не поддерживает фильтр по metadata напрямую
            pass

        # Fallback: постраничный перебор (без фильтрации на стороне API)
        cursor = None
        try:
            while True:
                params = {"limit": 50}
                if cursor:
                    params["cursor"] = cursor
                res = await asyncio.to_thread(Payment.list, params)
                items = getattr(res, "items", []) or []
                for p in items:
                    md = getattr(p, "metadata", {}) or {}
                    if md.get("payment_id") == local_payment_id or md.get("local_payment_id") == local_payment_id:
                        return dict(p)
                cursor = getattr(res, "next_cursor", None)
                if not cursor:
                    break
        except Exception as e:
            # логирование — в продакшне замените на нормальный логгер
            print("find_by_local_payment_id error:", e)

        return None

    async def get_payments_by_idemp(self, idemp: str) -> Optional[Any]:
        """
        Пытается найти платеж(и) по idempotence key. Поскольку idempotence_key обычно передаётся как заголовок
        и не всегда индексируется сервером для поиска, мы ищем в metadata (если туда записали idemp),
        и в крайнем случае перебираем платежи и фильтруем по сохранённой metadata.
        Возвращаем список совпадений (может быть пустым) или None при ошибке.
        """
        results: List[Dict[str, Any]] = []
        cursor = None
        try:
            # Попробуем сначала фильтрацией по metadata.idempotence_key
            params = {"limit": 1, "metadata.idempotence_key": idemp}
            res = await asyncio.to_thread(Payment.list, params)
            items = getattr(res, "items", None)
            if items:
                # вернём все найденные (SDK мог вернуть только одну страницу)
                for it in items:
                    results.append(dict(it))
                # если SDK вернул next_cursor — пройдём страницы
                cursor = getattr(res, "next_cursor", None)
                while cursor:
                    params = {"limit": 50, "cursor": cursor}
                    res = await asyncio.to_thread(Payment.list, params)
                    for it in getattr(res, "items", []) or []:
                        results.append(dict(it))
                    cursor = getattr(res, "next_cursor", None)
                return results
        except Exception:
            # если фильтрация по metadata не поддерживается, падаем в общий перебор
            pass

        # Общий перебор: ищем idemp в metadata.payment_id / metadata.idempotence_key / id / description
        try:
            cursor = None
            while True:
                params = {"limit": 50}
                if cursor:
                    params["cursor"] = cursor
                res = await asyncio.to_thread(Payment.list, params)
                items = getattr(res, "items", []) or []
                for p in items:
                    md = getattr(p, "metadata", {}) or {}
                    if md.get("idempotence_key") == idemp or md.get("payment_id") == idemp:
                        results.append(dict(p))
                    # некоторый клиент мог сохранить idemp в других полях — проверим id/description как последний шанс
                    elif getattr(p, "id", None) == idemp or (
                            getattr(p, "description", "") and idemp in getattr(p, "description")):
                        results.append(dict(p))
                cursor = getattr(res, "next_cursor", None)
                if not cursor:
                    break
        except Exception as e:
            print("get_payments_by_idemp error:", e)
            return None

        return results

    async def get_payments(self, created_at) -> List[Dict[str, Any]]:
        """
        Возвращает список платежей в диапазоне created_at.
        Параметр created_at может быть:
          - dict с ключами 'gte' и/или 'lt' значениями в ISO-формате,
          - кортеж/список (gte, lt),
          - строкой (в таком случае будет использован created_at.gte)
        """
        cursor = None
        data = {
            "limit": 50,
        }

        # построим параметры created_at в формате, ожидаемом SDK (ключи вида created_at.gte)
        try:
            if isinstance(created_at, dict):
                if "gte" in created_at:
                    data["created_at.gte"] = created_at["gte"]
                if "lt" in created_at:
                    data["created_at.lt"] = created_at["lt"]
            elif isinstance(created_at, (list, tuple)) and len(created_at) >= 1:
                data["created_at.gte"] = created_at[0]
                if len(created_at) > 1 and created_at[1]:
                    data["created_at.lt"] = created_at[1]
            elif isinstance(created_at, str):
                data["created_at.gte"] = created_at
            # если created_at пустой или не поддерживаемый формат — просто вернём все записи постранично
        except Exception as e:
            print("get_payments param build error:", e)

        results: List[Dict[str, Any]] = []
        try:
            while True:
                params = dict(data)
                if cursor:
                    params["cursor"] = cursor
                res = await asyncio.to_thread(Payment.list, params)
                items = getattr(res, "items", []) or []
                for p in items:
                    results.append(dict(p))
                cursor = getattr(res, "next_cursor", None)
                if not cursor:
                    break
        except Exception as e:
            print("get_payments error:", e)

        return results

    async def create_payment(
            self,
            amount: Any,
            return_url: str,
            description: str,
            user_id: str,
            payment_id: str,
            idemp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Создаёт платёж (асинхронно, через to_thread).
        Если idemp передан, попытается:
          1) передать его как idempotence_key (если версия SDK поддерживает такой аргумент);
          2) или — записать idemp в metadata (backup).
        Возвращает dict(payment) или бросает исключение (если хотите — можно вернуть структуру с ошибкой).
        """
        # нормализуем сумму
        if isinstance(amount, (float, int, str, Decimal)):
            # SDK ожидает словарь {"value": "100.00", "currency": "RUB"}
            amount_val = str(Decimal(amount).quantize(Decimal("0.01")))
        else:
            # если передали уже dict — попробуем использовать как есть
            if isinstance(amount, dict) and "value" in amount and "currency" in amount:
                amount_val = amount
            else:
                amount_val = str(amount)

        paydata = {
            "amount": {
                "value": amount_val if isinstance(amount_val, str) else amount_val["value"],
                "currency": "RUB" if not (
                            isinstance(amount_val, dict) and amount_val.get("currency")) else amount_val.get("currency")
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "capture": True,
            "description": description,
            "metadata": {
                "user_id": user_id,
                "payment_id": payment_id,
            }
        }

        if idemp:
            # сохраняем в metadata как резервную стратегию (чтобы потом можно было искать по idemp)
            paydata["metadata"]["idempotence_key"] = idemp

        try:
            # Первый вариант — попробовать передать idempotence_key как аргумент (некоторые версии SDK поддерживают это)
            if idemp:
                try:
                    res = await asyncio.to_thread(Payment.create, paydata, idemp)
                except TypeError:
                    # SDK не принимает idempotence_key в сигнатуре -> fallback
                    res = await asyncio.to_thread(Payment.create, paydata)
            else:
                res = await asyncio.to_thread(Payment.create, paydata)

            return dict(res)
        except Exception as e:
            # В продакшне используйте нормальный логгер и более детальную обработку (например, парсинг ошибок SDK)
            print("create_payment error:", e)
            # Можно вернуть структуру с описанием ошибки, чтобы вызывающая сторона не падала
            return {"error": str(e)}





