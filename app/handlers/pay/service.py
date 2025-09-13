import asyncio
import datetime
import hashlib
import logging
import uuid
from datetime import time
import datetime as dt
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import aiohttp
from typing import Optional, List, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
import ipaddress

from app.core.abs.unit_of_work import IUnitOfWorkWallet, IUnitOfWorkPayment
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
            PaymentsOut):
        session = await self.session_service.validate_access_token_session(check_data)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка целостности данных"
            )

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
        ))

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

        return update_data

    #todo - необходимо дописать момент, чтобы он позволял нам переводить статусы именно от программы
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
        """
        Универсальный обработчик webhook'ов от платёжного провайдера (например YooKassa).
        Ожидает: payload (распакованный JSON), headers (словарь заголовков), remote_addr (IP клиента, опционально).
        Что делает:
         - пытается определить локальную запись платежа (по Idempotence-Key или по внешнему payment id);
         - проверяет статус платежа;
         - если платёж успешно завершён и локально ещё не зачислен — зачисляет средства на кошелёк;
         - обновляет статус/внешний id/confirmation в таблице payments;
         - защищено от повторного зачисления (idempotency по локальному статусу).
        """
        logger = logging.getLogger("payments.webhook")
        try:
            # 1) Небольшая валидация IP (если передали remote_addr) — только логируем, не блокируем.
            if remote_addr:
                try:
                    ip = ipaddress.ip_address(remote_addr)
                except Exception:
                    logger.warning("Invalid remote_addr sent to webhook: %s", remote_addr)

            # 2) Извлекаем объект платёжа из payload в максимально общих вариантах
            payment_obj = None
            if isinstance(payload, dict):
                # типичная структура: {"event":"payment.succeeded","object":{...}}
                payment_obj = payload.get("object") or payload.get("payment") or payload
                # если wrapper в object.object
                if isinstance(payment_obj, dict) and payment_obj.get("object"):
                    payment_obj = payment_obj.get("object")
            else:
                payment_obj = {}

            if not isinstance(payment_obj, dict):
                payment_obj = {}

            ext_payment_id = payment_obj.get("id") or payload.get("id") or payload.get("payment_id")
            # статус может приходить в разных полях — пытаемся угадать
            raw_status = (payment_obj.get("status") or payload.get("status") or payload.get("event") or "").strip()
            status_normalized = raw_status.lower() if isinstance(raw_status, str) else None

            # 3) Попытка найти локальную запись: сначала по Idempotence-Key из заголовков
            idemp = headers.get("Idempotence-Key") or headers.get("Idempotence-key") or headers.get("idempotence-key")
            local_payment = None

            if idemp:
                try:
                    local_payment = await self.uow.payment_repo.get_payments_by_idempotency_id(idemp)
                except AttributeError:
                    # репозиторий может не поддерживать этот метод — логируем и идём дальше
                    logger.debug("payment_repo.get_payments_by_idempotency_id missing")

            # 4) Если не нашли по идемпотенции — пробуем по внешнему payment id через возможный репо-метод
            if local_payment is None and ext_payment_id:
                # допустимые имена метода, которые могли быть в repo
                possible_getters = (
                    "get_payments_by_yookassa_id",
                    "get_payments_by_external_id",
                    "get_payments_by_payment_id",
                    "get_by_yookassa_id",
                    "get_by_external_id",
                )
                getter = None
                for name in possible_getters:
                    getter = getattr(self.uow.payment_repo, name, None)
                    if callable(getter):
                        try:
                            local_payment = await getter(ext_payment_id)
                        except Exception as e:
                            logger.debug("repo getter %s raised: %s", name, e)
                        break

            # 5) Если всё ещё не нашли — логируем и завершаем (не создаём новые записи)
            if local_payment is None:
                logger.info("Webhook: local payment not found (idemp=%s ext_id=%s). Payload: %s", idemp, ext_payment_id,
                            payload)
                return None

            # 6) Защита от двойного зачисления: если локально уже succeeded — ничего не делаем
            local_status = getattr(local_payment, "status", None)
            if local_status and str(local_status).lower() in ("succeeded", "paid", "completed"):
                logger.info("Webhook: payment %s (local id=%s) already in final state '%s', skipping", ext_payment_id,
                            getattr(local_payment, "id", None), local_status)
                return local_payment

            # 7) Если платёж успешен — зачисляем средства
            success_states = {"succeeded", "paid", "success", "completed"}
            try:
                if status_normalized in success_states:
                    # определяем сумму (провайдеры обычно дают amount: {value: "100.00", currency: "RUB"})
                    raw_amount = None
                    if "amount" in payment_obj and isinstance(payment_obj.get("amount"), dict):
                        raw_amount = payment_obj.get("amount", {}).get("value")
                    # fallback: иногда amount передается как simple field
                    raw_amount = raw_amount or payment_obj.get("sum") or payment_obj.get("amount") or getattr(
                        local_payment, "amount", None)

                    try:
                        dec_amount = Decimal(str(raw_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    except Exception:
                        # если всё плохо — берем сумму из локальной записи
                        dec_amount = Decimal(str(getattr(local_payment, "amount", 0))).quantize(Decimal("0.01"),
                                                                                                rounding=ROUND_HALF_UP)

                    # Выполняем изменение баланса — используем репозиторный вызов update_wallets_user
                    wallet_id = getattr(local_payment, "wallet_id", None)
                    if wallet_id is None:
                        logger.error("Webhook: local payment has no wallet_id (local id=%s). Can't credit.",
                                     getattr(local_payment, "id", None))
                        # но обновим статус платежа в любом случае
                        await self.uow.payment_repo.update_payments(UpdatePayments(
                            id=getattr(local_payment, "id"),
                            status=raw_status,
                            payment_id=ext_payment_id,
                            confirmation_url=(payment_obj.get("confirmation") or {}).get("confirmation_url"),
                            confirmation_type=(payment_obj.get("confirmation") or {}).get("type"),
                        ))
                        return local_payment

                    # Само зачисление: репозиторный метод принимает UpdateWallets (id, amount)
                    await self.wallet_service.update_wallets_user(UpdateWallets(
                        id=wallet_id,
                        amount=dec_amount
                    ))

                    # Обновляем локальную запись платежа (статус, внешний id, confirmation)
                    updated = await self.uow.payment_repo.update_payments(UpdatePayments(
                        id=getattr(local_payment, "id"),
                        status=raw_status,
                        payment_id=ext_payment_id,
                        confirmation_url=(payment_obj.get("confirmation") or {}).get("confirmation_url"),
                        confirmation_type=(payment_obj.get("confirmation") or {}).get("type"),
                    ))

                    logger.info("Webhook: payment %s (local id=%s) succeeded — wallet %s credited %s", ext_payment_id,
                                getattr(local_payment, "id"), wallet_id, dec_amount)
                    return updated

                else:
                    # Неуспешный / промежуточный статус — просто записываем статус и внешний id
                    updated = await self.uow.payment_repo.update_payments(UpdatePayments(
                        id=getattr(local_payment, "id"),
                        status=raw_status,
                        payment_id=ext_payment_id,
                        confirmation_url=(payment_obj.get("confirmation") or {}).get("confirmation_url"),
                        confirmation_type=(payment_obj.get("confirmation") or {}).get("type"),
                    ))
                    logger.info("Webhook: payment %s (local id=%s) updated to status '%s'", ext_payment_id,
                                getattr(local_payment, "id"), raw_status)
                    return updated
            except IntegrityError as ie:
                # Возможная гонка при зачислении/обновлении: логируем и пробрасываем для ретрая внешним веб-сервером
                logger.exception("Webhook integrity error while processing payment %s local id=%s: %s", ext_payment_id,
                                 getattr(local_payment, "id"), ie)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB integrity error")
            except Exception as e:
                logger.exception("Webhook processing failed for payment %s local id=%s: %s", ext_payment_id,
                                 getattr(local_payment, "id"), e)
                raise

        except Exception as e:
            logger.exception("Unhandled exception in webhook_api: %s", e)
            # пробрасываем ошибку выше — внешний HTTP-эндпоинт должен вернуть 500 чтобы провайдер повторил webhook
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
    """Ошибка взаимодействия с API."""
    pass


class SqlAlchemyServicePaymentApi:
    """
    Асинхронный клиент для создания/получения платежей через HTTP API.

    Args:
        http_client: базовый URL (например "https://api.yookassa.ru/v3/payments")
        secret_key: секретный ключ (используется как пароль в BasicAuth)
        shop_id: идентификатор магазина (используется как логин в BasicAuth)
        timeout: общий таймаут для запросов в секундах
        max_retries: число попыток при transient ошибках
    """
    def __init__(
        self,
        http_client: str,
        secret_key: str,
        shop_id: str,
        timeout: int = 10,
        max_retries: int = 3,
    ):
        self.http_client = http_client.rstrip("/")  # базовый URL
        self.secret_key = secret_key
        self.shop_id = shop_id
        self.timeout = timeout
        self.max_retries = max_retries

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Внутренний метод для выполнения request с retry и обработкой ошибок.
        """
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                auth = aiohttp.BasicAuth(self.shop_id, self.secret_key)
                async with aiohttp.ClientSession(auth=auth, timeout=timeout) as session:
                    async with session.request(method, url, headers=headers, json=json, params=params) as resp:
                        text = await resp.text()
                        # Попытка распарсить JSON, иначе вернуть текст
                        try:
                            data = await resp.json()
                        except Exception:
                            data = text

                        if 200 <= resp.status < 300:
                            return data
                        # Для ошибок API — бросаем ApiError с телом ответа
                        raise ApiError(f"HTTP {resp.status}: {data}")
            except (aiohttp.ClientError, asyncio.TimeoutError, ApiError) as e:
                last_exc = e
                # transient? — попробуем повторить (exponential backoff)
                if attempt < self.max_retries:
                    backoff = 2 ** (attempt - 1)
                    await asyncio.sleep(backoff)
                    continue
                # если попытки закончились — пробрасываем
                raise

        # safety net
        raise last_exc or ApiError("Unknown request error")

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
        Создаёт платёж.

        amount: Decimal | float | str — сумма (будет форматирована в "X.YY")
        return_url: URL для редиректа
        description: описание платежа
        user_id: локальный идентификатор пользователя (для описания)
        payment_id: локальный идентификатор платежа (сохраним в metadata.local_payment_id)
        idemp: идемпотентный ключ; если None — сгенерируем UUID4
        """
        # нормализуем amount в строку с двумя знаками после запятой
        try:
            dec = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"Неправильный формат суммы: {amount}") from e

        idemp = idemp or str(uuid.uuid4())

        headers = {
            "Content-Type": "application/json",
            "Idempotence-Key": idemp,
        }

        payload: Dict[str, Any] = {
            "amount": {"value": f"{dec:.2f}", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "capture": True,
            "description": description or f"Topup for user {user_id}",
            "metadata": {"local_payment_id": str(payment_id)},
        }

        url = self.http_client  # предполагаем, что это POST endpoint для создания платежа
        data = await self._request("POST", url, headers=headers, json=payload)
        return data

    async def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Получить платёж по внешнему payment_id (тот, что вернул API после создания).
        Делает GET на {base}/{payment_id}.
        """
        url = f"{self.http_client}/{payment_id}"
        data = await self._request("GET", url)
        return data

    async def get_payments_by_idemp(self, idemp: str) -> Optional[Any]:
        """
        Попытаться получить информацию по идемпотентному ключу.
        Реализация зависит от API провайдера: некоторые поддерживают поиск по заголовку
        'Idempotence-Key' при GET, другие — нет.

        Мы пробуем сделать GET на базовый endpoint с этим заголовком.
        Если API не поддерживает такую операцию, возможен ApiError или пустой ответ — метод вернёт то,
        что вернул сервер, либо None.
        """
        headers = {"Idempotence-Key": idemp}
        try:
            data = await self._request("GET", self.http_client, headers=headers)
            return data
        except ApiError:
            # Если API не поддерживает поиск по идемпотентности — вернуть None
            return None

    # Дополнительный удобный метод — поиск локального payment по metadata.local_payment_id
    async def find_by_local_payment_id(self, local_payment_id: str, page_limit: int = 50) -> Optional[Dict[str, Any]]:
        """
        Если провайдер поддерживает листинг платежей (GET base_url?limit=...), можно
        пробежать страницы и найти запись с metadata.local_payment_id == local_payment_id.
        Это универсальная, но медленная операция — зависит от API и использования пагинации.
        """
        params = {"limit": page_limit}
        next_cursor = None

        while True:
            if next_cursor:
                params["cursor"] = next_cursor
            try:
                resp = await self._request("GET", self.http_client, params=params)
            except ApiError:
                return None

            # ожидаем, что resp содержит список платежей в resp.get("items") или resp["payments"]
            items = None
            if isinstance(resp, dict):
                items = resp.get("items") or resp.get("payments") or resp.get("payments_list") or resp.get("data")
            if items is None:
                # неожиданный формат
                return None

            for item in items:
                meta = item.get("metadata") or {}
                if str(meta.get("local_payment_id")) == str(local_payment_id):
                    return item

            # пагинация — пробуем получить cursor/next
            next_cursor = None
            if isinstance(resp, dict):
                # общие места где может быть cursor/next
                next_cursor = resp.get("next_cursor") or resp.get("next") or resp.get("cursor") or resp.get("nextPageToken")
            if not next_cursor:
                break

        return None
