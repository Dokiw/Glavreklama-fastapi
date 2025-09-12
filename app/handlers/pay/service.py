import asyncio
import datetime
import hashlib
import logging
import uuid
from datetime import time
import datetime as dt
from typing import Optional, List

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
    def __init__(self, uow: IUnitOfWorkPayment, session_service: AsyncSessionService):
        self.uow = uow
        self.session_service = session_service

    @transactional()
    async def create_payments(self, create_data: CreatePaymentsService, check_data: CheckSessionAccessToken) -> (
            CreatePaymentsOut):
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
        return result

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

class SqlAlchemyServicePaymentApi(AsyncApiPaymentService):

    #todo - подключить апи
    async def create_payment(self):
        payload: Dict[str, Any] = {
            "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "capture": True,
            "description": description or f"Topup for user {user_id}",
            "metadata": {"local_payment_id": str(new_payment.id)},
        }
        headers = {"Idempotence-Key": idemp, "Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(YOOKASSA_API, json=payload, headers=headers, auth=(SHOP_ID, SECRET_KEY),
                                         timeout=15.0)
            except Exception as e:
            new_payment.status = "FAILED"
            new_payment.attempts = (new_payment.attempts or 0) + 1
            await self.db.commit()
                raise HTTPException(status_code=502, detail=str(e))

        if resp.status_code >= 400:
            new_payment.status = "FAILED"
        new_payment.attempts = (new_payment.attempts or 0) + 1

        raise HTTPException(status_code=502, detail=f"Provider error: {resp.status_code} {resp.text}")

        return ch



