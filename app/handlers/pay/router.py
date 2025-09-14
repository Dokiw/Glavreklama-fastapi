import logging
from typing import Dict, Any
# paymentServiceDep должен быть Annotated/Depends на SqlAlchemyServicePayment
from typing import Optional, List

from fastapi import APIRouter, Request, Depends, Body

from app.handlers.pay.dependencies import paymentServiceDep  # <- проверь путь, если у тебя иначе
from app.handlers.pay.dependencies import walletServiceDep  # <- проверь путь
from app.handlers.pay.schemas import (
    CreatePaymentsService,
    UpdatePayments,
    PaymentsOut, CreatePaymentsOut,
)
from app.handlers.pay.schemas import (
    UpdateWalletsService,
    OutWallets,
)
from app.handlers.session.schemas import CheckSessionAccessToken
from app.main import logger
from app.method.get_token import get_token

router = APIRouter(prefix="/payment", tags=["payment"])


@router.get("/")
async def hub():
    return {"status": True}





@router.post("/create_payment", response_model=Optional[CreatePaymentsOut])
async def create_payment(
    user_id: int,
    wallet_id: int,
    amount: float,
    return_url: str,
    payment_service: paymentServiceDep,
    confirmation_type: Optional[str] = None,
    description: Optional[str] = None,
    currency: Optional[str] = "RUB",
    capture: Optional[bool] = True,
    metadata_payments: Optional[Dict[str, Any]] = None,
    request: Request = None,
    access_token: str = Depends(get_token),
):
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token,
    )

    create_data = CreatePaymentsService(
        user_id=user_id,
        wallet_id=wallet_id,
        amount=amount,
        return_url=return_url,
        confirmation_type=confirmation_type,
        description=description,
        currency=currency,
        capture=capture,
        metadata_payments=metadata_payments,
    )

    return await payment_service.create_payments(create_data=create_data, check_data=csat)


@router.post("/update_payment", response_model=Optional[PaymentsOut])
async def update_payment(
    payment_service: paymentServiceDep,
    update_data: UpdatePayments = Body(...),
    user_id: int = None,
    request: Request = None,
    access_token: str = Depends(get_token),
):
    """
    update_data: передаём UpdatePayments (в body) — содержит id и поля для обновления.
    user_id: передаём для валидации сессии (если нужен).
    """
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token,
    )

    return await payment_service.update_payments(update_data=update_data, check_data=csat)


@router.post("/get_by_user_id", response_model=Optional[List[PaymentsOut]])
async def get_by_user_id(
    payment_service: paymentServiceDep,
    user_id: int,
    request: Request,
    access_token: str = Depends(get_token),
):
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token,
    )

    return await payment_service.get_payments_by_user_id(check_data=csat)


@router.post("/get_by_id", response_model=Optional[PaymentsOut])
async def get_by_id(
    payment_service: paymentServiceDep,
    payments_id: str,
    user_id: int,
    request: Request,
    access_token: str = Depends(get_token),
):
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token,
    )

    return await payment_service.get_payments_by_id(payments_id=payments_id, check_data=csat)


@router.post("/get_by_idempotency", response_model=Optional[PaymentsOut])
async def get_by_idempotency(
    payment_service: paymentServiceDep,
    idempotency_id: str,
    user_id: int,
    request: Request,
    access_token: str = Depends(get_token),
):
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token,
    )

    return await payment_service.get_payments_by_idempotency_id(idempotency_id=idempotency_id, check_data=csat)


@router.post("/webhook", response_model=Optional[PaymentsOut])
async def webhook(
    payment_service: paymentServiceDep,
    request: Request,
):
    """
    Вебхук от провайдера — без проверки токена.
    Берём json, заголовки и remote_addr, передаём в сервисный обработчик webhook_api.
    Возвращаем то, что вернул сервис (или None).
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    logger.info("Webhook payload: %s", payload)

    headers = {k: v for k, v in request.headers.items()}
    remote_addr = None
    if request.client:
        remote_addr = request.client.host

    result = await payment_service.webhook_api(payload=payload, headers=headers, remote_addr=remote_addr)
    # Обычно для вебхука обычно возвращают простой 200 или объект; возвращаем объект сервиса если есть
    return result


@router.post("/create_or_get_wallet", response_model = Optional[OutWallets])
async def create_or_get_wallet(
    wallet_service: walletServiceDep,
    user_id: int,
    request: Request,
    access_token: str = Depends(get_token),
):
    """
    Создать кошелёк для user_id, либо вернуть существующий.
    """
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token,
    )

    return await wallet_service.create_wallet_or_get_wallet(check_data=csat)


@router.post("/update_wallet", response_model = Optional[OutWallets])
async def update_wallet(
    wallet_service: walletServiceDep,
    update_data: UpdateWalletsService = Body(...),
    admin_user_id: int = None,
    request: Request = None,
    access_token: str = Depends(get_token),
):
    """
    Обновление баланса кошелька (admin-like operation).
    update_data должен быть UpdateWalletsService (id, amount, reason и т.д.)
    admin_user_id — пользователь, от имени которого выполняется операция (для проверки сессии).
    """
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=admin_user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token,
    )

    return await wallet_service.update_wallets_user(update_data=update_data, check_data=csat)


@router.post("/get_wallet_by_id", response_model = Optional[OutWallets])
async def get_wallet_by_id(
    wallet_service: walletServiceDep,
    id: int,
    user_id: int,
    request: Request,
    access_token: str = Depends(get_token),
):
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token,
    )

    return await wallet_service.get_wallet_by_id(id=id, check_data=csat)