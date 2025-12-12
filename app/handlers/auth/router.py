from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Body, Form

from app.handlers.auth.dependencies import AuthServiceDep
from app.handlers.auth.schemas import LogInUser, UserCreate, AuthResponse, RoleUser, AuthResponseProvide, PaginateUser, \
    LogInUserBot
from app.handlers.providers.schemas import ProviderLoginRequest
from app.handlers.session.schemas import CheckSessionAccessToken
from app.method.get_token import get_token

router = APIRouter(prefix="/auth", tags=["Auth"])



@router.get("/")
async def hub():
    """
    Используется для возврата 200-го статуса на главной странице FastApi()
    :return:
    """
    return HTTPException(200, 'Status - True')

@router.post("/login", response_model=AuthResponse)
async def login(
        oauth_client: str,
        log_in_user: LogInUser,
        request: Request,
        auth_service: AuthServiceDep
):
    """
    Необходимый метод для авторизации в системе, собирает данные о пользователе,
    передает их в сервис авторизации и возвращает ответ
    :param oauth_client:
    :param log_in_user:
    :param request:
    :param auth_service:
    :return:
    """
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    return await auth_service.login(log_in_user, ip, user_agent=user_agent, oauth_client=oauth_client)


@router.post("/login_via_bots", response_model=AuthResponse)
async def login_via_bots(
        log_in_user: LogInUserBot,
        request: Request,
        auth_service: AuthServiceDep
):
    """
    Необходимо для авторизации через бота телеграм, собирает данные о пользователе,
    передает их в сервис авторизации и возвращает ответ
    :param log_in_user:
    :param request:
    :param auth_service:
    :return:
    """

    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    return await auth_service.login_via_bots(log_in_user, ip, user_agent=user_agent)


@router.post("/register", response_model=AuthResponse)
async def register(oauth_client: str, user_create: UserCreate, request: Request, auth_service: AuthServiceDep):
    """
    Необходим для регистрации нового пользователя, собирает данные о пользователе,
    передает их в сервис регистрации и возвращает ответ
    :param oauth_client:
    :param user_create:
    :param request:
    :param auth_service:
    :return:
    """
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    return await auth_service.register(oauth_client=oauth_client, user_data=user_create, ip=ip, user_agent=user_agent)


# В текущий момент не нужен
# @router.post("/role", response_model=RoleUser)
# async def indicate(auth_service: AuthServiceDep,user_id: int, request: Request, access_token: str = Depends(get_token)):
#     # Получаем IP и User-Agent из запроса
#     ip = request.client.host
#     user_agent = request.headers.get("user-agent", "")
#
#     return await auth_service.identification(user_id, ip, user_agent, access_token)


@router.post("/logout")
async def logout(auth_service: AuthServiceDep, id_user: int, request: Request, access_token: str = Depends(get_token)):
    # Получаем IP и User-Agent из запроса
    """
    Выход пользователя из системы, собирает данные о пользователе,
    передает их в сервис выхода из системы и возвращает ответ
    :param auth_service:
    :param id_user:
    :param request:
    :param access_token:
    :return:
    """
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    return await auth_service.logout(id_user=id_user, ip=ip, user_agent=user_agent, access_token=access_token)


@router.post("/login_provider", response_model=AuthResponseProvide)
async def register(oauth_client: str, request: Request, auth_service: AuthServiceDep,
                   login_data: ProviderLoginRequest = Body()):
    """
    Необходима для авторизации через внешний провайдер - telegram, google, собирает данные о пользователе,
    передает их в сервис авторизации внешнего провайдера и возвращает ответ
    :param oauth_client:
    :param request:
    :param auth_service:
    :param login_data:
    :return:
    """
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    return await auth_service.login_from_provider(client_id=oauth_client, user_data=login_data, ip=ip,
                                                  user_agent=user_agent)


@router.post("/register_provider", response_model=AuthResponseProvide)
async def register_from_provider_or_get(
        oauth_client: str,
        request: Request,
        auth_service: AuthServiceDep,
        payload: str = Form(...),
):
    """
    Регистрация пользователя через внешний провайдер - telegram, google, собирает данные о пользователе,
    передает их в сервис регистрации через внешний провайдер и возвращает ответ
    :param oauth_client:
    :param request:
    :param auth_service:
    :param payload:
    :return:
    """
    init_data_str = payload
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    return await auth_service.register_from_provider_or_get(init_data_str, ip, user_agent, oauth_client)


@router.post("/get_users", response_model=PaginateUser)
async def get_users(
        auth_service: AuthServiceDep,
        id_user: int,
        offset: int,
        limit: Optional[int],
        request: Request,
        access_token: str = Depends(get_token),
):
    """
    Получение списка пользователей. Принимает идентификатор пользователя, параметры пагинации
    и токен доступа. Собирает ip и user-agent клиента, передаёт всё в сервис получения пользователей
    и возвращает список пользователей
    :param auth_service:
    :param id_user:
    :param offset:
    :param limit:
    :param request:
    :param access_token:
    :return:
    """
    # Получаем IP и User-Agent из запроса
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    return await auth_service.get_users(id_user=id_user, ip=ip, offset=offset, limit=limit,
                                        user_agent=user_agent, access_token=access_token)


@router.post("/get_roles", response_model=List[Optional[RoleUser]])
async def get_roles(
        auth_service: AuthServiceDep,
        user_id: int,
        request: Request,
        access_token: str = Depends(get_token),
):
    """
    Получение ролей пользователя. Принимает id пользователя и токен доступа,
    собирает ip и user-agent клиента, формирует объект проверки сессии,
    передаёт данные в сервис получения ролей и возвращает список ролей
    :param auth_service:
    :param user_id:
    :param request:
    :param access_token:
    :return:
    """
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")


    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token,
    )

    return await auth_service.get_roles(check_data=csat)


@router.post("/update_role")
async def update_role(
        auth_service: AuthServiceDep,
        role_id: int,
        user_id: int,
        request: Request,
        access_token: str = Depends(get_token),
):
    """
    Обновление роли пользователя. Принимает id роли и id пользователя,
    собирает ip и user-agent клиента, формирует данные проверки сессии,
    передаёт их в сервис обновления роли и возвращает ответ
    :param auth_service:
    :param role_id:
    :param user_id:
    :param request:
    :param access_token:
    :return:
    """
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    csat = CheckSessionAccessToken(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent,
        access_token=access_token,
    )

    return await auth_service.update_role(role_id=role_id, check_data=csat)

