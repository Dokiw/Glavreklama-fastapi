from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Header, Request, Body

from app.handlers.auth.schemas import LogInUser, UserCreate, LogOutUser, AuthResponse, RoleUser
from app.handlers.auth.dependencies import AuthServiceDep, get_auth_service_dep, get_auth_service
from app.handlers.auth.service import SqlAlchemyAuth
from app.handlers.providers.schemas import ProviderLoginRequest

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/")
async def hub():
    return HTTPException(200, 'Status - True')


@router.post("/login", response_model=AuthResponse)
async def login(
        log_in_user: LogInUser,
        request: Request,
        auth_service: AuthServiceDep
):
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    return await auth_service.login(log_in_user, ip, user_agent=user_agent)


@router.post("/register", response_model=AuthResponse)
async def register(user_create: UserCreate, request: Request, auth_service: AuthServiceDep):
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    return await auth_service.register(user_data=user_create, ip=ip, user_agent=user_agent)


@router.post("/role", response_model=RoleUser)
async def indicate(user_id: int, request: Request, access_token: str, auth_service: AuthServiceDep):
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    return await auth_service.identification(user_id, ip, user_agent, access_token)


@router.post("/logout")
async def logout(id_user: int, request: Request, access_token: str, auth_service: AuthServiceDep):
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    return await auth_service.logout(id_user=id_user, ip=ip, user_agent=user_agent, access_token=access_token)


@router.post("/login_provider", response_model=AuthResponse)
async def register(request: Request, auth_service: AuthServiceDep, login_data: ProviderLoginRequest = Body()):
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    return await auth_service.login_from_provider(user_data=login_data, ip=ip, user_agent=user_agent)


@router.post("/register_provider", response_model=Dict[str, Any])
async def register_from_provider_or_get(
        request: Request,
        auth_service: AuthServiceDep,
):
    raw_body = await request.body()  # <- оригинальная байтовая строка, важна для диагностики
    try:
        parsed = await request.json()
    except Exception:
        parsed = None

    if parsed is None:
        return {"detail": "Не удалось распарсить JSON тела", "raw_body": raw_body.decode("utf-8", errors="replace")}

    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    return await auth_service.register_from_provider_or_get(parsed, ip, user_agent)
