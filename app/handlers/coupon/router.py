from fastapi import APIRouter, HTTPException, Depends, Header, Request, Body, Form

from app.handlers.coupon.dependencies import couponServiceDep
from app.handlers.coupon.schemas import OutCoupon, CreateCouponService
from app.handlers.session.schemas import CheckSessionAccessToken
from app.method.get_token import get_token

router = APIRouter(prefix="/coupon", tags=["coupon"])


@router.get("/")
async def hub():
    return HTTPException(200, 'Status - True')


@router.post("/create_coupon", response_model=OutCoupon)
async def create_coupon(
        coupon_data: CreateCouponService,
        user_id: int,
        request: Request,
        coupon_service: couponServiceDep,
        access_token: str = Depends(get_token)
):
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token
    )

    return await coupon_service.create_coupon(coupon_data=coupon_data, check_data=CheckSessionAccessToken)


@router.post("/used_coupon", response_model=OutCoupon)
async def used_coupon(
        token: str,
        user_id: int,
        request: Request,
        coupon_service: couponServiceDep,
        access_token: str = Depends(get_token)
):
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token
    )

    return await coupon_service.used_coupon(user_id=user_id, token=token, check_data=CheckSessionAccessToken)


@router.post("/get_by_user_id", response_model=OutCoupon)
async def get_by_user_id(
        user_id: int,
        request: Request,
        coupon_service: couponServiceDep,
        access_token: str = Depends(get_token)
):
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token
    )

    return await coupon_service.get_by_user_id(user_id=user_id, check_data=CheckSessionAccessToken)


@router.post("/get_info_by_coupon_id", response_model=OutCoupon)
async def get_info_by_coupon_id(
        id: int,
        user_id: int,
        request: Request,
        coupon_service: couponServiceDep,
        access_token: str = Depends(get_token)
):
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token
    )

    return await coupon_service.get_info_by_coupon_id(id=id, check_data=CheckSessionAccessToken)

@router.post("/get_by_token_hash", response_model=OutCoupon)
async def get_by_token_hash(
        token: str,
        user_id: int,
        request: Request,
        coupon_service: couponServiceDep,
        access_token: str = Depends(get_token)
):
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token
    )

    return await coupon_service.get_by_token_hash(token=token, check_data=CheckSessionAccessToken)


