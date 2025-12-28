import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends,  Request

from app.handlers.coupon.dependencies import couponServiceDep
from app.handlers.coupon.schemas import OutCoupon, CreateCouponService
from app.handlers.session.schemas import CheckSessionAccessToken
from app.method.get_token import get_token

router = APIRouter(prefix="/coupon", tags=["coupon"])


@router.get("/")
async def hub():
    """
    Используется для возврата 200-го статуса на главной странице FastApi()
    :return:
    """
    return HTTPException(200, 'Status - True')


@router.post("/create_coupon", response_model=Optional[OutCoupon] | datetime.datetime)
async def create_coupon(
        name: str,
        user_id: int,
        request: Request,
        coupon_service: couponServiceDep,
        access_token: str = Depends(get_token)
):
    """
    Создание купона, принимает имя купона и id пользователя, собирает ip и user-agent,
    формирует данные проверки сессии и данные для создания купона, передаёт их в сервис
    и возвращает результат операции
    :param name:
    :param user_id:
    :param request:
    :param coupon_service:
    :param access_token:
    :return:
    """
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token
    )

    ccs = CreateCouponService(
        user_id=user_id,
        description=None,
        name=name,
        status=None
    )

    return await coupon_service.create_coupon(coupon_data=ccs, check_data=csat)


@router.post("/used_coupon", response_model=Optional[OutCoupon])
async def used_coupon(
        token: str,
        user_id: int,
        request: Request,
        coupon_service: couponServiceDep,
        access_token: str = Depends(get_token)
):
    """
    Использование купона, принимает токен купона и id пользователя, собирает ip и user-agent,
    формирует данные проверки сессии, передаёт их в сервис и возвращает результат операции
    :param token:
    :param user_id:
    :param request:
    :param coupon_service:
    :param access_token:
    :return:
    """
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token
    )

    return await coupon_service.used_coupon(token=token, check_data=csat)

@router.post("/used_any_coupon", response_model=Optional[OutCoupon])
async def used_any_coupon(
        token: str,
        user_id: int,
        user_admin_id: int,
        request: Request,
        coupon_service: couponServiceDep,
        access_token: str = Depends(get_token)
):
    """

    :param token:
    :param user_id:
    :param user_admin_id:
    :param request:
    :param coupon_service:
    :param access_token:
    :return:
    """
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_admin_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token
    )

    return await coupon_service.used_any_coupon(user_id=user_id, token=token, check_data=csat)


@router.post("/get_by_user_id", response_model=Optional[List[OutCoupon]])
async def get_by_user_id(
        user_id: int,
        request: Request,
        coupon_service: couponServiceDep,
        access_token: str = Depends(get_token)
):
    """
    Получение купонов пользователя, принимает id пользователя, собирает ip и user-agent,
    формирует данные проверки сессии, передаёт их в сервис и возвращает результат операции
    :param user_id:
    :param request:
    :param coupon_service:
    :param access_token:
    :return:
    """
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token
    )

    return await coupon_service.get_by_user_id(check_data=csat)


@router.post("/get_by_any_user_id", response_model=Optional[List[OutCoupon]])
async def get_by_any_user_id(
        user_id: int,
        admin_user_id: int,
        request: Request,
        coupon_service: couponServiceDep,
        access_token: str = Depends(get_token)
):
    """

    :param user_id:
    :param admin_user_id:
    :param request:
    :param coupon_service:
    :param access_token:
    :return:
    """
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=admin_user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token
    )

    return await coupon_service.get_by_any_user_id(id_user=user_id, check_data=csat)


@router.post("/get_info_by_coupon_id", response_model=Optional[OutCoupon])
async def get_info_by_coupon_id(
        id: int,
        user_id: int,
        request: Request,
        coupon_service: couponServiceDep,
        access_token: str = Depends(get_token)
):
    """
    Получение информации о купоне по id, принимает id купона и id пользователя,
    собирает ip и user-agent, формирует данные проверки сессии, передаёт их в сервис
    и возвращает результат операции
    :param id:
    :param user_id:
    :param request:
    :param coupon_service:
    :param access_token:
    :return:
    """
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token
    )

    return await coupon_service.get_info_by_coupon_id(id=id, check_data=csat)


@router.post("/get_by_token_hash", response_model=Optional[OutCoupon])
async def get_by_token_hash(
        token: str,
        user_id: int,
        request: Request,
        coupon_service: couponServiceDep,
        access_token: str = Depends(get_token)
):
    """
    Получение купона по хэшу токена, принимает токен и id пользователя, собирает ip и user-agent,
    формирует данные проверки сессии, передаёт их в сервис и возвращает результат операции
    :param token:
    :param user_id:
    :param request:
    :param coupon_service:
    :param access_token:
    :return:
    """
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token
    )

    return await coupon_service.get_by_token_hash(token=token, check_data=csat)
